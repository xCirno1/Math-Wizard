from collections import Counter
from collections.abc import Iterable
from decimal import Decimal
from typing import overload, Literal, cast

from parser.objects import Group, Operator, Equals, Number, ParenthesizedGroup, Fraction, RelationalOperator, Variable
from parser.utility import gts

from .core import Positions, Result, TrueForAll
from .datatype import No_RO, CompleteEquation
from .logging import _log
from .utility import determine_equation_type


def _log_key(key: Group) -> str:
    if key.variable is None:
        return "Number"
    return f"{key.variable.name}{'^' if (p := gts(key.power)) else ''}{p if p else ''}"


def separate_lhs_rhs(equation: CompleteEquation) -> tuple[No_RO, No_RO]:
    positions = Positions(equation)
    equals = positions.ro_positions[0][1]  # This should always be the RO '='
    return equation[:equals], equation[equals + 1:]


def allowed_addition(parsed_group: No_RO, i: int):  # This should be refactored after fractions are implemented
    is_not_before_mul = (parsed_group[i + 1] != Operator.Mul) if i != len(parsed_group) - 1 else True
    is_not_after_mul = (parsed_group[i - 1] != Operator.Mul) if i > 1 else True
    return is_not_after_mul and is_not_before_mul


def clean_deletion(parsed_group: No_RO, index: int, first_element: int | None):
    # Delete object with given index safely (removes addition sign)
    # `index` is the index of object to delete, while `first_element` is the index of main object
    if not len(parsed_group):
        return
    if index == 0 and index != first_element:  # First object in the list
        return parsed_group.pop(index)
    if index != first_element and parsed_group[index - 1] == Operator.Add:
        parsed_group.pop(index - 1)


def safe_delete_addition(groups: CompleteEquation | No_RO, index: int, is_deleted: bool = True):
    # Safe delete an object at given index (delete addition sign that wraps the object)
    if not is_deleted:
        del groups[index]
    if groups[index - 1] == Operator.Add:  # Even if idx = 0, means lhs[-1] will not be an Operator
        del groups[index - 1]
    # The order shifts one time to the left, so adjust based on that
    if index == 0 and len(groups) > 1 and groups[0] == Operator.Add:
        del groups[index]
    return groups


def combine_similar_groups(parsed_group: No_RO):
    # Combine all similar groups (same variable and power) on one side
    positions = Positions(parsed_group)
    done = set()
    for key in list(positions.variable_groups.keys()):  # Iterate until there's only 1 group left of each kind
        if key in done:  # This key has already been checked
            continue
        done.add(key)
        positions.update_data(parsed_group)
        variables = positions.variable_groups
        indexes = list(reversed(variables[key]))
        first_element = variables[key][0]
        iterate_times = 0
        for index in indexes:
            if allowed_addition(parsed_group, index):
                group = cast(Group, parsed_group.pop(index))
                coefficient = group.get_value()
                key.number = Number.from_data(key.get_value() + coefficient)
                clean_deletion(parsed_group, index, first_element)
                iterate_times += 1
        if iterate_times != 0:  # That means we have combined something, we don't want to keep junk group and log here
            parsed_group.insert(first_element, key)
            _log.info("Finished combining key '%s', got '%s' as the result", _log_key(key), gts(parsed_group))

    return parsed_group


def merge_lhs_and_rhs(lhs: No_RO, rhs: No_RO) -> CompleteEquation | TrueForAll:
    # Merge lhs to rhs
    lhs_pos, rhs_pos = Positions(lhs), Positions(rhs)
    for key in set(list(lhs_pos.variable_groups) + list(rhs_pos.variable_groups)):
        lhs_pos.update_data(lhs)
        rhs_pos.update_data(rhs)
        lhs_variables, rhs_variables = lhs_pos.variable_groups, rhs_pos.variable_groups
        if key.variable is None:  # Design: Non-variable group should be on the right hand side
            # There should always be one group only here, the non-variable group
            if (lhs_index := lhs_variables.get(key)) is not None and allowed_addition(lhs, lhs_index[0]):
                try:
                    rhs_group = cast(Group, rhs[rhs_variables[key][0]])
                except KeyError:
                    continue
                if key not in rhs_variables:
                    if not rhs[-1] == Operator.Add:  # Maybe useful
                        rhs.append(Operator.Add)
                    rhs.insert(x := len(rhs), key)  # Create a new group at the end of rhs if not exist
                    rhs_variables[key] = [x]
                result = rhs_group.get_value() - cast(Group, lhs.pop(lhs_index[0])).get_value()
                rhs_group.number = Number.from_data(result)
                clean_deletion(lhs, lhs_index[0], -1)
                _log.info("Finished merging non-variable group, got '%s'", gts(lhs + [Equals] + (rhs or [Group()])))
        else:
            try:
                lhs_group = cast(Group, lhs[idx := lhs_variables[key][0]])
            except KeyError:
                continue
            if (rhs_index := rhs_variables.get(key)) is not None:
                if key not in lhs_variables:
                    if not lhs[-1] == Operator.Add:  # Maybe useful
                        lhs.append(Operator.Add)
                    lhs.insert(x := len(lhs), key)  # Create a new group at the end of lhs if not exist
                    lhs_variables[key] = [x]
                if lhs == rhs:  # A pretty common case where there are infinite number of solutions
                    return TrueForAll(key.variable.name)
                result = lhs_group.get_value() - cast(Group, rhs.pop(rhs_index[0])).get_value()
                lhs_group.number = Number.from_data(result)
                clean_deletion(rhs, rhs_index[0], -1)
                # If result is 0, then check if any variable still exist in the equation.
                # If none exist, don't delete the 0x, otherwise delete it
                del lhs[idx]  # Delete, so the contains_variable check ignores it. Can't think of a better way.
                if result == 0 and any([g.contains_variable for g in lhs + rhs if not isinstance(g, (Operator, RelationalOperator))]):
                    lhs = safe_delete_addition(lhs, idx)
                else:
                    lhs.insert(idx, lhs_group)

            _log.info("Finished merging variable group '%s', got '%s'", _log_key(key), gts(lhs + [Equals] + (rhs or [Group()])))
        if not rhs:  # Case like `x + 3 = ` might happen
            rhs.append(Group())
    return lhs + [Equals] + rhs


def join_chained_groups(groups: No_RO) -> No_RO:
    existing_groups = {}
    new = []
    for group in groups:
        if isinstance(group, Group):
            existing_groups[group] = existing_groups.get(group, 0) + 1
    for key in existing_groups:
        if key.power:
            raise NotImplementedError("Joining groups with existing powers are not supported.")
        if (n := existing_groups[key]) > 1:
            key = ParenthesizedGroup(groups=[key], power=[Group.from_value(Decimal(n))])
        new += [key, Operator.Mul]
    if new[-1] == Operator.Mul:
        del new[-1]
    return new


@overload
def get_common_factors(groups: No_RO, highest: Literal[False]) -> list[int]: ...
@overload
def get_common_factors(groups: No_RO, highest: Literal[True] = True) -> int: ...
@overload
def get_common_factors(groups: No_RO, highest: bool = ...) -> int | list[int]: ...


def get_common_factors(groups: No_RO, highest: bool = True) -> int | list[int]:
    factors: list[int] = []
    checked_group = 0
    index = -1
    for group in groups:
        index += 1
        if isinstance(group, ParenthesizedGroup):
            factors += get_common_factors(group.groups, highest=False)
        elif isinstance(group, Group):
            try:
                # Maybe deal common factors differently for Groups with exponent
                # For example 25 ^ 25 = 625 but there's 125 as a factor of 625 which isn't a factor of 25
                factors += group.number.factors
            except ValueError:
                return 1 if highest else [1]
            if groups[index - 1] == Operator.Mul:  # Will not raise IndexError because last group shouldn't be operator
                continue  # Don't increment checked_group for chained multiplications
        elif isinstance(group, Fraction):
            factors += get_common_factors(group.numerator, highest=False)
        else:  # Operator
            continue
        checked_group += 1
    common_factors = [item for item, count in Counter(factors).items() if count == checked_group]  # Always in order
    return max(common_factors or [1]) if highest else common_factors


def divide_multiplications(groups: No_RO, divisor: int | Decimal) -> No_RO:
    # This should already be only the multiplications, no other operators
    # For example: 5x * 3x * 10x, divisor = 5 become x * 3x * 10x
    for group in groups:
        if isinstance(group, Group):
            if (coefficient := group.number.value) >= divisor and coefficient / divisor % 1 == 0:
                group.number.value /= divisor
                return groups
            elif (coefficient := group.number.value) < divisor and coefficient / divisor % 1 == 0:
                continue
    raise TypeError("This is a bug. This function should only be called when a common factor is found.")


def _divide(group: Group, divisor: int | Decimal, power: Group | None = None, override: bool = False) -> No_RO:
    power = power or cast(Group, group.power[0])
    if not override and divisor == abs(int(group.number.value)):  # For example: (5^3)/(5) is equals (5^2)/(5)
        power.number.integer -= 1  # Cases like (-5^2)/(5) should be handled as -(5^2)/(5)
        return [group]
    # For example: (15^2)/5 -> 15/5 * 15 -> 3 * 15
    new = group.copy()
    new.power = []
    # Equivalent to: chain = [new, Operator.Mul] * int(val) but here, elements will have the same memory location
    chain = [new.copy() if i % 2 == 0 else Operator.Mul for i in range(int(power.number.value * 2))]
    del chain[-1]  # Delete extra * operator
    result = divide_multiplications(chain, divisor=divisor)
    return result


def divide_powered_group(group: Group | ParenthesizedGroup, divisor: int | Decimal) -> No_RO:
    # Divide powered groups by a divisor
    if not group.power:
        return [group]
    if group.power_contains_variable:  # For example: 5^(1 + x) should be treated as 5 * 5^x
        raise NotImplementedError  # This will be implemented when we support exponential algebra
    if isinstance(group, ParenthesizedGroup):
        if len(group.groups) > 1:  # Cases like (5x - 10)^2 shouldn't be solved directly here
            raise TypeError("ParenthesizedGroup with exponents with more than 2 sub-groups is not supported yet.")
        chain = _divide(cast(Group, group.groups[0]), divisor=divisor, power=cast(Group, group.power[0]), override=True)
        a = join_chained_groups(chain)
        return a
    group.power = combine_similar_groups(group.power)
    if isinstance((g := group.power[0]), Group) and g.number.value % 1 == 0 and group.number.value % divisor == 0:
        # NOTE: Here, 5x^2 should be treated as 5 * x^2 -> x^2, not (5x)^2. This is a common mistake.
        if group.variable:
            raise TypeError("Variables should not enter here.")
        return _divide(group, divisor=divisor)
    else:
        raise NotImplementedError("Shouldn't reach here, this is a bug.")


def divide_all(groups: No_RO, divisor: int | Decimal) -> No_RO:
    # Divide every group in a side by a divisor
    new = []
    index = -1
    skip = 0
    for group in groups:
        if skip > 0:
            skip -= 1
            continue
        index += 1
        if isinstance(group, (Operator, Fraction)):
            new.append(group)
            continue
        if isinstance(group, Fraction):
            # Awaiting test case
            if o := overlapping_common_factors(get_common_factors(group.numerator, highest=False), Number.from_data(divisor).factors):
                group.numerator = divide_all(group.numerator, divisor=o)
            if not divisor or divisor != o:  # At least one of the if-statements should be executed
                group.denominator = multiply_all(group.numerator, multiplier=divisor//o)
        if group.power:  # In case of like 5^2, fallback to divide_powered_group
            if not (isinstance(group, Group) and group.variable):  # We shouldn't solve variables with power here
                new += divide_powered_group(group, divisor=divisor)
                continue
        if isinstance(group, ParenthesizedGroup):
            if not group.power:
                group.groups = divide_all(group.groups, divisor=divisor)
            else:
                raise NotImplementedError("ParenthesizedGroups with exponent is not supported yet.")
        elif isinstance(group, Group):
            if index + 1 < len(groups) - 1 and groups[index + 1] == Operator.Mul:  # For chained multiplication
                for x in range(1, len(groups) - index):  # Loop until chain is broken, x will not be unbound
                    if index + x > len(groups) - 1 or (isinstance(groups[index + x], Operator) and groups[index + x] != Operator.Mul):
                        break
                chain_mul = groups[index:index + x + 1]  # pyright: ignore reportUnboundVariable
                new += divide_multiplications(chain_mul, divisor=divisor)
                skip = len(chain_mul) - 1
                continue
            else:
                group.number.value /= divisor
        new.append(group)
    return new


def divide_both_side(groups: CompleteEquation, divisor: int | None = None) -> CompleteEquation:
    # Divide both side by a common factor
    lhs, rhs = separate_lhs_rhs(groups)
    c_factors = get_common_factors(lhs, highest=False) + get_common_factors(rhs, highest=False)
    if divisor is None:
        try:
            divisor = max([item for item, count in Counter(c_factors).items() if count == 2])
        except ValueError:  # That means common factor count of one of the sides is 0
            divisor = 1
    result: CompleteEquation = divide_all(lhs, divisor) + [Equals] + divide_all(rhs, divisor)
    _log.info("Finished dividing groups with similar coefficient (%s), got '%s'", divisor, gts(result))

    return result


def calculate_non_groups_muls(groups: CompleteEquation):
    # Calculate for example in this equation: `5x * 2 = 14`, 5x * 2 should be calculated first.
    positions = Positions(groups)
    operators = positions.operators
    if not (mul_positions := operators.get(Operator.Mul)):
        return groups
    mul_positions.reverse()
    for index in mul_positions:
        if isinstance((before := groups[index - 1]), Group) and isinstance((after := groups[index + 1]), Group) and not before.power and not after.power:
            if (before.variable is not None and after.variable is not None) and before.variable != after.variable:
                raise NotImplementedError  # Support for example 5x * 3y
            variable = before.variable or after.variable
            new = Group.from_value(value=after.get_value() * before.get_value(), variable=variable)
            del groups[index - 1], groups[index - 1], groups[index - 1]  # When deleting, items shift to the left
            groups.insert(index - 1, new)
    _log.info("Finished calculating multiplications, got '%s'", gts(groups))
    return groups


def multiply_all(groups: CompleteEquation | No_RO, multiplier: int | Decimal) -> CompleteEquation:
    # Currently only works for non-variable multiplier
    is_on_chain = False
    new = []
    for group in groups:
        if isinstance(group, Group):
            if not is_on_chain:  # For example: 5x * 3 * 2 (mult=3) should be treated as 15x * 3 * 2, not 15x * 9 * 6
                group.number.value *= multiplier
        elif isinstance(group, Fraction):
            if multiplier in get_common_factors(group.denominator, highest=False):
                # For example: 5x/10 (mult=5) should be treated as 5x/2
                group.denominator = divide_all(group.denominator, divisor=multiplier)
                if cast(Group, group.denominator[0]).number.integer == 1:
                    group = ParenthesizedGroup(numerator) if len(numerator := group.numerator) > 1 else numerator[0]
            else:  # For example: 5x/3 (mult=5) should be treated as 25x/3
                group.numerator = multiply_all(group.numerator, multiplier=multiplier)
        elif isinstance(group, ParenthesizedGroup):
            if not is_on_chain and not group.power:  # Design: Always multiply the first PG on the chain sequence
                group.groups = multiply_all(group.groups, multiplier=multiplier)
            if group.power:
                raise NotImplementedError("ParenthesizedGroups with exponent is not supported yet.")
        elif isinstance(group, Operator):
            is_on_chain = True if group == Operator.Mul else False
        new.append(group)
    return new


def simplify_side(positions: Positions):
    groups = positions.groups
    initial = gts(groups)
    _log.info("START OF SIMPLIFYING SIDE '%s'.", initial)
    if positions.fractions:  # Multiply every group by every fraction's denominator
        groups = calculate_fractions(groups)
    groups = calculate_non_groups_muls(groups)  # Multiply groups which can be multiplied
    positions.update_data(groups)
    groups = combine_similar_groups(groups)
    groups = clean_parenthesized_groups(Positions(groups))  # TODO: Add some checks
    _log.info("Combined all similar groups in side '%s', got '%s'.", initial, gts(groups))
    _log.info("END OF SIMPLIFYING SIDE '%s', got '%s'.", initial, gts(groups))
    return groups


def overlapping_common_factors(*factors: Iterable[int]) -> int:
    total_factors = []
    for f in factors:
        total_factors.extend(f)
    if overlap := (x for x in total_factors if total_factors.count(x) == len(factors)):
        return max(overlap)
    return 0


def calculate_fractions(groups: CompleteEquation):
    positions = Positions(groups)
    frac_pos = positions.fractions.values()
    for index in frac_pos:
        fraction = cast(Fraction, groups[index])
        initial = gts([fraction])  # For logging purposes
        fraction.denominator = deno = simplify_side(Positions(fraction.denominator))
        fraction.numerator = num = simplify_side(Positions(fraction.numerator))
        if len(deno) > 1 or not isinstance(deno[0], Group):  # Implement later
            raise NotImplementedError
        deno_coefficient = deno[0].number.value
        to_divide = 1
        # Check if there's a common factor between numerator and denominator
        if numerator_factors := get_common_factors(num, highest=False):
            if numerator_factors[-1] % deno[0].number.value == 0:
                to_divide = deno_coefficient
            else:
                to_divide = overlapping_common_factors(get_common_factors(deno, highest=False), numerator_factors)

        if to_divide == 1:  # There is no common factor
            groups = multiply_all(groups, multiplier=deno_coefficient)  # Assume there's no variable in deno
            _log.info("Simplified fraction '%s' by multiplying all groups by '%s', got '%s'", initial, deno_coefficient, gts(groups))
        else:
            fraction.numerator = divide_all(num, divisor=to_divide)
            fraction.denominator = divide_all(deno, divisor=to_divide)
            if fraction.denominator[0].get_value() == 1:  # type: ignore # Assume there's no variable in deno
                if len(fraction.numerator) == 1:
                    groups[index] = fraction.numerator[0]
                else:
                    # It is safe to convert to PG since `calculate_fractions` comes before `clean_parenthesized_groups`
                    groups[index] = ParenthesizedGroup(groups=fraction.numerator)
            # Maybe add check if fraction deno is not 1, multiply_all directly instead of waiting for the next recursion
            _log.info("Simplified fraction '%s' by dividing numerator and denominator by '%s', got '%s'", initial, to_divide, gts(groups))
    return groups


def simplify_equation(groups: CompleteEquation, positions: Positions) -> CompleteEquation | Result:
    if positions.fractions:  # Multiply every group by every fraction's denominator
        groups = calculate_fractions(groups)
    if (factor := get_common_factors(groups=groups, highest=True)) != 1:  # Speed things up
        groups = divide_both_side(groups, factor)  # Divide both side with a common factor
    groups = calculate_non_groups_muls(groups)  # Multiply groups which can be multiplied
    positions.update_data(groups)
    equals = positions.ro_positions[0][1]  # This should always be the RO '='
    lhs, rhs = cast(tuple[No_RO, No_RO], (groups[:equals], groups[equals + 1:]))
    combined_lhs, combined_rhs = combine_similar_groups(lhs), combine_similar_groups(rhs)
    _log.info("Combined all similar groups in lhs and rhs, got lhs '%s' and rhs '%s'", gts(lhs), gts(rhs))
    merged = merge_lhs_and_rhs(combined_lhs, combined_rhs)  # Can return TrueForAll instance
    if isinstance(merged, TrueForAll):
        return Result({Variable(merged.name): merged})
    _log.info("Merged lhs and rhs, got '%s'", gts(merged))
    return merged


def create_cases(groups: No_RO, equals: Group) -> Result:
    final: Result = Result({})
    for group in groups:
        if isinstance(group, Operator):
            continue
        case = group.groups if isinstance(group, ParenthesizedGroup) else [group]
        result = determine_equation_type(case + [Equals, equals])
        if isinstance(result, bool):  # This is for non-variable group, for example `2(x + 1)`. The `2` here
            continue                  # will be created as a new case, so 2 = 0 will result to False
        final.compare(result.variables_map)
    return final


def side_equals_zero(positions: Positions) -> tuple[bool, No_RO | None]:  # Returns (bool, non-zero side groups)
    rhs = combine_similar_groups(positions.rhs)[0]
    lhs = combine_similar_groups(positions.lhs)[0]
    if (isinstance(rhs, Group) and rhs.is_zero) or (isinstance(lhs, Group) and lhs.is_zero):
        return True, positions.lhs if isinstance(rhs, Group) else positions.rhs
    return False, None


def clean_parenthesized_groups(positions: Positions) -> CompleteEquation:
    new: CompleteEquation = []
    index = -1
    for parent in positions.groups:
        index += 1
        if isinstance(parent, ParenthesizedGroup):
            if parent.groups:
                parent.groups = simplify_side(Positions(parent.groups))
            before = positions.groups[index - 1]
            if parent.is_negative:  # If negative, instantly multiply everything inside PG
                for group_inside in parent.groups:  # TODO: Implement chain multiplication here
                    if isinstance(group_inside, Group):  # TODO: Implement multiplying group by fraction or PG
                        group_inside.number.is_negative = not group_inside.number.is_negative  # Same as `group.value * -1`
                    new.append(group_inside)
                continue
            # Check case for x(x + 3) or (x + 3)(x - 3) or x/3(x + 3), just skip
            if index > 0 and before == Operator.Mul:
                ...
                # g_before = positions.groups[index - 2]  # Implement something here
            elif index > 0 and before == Operator.Add or isinstance(before, RelationalOperator):
                inside = calculate_non_groups_muls(parent.groups)
                new.append(inside[0] if len(inside) == 1 else ParenthesizedGroup(inside))
                continue
            if len(parent.groups) == 1:
                new.append(parent.groups[0])
                continue
        new.append(parent)
    positions.update_data(new)
    _log.info("ParenthesizedGroups cleaned, got '%s'", gts(new))
    return new


def solve_algebra(parsed_group: CompleteEquation) -> CompleteEquation | Result:
    origin = parsed_group.copy()
    _log.info("Solving problem '%s'", gts(parsed_group))

    positions = Positions(parsed_group)
    # CASE: PG * PG * ... = 0
    false_operator_case = len(keys := positions.operators.keys()) > 1 or Operator.Mul not in keys
    if (side := side_equals_zero(positions))[0] and not false_operator_case and len(positions.parent_loc):
        return create_cases(cast(No_RO, side[1]), Group())
    result = simplify_equation(parsed_group, positions)
    if isinstance(result, Result):
        return result
    if result == origin:  # We're not making progress
        result = clean_parenthesized_groups(positions)
    positions.update_data(result)
    return result
