from parser import Operator, Group, ParenthesizedGroup, RelationalOperator, Fraction

mul_and_div = [Operator("*"), Operator("/")]
No_RO = list[Group | Operator | ParenthesizedGroup | Fraction]
CompleteEquation = list[Group | Operator | RelationalOperator | ParenthesizedGroup | Fraction]
Maybe_RO = No_RO | CompleteEquation
