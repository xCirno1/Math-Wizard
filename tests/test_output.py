import solver


def test_output_with_exponential_E():
    assert str(solver.solve("960 + 600 + 700").other_value) == "2260"
    assert str(solver.solve("3E14 + 6E14 + 7E14").other_value) == "1.6E+15"
    assert str(solver.solve("3E-14 + 6E-14 + 7E-14").other_value) == "1.6E-13"
