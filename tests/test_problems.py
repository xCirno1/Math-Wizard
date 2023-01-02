import pytest

import solver

from decimal import Decimal


@pytest.mark.parametrize("number, problems", list(enumerate(open(r"tests\test_problems.txt").readlines())))
def test_main(number, problems):
    problem, answer = problems.split("==")
    solved = solver.solve(problem)
    error_message = f"{number} | {problem} = {solved} ❌ [Expected answer: {answer[:-1]}]"
    assert solved == Decimal(answer[:-1]), error_message


