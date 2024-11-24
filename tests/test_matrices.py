import pytest

from solver.errors import NonInvertibleMatrixError
from solver.matrices import Matrix, DimensionMismatch, NormEnum, Identity

m0 = []

m1 = [
    [1, 2, 3],
    [3, 2, 1],
    [0, 0, 8]
]

m2 = [
    [3, 2, 1],
    [9, 9, 9],
    [-1, -8, -18]
]

m3 = [
    [1, 2, 3, 4],
    [5, 6, 7, 8]
]

m4 = [
    [4, 2],
    [5, 6],
    [0, 0],
    [-1, -5]
]

m5 = [
    [1, 2],
    [3, 4]
]

m6 = [
    [1, 2, 1, 2, 2],
    [-1, 4, -5, -6, 5],
    [-7, 1, 0, 18, 4],
    [9, 8, -7, -6, 2],
    [8, 3, 7, 5, 0]
]

singular = [
    [3, 12],
    [2, 8]
]

r1 = [
    [10, 20, 10],
    [-20, -30, 10],
    [30, 50, 0]
]

r2 = [
    [1, 1, 0, 2],
    [-1, -1, 0, -2]
]

r3 = [
    [1, 2, 1],
    [-2, -3, 1],
    [3, 5, 0]
]

sparse = [
    [0, 0, 3, 0, 4],
    [0, 0, 5, 7, 0],
    [0, 0, 0, 0, 0],
    [0, 2, 6, 0, 0]
]

i1 = [
    [1, 0],
    [0, 1]
]

almost_identity = [
    [1, 0, 0, 6],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1],
]

diag = [
    [0, 0, 0, 0],
    [0, 23, 0, 0],
    [0, 0, 21, 0],
    [0, 0, 0,-55],
]

tridiagonal = [
    [1,  1,  0,  0,  0,  0],
    [1,  1,  1,  0,  0,  0],
    [0,  1,  1,  1,  0,  0],
    [0,  0,  1,  1,  1,  0],
    [0,  0,  0,  1,  1,  1],
    [0,  0,  0,  0,  1,  1]
]

involutary = [
    [-5, -8, 0],
    [3, 5, 0],
    [1, 2, -1]
]

orthogonal = [
    [0, 0, 0, 1],
    [0, 0, 1, 0],
    [1, 0, 0, 0],
    [0, 1, 0, 0],
]

k1 = [
    [0, 5],
    [6, 7]

]

k2 = [
    [1, -4, 7],
    [-2, 3, 3]
]

k3 = [
    [8, -9, -6, 5],
    [1, -3, -4, 7],
    [2, 8, -8, -3],
    [1, 2, -5, -1],

]

def test_invalid_matrix():
    with pytest.raises(DimensionMismatch) as excinfo:
        Matrix([[1, 2, 3], [1, 2]])
    assert excinfo.value.dimensions == [(0, 3), (0, 2)]
    with pytest.raises(DimensionMismatch) as excinfo:
        Matrix(m3) ** 2
    assert excinfo.value.dimensions == [(2, 4)]
    with pytest.raises(NonInvertibleMatrixError) as excinfo:
        Matrix(singular).inverse()

def test_matrix_add():
    assert Matrix(m1) + Matrix(m2) == Matrix(m2) + Matrix(m1)
    assert (Matrix(m1) + Matrix(m2)).matrix == [[4, 4, 4], [12, 11, 10], [-1, -8, -10]]
    assert (Matrix(m1) - Matrix(m2)).matrix == [[-2, 0, 2], [-6, -7, -8], [1, 8, 26]]
    assert (Matrix(m2) - Matrix(m1)).matrix == [[2, 0, -2], [6, 7, 8], [-1, -8, -26]]

def test_matrix_size():
    assert Matrix(m0).size == (0, 0)
    assert Matrix(m1).size == (3, 3)
    assert Matrix(m3).size == (2, 4)

def test_matrix_transpose():
    assert Matrix(m1).transpose().matrix == [[1, 3, 0], [2, 2, 0], [3, 1, 8]]
    assert Matrix(m2).transpose().matrix == [[3, 9, -1], [2, 9, -8], [1, 9, -18]]
    assert Matrix(m3).transpose().matrix == [[1, 5], [2, 6], [3, 7], [4, 8]]

def test_matrix_multiplication():
    assert (Matrix(m2) * 4).matrix == [[12, 8, 4], [36, 36, 36], [-4, -32, -72]]
    assert (2 * Matrix(m4) * 8).matrix == [[64, 32], [80, 96], [0, 0], [-16, -80]]

    assert (Matrix(m1) * Matrix(m2)).matrix == [[18, -4, -35], [26, 16, 3], [-8, -64, -144]]
    assert (Matrix(m3) * Matrix(m4)).matrix == [[10, -6], [42, 6]]

def test_matrix_power():
    assert (Matrix(m5) ** 4).matrix == [[199, 290], [435, 634]]
    assert (Matrix(m6) ** 0).matrix == [[1, 0, 0, 0, 0], [0, 1, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 0, 1, 0], [0, 0, 0, 0, 1]]
    assert (Matrix(m2) ** -3).matrix == [[79.67123914037494, -25.68043489305492, -8.320073159579332], [-139.97073616826705, 45.11929075852258, 14.618198445358939], [57.13763145861912, -18.418127317990145, -5.967535436671239]]

def test_matrix_determinant():
    assert Matrix(m0).determinant() == 1
    assert Matrix(m1).determinant() == -32
    assert Matrix(m5).determinant() == -2
    assert Matrix(m6).determinant() == 158

def test_matrix_adjugate():
    assert Matrix(m0).adjugate().matrix == []
    assert Matrix(m5).adjugate().matrix == [[4, -2], [-3, 1]]
    assert Matrix(m2).adjugate().matrix == [[-90, 28, 9], [153, -53, -18], [-63, 22, 9]]
    assert Matrix(m6).adjugate().matrix == [[-5959, 1968, 674, -309, 1948], [10539, -3488, -1192, 565, -3432], [3115, -1020, -358, 151, -1000], [-1150, 372, 138, -56, 374], [-7888, 2642, 896, -430, 2584]]

def test_matrix_trace():
    assert Matrix(m0).trace() == 0
    assert Matrix(m2).trace() == -6
    assert Matrix(m6).trace() == -1

def test_matrix_ref():
    assert Matrix(m0).ref().matrix == []
    assert Matrix(r1).ref().matrix == [[1.0, 2.0, 1.0], [0.0, 1.0, 3.0], [0.0, 0.0, 0.0]]
    assert Matrix(r2).ref().matrix == [[1.0, 1.0, 0.0, 2.0], [0.0, 0.0, 0.0, 0.0]]
    assert Matrix(r3).ref().matrix == [[1.0, 2.0, 1.0], [0.0, 1.0, 3.0], [0.0, 0.0, 0.0]]
    assert Matrix(m6).ref().matrix == [[1.0, 2.0, 1.0, 2.0, 2.0], [0.0, 1.0, -0.6666666666666666, -0.6666666666666666, 1.1666666666666667], [0.0, 0.0, 1.0, 2.4705882352941178, 0.029411764705882353], [0.0, 0.0, 0.0, 1.0, -0.1447368421052631], [0.0, 0.0, 0.0, 0.0, 1.0]]

def test_matrix_rank():
    assert Matrix(m0).rank() == 0
    assert Matrix(r1).rank() == 2
    assert Matrix(r2).rank() == 1
    assert Matrix(r3).rank() == 2
    assert Matrix(m6).rank() == 5

def test_matrix_norm():
    assert Matrix(m6).norm(p=NormEnum.ONE) == 37
    assert Matrix(m6).norm(p=NormEnum.INFINITY) == 32
    assert Matrix(m6).norm(p=NormEnum.FROBENIUS) == 29.79932885150268
    assert Matrix(m3).norm(p=NormEnum.TWO) == 14.2828568570857

def test_matrix_condition_number():
    assert Matrix(m2).condition_number() == 224.0
    assert Matrix(m6).condition_number() == 3891.848101265823

def test_matrix_hadamard_product():
    assert Matrix(m3).hadamard_product(Matrix(m3)).matrix == [[1, 4, 9, 16], [25, 36, 49, 64]]
    assert Matrix(m3).hadamard_product(Matrix(r2)).matrix == [[1, 2, 0, 8], [-5, -6, 0, -16]]

def test_matrix_hadamard_division():
    assert Matrix(m3).hadamard_division(Matrix(m3)).matrix == [[1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0]]
    assert Matrix(r1).hadamard_division(Matrix(m2)).matrix == [[3.3333333333333335, 10.0, 10.0], [-2.2222222222222223, -3.3333333333333335, 1.1111111111111112], [-30.0, -6.25, -0.0]]

def test_submatrix():
    assert Matrix(m6).submatrix(row_indices=[0, 3], col_indices=[0, 3, 4]).matrix == [[1, 2, 2], [9, -6, 2]]
    assert Matrix(m3).submatrix(row_indices=[0], col_indices=[1, 3]).matrix == [[2, 4]]

def test_matrix_is_sparse():
    assert Matrix(sparse).is_sparse is True
    assert Matrix(m4).is_sparse is False
    assert Matrix(m0).is_sparse is False

def test_matrix_is_identity():
    assert Matrix(i1).is_identity is True
    assert Identity(15).is_identity is True
    assert Matrix(m6).is_identity is False
    assert Matrix(almost_identity).is_identity is False

def test_matrix_is_diagonal():
    assert Matrix(almost_identity).is_diagonal is False
    assert Matrix(i1).is_diagonal is True
    assert Matrix(m5).is_diagonal is False
    assert Matrix(diag).is_diagonal is True

def test_matrix_is_tridiagonal():
    assert Matrix(tridiagonal).is_tridiagonal is True
    assert Matrix(diag).is_tridiagonal is True
    assert Matrix(m5).is_tridiagonal is True
    assert Matrix(m6).is_tridiagonal is False
    assert Matrix(almost_identity).is_tridiagonal is False
    assert Matrix(diag).is_tridiagonal is True

def test_matrix_bandwidth():
    assert Matrix(tridiagonal).bandwidth == 1
    assert Matrix(diag).bandwidth == 0
    assert Matrix(m6).bandwidth == 4
    assert Matrix(m2).bandwidth == 2

def test_matrix_is_involutary():
    assert Matrix(involutary).is_involutory is True
    assert Matrix(i1).is_involutory is True
    assert Matrix(tridiagonal).is_involutory is False
    assert Matrix(m6).is_involutory is False
    assert Matrix(m3).is_involutory is False

def test_matrix_is_orthogonal():
    assert Matrix(i1).is_orthogonal is True
    assert Matrix(involutary).is_orthogonal is False
    assert Matrix(orthogonal).is_orthogonal is True
    assert Matrix(m3).is_orthogonal is False
    assert Matrix(diag).is_orthogonal is False

def test_matrix_element_wise_subtract():
    assert Matrix(m5).element_wise_subtract(3).matrix == [[-2, -1], [0, 1]]
    assert Matrix(m6).element_wise_subtract(-4.5).matrix == [[5.5, 6.5, 5.5, 6.5, 6.5], [3.5, 8.5, -0.5, -1.5, 9.5], [-2.5, 5.5, 4.5, 22.5, 8.5], [13.5, 12.5, -2.5, -1.5, 6.5], [12.5, 7.5, 11.5, 9.5, 4.5]]
    assert Matrix(m4).element_wise_subtract(0.5).matrix == [[3.5, 1.5], [4.5, 5.5], [-0.5, -0.5], [-1.5, -5.5]]

def test_matrix_element_wise_addition():
    assert Matrix(m5).element_wise_add(3).matrix == [[4, 5], [6, 7]]
    assert Matrix(m6).element_wise_add(-4.5).matrix == [[-3.5, -2.5, -3.5, -2.5, -2.5], [-5.5, -0.5, -9.5, -10.5, 0.5], [-11.5, -3.5, -4.5, 13.5, -0.5], [4.5, 3.5, -11.5, -10.5, -2.5], [3.5, -1.5, 2.5, 0.5, -4.5]]
    assert Matrix(m4).element_wise_add(0.5).matrix == [[4.5, 2.5], [5.5, 6.5], [0.5, 0.5], [-0.5, -4.5]]

def test_matrix_kronecker_product():
    assert Matrix(m5).kronecker_product(Matrix(k1)).matrix == [[0, 5, 0, 10], [6, 7, 12, 14], [0, 15, 0, 20], [18, 21, 24, 28]]
    assert Matrix(k2).kronecker_product(Matrix(k3)).matrix == [
        [8, -9, -6, 5, -32, 36, 24, -20, 56, -63, -42, 35],
        [1, -3, -4, 7, -4, 12, 16, -28, 7, -21, -28, 49],
        [2, 8, -8, -3, -8, -32, 32, 12, 14, 56, -56, -21],
        [1, 2, -5, -1, -4, -8, 20, 4, 7, 14, -35, -7],
        [-16, 18, 12, -10, 24, -27, -18, 15, 24, -27, -18, 15],
        [-2, 6, 8, -14, 3, -9, -12, 21, 3, -9, -12, 21],
        [-4, -16, 16, 6, 6, 24, -24, -9, 6, 24, -24, -9],
        [-2, -4, 10, 2, 3, 6, -15, -3, 3, 6, -15, -3]
    ]

def test_matrix_other_operations():
    assert (Matrix(m2) / 4).matrix == [[0.75, 0.5, 0.25], [2.25, 2.25, 2.25], [-0.25, -2.0, -4.5]]
    assert (Matrix(m1) // 2).matrix == [[0, 1, 1], [1, 1, 0], [0, 0, 4]]
