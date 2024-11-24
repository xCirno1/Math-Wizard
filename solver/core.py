from __future__ import annotations

from decimal import Decimal
from typing import Mapping, TYPE_CHECKING, TypeAlias, cast

from parser.objects import Group, Operator, ParenthesizedGroup, RelationalOperator, Number, Variable, Fraction
from parser.utility import truncate_trailing_zero


if TYPE_CHECKING:
    from .datatype import Maybe_RO, No_RO, Tuple_NO_RO

    RETURN: TypeAlias = tuple[
        list[int],  # ParenthesizedGroup Locations
        dict[Operator, list[int]],  # Operator Locations
        list[int],  # Power-existing Group/ParenthesizedGroup locations
        dict[Fraction, int],  # Fraction locations
        list[tuple[RelationalOperator, int]],  # Relational operator locations
        dict[Group, list[int]]  # Unique Variable group locations
    ]
    VAR_VALUE: TypeAlias = Decimal | Fraction | Tuple_NO_RO | "NoSolution" | "TrueForAll" | "Range"


class NoSolution:
    def __eq__(self, other):
        return isinstance(other, NoSolution)

    def __hash__(self):
        return 1

    def __str__(self):
        return "No Solution"


class TrueForAll:
    """Construct a TrueForAll object where x is True (x ∈ R)."""

    def __init__(self, var_name: str):
        self.name = var_name

    def __eq__(self, other):
        return isinstance(other, NoSolution)

    def __hash__(self):
        return 2

    def __str__(self):
        return f"True for all {self.name}"


class Range:
    """Construct a Range object with a given lower bound (lb), upper bound (ub), lb is equal, and ub is equal."""
    def __init__(self, var_name: str, lb: int, ub: int, lb_eq: bool, ub_eq) -> None:
        self.name = var_name
        self.lb = lb
        self.ub = ub
        self.lb_eq = lb_eq
        self.ub_eq = ub_eq

    def __str__(self) -> str:
        ub_sym = "≤" if self.ub_eq else "<"
        lb_sym = "≤" if self.lb_eq else "<"

        return f"{self.lb} {lb_sym} {self.name} {ub_sym} {self.ub}"


class Positions:
    def __init__(self, parsed_groups: Maybe_RO):
        self.groups = parsed_groups
        self.parent_loc: list[int] = []
        self.operators: dict[Operator, list[int]] = {}
        self.existing_powers: list[int] = []
        self.fractions: dict[Fraction, int] = {}
        self.ro_positions: list[tuple[RelationalOperator, int]] = []
        self.variable_groups: dict[Group, list[int]] = {}

        self.update_data(self.groups)

    def get_mul_div_pos(self) -> dict[int, Operator]:  # Returns `{index: Operator}` sorted by index
        mul, div = self.operators.get(Operator.Mul, []), self.operators.get(Operator.Div, [])

        mul_and_div: dict[int, Operator] = {**{i: Operator.Mul for i in mul}, **{i: Operator.Div for i in div}}
        return {k: v for k, v in sorted(mul_and_div.items())}

    def update_data(self, parsed_groups: No_RO):
        self.parent_loc, self.operators, self.existing_powers, self.fractions, self.ro_positions, self.variable_groups = get_positions(parsed_groups)

    @property
    def rhs(self) -> No_RO:  # Assuming has only 1 RO
        return self.groups[self.ro_positions[0][1] + 1:]

    @property
    def lhs(self) -> No_RO:  # Assuming has only 1 RO
        return self.groups[:self.ro_positions[0][1]]


def get_positions(parsed_group: Maybe_RO) -> RETURN:  # Increases performance a lot
    operator_positions = {}
    parenthesized_group_positions = []
    available_powers = []
    fractions = {}
    relational_operator_positions = []
    variable_groups = {}  # Similar groups (same power and variable name), but coefficient may vary
    for index, group in enumerate(parsed_group):
        if isinstance(group, Operator):
            operator_positions[group] = operator_positions.get(group, []) + [index]
        elif isinstance(group, ParenthesizedGroup):
            parenthesized_group_positions.append(index)
            if group.power:
                available_powers.append(index)
        elif isinstance(group, Group):
            new = Group().from_data(Number(), Variable(v.name) if (v := group.variable) else None, power=group.power)
            variable_groups[new] = variable_groups.get(new, []) + [index]
            if group.power:
                available_powers.append(index)
        elif isinstance(group, Fraction):
            fractions[group] = index
        elif isinstance(group, RelationalOperator):
            relational_operator_positions.append((group, index))
    return parenthesized_group_positions, operator_positions, available_powers, fractions, relational_operator_positions, variable_groups


def _normalize(value):
    if isinstance(value, Decimal):
        return truncate_trailing_zero(Decimal(f"{value:.12e}"))
    return value


class Result:
    def __init__(self, data: Mapping[Variable, VAR_VALUE | set[VAR_VALUE]] | bool | Decimal):
        self.variables_map = data if isinstance(data, dict) else {}
        self.other_value = data if isinstance(data, (bool, Decimal)) else None

    def compare(self, target: Mapping[Variable, VAR_VALUE | set[VAR_VALUE]]):
        # Add value to a variable by a set or not by a set
        for var in target:
            if not isinstance(vals := target[var], set):
                vals = {vals}
            for val in vals:
                hashable_target = tuple(val) if isinstance(val, list) else val
                hashable_target = cast("VAR_VALUE", hashable_target)
                if (val_orig := self.variables_map.get(var, {})) != {}:
                    val_orig = cast("VAR_VALUE | set[VAR_VALUE]", val_orig)
                    if not isinstance(val_orig, set):
                        val_orig = {tuple(val_orig) if isinstance(val_orig, list) else val_orig}
                    val_orig = cast("set[VAR_VALUE]", val_orig)
                    val_orig.add(hashable_target)
                    self.variables_map[var] = val_orig
                else:
                    self.variables_map[var] = hashable_target
        return self

    def __setattr__(self, key, value):
        if key == "variables_map":
            for var in value:
                value[var] = _normalize(value[var])
        elif key == "other_value":
            value = _normalize(value)
        super().__setattr__(key, value)

    def __getattr__(self, item):
        if len(item) != 1:  # It's not a valid variable
            return self.__getattribute__(item)
        variable = [self.variables_map[i] for i in self.variables_map if i.name == item]
        return None if not variable else variable[0]

    def __repr__(self):
        if isinstance(self.other_value, bool) or self.other_value is not None:
            return str(self.other_value)
        return str(self.variables_map or "<Empty Result>")

    def to_decimal(self) -> Decimal | None:
        # Converts Result instance to a Decimal if applicable
        return self.other_value if isinstance(self.other_value, Decimal) else None
