from collections import Counter
from typing import cast, TypeVar

from parser.objects import Variable, Operator, ParenthesizedGroup, RelationalOperator, Fraction, Group
from parser.utility import gts

from .logging import _log
from .datatype import Maybe_RO, CompleteEquation
from .core import Result, NoSolution
from .errors import SolutionNotFoundError
from .logging import set_log_equation

T = TypeVar("T", bound=Maybe_RO)


def clean_equation(parsed_group: T, base: bool = True) -> T:
    for index, group in enumerate(parsed_group):
        if not base and isinstance(group, RelationalOperator):
            raise TypeError("Relational operators cannot be inside power or ParenthesizedGroup.")

        if isinstance(group, ParenthesizedGroup):
            group.groups = clean_equation(group.groups, base=False)
            group.power = clean_equation(group.power, base=False)
        elif isinstance(group, Group):
            group.power = clean_equation(group.power, base=False)
        if index == 0:
            continue
        before = parsed_group[index - 1]
        if isinstance(group, (Group, ParenthesizedGroup)) and isinstance(before, (Group, ParenthesizedGroup)):
            if isinstance(group, ParenthesizedGroup):
                if group.is_negative:
                    parsed_group.insert(index, Operator.Add)
                else:  # For multiplications with ParenthesizedGroup without the "*" Operator
                    parsed_group.insert(index, Operator.Mul)
            else:  # For possibly negative values or double negative sign ('--')
                parsed_group.insert(index, Operator.Add)
    if base:
        _log.info("Finished cleaning equation, got '%s'", gts(parsed_group))
    return parsed_group


class EquationIdentity:
    def __init__(self):
        self.variable_count: dict[Variable, int] = {}
        self.relational_operators: list[tuple[RelationalOperator, int]] = []
        self.fractions: dict[Fraction, int] = {}
        self.parenthesized_groups: dict[ParenthesizedGroup, int] = {}
        self.has_powers: bool = False


def get_equation_identity(parsed_groups: Maybe_RO) -> EquationIdentity:
    identity = EquationIdentity()
    for index, group in enumerate(parsed_groups):
        if isinstance(group, RelationalOperator):
            identity.relational_operators.append((group, index))

        if isinstance(group, (RelationalOperator, Operator)):
            continue
        if isinstance(group, (Group, ParenthesizedGroup)):
            if group.power:
                identity.has_powers = True
                power = get_equation_identity(group.power)
                base = Counter(identity.variable_count)
                base.update(power.variable_count)
                identity.variable_count = dict(base)

        if isinstance(group, Fraction):
            identity.fractions[group] = index
            numerator, denominator = get_equation_identity(group.numerator), get_equation_identity(group.denominator)
            base = Counter(identity.variable_count)
            base.update(numerator.variable_count)
            base.update(denominator.variable_count)
            identity.variable_count = dict(base)

        elif isinstance(group, Group):
            if (var := group.variable) is not None:  # There's variable
                identity.variable_count[var] = identity.variable_count.get(var, 0) + 1

        elif isinstance(group, ParenthesizedGroup):
            identity.parenthesized_groups[group] = index
            inside = get_equation_identity(group.groups)
            base = Counter(identity.variable_count)
            base.update(inside.variable_count)
            identity.variable_count = dict(base)

    return identity


def convert_division_to_fraction(groups: CompleteEquation):  # Performs a detailed-lookup and might be slow
    new: CompleteEquation = []
    index = 0
    for group in groups:
        if isinstance(group, (ParenthesizedGroup, Group)) and group.power:
            group.power = convert_division_to_fraction(group.power)
        if isinstance(group, Operator) and group.symbol == "/":
            group = Fraction(numerator=[new.pop(-1)], denominator=[groups.pop(index + 1)])
        elif isinstance(group, ParenthesizedGroup):
            group.groups = convert_division_to_fraction(group.groups)
        new.append(group)
        index += 1
    _log.info("Finished converting division to fraction, got '%s'", gts(new))
    return new


def determine_equation_type(groups: CompleteEquation, identity: EquationIdentity | None = None, base: bool = False) -> Result:
    set_log_equation(gts(groups))
    _log.info("Attempting to solve '%s'", gts(groups))

    identity = identity or get_equation_identity(groups)
    if len(identity.variable_count) == 0 and not identity.relational_operators:  # Basic PEMDAS
        from .solve_basic import solve_basic

        _log.info("Identified as [BASIC PEMDAS]")
        _log.info("[START OF SOLVING PEMDAS]")
        return Result(solve_basic(groups))

    elif len(identity.variable_count) == 0 and identity.relational_operators:  # Basic PEMDAS with relational operator
        # Evaluates every Relational Operator left hand side and right hand side accordingly
        # We don't evaluate the first expression with rest of other expression
        from .solve_basic import solve_basic
        _log.info("Identified as [BASIC PEMDAS with RELATIONAL OPERATOR]")
        _log.info("[START OF SOLVING PEMDAS WITH RELATIONAL OPERATOR]")
        cond, count, last = (), -1, None
        for ro, index in identity.relational_operators:
            count += 1
            next_ro = _next[count + 1][1] if count != len(_next := identity.relational_operators) - 1 else len(groups)
            after = solve_basic(groups[index + 1:next_ro])
            if count == 0:  # First element
                last = solve_basic(groups[:index])
            cond += (ro(first=last, second=after),)
            last = after
        return Result(all(cond))

    elif len(identity.variable_count) == 1 and identity.relational_operators:
        from .solve_algebra import solve_algebra, divide_both_side

        _log.info("Identified as [BASIC ALGEBRA]")
        _log.info("[START OF SOLVING ALGEBRA]")

        # In the format of <variable> = <non-variable>
        identity = get_equation_identity(groups)
        if len(groups) == 3 and list(identity.variable_count.values())[0] == 1 and isinstance(groups[0], Group) and not identity.has_powers and not identity.parenthesized_groups:
            if groups[0].number.is_negative:
                groups = divide_both_side(groups, -1)
            result = cast(tuple[Group, RelationalOperator, Group], tuple(divide_both_side(groups)))
            if (var_obj := (var_group := result[0]).variable) is None:
                raise TypeError
            # In the format of n<variable> = <non-variable>, where n > 1 and non-variable != 0
            if (non_var := result[2]).get_value() != 0 and var_group.number.value != 1:
                try:
                    fraction = Fraction(numerator=[non_var], denominator=[Group.from_value(var_group.get_value())])
                except ZeroDivisionError:
                    return Result({var_obj: NoSolution()})  # For `0x = <non-var>` cases
                return Result({var_obj: fraction})
            return Result({var_obj: non_var.get_value()})

        solved = solve_algebra(convert_division_to_fraction(groups) if base else groups)
        if isinstance(solved, Result):
            return solved
        try:
            return determine_equation_type(solved)  # Keep recurring until it's found, otherwise, raise RecursionError
        except RecursionError:
            raise SolutionNotFoundError(solved) from None

    raise NotImplementedError("Problem of that type is not supported yet.")
