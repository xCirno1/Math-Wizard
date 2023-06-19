import logging

from decimal import Decimal
from parser import Variable, Operator, ParenthesizedGroup, RelationalOperator, gts, Fraction

from .solve_basic import solve_basic
from .solve_algebra import solve_algebra
from .datatype import Maybe_RO, CompleteEquation

_log = logging.getLogger(__name__)


class EquationIdentity:
    def __init__(self):
        self.variable_count: dict[Variable, int] = {}
        self.relational_operators: list[tuple[RelationalOperator, int]] = []


def get_equation_identity(parsed_groups: Maybe_RO) -> EquationIdentity:
    identity = EquationIdentity()
    for index, group in enumerate(parsed_groups):
        if isinstance(group, RelationalOperator):
            identity.relational_operators.append((group, index))

        if isinstance(group, (RelationalOperator, Operator, ParenthesizedGroup, Fraction)):
            continue

        if (var := group.variable) is not None:  # There's variable
            identity.variable_count[var] = identity.variable_count.get(var, 0) + 1

    return identity


def convert_division_to_fraction(groups: CompleteEquation):
    _log.info("Converting division to fraction of equation '%s'", gts(groups))
    new: CompleteEquation = []
    index = 0
    for group in groups:
        if isinstance(group, Operator) and group.symbol == "/":
            new.append(Fraction(numerator=[new.pop(-1)], denominator=[groups.pop(index + 1)]))  # type: ignore
        else:
            new.append(group)
        index += 1
    _log.info("Finished converting, got '%s'", gts(groups))
    return new


def determine_equation_type(parsed_groups: CompleteEquation) -> Decimal | bool | list:
    _log.info("Determining equation type...")
    identity = get_equation_identity(parsed_groups)

    if len(identity.variable_count) == 0 and not identity.relational_operators:  # Basic PEMDAS
        _log.info("Identified as [BASIC PEMDAS]")
        _log.info("[START OF SOLVING PEMDAS]")
        return solve_basic(parsed_groups)  # type: ignore  # Need to find a way to fix the hints

    elif len(identity.variable_count) == 0 and identity.relational_operators:  # Basic PEMDAS with relational operator
        _log.info("Identified as [BASIC PEMDAS with RELATIONAL OPERATOR]")
        relational_operator, index = identity.relational_operators[0]  # TODO: Allow multiple relational operators
        first, second = parsed_groups[:index], parsed_groups[index + 1:]
        _log.info("[START OF SOLVING PEMDAS WITH RELATIONAL OPERATOR]")
        return relational_operator(first=solve_basic(first), second=solve_basic(second))  # type: ignore

    elif len(identity.variable_count) == 1 and identity.relational_operators:
        _log.info("Identified as [BASIC ALGEBRA]")
        parsed_groups = convert_division_to_fraction(parsed_groups)
        _log.info("[START OF SOLVING ALGEBRA]")
        return solve_algebra(parsed_groups)

    raise NotImplementedError
