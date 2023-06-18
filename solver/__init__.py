import logging

from typing import TypeVar

from parser import Group, Operator, ParenthesizedGroup, parse_group, RelationalOperator, gts
from .utility import determine_equation_type
from .datatype import CompleteEquation, Maybe_RO

# Setup logging
handler = logging.FileHandler('logs.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

_log = logging.getLogger(__name__)
_log.setLevel(logging.DEBUG)
_log.addHandler(handler)

T = TypeVar("T", bound=Maybe_RO)


def clean_equation(parsed_group: T, base: bool = True) -> T:
    if base:
        _log.info("Cleaning equation '%s'", gts(parsed_group))
    for index, group in enumerate(parsed_group):
        if not base and isinstance(group, RelationalOperator):
            raise TypeError("Relational operators cannot be inside power or ParenthesizedGroup.")

        if isinstance(group, ParenthesizedGroup):
            group.groups = clean_equation(group.groups, base=False)
            group.power = clean_equation(group.power, base=False)
        elif isinstance(group, Group):
            group.power = clean_equation(group.power, base=False)
        if index == 0:
            continue
        before = parsed_group[index - 1]
        if isinstance(group, (Group, ParenthesizedGroup)) and isinstance(before, (Group, ParenthesizedGroup)):
            if isinstance(group, ParenthesizedGroup):
                if group.is_negative:
                    parsed_group.insert(index, Operator("+"))
                else:  # For multiplications with ParenthesizedGroup without the "*" Operator
                    parsed_group.insert(index, Operator("*"))
            else:  # For possibly negative values or double negative sign ('--')
                parsed_group.insert(index, Operator("+"))
    if base:
        _log.info("Finished cleaning equation, got '%s'", gts(parsed_group))
    return parsed_group


def solve(equation: CompleteEquation | str):
    _log.info("Solving equation '%s'", gts(equation) if isinstance(equation, list) else equation)
    if isinstance(equation, str):
        _log.info("Parsing equation...")
        equation = parse_group(equation)
        _log.info("Finished parsing equation, got '%s'", gts(equation))
    equation = clean_equation(equation)
    result = determine_equation_type(equation)
    _log.info("Equation solved, got '%s' as the answer!", gts(result) if isinstance(result, list) else result)

    return result  # We shouldn't convert to string automatically here
