import pytest
import re
from numsy import solver

from decimal import Decimal

problems = list(enumerate([x for x in open(r"tests/test_problems.txt", encoding="UTF-8").readlines() if not x.startswith("#") and x != "\n"]))


@pytest.mark.parametrize("number, problem", problems)
def test_main(number, problem: str):
    problem, answer = re.match("(.+)==(.+)", problem.replace(" ", "")).groups()
    solved = solver.solve(problem)
    if isinstance(solved.other_value, bool):
        result = str(solved.other_value) == answer.strip()
    elif isinstance(solved.other_value, (float, Decimal, int)):
        result = solved.other_value == Decimal(answer.strip())
    else:
        raise NotImplementedError

    error_message = f"{number} | {problem}, got {solved} ❌ [Expected answer: {answer.strip()}]"
    assert result, error_message
