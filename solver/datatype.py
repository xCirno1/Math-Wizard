from typing import TypeVar

from parser import Operator, Group, ParenthesizedGroup, RelationalOperator, Fraction

T_RO = TypeVar('T_RO', bound=RelationalOperator)

mul_and_div = [Operator("*"), Operator("/")]
No_RO = list[Group | Operator | ParenthesizedGroup | Fraction]
CompleteEquation = list[Group | Operator | T_RO | ParenthesizedGroup | Fraction]
Maybe_RO = No_RO | CompleteEquation
