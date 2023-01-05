import typing

from decimal import Decimal

from parser import Group, Operator, ParenthesizedGroup, Number
from . import datatype


class Positions:
    def __init__(self, parsed_groups: list[Group | Operator | ParenthesizedGroup]):
        self.groups = parsed_groups
        self.parent_loc = []
        self.operators = {}
        self.existing_powers = []

    def get_mul_and_div_pos(self):
        mul, div = self.operators.get(Operator("*"), []), self.operators.get(Operator("/"), [])

        mul_and_div = {**{i: Operator("*") for i in mul}, **{i: Operator("/") for i in div}}
        return {k: v for k, v in sorted(mul_and_div.items())}

    def get_add_pos(self):
        return self.operators.get(Operator("+"), [])

    def update_data(self, parsed_groups: list[Group | Operator | ParenthesizedGroup]):
        self.parent_loc, self.operators, self.existing_powers = get_PEMDAS_positions(parsed_groups)

    @classmethod
    def from_data(cls, parsed_groups: list[Group | Operator | ParenthesizedGroup]):
        self = cls(parsed_groups)
        self.parent_loc, self.operators, self.existing_powers = get_PEMDAS_positions(parsed_groups)
        return self


def create_new_group(rv1: Decimal | int, rv2: Decimal | int | None = None, operator: Operator | None = None, power = None): # TODO: Awaiting hints
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
    num = Number.from_data(value=abs(int(whole)), decimal=f"0.{dec}", is_negative=whole[0] == "-")
    group = Group.from_data(num)
    if power is not None:
        group.power = power
    return group


def get_PEMDAS_positions(parsed_group: list[Group | Operator | ParenthesizedGroup]) -> tuple[list[int], dict[Operator, list[int]], list[int]]:
    operator_positions = {}
    parenthesized_group_positions = []
    available_powers = []
    for index, group in enumerate(parsed_group):
        if isinstance(group, Operator):
            operator_positions[group] = operator_positions.get(group, []) + [index]
        elif isinstance(group, ParenthesizedGroup):
            parenthesized_group_positions.append(index)
            if group.power:
                available_powers.append(index)
        elif isinstance(group, Group):
            if group.power:
                available_powers.append(index)
    return parenthesized_group_positions, operator_positions, available_powers


def combine_groups(positions, parsed_groups, operator):
    if operator == datatype.mul_and_div:
        index, operator = list(positions.get_mul_and_div_pos().items())[0]
    elif operator == Operator("+"):
        index = positions.get_add_pos()[0]
    else:
        raise NotImplementedError
    before = typing.cast(Group, parsed_groups[index - 1]).get_real_value()
    after = typing.cast(Group, parsed_groups[index + 1]).get_real_value()
    parsed_groups.insert(index - 1, create_new_group(before[-1], after[-1], operator))
    del parsed_groups[index:index + 3]


def calculate_group_power(group: Group, calculated_power) -> int | Decimal:
    rv = group.get_real_value()[-1]
    return -(rv ** calculated_power) if rv < 0 else (rv ** calculated_power)


def solve_basic(parsed_groups: list[Group | Operator | ParenthesizedGroup]) -> Decimal | int:
    positions = Positions.from_data(parsed_groups)
    parenthesized_groups, operators = positions.parent_loc, positions.operators
    for i in parenthesized_groups:  # The index here is static, so we don't need to re-calculate it
        if isinstance(par := parsed_groups[i], ParenthesizedGroup):  # Type checking purposes
            power = par.power
            result = solve_basic(par.groups)
            parsed_groups[i] = create_new_group(Decimal(-result if par.is_negative else result), power=power)

    positions.update_data(parsed_groups)
    for i in positions.existing_powers:
        if isinstance((group := parsed_groups[i]), Group):
            result = solve_basic(group.power)
            parsed_groups[i] = create_new_group(calculate_group_power(group, result))

    for _ in positions.get_mul_and_div_pos():
        positions.update_data(parsed_groups)
        combine_groups(positions, parsed_groups, datatype.mul_and_div)

    for _ in positions.get_add_pos():
        positions.update_data(parsed_groups)
        combine_groups(positions, parsed_groups, Operator("+"))

    if len(parsed_groups) == 1:
        return typing.cast(Group, parsed_groups[0]).get_real_value()[-1]

    raise NotImplementedError("There's a bug here or the input is invalid")
