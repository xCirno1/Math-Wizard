from __future__ import annotations

import parser

from decimal import Decimal


def test_basic_parenthesized_power():
    group: list[parser.Group] = parser.parse_group("2x^(3 + 5m - 6)", groups_only=True)

    assert len(group) == 1
    assert group[0].variable.name == "x"
    assert group[0].number.value == 2
    assert group[0].power[0].number.value == 3 and group[0].power[0].variable is None
    assert group[0].power[1].variable.name == "m"
    assert group[0].power[2].number.is_negative


def test_long_and_parenthesized_power():
    group: list[parser.Group] = parser.parse_group("2x^2 + 3 + 18x - 3 + 4x^(5x + 2)", groups_only=True)

    assert len(group) == 5
    assert group[0].variable.name == "x" and not group[0].number.is_negative and group[0].power[0].number.value == 2
    assert group[1].number.value == 3 and group[1].variable is None
    assert group[2].number.value == 18 and group[2].power == []
    assert group[3].number.is_negative and group[3].variable is None and group[3].number.value == 3
    assert (group[4].number.value == 4 and group[4].variable.name == "x" and group[4].power[0].number.value == 5 and
            group[4].power[1].number.value == 2)


def test_different_variable_power():
    group: list[parser.Group] = parser.parse_group("2m^4x", groups_only=True)

    assert len(group) == 1
    assert group[0].number.value == 2 and group[0].variable.name == "m"
    assert group[0].power[0].number.value == 4 and group[0].power[0].variable.name == "x"


def test_basic_double_digit_power():
    group: list[parser.Group] = parser.parse_group("10^10", groups_only=True)

    assert len(group) == 1
    assert group[0].number.value == 10
    assert group[0].power[0].number.value == 10


def test_parenthesized_and_nested_power():
    group: list[parser.Group] = parser.parse_group("5 + 2x^(3^-4y + 6)", groups_only=True)

    assert group[0].number.value == 5
    assert group[1].number.value == 2 and group[1].variable.name == "x"
    assert group[1].power[0].number.value == 3 and group[1].power[0].variable is None and not group[1].power[
        0].number.is_negative
    assert group[1].power[0].power[0].number.value == 4 and group[1].power[0].power[0].number.is_negative and \
           group[1].power[0].power[0].variable.name == "y"
    assert group[1].power[1].number.value == 6 and group[1].power[1].variable is None and not group[1].power[
        1].number.is_negative


def test_nested_power():
    group: list[parser.Group] = parser.parse_group("5 + 2x^3^-4y", groups_only=True)

    assert len(group) == 2
    assert group[1].power[0].number.value == 3 and group[1].power[0].variable is None
    assert group[1].power[0].power[0].number.value == 4 and group[1].power[0].power[0].variable.name == "y" and \
           group[1].power[0].power[0].number.is_negative


def test_complex_power():
    group: list[parser.Group] = parser.parse_group("2x^62 * 3^(2y^(3.2 - 2) + 4x^4)", groups_only=True)

    assert group[0].variable.name == "x" and group[0].number.value == 2 and group[0].power[0].variable is None and \
           group[0].power[0].number.value == 62
    assert group[1].number.value == 3 and group[1].variable is None and not group[1].number.is_negative
    assert group[1].power[0].number.value == 2 and group[1].power[0].variable.name == "y" and not group[1].power[
        0].number.is_negative
    assert group[1].power[0].power[0].number.value == 3 and group[1].power[0].power[0].variable is None and not \
    group[1].power[0].power[0].number.is_negative
    assert group[1].power[0].power[1].number.value == 2 and group[1].power[0].power[1].variable is None and \
           group[1].power[0].power[1].number.is_negative
    assert group[1].power[1].number.value == 4 and group[1].power[1].variable.name == "x" and not group[1].power[
        0].number.is_negative
    assert group[1].power[1].power[0].number.value == 4 and group[1].power[1].power[0].variable is None and not \
    group[1].power[1].power[0].number.is_negative


def test_complex_power_and_decimal():
    group: list[parser.Group] = parser.parse_group("2x^62.324 * 3.09^(2.89y^(3.22 - 2.8) + 4.9x^4.02)", groups_only=True)
    assert group[0].power[0].number.decimal == Decimal("0.324")
    assert group[1].number.decimal == Decimal("0.09")
    assert group[1].power[0].number.decimal == Decimal("0.89")
    assert group[1].power[0].power[0].number.decimal == Decimal("0.22") and group[1].power[0].power[1].number.decimal == Decimal("0.8")
    assert group[1].power[1].number.decimal == Decimal("0.9")
    assert group[1].power[1].power[0].number.decimal == Decimal("0.02")
