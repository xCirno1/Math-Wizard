from parser import Group, Operator, ParenthesizedGroup, RelationalOperator, Number, Variable
from .datatype import Maybe_RO

from typing import overload


class Positions:
    def __init__(self, parsed_groups: Maybe_RO):
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

    @overload
    def get_relational_operator_positions(self, __ro: RelationalOperator) -> list[int]:
        ...

    @overload
    def get_relational_operator_positions(self) -> list[tuple[RelationalOperator, int]]:
        ...

    def get_relational_operator_positions(self, _ro: RelationalOperator | None = None) -> list[tuple[RelationalOperator, int]] | list[int]:
        from .utility import get_equation_identity
        relational_operators = get_equation_identity(self.groups).relational_operators

        return [index for r, index in relational_operators if r == _ro] if _ro else relational_operators

    def get_variable_positions(self) -> dict[Group, list[int]]:
        pos = {}
        for index, group in enumerate(self.groups):
            if isinstance(group, Group):
                new = Group().from_data(Number(), Variable(v.name) if (v := group.variable) else None, power=group.power)
                pos[new] = pos.get(new, []) + [index]
        return pos

    def get_operators(self):
        return [operator for operator in self.groups if isinstance(operator, Operator)]

    @classmethod
    def from_data(cls, parsed_groups: Maybe_RO):
        self = cls(parsed_groups)
        self.parent_loc, self.operators, self.existing_powers = get_PEMDAS_positions(parsed_groups)
        return self


def get_PEMDAS_positions(parsed_group: Maybe_RO) -> tuple[list[int], dict[Operator, list[int]], list[int]]:
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
