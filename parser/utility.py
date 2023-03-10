from __future__ import annotations

from decimal import Decimal

from .objects import Number, Group, Variable, Operator, ParenthesizedGroup, RelationalOperator

MaybeRO = list[Group | Operator | RelationalOperator | ParenthesizedGroup] | list[Group | Operator | ParenthesizedGroup]


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


def prettify_output(__object: MaybeRO, indent: int = 0, base: bool = True):
    indent += 1
    string = ""
    if isinstance(__object, list):
        for count, group in enumerate(__object):
            spacing = "" if not base else "\n"
            _indent = indent if base else indent + 1
            if isinstance(group, Group):
                string += f"{spacing}{tab * (_indent - 1)}Group {count}:\n"
                string += preetify_variable(group.variable, _indent)
                string += preetify_number(group.number, _indent)
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


def groups_to_string(groups: MaybeRO):
    string = ""
    for index, group in enumerate(groups):
        if isinstance(group, Group):
            neg = " - " if group.number.is_negative else ""

            if neg and index != 0 and isinstance(groups[index - 1], Operator):
                neg = " -"

            var = group.variable.name if group.variable else ""
            val = abs(group.get_real_value()[-1])
            val = "" if val == Decimal("1") and var else val

            if var and group.number.value == 0:
                val = var = ""

            _pow = groups_to_string(group.power) if group.power else ""
            _pow = f"^({_pow})" if len(group.power) > 1 else f"^{_pow}" if _pow else ""
            string += f"{neg}{val}{var}{_pow}"

        elif isinstance(group, (Operator, RelationalOperator)):
            string += f" {group.symbol} "

        elif isinstance(group, ParenthesizedGroup):
            inside = groups_to_string(group.groups)  # Inside ParenthesizedGroup shouldn't be empty, so we are skipping that case
            _pow = groups_to_string(group.power) if group.power else ""
            _pow = f"^({_pow})" if len(group.power) > 1 else f"^{_pow}" if _pow else ""

            string += f"({inside}){_pow}"

    return string.strip()
