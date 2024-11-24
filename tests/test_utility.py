from numsy import parser
import numsy
import pytest

test_data = [
    "1 + 1",
    "1 - 1",
    "1 * -1",
    "1 = 0.1",
    "-1 = -1",
    "1 + 1 = 1 - 1"
]


@pytest.mark.parametrize("string", test_data)
def test_main(string):
    assert numsy.parser.utility.gts(parser.parse_group(string)) == string
