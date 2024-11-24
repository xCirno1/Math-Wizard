from __future__ import annotations

import decimal

from decimal import Decimal
from typing import TYPE_CHECKING

from .objects import Number, Group, Variable, Operator, ParenthesizedGroup, RelationalOperator, Fraction

if TYPE_CHECKING:
    from numsy.solver.datatype import Maybe_RO
    from numsy.solver.core import Result, NoSolution


VALID_OBJECTS = (Group, Operator, ParenthesizedGroup, RelationalOperator, Fraction)


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


def prettify_variable(variable_object: Variable | None, indent: int = 1):
    string = ""
    name = variable_object if variable_object is None else variable_object.name
    string += f"{tab * indent}┣ Variable name: {name}\n"
    return string


def prettify_number(number_object: Number, indent: int = 1):
    string = ""
    value = str(number_object.integer) + (f".{number_object.decimal}" if number_object.decimal else "")
    string += f"{tab * indent}┣ Value: {value}\n"
    string += f"{tab * indent}┣ Negative: {number_object.is_negative}\n"
    return string


def prettify_output(__object: Maybe_RO, indent: int = 0, base: bool = True):
    indent += 1
    string = ""
    if isinstance(__object, list):
        for count, group in enumerate(__object):
            spacing = "" if not base else "\n"
            _indent = indent if base else indent + 1
            if isinstance(group, Group):
                string += f"{spacing}{tab * (_indent - 1)}Group {count}:\n"
                string += prettify_variable(group.variable, _indent)
                string += prettify_number(group.number, _indent)
                if group.power:
                    string += f"{tab * _indent}┣ Powers:\n"
                    string += prettify_output(group.power, _indent, base=False)
                else:
                    string += f"{tab * _indent}┣ Powers: -\n"
            elif isinstance(group, ParenthesizedGroup):
                string += f"Parentheses:\n"
                string += prettify_output(group.groups, _indent - 1, base=False)

            elif isinstance(group, Operator):
                string += f"{spacing}{tab * (_indent - 1)}Operator: {group.symbol}\n"
    return string


def groups_to_string(groups: Maybe_RO | Result | NoSolution):
    string = ""
    if isinstance(groups, VALID_OBJECTS):
        return groups_to_string([groups])
    if isinstance(groups, Decimal):
        return str(truncate_trailing_zero(groups))
    if not isinstance(groups, list):  # NoSolution or Result instances
        return str(groups)
    for index, group in enumerate(groups):
        if isinstance(group, Group):
            neg = " - " if group.number.is_negative else ""

            if neg and (isinstance((before := groups[index - 1]), (Operator, RelationalOperator)) or index == 0):
                neg = "-"
                if index != 0 and before == Operator("+"):
                    neg = " - "

            var = group.variable.name if group.variable else ""
            val = truncate_trailing_zero(abs(group.get_value()))
            val = "" if val == Decimal("1") and var else val
            _pow = ""
            if group.power and not (isinstance((p := group.power[0]), Group) and p.number.integer == 1):
                _pow = groups_to_string(group.power) if group.power else ""
            _pow = f"^({_pow})" if len(group.power) > 1 else f"^{_pow}" if _pow else ""
            string += f"{neg}{val}{var}{_pow}"

        elif isinstance(group, (Operator, RelationalOperator)):
            check = isinstance(_next := groups[index + 1], Group) and _next.number.is_negative
            check2 = isinstance(_next := groups[index + 1], ParenthesizedGroup) and _next.is_negative
            if group == Operator("+") and (check or check2):  # For example: 5 + -3 should be parsed as 5 - 3
                continue
            string += f" {group.symbol} "

        elif isinstance(group, ParenthesizedGroup):
            inside = groups_to_string(group.groups)  # Inside ParenthesizedGroup shouldn't be empty
            _pow = groups_to_string(group.power) if group.power else ""
            _pow = f"^({_pow})" if len(group.power) > 1 else f"^{_pow}" if _pow else ""
            neg = "-" if group.is_negative else ""
            string += f"{neg}({inside}){_pow}"

        elif isinstance(group, Fraction):
            string += f"{groups_to_string(group.numerator)}/{groups_to_string(group.denominator)}"

    return string.strip()


gts = groups_to_string


def truncate_trailing_zero(number: Decimal) -> Decimal:
    try:
        if "." not in (string := str(number)):
            return number
        whole, dec = string.split(".")
        after_e = ""
        if "E" in dec:
            dec, after_e = dec.split("E")
            after_e = "E" + after_e
        dec = dec.rstrip("0")
        return Decimal(f"{whole}{after_e}") if not dec else Decimal(f"{whole}.{dec}{after_e}")

    except decimal.InvalidOperation:
        raise RuntimeError("Expression is too large.") from None
