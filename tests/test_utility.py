import parser
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
    assert parser.utility.gts(parser.parse_group(string)) == string
