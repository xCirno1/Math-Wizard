from parser import Group, Variable, Operator, ParenthesizedGroup, RelationalOperator

from .solve_basic import solve_basic


class EquationIdentity:
    variable_count: dict[Variable, int] = {}
    prove: bool = False


def get_equation_identity(parsed_groups: list[Group | Operator | RelationalOperator | ParenthesizedGroup]) -> EquationIdentity:
    identity = EquationIdentity()
    for group in parsed_groups:
        if isinstance(group, RelationalOperator):
            identity.prove = True
        if isinstance(group, (RelationalOperator, Operator, ParenthesizedGroup)):
            continue

        if (var := group.variable) is not None:  # There's variable
            identity.variable_count[var] = identity.variable_count.get(var, 0) + 1

    return identity


def get_relational_operator_position(parsed_groups) -> tuple[RelationalOperator, int]:
    for i, element in enumerate(parsed_groups):
        if isinstance(element, RelationalOperator):
            return element, i
    raise ValueError("No relational operator found. This is a bug.")


def determine_equation_type(parsed_groups: list[Group | Operator | RelationalOperator | ParenthesizedGroup]) -> int | bool:
    identity = get_equation_identity(parsed_groups)
    if len(identity.variable_count) == 0 and not identity.prove:
        return solve_basic(parsed_groups)  # type: ignore  # Need to find a way to fix the hints

    elif len(identity.variable_count) == 0 and identity.prove:
        relational_operator, index = get_relational_operator_position(parsed_groups)
        first, second = parsed_groups[:index], parsed_groups[index + 1:]
        return relational_operator(first=solve_basic(first), second=solve_basic(second))  # type: ignore

    raise NotImplementedError
