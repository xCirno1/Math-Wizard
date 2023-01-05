from __future__ import annotations

from .objects import Number, Group, Variable, Operator, ParenthesizedGroup, Equals, RelationalOperator


def verify_parentheses(s: str) -> bool:
    if len(s) % 2 != 0:  # len() is O(1), so, it is faster on large strings
        return False
    match = {
        "]": "[",
        "}": "{",
        ")": "(",
    }
    expecting = []
    for char in s:
        if char in match.values():
            expecting.append(char)
        elif char in match:
            try:
                if expecting.pop() != match[char]:
                    return False
            except IndexError:
                return False
    return not expecting


def match_parentheses(string: str) -> list[tuple[int, int]]:
    stack: list[int] = []
    parentheses_locs: dict[int, int] = {}
    for index, character in enumerate(string):
        if character == '(':
            stack.append(index)
        elif character == ')':
            parentheses_locs[stack.pop()] = index
            if not stack:
                return list(sorted([(k, v) for k, v in parentheses_locs.items()], key=lambda e: e[0]))
    return list(sorted([(k, v) for k, v in parentheses_locs.items()], key=lambda e: e[0]))


tab = "\t"


def preetify_variable(variable_object: Variable | None, indent: int = 1):
    string = ""
    name = variable_object if variable_object is None else variable_object.name
    string += f"{tab * indent}┣ Variable name: {name}\n"
    return string


def preetify_number(number_object: Number, indent: int = 1):
    string = ""
    value = str(number_object.value) + (f".{number_object.decimal}" if number_object.decimal else "")
    string += f"{tab * indent}┣ Value: {value}\n"
    string += f"{tab * indent}┣ Negative: {number_object.is_negative}\n"
    return string


def prettify_output(__object: list[Group | Operator | RelationalOperator | ParenthesizedGroup] | list[Group | Operator | ParenthesizedGroup], indent: int = 0, base: bool = True):
    indent += 1
    string = ""
    if isinstance(__object, list):
        for count, group in enumerate(__object):
            spacing = "" if not base else "\n"
            _indent = indent if base else indent + 1
            if isinstance(group, Group):
                string += f"{spacing}{tab * (_indent - 1)}Group {count}:\n"
                string += preetify_variable(group.variable, _indent)
                string += preetify_number(group.value, _indent)
                if group.power:
                    string += f"{tab * _indent}┣ Powers:\n"
                    string += prettify_output(group.power, _indent, base=False)
                else:
                    string += f"{tab * _indent}┣ Powers: -\n"
            elif isinstance(group, ParenthesizedGroup):
                string += f"Parentheses:\n"
                string += prettify_output(group.groups, _indent - 1, base=False)  # type: ignore

            elif isinstance(group, Operator):
                string += f"{spacing}{tab * (_indent - 1)}Operator: {group.symbol}\n"
    return string


def readjust_index(original_string: str, to_readjust: int):
    index = 0
    differ = 0
    for ptr, char in enumerate(original_string):
        if char == " ":
            if index <= to_readjust:
                index -= 1
                differ += 1
            else:
                return to_readjust + differ
        index += 1
    return len(original_string) - 1
