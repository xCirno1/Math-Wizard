from typing import TypeVar, TypeAlias

from numsy.parser import Operator, Group, ParenthesizedGroup, RelationalOperator, Fraction

T_RO = TypeVar('T_RO', bound=RelationalOperator)

mul_and_div = [Operator.Mul, Operator.Div]
No_RO: TypeAlias = list[Group | Operator | ParenthesizedGroup | Fraction]
CompleteEquation: TypeAlias = list[Group | Operator | T_RO | ParenthesizedGroup | Fraction]
Maybe_RO: TypeAlias = No_RO | CompleteEquation
Tuple_NO_RO: TypeAlias = tuple[Group | Operator | ParenthesizedGroup | Fraction]
