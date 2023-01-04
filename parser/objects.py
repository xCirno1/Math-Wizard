from __future__ import annotations

from decimal import Decimal


class Character:
    digit = 1
    power = 2
    variable = 3
    operator = 4
    opening_parentheses = 5
    closing_parentheses = 6
    integrity = 7
    space = 8
    decimal = 9
    equals = 10
    exclamation = 11
    greater_than = 12
    lower_than = 13


class Positive: ...
class Negative: ...


class Integrity:
    negative = Positive
    positive = Negative


class Operator:
    def __init__(self, symbol: str):
        self.symbol = symbol

    def __repr__(self):
        return f"<Operator symbol='{self.symbol}'>"

    def __hash__(self):
        return hash(self.symbol)

    def __eq__(self, other):
        return self.symbol == other.symbol if isinstance(other, Operator) else False


class Number:
    def __init__(self):
        self.value: int = 0
        self.is_negative = False
        self.decimal: Decimal | None = None
        self.modified = False

    @classmethod
    def from_data(cls, value: int | float, decimal: float | str = 0, is_negative: bool = False) -> Number:
        self = cls()
        self.decimal = Decimal(decimal)
        if isinstance(value, int):
            self.value = value
        else:
            digit, dec = str(value).split(".")
            self.value, self.decimal = int(digit), Decimal(f"0.{dec}")
        self.is_negative = is_negative
        return self

    def append_digit(self, string: str, decimal: bool = False) -> Number:
        if decimal:
            if self.decimal is None:
                self.decimal = Decimal(f"0.{string}")
            else:
                self.decimal = Decimal(f"{self.decimal}{string}")
        else:
            self.value = int(str(self.value) + string)
        return self

    @property
    def _is_base(self):
        return not self.value and not self.decimal and not self.modified

    @_is_base.setter
    def _is_base(self, value):
        self.modified = not value

    def __repr__(self):
        return f"<Number value={self.value} decimal={self.decimal} negative={self.is_negative}>"


class Variable:
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f"<Variable name={self.name}>"


class Group:
    def __init__(self):
        self.variable: Variable | None = None
        self.value: Number = Number()
        self.power: list[Group | Operator | ParenthesizedGroup] = []
        self.childs = []  # Currently, it should hold 1 object, Variable
        self.modified = False

    @classmethod
    def from_data(cls, value: Number, variable: Variable | None = None, power: list[Group | Operator | ParenthesizedGroup] | None = None) -> Group:
        self = cls()
        self.variable = variable
        self.value = value or self.value
        self.power = power if power is not None else []
        return self

    def get_real_value(self) -> tuple[Group, int, Decimal | int]:
        total = self.value.value + (d if (d := self.value.decimal) else 0)
        total *= -1 if self.value.is_negative else 1
        return self, self.value.value, total

    @property
    def _is_base(self):
        return self.variable is None and not self.power and not self.childs and self.value._is_base and not self.modified

    @_is_base.setter
    def _is_base(self, value):
        self.modified = not value

    def __repr__(self):
        return f"<Group number={self.value} variable={self.variable} power={self.power}>"


class Equals:
    def __eq__(self, other):
        return isinstance(other, self.__class__)


class ParenthesizedGroup:
    def __init__(self, groups: list[Group | Operator | ParenthesizedGroup], power: list[Group | Operator | ParenthesizedGroup] | None = None):
        self.groups = groups
        self.power = power or []
        self.is_negative = False

    def __repr__(self):
        return f"<ParenthesizedGroup groups={[group for group in self.groups]} power={[p for p in self.power]} is_negative={self.is_negative}>"
