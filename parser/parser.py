from __future__ import annotations

from .utility import match_parentheses
from .errors import UnmatchedParenthesis
from .checker import check_integrity
from .objects import (
    Character,
    Group,
    Integrity,
    Variable,
    Operator,
    Equals,
    ParenthesizedGroup,
    LowerThan,
    LowerThanOrEquals,
    GreaterThan,
    GreaterThanOrEquals,
    NotEquals
)


def verify_type(character: str):
    # TODO: Refactor using enum
    if character.isdigit():
        return Character.digit
    elif character == "^":
        return Character.power
    elif character == "-":
        return Character.integrity
    elif character in "+/*":
        return Character.operator
    elif character in "()":
        return Character.opening_parentheses if character == "(" else Character.closing_parentheses
    elif character == ".":
        return Character.decimal
    elif character == "=":
        return Character.equals
    elif character == "≠":
        return Character.not_equals
    elif character == "<":
        return Character.lower_than
    elif character == ">":
        return Character.greater_than
    elif character == "≤":
        return Character.lower_than_or_equals
    elif character == "≥":
        return Character.greater_than_or_equals
    elif character == "!":
        return Character.exclamation

    return Character.variable


def parse_single_group(string: str) -> tuple[int, str]:  # This is to get the substring between the parentheses
    if string.startswith("("):
        opening, closing = match_parentheses(string)[0]  # Get the position of opening and closing parentheses
        return closing + 1, string[opening + 1:closing]
    after_obj = False
    for index, char in enumerate(string):
        _type = verify_type(char)
        if _type in (Character.operator, Character.integrity, Character.opening_parentheses) and after_obj:
            return index, string[:index]
        elif _type in (Character.digit, Character.variable):
            after_obj = True
        elif _type == Character.power:
            after_obj = False
    return len(string), string  # Until the end of the query


def substitute_unnecessary_differ(string: str):
    _dict = {
        ">=": "≥",
        "<=": "≤",
        "==": "="
    }
    for k, v in _dict.items():
        string = string.replace(k, v)
    return string


def parse_group(string: str, provided_group: Group | None = None, last_object: object = None, groups_only: bool = False, start_from: int = 0):
    string = substitute_unnecessary_differ(string)
    check_integrity(string)
    groups, last__object, group, jump_to, after_decimal, group_is_parent = [], last_object, provided_group or Group(), start_from, False, False
    for index, char in enumerate(string):
        if jump_to:
            if index == jump_to:
                jump_to = 0
            else:
                continue
        if char == " ":
            continue

        __type = verify_type(char)
        if __type is Character.decimal:
            after_decimal = True
        elif __type is Character.digit:
            group._is_base = False  # This is for the number 0, so the parser doesn't see it as a base group
            last__object = Character.digit
            if after_decimal:
                group.value.append_digit(char, decimal=True)
                continue
            if not group.power:
                group.value.append_digit(char)
        else:
            after_decimal = False

        if __type is Character.integrity:  # Remove ambiguity between negative and subtraction
            if last__object not in (Character.operator, Integrity.negative):  # We need to create a new group object
                if not group._is_base:
                    groups.append(group)
                group = Group()

            group.value.is_negative = not group.value.is_negative  # This is for handling '--' (double negative) situation

            last__object = Integrity.negative

        elif __type is Character.power:
            last__object = Character.power
            i, rest = parse_single_group(string[index + 1:])
            power = parse_group(rest, last_object=last__object, groups_only=groups_only)
            if group_is_parent:
                jump_to, groups[-1].power = index + 1 + i, power
            else:
                jump_to, group.power = index + 1 + i, power

        elif __type is Character.opening_parentheses:
            if not group._is_base:
                groups.append(group)
            i, rest = parse_single_group(string[index:])
            content = parse_group(rest, last_object=last__object, groups_only=groups_only)
            par = ParenthesizedGroup(content)
            if last__object == Integrity.negative:
                par.is_negative = group.value.is_negative
            groups.append(par)
            jump_to = index + i
            group_is_parent = True
            group = Group()

        elif __type is Character.closing_parentheses:
            raise UnmatchedParenthesis(index + 1, is_closing_parenthesis=True)

        elif __type is Character.operator:
            last__object = Character.operator
            if not group._is_base:
                groups.append(group)
            if not groups_only:
                groups.append(Operator(char))
            group = Group()

        elif __type is Character.variable:
            group.variable = Variable(char)

        elif __type in (Character.equals, Character.greater_than, Character.greater_than_or_equals, Character.lower_than, Character.lower_than_or_equals, Character.not_equals):
            last__object = __type
            entry = {
                Character.equals: Equals,
                Character.greater_than: GreaterThan,
                Character.greater_than_or_equals: GreaterThanOrEquals,
                Character.lower_than: LowerThan,
                Character.lower_than_or_equals: LowerThanOrEquals,
                Character.not_equals: NotEquals
            }
            if not group._is_base:
                groups.append(group)
            groups.append(entry[__type](char))
            group = Group()

    if not group._is_base:
        groups.append(group)
    return groups
