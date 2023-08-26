from __future__ import annotations

import sys

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .datatype import Maybe_RO


class SolutionNotFoundError(Exception):
    def __init__(self, equation: Maybe_RO):
        self.equation = equation
        self.recursion_limit = sys.getrecursionlimit()
        super().__init__(f"Unable to solve equation. Recursion limit reached ({self.recursion_limit}).")
