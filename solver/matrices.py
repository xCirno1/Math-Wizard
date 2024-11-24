from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
from math import sqrt
from typing import Final, Literal, TypeAlias, Callable, overload


from solver.errors import DimensionMismatch, NonInvertibleMatrixError

MatrixBase: TypeAlias = list[list[float]]

def _dot(m1: Matrix | MatrixBase, m2: Matrix | MatrixBase):
    res = 0
    for i in range(len(m1[0])):
        res += (m1[0][i]) * m2[0][i]
    return res

class NormEnum(Enum):
    ONE = 1
    INFINITY = 2
    FROBENIUS = 3

    TWO = FROBENIUS

class Matrix:
    def __init__(self, matrix: Sequence[Sequence[float]]) -> None:
        first_len = None
        for m in matrix:
            if first_len is None:
                first_len = len(m)
            else:
                if len(m) != first_len:
                    raise DimensionMismatch("All row lengths must match the length of the first row.",[(0, first_len), (0, len(m))])

        self.matrix = [list(m) for m in matrix]

    @property
    def rows(self):
        """Returns the number of rows in the matrix.

        Returns:
            int: The number of rows in the matrix.
        """

        return len(self.matrix)

    @property
    def cols(self):
        """Returns the number of columns in the matrix.

        Returns:
            int: The number of columns in the matrix.
        """
        return len(self.matrix[0]) if len(self.matrix) else 0

    @property
    def size(self):
        """Returns the dimensions of the matrix as a tuple (rows, cols).

        Returns:
            tuple: A tuple containing the number of rows and columns of the matrix.
        """
        return self.rows, self.cols

    @property
    def is_square(self):
        """Checks if the matrix is square. A square matrix has the same number of rows and columns.

        Returns:
            bool: `True` if the matrix is square, `False` otherwise.
        """

        return self.rows == self.cols

    @property
    def is_invertible(self):
        """Determines whether the matrix is invertible which is simply if the determinant is non-zero.

        Returns:
            bool: `True` if the matrix is invertible, `False` if not.
        """
        return self.is_square and self.determinant() != 0

    @property
    def is_empty(self):
        """Checks if the matrix is empty.

        Returns:
            bool: `True` if the matrix is empty, `False` otherwise.
        """
        return self.size == (0, 0)

    @property
    def is_sparse(self):
        """Checks if the matrix is sparse. A matrix is considered sparse if more than half of its elements are zero.

        Returns:
            bool: `True` if the matrix is sparse, `False` otherwise. An empty matrix is considered non-sparse.
        """

        if self.is_empty:
            return False
        return sum([len(list(filter(lambda col: not col, row))) for row in self.matrix]) >= (self.rows * self.cols / 2)

    @property
    def is_zero(self):
        """Checks if the matrix is a zero matrix. A zero matrix is a matrix where all elements are zero.

        Returns:
            bool: `True` if the matrix is a zero matrix, `False` otherwise.
        """

        return self.is_square and all((col == 0 for col in row) for row in self.matrix)


    @property
    def is_identity(self):
        """Checks if the matrix is an identity matrix. An identity matrix is a square matrix where all the diagonal
        elements are 1 and all off-diagonal elements are 0.

        Returns:
            bool: `True` if the matrix is an identity matrix, `False` otherwise.
        """
        return self.is_square and all(self[i, j] == (1 if i == j else 0) for i in range(self.rows) for j in range(self.cols))

    @property
    def is_diagonal(self):
        """Checks if the matrix is a diagonal matrix. A diagonal matrix is a square matrix where all off-diagonal
        elements are zero and the diagonal elements can be any value.

        Returns:
            bool: `True` if the matrix is diagonal, `False` otherwise.
        """

        return self.is_square and all((self[i, j] == 0) if i != j else 1 for i in range(self.rows) for j in range(self.cols))

    @property
    def is_tridiagonal(self):
        """Checks if the matrix is a tridiagonal matrix. A tridiagonal matrix is a square matrix where all elements
        outside the main diagonal and the first diagonals above and below it are zero.

        Returns:
            bool: `True` if the matrix is tridiagonal, `False` otherwise.
        """

        return self.is_square and all(self[i, j] == 0 for i in range(self.rows) for j in range(self.cols) if abs(i - j) > 1)

    @property
    def bandwidth(self):
        """Calculates the bandwidth of the matrix. The bandwidth of a matrix is the width of the band of non-zero
        elements around the main diagonal.

        Returns:
            int: The bandwidth of the matrix.
        """

        return max(abs(i - j) for j in range(self.cols) for i in range(self.rows) if self[i, j] != 0)

    @property
    def is_involutory(self):
        """Checks if the matrix is involutory. A matrix is involutory if the matrix is equal to its own inverse.

        Returns:
            bool: `True` if the matrix is involutory, `False` otherwise.
        """
        return self.is_invertible and self == self.inverse()

    @property
    def is_orthogonal(self):
        """Checks if the matrix is orthogonal. A matrix is orthogonal if its transpose is equal to its inverse.

        Returns:
            bool: `True` if the matrix is orthogonal, `False` otherwise.
        """
        return self.is_invertible and self.transpose() == self.inverse()

    def _map(self, func: Callable[[float, int, int], float]):
        """An internal function to map each element inside the matrix with a function.
        The current value, i, j will be passed respectively to the callback function.
        """
        res = []
        i = 0
        for r in self.matrix:
            inside = []
            j = 0
            for o in r:
                inside.append(func(o, j, i))
                j += 1
            res.append(inside)
            i += 1
        return Matrix(res)

    def _dot(self, other: Matrix):
        return _dot(self.matrix, other)

    def _gaussian_eliminate(self):
        rank = min(self.cols, self.rows)
        mat = self.matrix.copy()
        for row in range(rank):
            if mat[row][row] != 0:
                pivot = mat[row][row]
                for i in range(self.cols):
                    mat[row][i] /= pivot

                for col in range(row + 1, self.rows):
                    if mat[col][row] != 0:
                        multiplier = mat[col][row]
                        for i in range(self.cols):
                            mat[col][i] -= multiplier * mat[row][i]
            else:
                for i in range(row + 1, self.rows):
                    if mat[i][row] != 0:
                        mat[row], mat[i] = mat[i], mat[row]
                        break
                else:
                    rank -= 1
                    for i in range(self.rows):
                        mat[i][row] = mat[i][rank]
                    row -= 1
        return Matrix(mat), rank

    def transpose(self):
        """Returns the transpose of the matrix.

        The transpose of a matrix is obtained by swapping its rows and columns.
        Specifically, element (i, j) in the original matrix becomes element (j, i) in the transposed matrix.

        Returns:
            Matrix: A new matrix representing the transpose of the original matrix.
        """
        res = []
        for j in range(self.cols):  # Iterate over columns first instead of rows
            row = []
            for i in range(self.rows):
                row.append(self[i][j])
            res.append(row)
        return Matrix(res)

    def determinant(self) -> float:
        """ Computes the determinant of a square matrix using cofactor expansion (Laplace expansion).

        This method calculates the determinant by expanding along the first row of the matrix.

        Returns:
            float: The determinant of the matrix.

        Raises:
            `DimensionMismatch`: If the matrix is not square (the number of rows and columns are not equal).

        Notes:
            - The determinant is computed recursively by finding minors and expanding the cofactors.
            - For a 1x1 matrix, the determinant is the single element in the matrix.
            - The determinant of a square matrix `A` is given by:
                det(A) = Σ (-1)^(i+j) * A[i][j] * det(minor(A, i, j)) (summed over a row or column).
            - This implementation always expands along the first row for simplicity.

        Example:
            For the matrix:
                | 1  2 |
                | 3  4 |

            The determinant is:
                det(A) = 1 * 4 - 2 * 3 = -2
        """
        if self.rows != self.cols:
            raise DimensionMismatch(f"Matrix must be a square matrix with same number of rows and columns.", [self.size])
        if self.size == (1, 1):
            return self[0, 0]
        elif self.size == (0, 0):
            return 1
        res = 0
        j = 0
        for column in self.matrix[0]:
            K = [x[:j] + x[j + 1:] for x in self.matrix[1:]]
            res += ((-1)**j) * column * Matrix(K).determinant()
            j += 1
        return res

    def adjugate(self) -> Matrix:
        """Computes the adjugate (adjoint) of a square matrix.

        The adjugate of a square matrix is the transpose of its cofactor matrix. Each element in the cofactor matrix
        is the determinant of the minor matrix, multiplied by (-1) raised to the sum of its row and column indices.

        Returns:
            `Matrix`: The adjugate of the current matrix.

        Raises:
            `DimensionMismatch`: If the matrix is not square (the number of rows and columns are not equal).

        Example:
            For the matrix:
                | 1  2 |
                | 3  4 |

            The adjugate is:
                |  4 -2 |
                | -3  1 |
        """

        if self.rows != self.cols:
            raise DimensionMismatch(f"Matrix must be a square matrix with same number of rows and columns.", [self.size])
        if self.size == (1, 1):
            return self
        def callback(_: float, i: int, j: int) -> float:
            co = [x[:j] + x[j + 1:] for x in self.matrix[:i] + self.matrix[i + 1:]]
            return ((-1) ** (i + j)) * Matrix(co).determinant()
        return self._map(callback)

    def inverse(self) -> Matrix:
        """Calculates the inverse of the matrix using the adjugate method.

        The inverse of a square matrix `A` is computed as:
            A^(-1) = adj(A) / det(A)
        where `adj(A)` is the adjugate (or adjoint) matrix and `det(A)` is the determinant of `A`.

        If the determinant of the matrix is zero, the matrix is singular and cannot be inverted. In such cases, a
        `NonInvertibleMatrixError` is raised.

        Returns:
            `Matrix`: The inverse of the matrix if it exists.

        Raises:
            `NonInvertibleMatrixError`: If the matrix is singular (det(A) == 0) and therefore cannot be inverted.
        """
        if not self.is_invertible:
            raise NonInvertibleMatrixError()
        return self.adjugate()/self.determinant()

    def trace(self) -> float:
        """Calculates the trace of the matrix.

        The trace of a matrix is the sum of the diagonal elements, i.e., the elements at positions (i, i) for all i.

        Returns:
            float: The trace of the matrix, which is the sum of the diagonal elements.

        Raises:
            DimensionMismatch: If the matrix is not square (the number of rows and columns are not equal).
        """
        if self.rows != self.cols:
            raise DimensionMismatch(f"Matrix must be a square matrix with same number of rows and columns.", [self.size])
        return sum(self[i, i] for i in range(self.rows))

    def row_echelon_form(self) -> Matrix:
        """Computes the Row Echelon Form (REF) of the matrix.

        This method uses Gaussian elimination to transform the matrix into row echelon form (REF),
        where the leading entry (pivot) in each non-zero row is 1, and all entries below the pivots are zero.
        The matrix is transformed in-place, and the result is returned.

        The Row Echelon Form of a matrix has the following properties:
            - All non-zero rows are above any rows of all zeros.
            - The leading entry in each non-zero row is 1 and is the only non-zero entry in its column.
            - The leading entry of each non-zero row appears to the right of the leading entry of the previous row.

        This method may differ from other CAS (Computer Algebra System) implementations of row echelon form,
        as some implementations may have different sequence of elementary row operations or pivoting strategies used.

        Returns:
            `Matrix`: The matrix transformed into Row Echelon Form (REF).
        """
        return self._gaussian_eliminate()[0]

    def rank(self) -> int:
        """Calculates the rank of the matrix.

        The rank of a matrix is the number of linearly independent rows or columns in the matrix.
        This method uses Gaussian elimination (row reduction) to compute the rank by transforming the matrix to row echelon form.

        Returns:
            int: The rank of the matrix, which is the number of non-zero rows in the row echelon form.
        """
        return self._gaussian_eliminate()[1]

    def norm(self, p: NormEnum = NormEnum.INFINITY) -> float:
        """Calculates the norm of the matrix.

        This method computes the norm of the matrix based on the specified norm type. Supported norm types include:
        1. **One Norm (`NormEnum.ONE`)**: The maximum absolute column sum of the matrix.
        2. **Infinity Norm (`NormEnum.INFINITY`)**: The maximum absolute row sum of the matrix. *(Default)*
        3. **Frobenius Norm (`NormEnum.FROBENIUS`)**: The square root of the sum of the squares of all elements in the matrix.
            This is equal to the square root of the trace of the matrix multiplied by its transpose.

        Parameters:
            p (`NormEnum`, optional): The type of norm to compute. Must be one of the values in the `NormEnum` enumeration.
                Defaults to `NormEnum.INFINITY`.

        Returns:
            float: The computed norm of the matrix.
        """
        match p:
            case NormEnum.ONE:
                return max(sum(abs(col) for col in row) for row in self.transpose().matrix)
            case NormEnum.INFINITY:
                return max(sum(abs(col) for col in row) for row in self.matrix)
            case NormEnum.FROBENIUS:
                return sqrt((self.transpose() * self).trace())

    def condition_number(self, p: NormEnum = NormEnum.INFINITY) -> float:
        """Calculates the condition number of the matrix.

        The condition number is a measure of the sensitivity of the solution of a system of linear equations
        to errors in the data. It is defined as the product of the norm of the matrix and the norm of its inverse.

        Parameters:
            p (`NormEnum`, optional): The type of norm to use for calculating the condition number.
                Must be one of the values in the `NormEnum` enumeration. Defaults to `NormEnum.INFINITY`.

        Returns:
            float: The condition number of the matrix.

        Raises:
            `DimensionMismatch`: If the matrix is not square, as only square matrices have condition numbers.
            `NonInvertibleMatrixError`: If the matrix is singular and does not have an inverse.
        """
        return self.norm(p) * self.inverse().norm(p)

    def kronecker_product(self, other: Matrix) -> Matrix:
        """Computes the Kronecker product of two matrices.

        The Kronecker product, also known as the tensor product, of two matrices results in a block matrix
        formed by multiplying each element of the first matrix by the entire second matrix. The resulting matrix
        has dimensions `(self.rows * other.rows, self.cols * other.cols)`.

        Parameters:
            other (`Matrix`): The matrix to compute the Kronecker product with.

        Returns:
            `Matrix`: A new matrix representing the Kronecker product of the two matrices.
        """
        current_row = 0
        ret = []
        for row in self.matrix:
            for _ in range(other.rows):
                new = []
                for col in row:
                    new += [elem * col for elem in other[current_row]]
                ret.append(new)
                current_row += 1
            current_row = 0
        return Matrix(ret)

    def hadamard_product(self, other: Matrix) -> Matrix:
        """Computes the Hadamard product (element-wise product) of two matrices.

        The Hadamard product is the element-wise multiplication of two matrices of the same dimensions.

        Parameters:
            other (`Matrix`): The matrix to element-wise multiply with the current matrix. Must have the same dimensions as the current matrix.

        Returns:
            `Matrix`: A new matrix representing the Hadamard product of the two matrices.

        Raises:
            DimensionMismatch: If the dimensions of the two matrices are not the same.
        """
        if self.size != other.size:
            raise DimensionMismatch("The dimension of the first matrix must be equal to the second matrix.", [self.size, other.size])
        return self._map(lambda o, i, j: o * other[j, i])

    def hadamard_division(self, other: Matrix) -> Matrix:
        """Computes the Hadamard division (element-wise division) of two matrices.

        The Hadamard division is the element-wise division of two matrices of the same dimensions.

        Parameters:
            other (`Matrix`): The matrix to element-wise divide with the current matrix. Must have the same dimensions as the current matrix.

        Returns:
            `Matrix`: A new matrix representing the Hadamard division of the two matrices.

        Raises:
            `DimensionMismatch`: If the dimensions of the two matrices are not the same.
            `ZeroDivisionError`: If there is an attempt to divide by zero in the matrix.
        """

        if self.size != other.size:
            raise DimensionMismatch("The dimension of the first matrix must be equal to the second matrix.", [self.size, other.size])
        return self._map(lambda o, i, j: o / other[j, i])


    def element_wise_subtract(self, value: float):
        """Performs element-wise subtraction of a scalar from the matrix.

        Parameters:
            value (float): The scalar value to subtract from each element of the matrix.

        Returns:
            `Matrix`: A new matrix where each element is the result of subtracting the scalar value from the original matrix elements.
        """
        return self._map(lambda o, *_: o - value)

    def element_wise_add(self, value: float):
        """Performs element-wise addition of a scalar to the matrix.

        Parameters:
            value (float): The scalar value to add to each element of the matrix.

        Returns:
            `Matrix`: A new matrix where each element is the result of adding the scalar value to the original matrix elements.
        """
        return self._map(lambda o, *_: o + value)

    def submatrix(self, row_indices: list[int], col_indices: list[int]) -> Matrix:
        """Extracts a submatrix defined by specified row and column indices.

        A submatrix is created by selecting specific rows and columns from the original matrix.
        The order of rows and columns in the resulting submatrix matches the order of indices provided.

        Parameters:
            row_indices (`list[int]`): The list of row indices to include in the submatrix.
            col_indices (`list[int]`): The list of column indices to include in the submatrix.

        Returns:
            `Matrix`: A new matrix representing the submatrix defined by the specified indices.

        Raises:
            IndexError: If any index in `row_indices` or `col_indices` is out of bounds for the matrix.
        """
        return Matrix([[self[i, j] for j in col_indices] for i in row_indices])

    def __repr__(self) -> str:
        return f"<Matrix[{self.rows} x {self.cols}]>"

    def __eq__(self, value: object) -> bool:
        return isinstance(value, Matrix) and self.matrix == value.matrix

    @overload
    def __getitem__(self, item: int) -> list[float]: ...
    @overload
    def __getitem__(self, item: tuple[int, int]) -> float: ...
    def __getitem__(self, item: int | tuple[int, int]) -> float | list[int | float]:
        """Accesses elements of the matrix.

        This method allows accessing elements in the matrix using either a single index (to get a row) or
        a tuple of indices (to get a specific element in the matrix).

        **Overloaded behaviors:**
        1. **Single index (int)**: Returns the row at the specified index.
        2. **Tuple of indices (tuple[int, int])**: Returns the element at the specified row and column.

        Parameters:
            item (int): The index of the row to retrieve.
            item (tuple[int, int]): A tuple containing the row and column indices to retrieve a specific element.

        Returns:
            list[float]: The row at the specified index (if `item` is an integer).
            float: The element at the specified row and column (if `item` is a tuple of two integers).

        Raises:
            IndexError: If the index is out of bounds for the matrix.
        """
        return self.matrix[item[0]][item[1]] if isinstance(item, tuple) else self.matrix[item]

    def __add__(self, other: Matrix):
        """Adds another matrix to the current matrix.

        This method performs element-wise addition between two matrices. The two matrices
        must have the same dimensions for addition to be valid.

        Parameters:
            other (`Matrix`): The matrix to add to the current matrix.

        Returns:
            `Matrix`: A new matrix resulting from the element-wise addition.

        Raises:
            `DimensionMismatch`: If the dimensions of the two matrices are not the same.
        """
        if self.size != other.size:
            raise DimensionMismatch("The dimension of the first matrix must be equal to the second matrix.", [self.size, other.size])
        return self._map(lambda e, i, j: e + other[j][i])

    def __sub__(self, other: Matrix):
        """Subtracts another matrix from the current matrix.

        This method performs element-wise subtraction between two matrices. The two matrices must have the same
        dimensions for subtraction to be valid.

        Parameters:
            other (`Matrix`): The matrix to subtract from the current matrix.

        Returns:
            `Matrix`: A new matrix resulting from the element-wise subtraction.

        Raises:
            `DimensionMismatch`: If the dimensions of the two matrices are not the same.
        """
        if self.size != other.size:
            raise DimensionMismatch("The dimension of the first matrix must be equal to the second matrix.", [self.size, other.size])

        return self._map(lambda e, i, j: e - other[j][i])

    def __mul__(self, other: Matrix | float):
        """Multiplies the matrix with another matrix or a scalar.

        This method supports two types of multiplication:
        1. **Matrix multiplication**: Requires the number of columns in the first matrix to match the number
            of rows in the second matrix. The resulting matrix will have the dimensions `(self.rows, other.cols)`.
        2. **Scalar multiplication**: Multiplies each element of the matrix by the given scalar.

        Parameters:
            other (`Matrix` | float): The other operand. Can be another matrix (for matrix multiplication) or
                a scalar (for element-wise multiplication).

        Returns:
            `Matrix`: A new matrix resulting from the multiplication.

        Raises:
            `DimensionMismatch`: If the dimensions of the two matrices are incompatible for matrix multiplication.
        """
        if isinstance(other, Matrix) and self.rows != other.cols:
            raise DimensionMismatch("The number of rows of the second matrix must be "
                                    "equal to the number of columns of the first one.", [self.size, other.size])
        if isinstance(other, (float, int)):
            return self._map(lambda e, *_: e * other)

        res = []
        for row in self.matrix:
            inside = []
            for r in other.transpose().matrix:
                inside.append(_dot([row], [r]))
            res.append(inside)
        return Matrix(res)

    def __truediv__(self, other: float):
        """Divides each element of the matrix by a scalar.

        Parameters:
            other (float): The scalar to divide each element of the matrix by.

        Returns:
            `Matrix`: A new matrix with each element divided by the scalar.
        """
        return self._map(lambda e, *_: e / other)

    def __floordiv__(self, other: float):
        """Performs element-wise floor division of the matrix by a scalar.

        Parameters:
            other (float): The scalar to floor-divide each element of the matrix by.

        Returns:
            `Matrix`: A new matrix with each element floor-divided by the scalar.
        """
        return self._map(lambda e, *_: e // other)

    def __pow__(self, power: int, modulo: float | None = None):
        """Raises the matrix to a given power using matrix multiplication, with support for negative powers and modulo.

        This method raises the matrix to a positive or negative integer power by multiplying the matrix
        by itself repeatedly. If the power is negative, the matrix is first inverted before exponentiation.
        Optionally, the result can be taken modulo a given value after exponentiation.

        Parameters:
            power (int): The exponent to which the matrix is to be raised.
                Can be positive, negative, or zero.
            modulo (float | None, optional): If provided, the result of the exponentiation will be taken modulo this value.

        Returns:
            `Matrix`: The matrix raised to the specified power, optionally reduced modulo the given value.

        Raises:
            `DimensionMismatch`: If the matrix is not square (the number of rows and columns are not equal).
            `NonInvertibleMatrixError`: If the matrix is square but cannot be inverted when raising to a negative power (due to singularity).

        Example:
            >>> A = Matrix([[2, 3], [-1, 0]])
            >>> A_squared = A ** 2
            [[2, 3], [-1, 0]] * [[2, 3], [-1, 0]] = [[7, 6], [2, 3]]
            >>> A_inverse = A ** -1
            [[0.0, -1.0], [0.3333333333333333, 0.6666666666666666]]
            >>> A_identity = A ** 0
            [[1, 0], [0, 1]]
        """
        if self.rows != self.cols:
            raise DimensionMismatch("Matrix should be a square matrix to be powered.", [self.size])
        if power == 0:
            return Identity(self.cols)

        new = self.inverse() if power < 0 else self
        for _ in range(abs(power) - 1):
            new *= self.inverse() if power < 0 else self
        return new % modulo if modulo is not None else new

    def __mod__(self, other: float) -> Matrix:
        """Performs element-wise modulus operation with a scalar.

        Parameters:
            other (float): The scalar to compute the modulus of each element by.

        Returns:
            `Matrix`: A new matrix with each element modded by the scalar.
        """
        return self._map(lambda e, *_: e % other)

    def __len__(self):
        return self.cols * self.rows

    __rmul__ = __mul__
    ref = row_echelon_form
    cond = condition_number
    element_wise_multiply = hadamard_product
    element_wise_divide = hadamard_division


class Identity(Matrix):
    """A class representing the identity matrix, which is a special square matrix in which all the elements of
    the principal diagonal are ones, and all other elements are zeros.

    This class extends the `Matrix` class and provides fast path implementations for common matrix operations when
    the matrix is the identity matrix.
    """
    def __init__(self, size: int):
        self.matrix: Final = [[1 if i == j else 0 for j in range(size)] for i in range(size)]

    def __mul__(self, other: Matrix | float):
        if isinstance(other, Matrix):
            return other
        else:
            return super().__mul__(other)

    def __pow__(self, power: int, modulo=None) -> Matrix:
        return self

    @property
    def is_identity(self):
        return True

    @property
    def is_diagonal(self):
        return True

    @property
    def is_involutory(self):
        return True

    @property
    def is_orthogonal(self):
        return True

    def rank(self):
        return self.rows

    def inverse(self) -> Matrix:
        return self

    def adjugate(self) -> Matrix:
        return self

    def transpose(self) -> Matrix:
        return self

    def determinant(self) -> Literal[1]:
        return 1
