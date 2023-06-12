import pytest

import solver
import parser

problems = list(enumerate([x for x in open(r"tests/test_variables.txt", encoding="UTF-8").readlines() if not x.startswith("#") and x != "\n"]))


@pytest.mark.parametrize("number, problem", problems)
def test_main(number, problem):
    problem, answer = problem.split(",")
    solved = parser.groups_to_string(solver.solve(problem))
    result = str(solved) == answer.strip()

    error_message = f"{number} | {problem}, {solved} ❌ [Expected answer: {answer}]"
    assert result, error_message
