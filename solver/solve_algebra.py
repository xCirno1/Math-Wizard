import typing

from decimal import Decimal
from parser import Group, Operator, Equals, Number, RelationalOperator

from .core import Positions
from .datatype import No_RO, CompleteEquation


def allowed_addition(parsed_group: No_RO, i: int):  # This should be refactored after fractions are implemented
    is_not_before_mul = (parsed_group[i + 1] != Operator("*")) if i != len(parsed_group) - 1 else True
    is_not_after_mul = (parsed_group[i - 1] != Operator("*")) if i > 1 else True
    return is_not_after_mul and is_not_before_mul


def clean_equation(parsed_group: No_RO, index: int, first_element: int):
    if len(parsed_group) <= 1:
        return

    if index == 0 and index != first_element:
        return parsed_group.pop(index)

    if index != first_element and parsed_group[index - 1] == Operator("+"):
        parsed_group.pop(index - 1)


def combine_similar_groups(parsed_group: No_RO):
    positions = Positions(parsed_group)
    done = set()
    for key in list(positions.get_variable_positions().keys()):  # Iterate until there's only 1 group left of each kind
        if key in done:  # This key has already been checked
            continue
        done.add(key)
        variables = positions.get_variable_positions()
        indexes = list(reversed(variables[key]))
        first_element = variables[key][0]
        iterate_times = 0
        for index in indexes:
            if allowed_addition(parsed_group, index):
                group = typing.cast(Group, parsed_group.pop(index))
                coefficient = group.get_value()
                key.number = Number.from_data(key.get_value() + coefficient)
                clean_equation(parsed_group, index, first_element)
                iterate_times += 1
        if iterate_times != 0:  # That means we have combined something, we don't want to keep junk group here
            parsed_group.insert(first_element, key)
    return parsed_group


def merge_lhs_to_rhs(lhs: No_RO, rhs: No_RO):
    lhs_pos, rhs_pos = Positions(lhs), Positions(rhs)
    for key in set(list(lhs_pos.get_variable_positions()) + list(rhs_pos.get_variable_positions())):
        lhs_variables, rhs_variables = lhs_pos.get_variable_positions(), rhs_pos.get_variable_positions()
        if key.variable is None:  # Design: Non-variable group should be on the right hand side
            # There should always be one group only here right?
            if (lhs_index := lhs_variables.get(key)) is not None and allowed_addition(lhs, lhs_index[0]):
                try:
                    rhs_group = typing.cast(Group, rhs[rhs_variables[key][0]])
                except KeyError:
                    continue
                if key not in rhs_variables:
                    rhs.insert(x := len(rhs), key)  # Create a new group at the end if not exist
                    rhs_variables[key] = [x]
                result = rhs_group.get_value() - typing.cast(Group, lhs.pop(lhs_index[0])).get_value()
                rhs_group.number = Number.from_data(result)
                clean_equation(lhs, lhs_index[0], -1)
        else:
            try:
                lhs_group = typing.cast(Group, lhs[lhs_variables[key][0]])
            except KeyError:
                continue
            if (rhs_index := rhs_variables.get(key)) is not None:
                if key not in lhs_variables:
                    lhs.insert(x := len(lhs), key)  # Create a new group at the end if not exist
                    lhs_variables[key] = [x]

                result = lhs_group.get_value() - typing.cast(Group, rhs.pop(rhs_index[0])).get_value()
                lhs_group.number = Number.from_data(result)
                clean_equation(rhs, rhs_index[0], -1)

    return lhs + [Equals("=")] + rhs


def divide_both_side(parsed_group: tuple[Group, RelationalOperator, Group]):  # Implemented: Only one variable per side
    left, operator, right = parsed_group
    if not left.number.value:  # Raised in the format of "0x = ..."
        raise NotImplementedError("Variables with coefficient of 0 is not supported yet.")
    right.number.value /= left.number.value
    left.number = Number.from_data(Decimal(1))
    return [left, operator, right]


def calculate_equivalent_groups(parsed_group: CompleteEquation, positions: Positions):
    equals = positions.get_relational_operator_positions()[0][1]  # This should always be the RO '='
    lhs, rhs = typing.cast(tuple[No_RO, No_RO], (parsed_group[:equals], parsed_group[equals + 1:]))
    combined_lhs, combined_rhs = combine_similar_groups(lhs), combine_similar_groups(rhs)
    total = merge_lhs_to_rhs(combined_lhs, combined_rhs)
    if len(total) == 3:  # In the format of "<var> <RO> <number>"
        return divide_both_side(tuple(total))  # type: ignore
    return total  # Debugging purposes


def solve_algebra(parsed_group: CompleteEquation) -> dict:
    positions = Positions.from_data(parsed_group)

    result = calculate_equivalent_groups(parsed_group, positions)
    return result  # type: ignore
