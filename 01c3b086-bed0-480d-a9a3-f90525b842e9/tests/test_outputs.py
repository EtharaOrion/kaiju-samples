"""Behavioral tests for the SpectralCluster re-implementation.

These tests import the real solution modules and assert the mathematical
contracts described in TRUTH.md.  They are written to pass on a correct
implementation and fail on stubs (which return None / raise).
"""

import numpy as np
import pytest

# Import modules (not individual names) so a missing symbol does not cause a
# collection error -- individual attributes are resolved inside each test.
from spectralcluster import utils
from spectralcluster import laplacian
from spectralcluster import refinement
from spectralcluster import spectral_clusterer


# --------------------------------------------------------------------------- #
# utils.compute_affinity_matrix
# --------------------------------------------------------------------------- #




# --------------------------------------------------------------------------- #
# utils.compute_sorted_eigenvectors
# --------------------------------------------------------------------------- #




# --------------------------------------------------------------------------- #
# utils.compute_number_of_clusters
# --------------------------------------------------------------------------- #




# --------------------------------------------------------------------------- #
# utils.enforce_ordered_labels
# --------------------------------------------------------------------------- #




# --------------------------------------------------------------------------- #
# utils.get_cluster_centroids
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# laplacian.compute_laplacian
# --------------------------------------------------------------------------- #
def _W():
    return np.array([[0.0, 1.0, 1.0],
                     [1.0, 0.0, 1.0],
                     [1.0, 1.0, 0.0]])










# --------------------------------------------------------------------------- #
# refinement.CropDiagonal
# --------------------------------------------------------------------------- #
def _build_crop_diagonal():
    CropDiagonal = refinement.CropDiagonal
    # try both the plain and RefinementOptions-based constructor signatures
    try:
        return CropDiagonal()
    except TypeError:
        try:
            return CropDiagonal(refinement.RefinementOptions())
        except TypeError:
            pytest.skip("CropDiagonal constructor signature not recognized")


def test_affinity_matrix_values_and_symmetry():
    X = np.array([[1.0, 0.0],
                  [0.0, 1.0],
                  [1.0, 1.0]])
    A = utils.compute_affinity_matrix(X)
    assert A is not None
    A = np.asarray(A)
    assert A.shape == (3, 3)
    # symmetric
    assert np.allclose(A, A.T)
    # diagonal of 1 (a row's affinity to itself)
    assert np.allclose(np.diag(A), 1.0)
    # cos([1,0],[0,1]) = 0 -> (0+1)/2 = 0.5
    assert A[0, 1] == pytest.approx(0.5, abs=1e-9)
    # cos([1,0],[1,1]) = 1/sqrt(2) -> (that+1)/2
    expected = (1.0 / np.sqrt(2.0) + 1.0) / 2.0
    assert A[0, 2] == pytest.approx(expected, abs=1e-9)

def test_affinity_matrix_range():
    rng = np.random.RandomState(0)
    X = rng.randn(7, 4)
    A = np.asarray(utils.compute_affinity_matrix(X))
    assert A.min() >= -1e-9
    assert A.max() <= 1.0 + 1e-9

def test_sorted_eigenvectors_descending():
    A = np.array([[2.0, 1.0],
                  [1.0, 2.0]])
    w, v = utils.compute_sorted_eigenvectors(A)
    w = np.asarray(w)
    v = np.asarray(v)
    # eigenvalues sorted descending
    assert w[0] >= w[1]
    assert w[0] == pytest.approx(3.0, abs=1e-9)
    assert w[1] == pytest.approx(1.0, abs=1e-9)
    # column i is the eigenvector of eigenvalue i
    assert np.allclose(A @ v, v * w, atol=1e-8)

def test_sorted_eigenvectors_ascending():
    A = np.array([[2.0, 1.0],
                  [1.0, 2.0]])
    w, v = utils.compute_sorted_eigenvectors(A, descend=False)
    w = np.asarray(w)
    v = np.asarray(v)
    assert w[0] <= w[1]
    assert np.allclose(A @ v, v * w, atol=1e-8)

def test_number_of_clusters_eigengap():
    # clear gap between the 2nd and 3rd eigenvalue -> 2 clusters
    eig = np.array([10.0, 9.0, 1.0, 0.9])
    res = utils.compute_number_of_clusters(eig, 4, 1e-2)
    k = res[0] if isinstance(res, (tuple, list)) else res
    assert int(k) == 2

def test_number_of_clusters_respects_max():
    eig = np.array([10.0, 9.0, 8.0, 1.0, 0.5])
    res = utils.compute_number_of_clusters(eig, 2, 1e-2)
    k = res[0] if isinstance(res, (tuple, list)) else res
    assert 1 <= int(k) <= 2

def test_enforce_ordered_labels():
    labels = np.array([2, 2, 5, 5, 2, 0])
    out = np.asarray(utils.enforce_ordered_labels(labels))
    # first appearance: 2->0, 5->1, 0->2
    assert np.array_equal(out, np.array([0, 0, 1, 1, 0, 2]))

def test_enforce_ordered_labels_idempotent():
    labels = np.array([0, 1, 1, 2, 0])
    out = np.asarray(utils.enforce_ordered_labels(labels))
    assert np.array_equal(out, labels)
    # already-ordered input is a fixed point
    out2 = np.asarray(utils.enforce_ordered_labels(out))
    assert np.array_equal(out2, out)

def test_get_cluster_centroids():
    emb = np.array([[0.0, 0.0],
                    [2.0, 2.0],
                    [10.0, 0.0],
                    [10.0, 4.0]])
    labels = np.array([0, 0, 1, 1])
    centroids = np.asarray(utils.get_cluster_centroids(emb, labels))
    assert centroids.shape[0] == 2
    assert np.allclose(centroids[0], [1.0, 1.0])
    assert np.allclose(centroids[1], [10.0, 2.0])

def test_laplacian_affinity_unchanged():
    W = _W()
    out = np.asarray(laplacian.compute_laplacian(W, laplacian.LaplacianType.Affinity))
    assert np.allclose(out, W)

def test_laplacian_unnormalized():
    W = _W()
    out = np.asarray(laplacian.compute_laplacian(W, laplacian.LaplacianType.Unnormalized))
    D = np.diag(W.sum(axis=1))
    assert np.allclose(out, D - W)

def test_laplacian_graphcut():
    W = _W()
    out = np.asarray(laplacian.compute_laplacian(W, laplacian.LaplacianType.GraphCut))
    d = W.sum(axis=1)
    D = np.diag(d)
    Dinvsqrt = np.diag(1.0 / np.sqrt(d))
    expected = Dinvsqrt @ (D - W) @ Dinvsqrt
    assert np.allclose(out, expected)

def test_laplacian_randomwalk():
    W = _W()
    out = np.asarray(laplacian.compute_laplacian(W, laplacian.LaplacianType.RandomWalk))
    d = W.sum(axis=1)
    D = np.diag(d)
    Dinv = np.diag(1.0 / d)
    expected = Dinv @ (D - W)
    assert np.allclose(out, expected)

def test_crop_diagonal_uses_row_max_offdiagonal():
    op = _build_crop_diagonal()
    A = np.array([[5.0, 1.0, 3.0],
                  [1.0, 5.0, 2.0],
                  [3.0, 2.0, 5.0]])
    out = np.asarray(op.refine(A.copy()))
    # diagonal becomes each row's maximum OFF-diagonal value
    assert out[0, 0] == pytest.approx(3.0)
    assert out[1, 1] == pytest.approx(2.0)
    assert out[2, 2] == pytest.approx(3.0)
    # off-diagonal entries are untouched
    assert out[0, 1] == pytest.approx(1.0)
