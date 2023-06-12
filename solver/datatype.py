from parser import Operator, Group, ParenthesizedGroup, RelationalOperator

mul_and_div = [Operator("*"), Operator("/")]
No_RO = list[Group | Operator | ParenthesizedGroup]
CompleteEquation = list[Group | Operator | RelationalOperator | ParenthesizedGroup]
Maybe_RO = No_RO | CompleteEquation
