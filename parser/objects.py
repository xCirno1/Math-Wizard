from __future__ import annotations

from functools import cached_property
from itertools import chain
from typing import TYPE_CHECKING, ClassVar
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
    Addition: ClassVar  # Workaround for: Cannot assign member "Addition" for type "type[Operator]" pyright error
    Add: ClassVar
    Division: ClassVar
    Div: ClassVar
    Multiplication: ClassVar
    Mul: ClassVar

    def __init__(self, symbol: str):
        self.symbol = symbol

    def __repr__(self):
        return f"<Operator symbol='{self.symbol}'>"

    def __hash__(self):
        return hash(self.symbol)

    def __eq__(self, other):
        return self.symbol == other.symbol if isinstance(other, Operator) else False


Operator.Addition = Operator.Add = Operator("+")
Operator.Division = Operator.Div = Operator("/")
Operator.Multiplication = Operator.Mul = Operator("*")


class Number:
    def __init__(self):
        self._integer: int = 0
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
    def from_data(cls, value: Decimal | int, decimal: Decimal | str = "0.0", is_negative: bool = False, self: Number | None = None) -> Number:
        self = self or cls()
        self.decimal = Decimal(decimal)
        if int(value) == value:
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

    def copy(self):
        new = Number()
        new._integer = self._integer
        new.is_negative = self.is_negative
        new.decimal = self.decimal
        new.modified = self.modified
        return new

    @property
    def integer(self) -> int:
        return self._integer

    @integer.setter
    def integer(self, value: int | float):  # Float here is only to fix the typechecker
        if value % 1 == 0:
            value = int(value)
        if not isinstance(value, int):
            raise TypeError("Integer should be class int.")
        self._integer = abs(value)
        if value < 0:
            self.is_negative = True

    @property
    def _is_base(self):
        return not self.integer and not self.decimal and not self.modified

    @_is_base.setter
    def _is_base(self, value):
        self.modified = not value

    @cached_property
    def factors(self) -> set[int]:
        if self.value >= 1E10:
            raise ValueError("Value is too large.")
        if (n := abs(self.value)) % 1 != 0:
            return {1}  # RFC: Should we raise error, return {1} or return {1, self.value}?
        return set(chain.from_iterable([i, int(n) // i] for i in range(1, int(n.sqrt()) + 1) if n % i == 0))

    def __repr__(self):
        return f"<Number integer={self.integer} decimal={self.decimal} negative={self.is_negative}>"

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
        return cls.from_data(value=Number.from_data(abs(Decimal(num)), Decimal(f"0.{dec}"), value < 0), *args, **kwargs)

    def get_value(self) -> Decimal:
        return self.number.value

    def copy(self):
        new = Group()
        new.number = self.number.copy()
        new.variable = self.variable
        new.power = self.power
        new.modified = self.modified
        return new

    @property
    def _is_base(self):
        return self.variable is None and not self.power and self.number._is_base and not self.modified

    @_is_base.setter
    def _is_base(self, value):
        self.modified = not value

    @property
    def contains_variable(self) -> bool:
        return self.variable is not None or self.power_contains_variable

    @property
    def power_contains_variable(self) -> bool:
        return any(group.contains_variable for group in self.power if isinstance(group, (Group, ParenthesizedGroup)))

    @property
    def is_zero(self) -> bool:
        return self.variable is None and self.get_value() == 0  # Maybe remove `self.variable is None` check

    def __mul__(self, second: Group):
        from solver.solve_basic import solve_basic

        if not isinstance(second, Group):
            raise TypeError(f"Cannot multiply `Group` with {second.__class__}.")
        new = Group()
        if all((self.variable, second.variable)):  # Both has variable, for example 5x * 3x^2, become 15x^3
            if self.variable == second.variable:
                if self.power_contains_variable or second.power_contains_variable:  # Cannot directly combine here
                    raise NotImplementedError("Group with variable-contained power is not supported yet.")
                else:
                    # Using solve_basic here to simplify power to a single group
                    total_pow = (solve_basic(self.power) or 1) + (solve_basic(second.power) or 1)
                    new.power = [Group().from_value(Decimal(total_pow))]
            else:
                raise NotImplementedError("Multiplying groups which have different variables is not supported yet.")
        variable = self.variable if self.variable else second.variable
        coefficient = self.get_value() * second.get_value()
        new.variable = variable
        new.number.value = coefficient
        return new

    def __repr__(self):
        return f"<Group number={self.number} variable={self.variable} power={self.power}>"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.number == other.number and self.variable == other.variable and self.power == other.power

    def __hash__(self):
        return hash(self.variable) + hash(self.number) + hash(tuple(self.power))


class RelationalOperator:
    def __init__(self, symbol: str, func):
        self.symbol = symbol
        self.func = func

    def __call__(self, *args, **kwargs) -> bool:
        return self.func(**kwargs)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.symbol == other.symbol

    def __hash__(self):
        return hash(self.symbol)


Equals = RelationalOperator("=", lambda first, second: first == second)
NotEquals = RelationalOperator("!=", lambda first, second: first != second)
LowerThan = RelationalOperator("<", lambda first, second: first < second)
GreaterThan = RelationalOperator(">", lambda first, second: first > second)
GreaterThanOrEquals = RelationalOperator(">=", lambda first, second: first >= second)
LowerThanOrEquals = RelationalOperator("<=", lambda first, second: first <= second)


class ParenthesizedGroup:
    def __init__(self, groups: No_RO, power: No_RO | None = None):
        self.groups = groups
        self.power = power or []
        self.is_negative = False

    def __eq__(self, other):
        return isinstance(other, ParenthesizedGroup) and self.groups == other.groups

    def __hash__(self):
        return sum(hash(group) for group in self.groups)

    def __repr__(self):
        return f"<ParenthesizedGroup groups={[group for group in self.groups]} power={[p for p in self.power]} is_negative={self.is_negative}>"

    @property
    def contains_variable(self) -> bool:
        return any(group.contains_variable for group in self.groups if isinstance(group, (Group, ParenthesizedGroup)))

    @property
    def power_contains_variable(self) -> bool:
        return any(group.contains_variable for group in self.power if isinstance(group, (Group, ParenthesizedGroup)))


class Fraction:
    def __init__(self, numerator: No_RO, denominator: No_RO):
        self.numerator = numerator
        if isinstance(deno := denominator[0], Group) and deno.number.value == 0:
            # This is only raised when the denominator is given explicitly as zero, we don't raise in case of 1/(2 - 2)
            raise ZeroDivisionError("Fraction denominator cannot be 0.")
        self.denominator = denominator

    def __repr__(self):
        return f"<Fraction numerator={[group for group in self.numerator]} denominator={[group for group in self.denominator]}>"

    def __eq__(self, other):
        return isinstance(other, Fraction) and self.numerator == other.numerator and self.denominator == other.denominator

    def __hash__(self):
        return id(self)  # Not good

    @property
    def contains_variable(self):
        return any(group.contains_variable for group in (self.numerator + self.denominator) if isinstance(group, (Group, ParenthesizedGroup)))
