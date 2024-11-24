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

class BaseMatrixError(Exception): ...

class DimensionMismatch(BaseMatrixError):
    def __init__(self, reason: str, dimensions: list[tuple[int, int]]):
        self.dimensions = dimensions
        super().__init__(f"{reason} Got {' and '.join(f'{d[0]} x {d[1]}' for d in dimensions)} instead.")

class InvalidMatrixOperation(BaseMatrixError):
    def __init__(self, operation: str, additional_info: str = ""):
        self.operation = operation
        super().__init__(f"{operation} is not allowed between matrices. {additional_info}")

class NonInvertibleMatrixError(BaseMatrixError):
    def __init__(self) -> None:
        super().__init__(f"Cannot inverse matrix with a determinant of 0 (singular matrix).")