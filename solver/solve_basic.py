from decimal import Decimal
from typing import cast

from parser.objects import Group, Operator, Fraction, ParenthesizedGroup, Number
from parser.utility import gts, truncate_trailing_zero

from .core import Positions
from .datatype import No_RO
from .logging import _log


def convert_fraction_to_division(positions: Positions) -> No_RO:
    new = []
    for group in positions.groups:
        if isinstance(group, Fraction):
            new += group.numerator + [Operator.Div] + group.denominator
            continue
        new.append(group)
    return new


def create_new_group(v1: Decimal, v2: Decimal | None = None, operator: Operator | None = None, power: No_RO | None = None):
    if v2 is None and operator is None:
        result = v1
    elif operator is None:
        raise TypeError("Parameter 'rv2' must not be given if parameter 'operator' is not given.")
    elif v2 is None:
        raise TypeError("Parameter 'operator' must not be given if parameter 'rv2' is not given.")
    else:
        match operator.symbol:
            case "*": result = v1 * v2
            case "/": result = v1 / v2
            case "+": result = v1 + v2
            case _: raise TypeError("Unsupported operator.")
    try:
        whole, dec = f"{result.normalize():f}".split(".")
    except ValueError:
        whole, dec = str(truncate_trailing_zero(result)), 0
    num = Number.from_data(value=abs(Decimal(whole)), decimal=f"0.{dec}", is_negative=whole[0] == "-")
    group = Group.from_data(num)
    if power is not None:
        group.power = power
    return group


def combine_groups(positions: Positions, parsed_groups: No_RO, is_addition: bool):
    # If is_addition is True, Operator will be "+" else it is mul_and_div
    if not is_addition:
        index, operator = list(positions.get_mul_div_pos().items())[0]
    elif is_addition:
        operator = Operator.Add
        index = positions.operators[operator][0]
    else:
        raise NotImplementedError
    before = cast(Group, parsed_groups[index - 1]).get_value()
    after = cast(Group, parsed_groups[index + 1]).get_value()
    parsed_groups.insert(index - 1, create_new_group(before, after, operator))
    del parsed_groups[index:index + 3]


def solve_basic(parsed_groups: No_RO) -> Decimal:
    positions = Positions(parsed_groups)
    if positions.fractions:
        parsed_groups = convert_fraction_to_division(positions)
    for i in positions.parent_loc:  # The index here is static, so we don't need to re-calculate it
        if isinstance(par := parsed_groups[i], ParenthesizedGroup):  # Type checking purposes
            result = solve_basic(par.groups)
            if par.power:  # We handle powers in PG differently from normal Group
                result = cast(Group, par.groups[0]).get_value() ** solve_basic(par.power)
                par.power = []
            parsed_groups[i] = create_new_group(Decimal(-result if par.is_negative else result), power=par.power)
    _log.info("Finished calculating parentheses, got '%s'", gts(parsed_groups))

    positions.update_data(parsed_groups)

    for i in positions.existing_powers:
        if isinstance((group := parsed_groups[i]), Group):
            power = solve_basic(group.power)
            op = -1 if group.number.is_negative else 1
            parsed_groups[i] = create_new_group(op * abs(group.get_value()) ** power)
    _log.info("Finished calculating powers, got '%s'", gts(parsed_groups))

    for _ in positions.operators.get(Operator.Mul, []) + positions.operators.get(Operator.Div, []):
        positions.update_data(parsed_groups)
        combine_groups(positions, parsed_groups, is_addition=False)
    _log.info("Finished calculating multiplies and divisions, got '%s'", gts(parsed_groups))

    for _ in positions.operators.get(Operator.Add, []):
        positions.update_data(parsed_groups)
        combine_groups(positions, parsed_groups, is_addition=True)
    _log.info("Finished calculating additions and subtractions, got '%s'", gts(parsed_groups))

    if len(parsed_groups) == 1:
        return cast(Group, parsed_groups[0]).get_value()
    elif not len(parsed_groups):  # Empty result
        return None  # type: ignore  # for direct call on solve_basic

    raise NotImplementedError("There's a bug here or the input is invalid")
