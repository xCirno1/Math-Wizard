from typing import TypeVar

from parser import Group, Operator, ParenthesizedGroup, Equals, parse_group
from .utility import determine_equation_type


T = TypeVar("T", list[Group | ParenthesizedGroup | Operator], list[Group | Equals | Operator | ParenthesizedGroup])


def clean_equation(parsed_group: T, base: bool = True) -> T:
	for index, group in enumerate(parsed_group):
		if not base and isinstance(group, Equals):
			raise TypeError("Equals cannot be in power or ParenthesizedGroup.")

		if isinstance(group, ParenthesizedGroup):
			group.groups = clean_equation(group.groups, base=False)
			group.power = clean_equation(group.power, base=False)
		elif isinstance(group, Group):
			group.power = clean_equation(group.power, base=False)
		if index == 0:
			continue
		before = parsed_group[index - 1]
		if isinstance(group, (Group, ParenthesizedGroup)) and isinstance(before, (Group, ParenthesizedGroup)):
			if isinstance(group, ParenthesizedGroup):
				if group.is_negative:
					parsed_group.insert(index, Operator("+"))
				else:  # For multiplications with ParenthesizedGroup without the "*" Operator
					parsed_group.insert(index, Operator("*"))
			else:  # For possibly negative values or double negative sign ('--')
				parsed_group.insert(index, Operator("+"))
	return parsed_group


def solve(equation: list[Group | Operator | Equals | ParenthesizedGroup] | str):
	if isinstance(equation, str):
		equation = parse_group(equation)
	equation = clean_equation(equation)

	return determine_equation_type(equation)
