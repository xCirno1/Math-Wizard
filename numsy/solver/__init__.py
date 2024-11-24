from numsy.parser import parse_group
from numsy.solver.core import Result
from numsy.parser import gts

from .utility import determine_equation_type, clean_equation
from .datatype import CompleteEquation
from .logging import set_log_equation, setup_log, _log
from .matrices import *
from .errors import *

def solve(equation: CompleteEquation | str) -> Result:
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

    return result


# Setup logging
setup_log()
set_log_equation("N/A")
