from __future__ import annotations

from decimal import Decimal

from .utility import match_parentheses
from .errors import UnmatchedParenthesis, ParseError
from .checker import check_integrity
from .objects import (
    Character,
    Group,
    Integrity,
    Variable,
    Operator,
    Equals,
    Number,
    ParenthesizedGroup,
    LowerThan,
    LowerThanOrEquals,
    GreaterThan,
    GreaterThanOrEquals,
    NotEquals
)


def verify_type(character: str):
    if character.isdigit():
        return Character.digit
    match character:
        case "^": return Character.power
        case "-": return Character.integrity
        case "+" | "/" | "*": return Character.operator
        case "(" | ")": return Character.opening_parentheses if character == "(" else Character.closing_parentheses
        case ".": return Character.decimal
        case "=": return Character.equals
        case "≠": return Character.not_equals
        case "<": return Character.lower_than
        case ">": return Character.greater_than
        case "≤": return Character.lower_than_or_equals
        case "≥": return Character.greater_than_or_equals
        case "!": return Character.exclamation
        # Denoted with "E" (uppercase) to avoid ambiguity with the euler constant "e" (lowercase)
        case "E": return Character.scientific

    return Character.variable


RO = (
    Character.equals,
    Character.greater_than,
    Character.greater_than_or_equals,
    Character.lower_than,
    Character.lower_than_or_equals,
    Character.not_equals
)


def parse_single_group(string: str) -> tuple[int, str]:  # This is to get the substring between the parentheses
    if string.startswith("("):
        opening, closing = match_parentheses(string)[0]  # Get the position of opening and closing parentheses
        return closing + 1, string[opening + 1:closing]
    after_obj = False
    for index, char in enumerate(string):
        _type = verify_type(char)
        if _type in (Character.operator, Character.integrity, Character.opening_parentheses, *RO) and after_obj:
            return index, string[:index]
        elif _type in (Character.digit, Character.variable):
            after_obj = True
        elif _type == Character.power:
            after_obj = False
    return len(string), string  # Until the end of the query


def replace_to_valid_RO(string: str):
    _dict = {
        ">=": "≥",
        "<=": "≤",
        "==": "="
    }
    for k, v in _dict.items():
        string = string.replace(k, v)
    return string


def parse_group(string: str, provided_group: Group | None = None, last_object: object = None,
                groups_only: bool = False, start_from: int = 0, _from_recursion: bool = False):
    if not _from_recursion:  # Slight performance
        string = replace_to_valid_RO(string)
        check_integrity(string)
    groups, last_obj, group, jump_to, after_decimal, group_is_parent = [], last_object, provided_group or Group(), start_from, False, False
    scientific_value = None
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
            if last_obj is Character.scientific:
                groups.append(Operator("*"))
                group = Group.from_value(Decimal("10"))  # Create empty group to convert from E to "* 10^n"
                i, rest = parse_single_group(string[index:])
                scientific_value = "+" if scientific_value is None else scientific_value
                group.power = [Group.from_value(Decimal(scientific_value + rest))]
                jump_to, scientific_value = index + i, None
                # Make this a parent group to not make problems with PEMDAS operation
                groups.append(ParenthesizedGroup([groups.pop(-2), groups.pop(-1), group]))
                group = Group()
                last_obj = Character.digit
                continue

            if last_obj is Character.variable:
                raise ParseError(f"Digits cannot appear after variable names (found in position {index}). Perhaps you missed \"*\"?")

            group._is_base = False  # This is for the number 0, so the parser doesn't see it as a base group
            last_obj = Character.digit
            if after_decimal:
                group.number.append_digit(char, decimal=True)
                continue
            if not group.power and last_obj is not Character.scientific:
                group.number.append_digit(char)
        else:
            after_decimal = False

        if __type is Character.integrity:  # Remove ambiguity between negative and subtraction
            if last_obj is Character.scientific:
                scientific_value = "-"
                continue
            if groups and isinstance(groups[-1], ParenthesizedGroup):
                groups.append(Operator("+"))
            if last_obj not in (Character.operator, Integrity.negative):  # We need to create a new group object
                if not group._is_base:
                    groups.append(group)
                group = Group()
            # This is for handling '--' (double negative) situation
            group.number.is_negative = not group.number.is_negative

            last_obj = Integrity.negative

        elif __type is Character.power:
            last_obj = Character.power
            i, rest = parse_single_group(string[index + 1:])
            power = parse_group(rest, groups_only=groups_only)
            if group_is_parent:
                jump_to, groups[-1].power = index + 1 + i, power
            else:
                jump_to, group.power = index + 1 + i, power

        elif __type is Character.opening_parentheses:
            if not group._is_base:
                groups.append(group)
            i, rest = parse_single_group(string[index:])
            content = parse_group(rest, groups_only=groups_only)
            par = ParenthesizedGroup(content)
            if last_obj is Integrity.negative:
                par.is_negative = group.number.is_negative
            groups.append(par)
            jump_to = index + i
            group_is_parent = True
            group = Group()

        elif __type is Character.closing_parentheses:
            raise UnmatchedParenthesis(index + 1, is_closing_parenthesis=True)

        elif __type is Character.operator:
            if last_obj is Character.scientific and char == "+":
                scientific_value = "+"
                continue
            elif last_obj is Character.scientific and char != "+":
                raise TypeError(f"Unsupported operator {char} after scientific notation E.")
            last_obj = Character.operator
            if not group._is_base:
                groups.append(group)
            if not groups_only:
                groups.append(Operator(char))
            group = Group()

        elif __type is Character.variable:
            group.variable = Variable(char)
            if last_obj is not Character.digit:
                group.number.integer = 1
            last_obj = Character.variable

        elif __type in RO:
            last_obj = __type
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
            groups.append(entry[__type])
            group = Group()

        elif __type is Character.scientific:
            last_obj = Character.scientific
            groups.append(group)

    if not group._is_base:
        groups.append(group)
    return groups
