import pytest

import solver

from decimal import Decimal

problems = list(enumerate([x for x in open(r"tests/test_problems.txt").readlines() if not x.startswith("#") and x != "\n"]))


@pytest.mark.parametrize("number, problem", problems)
def test_main(number, problem):
    problem, answer = problem.split("==")
    solved = solver.solve(problem)
    if isinstance(solved, bool):
        result = str(solved) == answer.strip()
    elif isinstance(solved, (float, Decimal, int)):
        result = solved == Decimal(answer[:-1])
    else:
        raise NotImplementedError

    error_message = f"{number} | {problem} = {solved} ❌ [Expected answer: {answer[:-1]}]"
    assert result, error_message


