from parser import parse_group
from parser.utility import gts

from solver.solve_algebra import divide_all


def test_divide_all():
    assert gts(divide_all(parse_group("15 + 25 - 10"), divisor=5)) == "3 + 5 - 2"
    assert gts(divide_all(parse_group("25 * 10 + 25"), divisor=5)) == "5 * 10 + 5"
    assert gts(divide_all(parse_group("5 ^ 2 - 5"), divisor=5)) == "5 - 1"
    assert gts(divide_all(parse_group("5 ^ 2 - 5 ^ 2"), divisor=5)) == "5 - 5"
    assert gts(divide_all(parse_group("(5 ^ 2 - 5 ^ 2) - 10"), divisor=5)) == "(5 - 5) - 2"
    assert gts(divide_all(parse_group("(5x) ^ 3"), divisor=5)) == "x * (5x)^2"
    assert gts(divide_all(parse_group("(2x) ^ 2 - 4 + (10 - 6x)"), divisor=2)) == "x * 2x - 2 + (5 - 3x)"


def test_multiply_groups():
    assert gts(parse_group("5x")[0] * parse_group("3x")[0]) == "15x^2"
    assert gts(parse_group("x^2")[0] * parse_group("x^3")[0]) == "x^5"
    assert gts(parse_group("7")[0] * parse_group("2")[0]) == "14"
    assert gts(parse_group("7")[0] * parse_group("2x")[0]) == "14x"
