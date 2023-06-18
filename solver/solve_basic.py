import logging
import typing

from decimal import Decimal

from parser import Group, Operator, ParenthesizedGroup, Number, gts
from .core import Positions
from .datatype import mul_and_div, No_RO

_log = logging.getLogger(__name__)


def create_new_group(rv1: Decimal, rv2: Decimal | None = None, operator: Operator | None = None, power: No_RO | None = None):
    if rv2 is None and operator is None:
        result = rv1
    elif operator is None:
        raise TypeError("Parameter 'rv2' must not given if parameter 'operator' is not given.")
    elif rv2 is None:
        raise TypeError("Parameter 'operator' must not given if parameter 'rv2' is not given.")
    else:
        if operator.symbol == "*":
            result = rv1 * rv2
        elif operator.symbol == "/":
            result = rv1 / rv2
        elif operator.symbol == "+":
            result = rv1 + rv2
        else:
            raise TypeError("Unsupported operator.")
    try:
        whole, dec = str(result).split(".")
    except ValueError:
        whole, dec = str(result), 0
    num = Number.from_data(value=Decimal(abs(int(whole))), decimal=f"0.{dec}", is_negative=whole[0] == "-")
    group = Group.from_data(num)
    if power is not None:
        group.power = power
    return group


def combine_groups(positions, parsed_groups, operator):
    if operator == mul_and_div:
        index, operator = list(positions.get_mul_and_div_pos().items())[0]
    elif operator == Operator("+"):
        index = positions.get_add_pos()[0]
    else:
        raise NotImplementedError
    before = typing.cast(Group, parsed_groups[index - 1]).get_value()
    after = typing.cast(Group, parsed_groups[index + 1]).get_value()
    parsed_groups.insert(index - 1, create_new_group(before, after, operator))
    del parsed_groups[index:index + 3]


def calculate_group_power(group: Group, calculated_power) -> Decimal:
    rv = group.get_value()
    return -(rv ** calculated_power) if rv < 0 else (rv ** calculated_power)


def solve_basic(parsed_groups: No_RO) -> Decimal | int:
    positions = Positions.from_data(parsed_groups)
    parenthesized_groups, operators = positions.parent_loc, positions.operators
    _log.info("Calculating parentheses...")
    for i in parenthesized_groups:  # The index here is static, so we don't need to re-calculate it
        if isinstance(par := parsed_groups[i], ParenthesizedGroup):  # Type checking purposes
            power = par.power
            result = solve_basic(par.groups)
            parsed_groups[i] = create_new_group(Decimal(-result if par.is_negative else result), power=power)
    _log.info("Finished calculating parentheses, got '%s'", gts(parsed_groups))

    positions.update_data(parsed_groups)

    _log.info("Calculating powers...")
    for i in positions.existing_powers:
        if isinstance((group := parsed_groups[i]), Group):
            result = solve_basic(group.power)
            parsed_groups[i] = create_new_group(calculate_group_power(group, result))
    _log.info("Finished calculating powers, got '%s'", gts(parsed_groups))

    _log.info("Calculating multiplies and divisions...")
    for _ in positions.get_mul_and_div_pos():
        positions.update_data(parsed_groups)
        combine_groups(positions, parsed_groups, mul_and_div)
    _log.info("Finished calculating multiplies and divisions, got '%s'", gts(parsed_groups))

    _log.info("Calculating additions and subtractions...")
    for _ in positions.get_add_pos():
        positions.update_data(parsed_groups)
        combine_groups(positions, parsed_groups, Operator("+"))
    _log.info("Finished calculating additions and subtractions, got '%s'", gts(parsed_groups))

    if len(parsed_groups) == 1:
        return typing.cast(Group, parsed_groups[0]).get_value()

    raise NotImplementedError("There's a bug here or the input is invalid")
