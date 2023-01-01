from __future__ import annotations

from .objects import Number, Group, Variable, Operator, ParenthesizedGroup, Equals


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
    name = variable_object if variable_object is None else variable_object.name
    print(f"{tab * indent}┣ Variable name: {name}")


def preetify_number(number_object: Number, indent: int = 1):
    value = str(number_object.value) + (f".{number_object.decimal}" if number_object.decimal else "")
    print(f"{tab * indent}┣ Value: {value}")
    print(f"{tab * indent}┣ Negative: {number_object.is_negative}")


def display_preetified_output(__object: list[Group | Operator | Equals | ParenthesizedGroup] | list[Group | Operator | ParenthesizedGroup], indent: int = 0, base: bool = True, string: str = ""):
    indent += 1
    if isinstance(__object, list):
        for count, group in enumerate(__object):
            spacing = "" if not base else "\n"
            _indent = indent if base else indent + 1
            if isinstance(group, Group):
                print(f"{spacing}{tab * (_indent - 1)}Group {count}:")
                preetify_variable(group.variable, _indent)
                preetify_number(group.value, _indent)
                if group.power:
                    print(f"{tab * _indent}┣ Powers:")
                    display_preetified_output(group.power, _indent, base=False)
                else:
                    print(f"{tab * _indent}┣ Powers: -")
            elif isinstance(group, ParenthesizedGroup):
                print(f"Parentheses:")
                preetify_output(group.groups, _indent - 1, base=False)  # type: ignore

            elif isinstance(group, Operator):
                print(f"{spacing}{tab * (_indent - 1)}Operator: {group.symbol}")


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
