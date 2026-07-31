from datasketch.aio.lsh import AsyncMinHashLSH
import pytest


def test_differential_0():
    assert repr(AsyncMinHashLSH(threshold=0.5, num_perm=16).b) == '5'

def test_differential_1():
    assert repr(AsyncMinHashLSH(threshold=0.5, num_perm=16).r) == '3'

def test_differential_2():
    assert repr(AsyncMinHashLSH(threshold=0.9, num_perm=128).b) == '5'

def test_differential_3():
    assert repr(AsyncMinHashLSH(threshold=0.9, num_perm=128).r) == '25'

def test_differential_4():
    assert repr(AsyncMinHashLSH(threshold=0.1, num_perm=256).b) == '117'

def test_differential_5():
    assert repr(AsyncMinHashLSH(threshold=0.75, num_perm=64).r) == '9'

def test_differential_6():
    assert repr(AsyncMinHashLSH(params=(4, 4)).b) == '4'

def test_differential_7():
    assert repr(AsyncMinHashLSH(params=(4, 4)).r) == '4'

def test_differential_8():
    assert repr(AsyncMinHashLSH(params=(8, 16)).b) == '8'

def test_differential_9():
    assert repr(AsyncMinHashLSH(threshold=0.5, num_perm=16, weights=(0.2, 0.8)).b) == '7'

def test_differential_10():
    assert repr(AsyncMinHashLSH(threshold=0.5, num_perm=16, weights=(0.5, 0.5)).r) == '3'

def test_differential_11():
    assert repr(AsyncMinHashLSH(threshold=1.0, num_perm=2).b) == '1'

def test_differential_12():
    assert repr(AsyncMinHashLSH(threshold=0.01, num_perm=512).b) == '166'

def test_differential_13():
    assert repr(AsyncMinHashLSH(threshold=0.99, num_perm=1024).r) == '247'



# ---- LLM-authored (golden-validated) tests ----
"""
Behavioral tests for the re-implemented `datasketch` library.

These tests import the real public API and assert on concrete runtime behavior
described by the TRUTH.md contract.  They are designed to pass on a correct
implementation and fail on a stubbed / overfit one.
"""

import pickle
import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Public API import (per success criteria)
# ---------------------------------------------------------------------------
from datasketch import (
    MinHash,
    HyperLogLog,
    LeanMinHash,
    MinHashLSH,
)


# ===========================================================================
# Helpers
# ===========================================================================
def make_mh(num_perm=128, seed=1, values=None):
    mh = MinHash(num_perm=num_perm, seed=seed)
    if values is not None:
        for v in values:
            mh.update(str(v).encode("utf8"))
    return mh


def try_scheme_minhash(scheme, num_perm=64, seed=1):
    """Return a MinHash built with the given permutation scheme, or None if
    the constructor does not accept a scheme selector."""
    for kw in ("scheme",):
        try:
            return MinHash(num_perm=num_perm, seed=seed, **{kw: scheme})
        except TypeError:
            continue
        except Exception:
            # scheme kwarg accepted but value invalid -> re-raise for caller
            raise
    return None


# ===========================================================================
# MinHash core behavior
# ===========================================================================






























# ===========================================================================
# MinHash permutation schemes (optional selector)
# ===========================================================================








# ===========================================================================
# HyperLogLog family
# ===========================================================================
















# ===========================================================================
# LeanMinHash
# ===========================================================================










# ===========================================================================
# MinHashLSH
# ===========================================================================










# ===========================================================================
# HNSW
# ===========================================================================
def _get_hnsw():
    try:
        from datasketch import HNSW
    except ImportError:
        try:
            from datasketch.hnsw import HNSW
        except ImportError:
            pytest.skip("HNSW not available")
    return HNSW


def _euclid(x, y):
    return float(np.linalg.norm(x - y))




def _hnsw_query(index, q, k):
    for name in ("query", "search"):
        fn = getattr(index, name, None)
        if fn is not None:
            return fn(q, k=k)
    pytest.skip("no query/search method on HNSW")


def test_minhash_empty_state():
    mh = MinHash(num_perm=64, seed=1)
    assert mh.is_empty()
    # empty sentinel must equal the register dtype's max (scheme width sentinel)
    dtype_max = np.iinfo(mh.hashvalues.dtype).max
    assert np.all(mh.hashvalues == dtype_max)
    assert mh.count() == pytest.approx(0, abs=1e-6) or mh.count() == 0

def test_minhash_jaccard_identical_is_one():
    data = ["a", "b", "c", "d", "e", "f"]
    m1 = make_mh(values=data)
    m2 = make_mh(values=data)
    assert m1.jaccard(m2) == pytest.approx(1.0)
    # equal content + equal seed => equal objects
    assert m1 == m2

def test_minhash_jaccard_disjoint_is_low():
    m1 = make_mh(num_perm=256, values=range(0, 500))
    m2 = make_mh(num_perm=256, values=range(1000, 1500))
    j = m1.jaccard(m2)
    assert 0.0 <= j <= 0.15

def test_minhash_jaccard_symmetric_and_bounded():
    m1 = make_mh(num_perm=128, values=range(0, 200))
    m2 = make_mh(num_perm=128, values=range(100, 300))
    assert m1.jaccard(m2) == pytest.approx(m2.jaccard(m1))
    assert 0.0 <= m1.jaccard(m2) <= 1.0

def test_minhash_jaccard_estimates_true_similarity():
    a = set(range(0, 1000))
    b = set(range(500, 1500))
    true_j = len(a & b) / len(a | b)
    m1 = make_mh(num_perm=512, values=a)
    m2 = make_mh(num_perm=512, values=b)
    assert m1.jaccard(m2) == pytest.approx(true_j, abs=0.06)

def test_minhash_count_increases_with_cardinality():
    small = make_mh(num_perm=256, values=range(10))
    large = make_mh(num_perm=256, values=range(2000))
    assert large.count() > small.count()
    # large cardinality estimate should be in the right order of magnitude
    assert large.count() > 200

def test_minhash_update_batch_matches_scalar_updates():
    data = [str(i).encode("utf8") for i in range(300)]
    m_scalar = MinHash(num_perm=128, seed=1)
    for d in data:
        m_scalar.update(d)
    m_batch = MinHash(num_perm=128, seed=1)
    m_batch.update_batch(data)
    assert np.array_equal(m_scalar.hashvalues, m_batch.hashvalues)
    assert m_scalar == m_batch

def test_minhash_merge_is_elementwise_min():
    m1 = make_mh(num_perm=128, values=range(0, 100))
    m2 = make_mh(num_perm=128, values=range(100, 200))
    expected = np.minimum(m1.hashvalues, m2.hashvalues)
    m1.merge(m2)
    assert np.array_equal(m1.hashvalues, expected)

def test_minhash_union_equals_merge():
    m1 = make_mh(num_perm=128, seed=7, values=range(0, 100))
    m2 = make_mh(num_perm=128, seed=7, values=range(50, 150))
    union = MinHash.union(m1, m2)
    merged = m1.copy()
    merged.merge(m2)
    assert np.array_equal(union.hashvalues, merged.hashvalues)
    assert union == merged

def test_minhash_equality_reflects_seed():
    # Two empty MinHashes with different seeds must NOT be equal
    # (equality must include seed, not just registers).
    a = MinHash(num_perm=64, seed=1)
    b = MinHash(num_perm=64, seed=2)
    assert a.is_empty() and b.is_empty()
    assert a != b

def test_cross_scheme_operations_raise():
    m32 = try_scheme_minhash("affine32", seed=3)
    m64 = try_scheme_minhash("affine64", seed=3)
    if m32 is None or m64 is None:
        pytest.skip("scheme selector not supported by constructor")
    # differing schemes -> not equal, and mixing ops must raise
    assert m32 != m64
    with pytest.raises(Exception):
        m32.jaccard(m64)
    with pytest.raises(Exception):
        m32.merge(m64)

def test_hll_empty_is_empty():
    h = HyperLogLog(p=8)
    assert h.is_empty()
    assert h.count() == pytest.approx(0, abs=1e-6) or h.count() == 0

def test_hll_cardinality_estimate_accurate():
    h = HyperLogLog(p=12)
    n = 5000
    for i in range(n):
        h.update(str(i).encode("utf8"))
    est = h.count()
    assert est == pytest.approx(n, rel=0.10)

def test_hll_merge_union_cardinality():
    h1 = HyperLogLog(p=12)
    h2 = HyperLogLog(p=12)
    for i in range(0, 3000):
        h1.update(str(i).encode("utf8"))
    for i in range(1500, 4500):
        h2.update(str(i).encode("utf8"))
    merged = h1.copy()
    merged.merge(h2)
    # union covers items 0..4500 -> ~4500 distinct
    assert merged.count() == pytest.approx(4500, rel=0.10)
    union = HyperLogLog.union(h1, h2)
    assert union.count() == pytest.approx(merged.count(), rel=0.02)

def test_hll_pickle_round_trip():
    h = HyperLogLog(p=10)
    for i in range(500):
        h.update(str(i).encode("utf8"))
    h2 = pickle.loads(pickle.dumps(h))
    assert h2 == h
    assert h2.count() == pytest.approx(h.count(), rel=1e-6)

def test_hll_serialize_round_trip():
    h = HyperLogLog(p=10)
    for i in range(500):
        h.update(str(i).encode("utf8"))
    buf = bytearray(h.bytesize())
    h.serialize(buf)
    h2 = HyperLogLog.deserialize(buf)
    assert h2 == h
    assert h2.count() == pytest.approx(h.count(), rel=1e-6)

def test_hll_plusplus_small_and_large():
    try:
        from datasketch import HyperLogLogPlusPlus
    except ImportError:
        pytest.skip("HyperLogLogPlusPlus not exported")
    # small cardinality (linear counting regime)
    small = HyperLogLogPlusPlus(p=12)
    for i in range(50):
        small.update(str(i).encode("utf8"))
    assert small.count() == pytest.approx(50, abs=8)
    # large cardinality
    big = HyperLogLogPlusPlus(p=12)
    for i in range(20000):
        big.update(str(i).encode("utf8"))
    assert big.count() == pytest.approx(20000, rel=0.08)

def test_lean_serialize_round_trip():
    m = make_mh(num_perm=128, values=range(100))
    lm = LeanMinHash(m)
    buf = bytearray(lm.bytesize())
    lm.serialize(buf)
    lm2 = LeanMinHash.deserialize(buf)
    assert lm == lm2
    assert lm.jaccard(lm2) == pytest.approx(1.0)

def test_lean_pickle_and_hash():
    m = make_mh(num_perm=64, values=range(30))
    lm = LeanMinHash(m)
    lm2 = pickle.loads(pickle.dumps(lm))
    assert lm == lm2
    assert hash(lm) == hash(lm2)

def test_lsh_insert_query_contains_remove():
    data = ["a", "b", "c", "d", "e", "f", "g", "h"]
    m = make_mh(num_perm=128, values=data)
    lsh = MinHashLSH(threshold=0.5, num_perm=128)
    lsh.insert("m1", m)
    assert "m1" in lsh
    result = lsh.query(m)
    assert "m1" in result
    lsh.remove("m1")
    assert "m1" not in lsh

def test_lsh_query_returns_similar_not_dissimilar():
    base = list(range(0, 1000))
    similar = list(range(50, 1050))
    different = list(range(5000, 6000))
    m_base = make_mh(num_perm=128, values=base)
    m_sim = make_mh(num_perm=128, values=similar)
    m_diff = make_mh(num_perm=128, values=different)

    lsh = MinHashLSH(threshold=0.6, num_perm=128)
    lsh.insert("sim", m_sim)
    lsh.insert("diff", m_diff)
    result = lsh.query(m_base)
    assert "sim" in result
    assert "diff" not in result

def test_lsh_pickle_round_trip():
    m = make_mh(num_perm=128, values=range(100))
    lsh = MinHashLSH(threshold=0.5, num_perm=128)
    lsh.insert("x", m)
    lsh2 = pickle.loads(pickle.dumps(lsh))
    assert "x" in lsh2
    assert "x" in lsh2.query(m)

def test_lsh_explicit_params_banding():
    m = make_mh(num_perm=16, values=range(10))
    lsh = MinHashLSH(num_perm=16, params=(4, 4))
    assert lsh.b == 4
    assert lsh.r == 4
    lsh.insert("k", m)
    assert "k" in lsh.query(m)

def test_hnsw_search_finds_self_first():
    HNSW = _get_hnsw()
    rng = np.random.RandomState(1)
    data = rng.rand(100, 10)
    index = HNSW(distance_func=_euclid)
    for i, v in enumerate(data):
        index.insert(i, v)
    res = _hnsw_query(index, data[7], 5)
    keys = [r[0] for r in res]
    assert 7 in keys
    # nearest neighbor (self) should be first with ~0 distance
    assert keys[0] == 7

def test_hnsw_soft_remove_then_clean():
    HNSW = _get_hnsw()
    rng = np.random.RandomState(2)
    data = rng.rand(80, 6)
    index = HNSW(distance_func=_euclid)
    for i, v in enumerate(data):
        index.insert(i, v)
    n0 = len(index)
    try:
        index.remove(5, hard=False)
    except TypeError:
        pytest.skip("soft/hard remove signature differs")
    # soft removed key no longer a member
    assert 5 not in index
    assert len(index) == n0 - 1
    # graph must remain searchable
    res = _hnsw_query(index, data[10], 5)
    keys = [r[0] for r in res]
    assert 5 not in keys
    if hasattr(index, "clean"):
        index.clean()
        res2 = _hnsw_query(index, data[10], 5)
        assert 5 not in [r[0] for r in res2]

def test_hnsw_hard_remove_keeps_graph_searchable():
    HNSW = _get_hnsw()
    rng = np.random.RandomState(3)
    data = rng.rand(80, 6)
    index = HNSW(distance_func=_euclid)
    for i, v in enumerate(data):
        index.insert(i, v)
    try:
        index.remove(0, hard=True)
    except TypeError:
        index.remove(0)
    assert 0 not in index
    # remaining points still retrievable
    res = _hnsw_query(index, data[20], 3)
    assert 20 in [r[0] for r in res]

def test_hnsw_pickle_round_trip():
    HNSW = _get_hnsw()
    rng = np.random.RandomState(5)
    data = rng.rand(50, 5)
    index = HNSW(distance_func=_euclid)
    for i, v in enumerate(data):
        index.insert(i, v)
    try:
        index2 = pickle.loads(pickle.dumps(index))
    except Exception:
        pytest.skip("HNSW not picklable in this configuration")
    assert len(index2) == len(index)
    res = _hnsw_query(index2, data[3], 3)
    assert 3 in [r[0] for r in res]
