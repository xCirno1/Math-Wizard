from parser import Group, Equals, Variable, Operator, ParenthesizedGroup

from .solve_basic import solve_basic


class EquationIdentity:
    variable_count: dict[Variable, int] = {}
    prove: bool = False


def get_equation_identity(parsed_groups: list[Group | Operator | Equals | ParenthesizedGroup]) -> EquationIdentity:
    identity = EquationIdentity()
    for group in parsed_groups:
        if isinstance(group, Equals):
            identity.prove = True
        if isinstance(group, (Equals, Operator, ParenthesizedGroup)):
            continue

        if (var := group.variable) is not None:  # There's variable
            identity.variable_count[var] = identity.variable_count.get(var, 0) + 1

    return identity


def determine_equation_type(parsed_groups: list[Group | Operator | Equals | ParenthesizedGroup]) -> int:  # TODO: This is currently `int`
    identity = get_equation_identity(parsed_groups)
    if len(identity.variable_count) == 0 and not identity.prove:
        return solve_basic(parsed_groups)  # type: ignore
    return 1
