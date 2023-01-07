from parser import Group, Variable, Operator, ParenthesizedGroup, RelationalOperator

from .solve_basic import solve_basic


class EquationIdentity:
    def __init__(self):
        self.variable_count: dict[Variable, int] = {}
        self.relational_operators: list[tuple[RelationalOperator, int]] = []


def get_equation_identity(parsed_groups: list[Group | Operator | RelationalOperator | ParenthesizedGroup]) -> EquationIdentity:
    identity = EquationIdentity()
    for index, group in enumerate(parsed_groups):
        if isinstance(group, RelationalOperator):
            identity.relational_operators.append((group, index))

        if isinstance(group, (RelationalOperator, Operator, ParenthesizedGroup)):
            continue

        if (var := group.variable) is not None:  # There's variable
            identity.variable_count[var] = identity.variable_count.get(var, 0) + 1

    return identity


def determine_equation_type(parsed_groups: list[Group | Operator | RelationalOperator | ParenthesizedGroup]) -> int | bool:
    identity = get_equation_identity(parsed_groups)
    if len(identity.variable_count) == 0 and not identity.relational_operators:  # Basic PEMDAS
        return solve_basic(parsed_groups)  # type: ignore  # Need to find a way to fix the hints

    elif len(identity.variable_count) == 0 and identity.relational_operators:  # Basic PEMDAS with relational operator
        relational_operator, index = identity.relational_operators[0]  # TODO: Allow multiple relational operators
        first, second = parsed_groups[:index], parsed_groups[index + 1:]
        return relational_operator(first=solve_basic(first), second=solve_basic(second))  # type: ignore

    raise NotImplementedError
