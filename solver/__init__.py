from parser import parse_group
from parser.utility import gts

from .utility import determine_equation_type, clean_equation
from .datatype import CompleteEquation, Maybe_RO
from .logging import set_log_equation, setup_log, _log


def solve(equation: CompleteEquation | str):
    log_equation = gts(equation) if isinstance(equation, list) else equation
    set_log_equation(log_equation)
    _log.info("Solving equation '%s'", log_equation)
    if isinstance(equation, str):
        equation = parse_group(equation)
        _log.info("Finished parsing equation, got '%s'", gts(equation))
    equation = equation.copy()  # Copy so original equation (if it's CompleteEquation) doesn't change
    equation = clean_equation(equation)
    result = determine_equation_type(equation, base=True)
    _log.info("Equation solved, got '%s' as the answer!\n", gts(result))

    return result  # We shouldn't convert to string automatically here


# Setup logging
setup_log()
set_log_equation("N/A")
