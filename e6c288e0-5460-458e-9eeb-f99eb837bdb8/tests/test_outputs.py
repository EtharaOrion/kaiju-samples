from kui.asgi.applications import Kui
import pytest


def test_differential_0():
    assert repr(Kui()) == '<kui.asgi.applications.Kui object at 0xffffa95e99d0>'

def test_differential_1():
    with pytest.raises(Exception):
        Kui(debug=True)

def test_differential_2():
    assert repr(type(Kui()).__name__) == "'Kui'"

def test_differential_3():
    assert repr(sorted(Kui().state.keys()) if hasattr(Kui().state, 'keys') else []) == '[]'

def test_differential_4():
    assert repr(hasattr(Kui(), 'router')) == 'True'

def test_differential_5():
    assert repr(hasattr(Kui(), 'exception_handlers')) == 'False'

def test_differential_6():
    assert repr(hasattr(Kui(), 'lifespan')) == 'True'

def test_differential_7():
    assert repr(callable(Kui())) == 'True'

def test_differential_8():
    with pytest.raises(Exception):
        Kui(debug=False).debug

def test_differential_9():
    assert repr(isinstance(Kui().state, object)) == 'True'

def test_differential_10():
    with pytest.raises(Exception):
        list(iter(Kui().router)) == list(iter(Kui().router))

def test_differential_11():
    assert repr(Kui().should_exit if hasattr(Kui(), 'should_exit') else None) == 'False'

def test_differential_12():
    assert repr(hasattr(Kui(), 'templates')) == 'True'

def test_differential_13():
    assert repr(repr(type(Kui()))) == '"<class \'kui.asgi.applications.Kui\'>"'



# ---- LLM-authored (golden-validated) tests ----
import asyncio

import pytest


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _tree_append(tree, path, endpoint):
    m = getattr(tree, "append", None) or getattr(tree, "add", None)
    assert m is not None, "RadixTree has no append/add method"
    try:
        return m(path, endpoint)
    except TypeError:
        node = m(path)
        if node is not None:
            try:
                node.endpoint = endpoint
            except Exception:
                pass
        return node


def _tree_search(tree, path):
    res = tree.search(path)
    params, node = res  # kui/index.py RadixTree.search -> (params, node)
    return (params or {}), node


# ---------------------------------------------------------------------------
# State container (kui/utils/state.py)
# ---------------------------------------------------------------------------



    # after deletion attribute access -> AttributeError, item -> KeyError
