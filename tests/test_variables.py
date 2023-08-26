import pytest
import re
import solver

from parser.utility import gts

problems = list(enumerate([x for x in open(r"tests/test_variables.txt", encoding="UTF-8").readlines() if not x.startswith("#") and x != "\n"]))


@pytest.mark.parametrize("number, problem", problems)
def test_main(number, problem: str):
    match = re.match(r"(.+\s*),\s*(\w)\s*=\s*\{?([^}]*)?", problem.strip())
    problem, variable, expected_answer = match.groups()
    solved = getattr(solver.solve(problem), variable)
    if isinstance(solved, set):
        solved = set({gts(res) for res in solved})
        expected_answer = set(e.replace(" ", "") for e in expected_answer.split(","))
        result = solved == expected_answer
    else:
        solved = gts(solved)
        result = solved == expected_answer

    err_message = f"{number} | {problem}, got {variable} = {solved} ❌ [Expected answer: {variable} = {expected_answer}]"
    assert result, err_message
