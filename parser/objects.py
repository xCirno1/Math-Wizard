from __future__ import annotations

from typing import TYPE_CHECKING

from decimal import Decimal

if TYPE_CHECKING:
    from solver.datatype import No_RO


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
    greater_than_or_equals = 14
    lower_than_or_equals = 15
    not_equals = 16
    scientific = 17


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
        self.integer: int = 0
        self.is_negative = False
        self.decimal: Decimal = Decimal(0)
        self.modified = False

    @property
    def value(self) -> Decimal:
        return Decimal(f"{'-' if self.is_negative else ''}{self.integer + self.decimal}")

    @value.setter
    def value(self, value: Decimal):
        self.from_data(value, self=self)

    @classmethod
    def from_data(cls, value: Decimal, decimal: Decimal | str = "0.0", is_negative: bool = False, self: Number | None = None) -> Number:
        self = self or cls()
        self.decimal = Decimal(decimal)
        if isinstance(value, Decimal) and value % 1 == 0:  # Same as "if value is integer"
            self.integer = int(abs(value))
        else:
            digit, dec = str(value).split(".")
            self.integer, self.decimal = abs(int(digit)), Decimal(f"0.{dec}")
        self.is_negative = is_negative or value < 0
        return self

    def append_digit(self, string: str, decimal: bool = False) -> Number:
        if decimal:
            if str(self.decimal) == "0":  # This is for leading 0 bug, for example '0.03'
                self.decimal = Decimal(f"0.{string}")
            else:
                self.decimal = Decimal(f"{self.decimal:f}{string}")
        else:
            self.integer = int(str(self.integer) + string)
        return self

    @property
    def _is_base(self):
        return not self.integer and not self.decimal and not self.modified

    @_is_base.setter
    def _is_base(self, value):
        self.modified = not value

    def __repr__(self):
        return f"<Number value={self.integer} decimal={self.decimal} negative={self.is_negative}>"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.integer == other.integer and self.is_negative == other.is_negative and self.decimal == other.decimal

    def __hash__(self):
        return hash(self.integer) + hash(self.is_negative) + hash(self.decimal)


class Variable:
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f"<Variable name={self.name}>"

    def __eq__(self, other):
        return isinstance(other, Variable) and self.name == other.name

    def __hash__(self):
        return hash(self.name)


class Group:
    def __init__(self):
        self.variable: Variable | None = None
        self.number: Number = Number()
        self.power: No_RO = []
        self.childs = []  # Currently, it should hold 1 object, Variable
        self.modified = False

    @classmethod
    def from_data(cls, value: Number, variable: Variable | None = None, power: No_RO | None = None) -> Group:
        self = cls()
        self.variable = variable
        self.number = value or self.number
        self.power = power if power is not None else []
        return self

    @classmethod
    def from_value(cls, value: Decimal, *args, **kwargs):
        num, dec = value, "0"
        if "." in (val := str(value)):
            num, dec = val.split(".")
        return cls.from_data(value=Number.from_data(abs(Decimal(num)), Decimal(dec), value < 0), *args, **kwargs)

    def get_value(self) -> Decimal:
        return self.number.value

    @property
    def _is_base(self):
        return self.variable is None and not self.power and not self.childs and self.number._is_base and not self.modified

    @_is_base.setter
    def _is_base(self, value):
        self.modified = not value

    def is_same_variable(self, other: Group):
        return self.power == other.power and self.variable == other.variable

    def __repr__(self):
        return f"<Group number={self.number} variable={self.variable} power={self.power}>"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.number == other.number and self.variable == other.variable and self.power == other.power

    def __hash__(self):
        return hash(self.variable) + hash(self.number) + hash(tuple(self.power))


class RelationalOperator:
    def __init__(self, symbol):
        self.symbol = symbol

    def __call__(self, *args, **kwargs):
        classes = {
            Equals: lambda first, second: kwargs["first"] == kwargs["second"],
            NotEquals: lambda first, second: kwargs["first"] != kwargs["second"],
            LowerThan: lambda first, second: kwargs["first"] < kwargs["second"],
            GreaterThan: lambda first, second: kwargs["first"] > kwargs["second"],
            GreaterThanOrEquals: lambda first, second: kwargs["first"] >= kwargs["second"],
            LowerThanOrEquals: lambda first, second: kwargs["first"] <= kwargs["second"],
        }
        return classes[self.__class__](**kwargs)  # type: ignore

    def __eq__(self, other):
        return isinstance(other, self.__class__)


class Equals(RelationalOperator): ...
class NotEquals(RelationalOperator): ...
class LowerThan(RelationalOperator): ...
class GreaterThan(RelationalOperator): ...
class GreaterThanOrEquals(Equals, GreaterThan): ...


class LowerThanOrEquals(Equals, LowerThan):
    def __call__(self, *args, **kwargs):
        return kwargs["first"] <= kwargs["second"]


class ParenthesizedGroup:
    def __init__(self, groups: No_RO, power: No_RO | None = None):
        self.groups = groups
        self.power = power or []
        self.is_negative = False

    def __repr__(self):
        return f"<ParenthesizedGroup groups={[group for group in self.groups]} power={[p for p in self.power]} is_negative={self.is_negative}>"


class Fraction:
    def __init__(self, numerator: No_RO, denominator: No_RO):
        self.numerator = numerator
        if isinstance(deno := denominator[0], Group) and deno.number.value == 0:
            # This is only raised when the denominator is definitely zero, we don't raise in case of 1/(2 - 2)
            raise ZeroDivisionError("Fraction denominator cannot be 0.")
        self.denominator = denominator

    def __repr__(self):
        return f"<Fraction numerator={[group for group in self.numerator]} denominator={[group for group in self.denominator]}>"

    def __eq__(self, other):
        return isinstance(other, Fraction) and self.numerator == other.numerator and self.denominator == other.denominator