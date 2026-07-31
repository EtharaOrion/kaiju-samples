from tryalgo.PC_tree import *
import pytest


def test_differential_0():
    with pytest.raises(Exception):
        PC_tree({0, 1, 2, 3}).represent()

def test_differential_1():
    with pytest.raises(Exception):
        PC_tree({0, 1, 2, 3, 4, 5}).represent()

def test_differential_2():
    with pytest.raises(Exception):
        PC_tree(set(range(8))).frontier()

def test_differential_3():
    with pytest.raises(Exception):
        PC_tree({0, 1}).represent()

def test_differential_4():
    with pytest.raises(Exception):
        PC_tree({0, 1, 2}).frontier()

def test_differential_5():
    with pytest.raises(Exception):
        PC_tree(set(range(1))).represent()

def test_differential_6():
    with pytest.raises(Exception):
        PC_tree(set(range(10))).represent()

def test_differential_7():
    with pytest.raises(Exception):
        PC_tree({0, 1, 2, 3, 4}).frontier()

def test_differential_8():
    with pytest.raises(Exception):
        PC_tree(set(range(6))).frontier()

def test_differential_9():
    with pytest.raises(Exception):
        PC_tree({0, 1, 2, 3, 4, 5, 6, 7}).represent()

def test_differential_10():
    with pytest.raises(Exception):
        PC_tree(set(range(3))).represent()

def test_differential_11():
    with pytest.raises(Exception):
        PC_tree(set(range(12))).frontier()

def test_differential_12():
    with pytest.raises(Exception):
        PC_tree({0, 1, 2, 3}).frontier()

def test_differential_13():
    with pytest.raises(Exception):
        PC_tree(set(range(5))).represent()



# ---- LLM-authored (golden-validated) tests ----
"""Behavioral tests for the restored tryalgo library.

Each test imports the real public API and asserts algorithmic correctness
against known worked examples and invariants.
"""
import pytest


# ---------------------------------------------------------------------------
# Shortest paths
# ---------------------------------------------------------------------------








# ---------------------------------------------------------------------------
# BFS / DFS
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Strings
# ---------------------------------------------------------------------------










# ---------------------------------------------------------------------------
# Sequences / DP
# ---------------------------------------------------------------------------










# ---------------------------------------------------------------------------
# Binary search
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------










# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------






# ---------------------------------------------------------------------------
# Arithmetic
# ---------------------------------------------------------------------------








# ---------------------------------------------------------------------------
# our_std parsing helpers
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# Interval cover (dedicated test module coverage)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Freivalds matrix product verification
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Bipartite matching
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Topological order
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# PC-tree infeasibility exception
# ---------------------------------------------------------------------------


def test_subsetsum():
    from tryalgo.subsetsum import subset_sum
    assert subset_sum([1, 2, 3], 5) is True
    assert subset_sum([1, 2, 3], 7) is False

def test_fenwick_prefix_sum():
    from tryalgo.fenwick import Fenwick
    f = Fenwick([0, 0, 0, 0, 0])
    f.add(1, 5)   # 1-indexed
    f.add(3, 2)
    assert f.prefixSum(3) == 7
    assert f.intervalSum(1, 3) == 7

def test_our_heap():
    from tryalgo.our_heap import OurHeap
    h = OurHeap([(3, 'c'), (1, 'a'), (2, 'b')])
    assert h.pop() == (1, 'a')
    assert h.pop() == (2, 'b')
    h.push((0, 'z'))
    assert h.pop() == (0, 'z')

def test_our_queue_fifo():
    from tryalgo.our_queue import OurQueue
    q = OurQueue()
    q.push(1)
    q.push(2)
    q.push(3)
    assert q.pop() == 1
    assert q.pop() == 2
    q.push(4)
    assert q.pop() == 3
    assert q.pop() == 4
