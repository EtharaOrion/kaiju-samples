import importlib

import pytest


def _imp(name):
    """Import a pymonad submodule, tolerating either package or flat layout."""
    for candidate in (f"pymonad.{name}", name):
        try:
            return importlib.import_module(candidate)
        except Exception:
            continue
    pytest.skip(f"cannot import module {name}")


# ---------------------------------------------------------------------------
# Either
# ---------------------------------------------------------------------------























# ---------------------------------------------------------------------------
# Maybe
# ---------------------------------------------------------------------------



















# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------













# ---------------------------------------------------------------------------
# IO
# ---------------------------------------------------------------------------







# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------





# ---------------------------------------------------------------------------
# Monoid
# ---------------------------------------------------------------------------





# ---------------------------------------------------------------------------
# tools.curry
# ---------------------------------------------------------------------------


def test_either_left_right_repr():
    e = _imp("either")
    assert repr(e.Right(5)) == "Right 5"
    assert repr(e.Left("err")) == "Left err"

def test_either_is_left_is_right():
    e = _imp("either")
    r = e.Right(1)
    l = e.Left(2)
    assert r.is_right() is True
    assert r.is_left() is False
    assert l.is_left() is True
    assert l.is_right() is False

def test_either_insert_is_right():
    e = _imp("either")
    ins = e.Either.insert(7)
    assert ins.is_right() is True
    assert ins == e.Right(7)

def test_either_functor_identity():
    e = _imp("either")
    r = e.Right(10)
    assert r.map(lambda x: x) == r

def test_either_functor_composition():
    e = _imp("either")
    r = e.Right(3)
    f = lambda x: x + 1
    g = lambda x: x * 2
    assert r.map(f).map(g) == r.map(lambda x: g(f(x)))

def test_either_map_left_short_circuits():
    e = _imp("either")
    l = e.Left("boom")
    assert l.map(lambda x: x + 1) == l

def test_either_bind_left_identity():
    e = _imp("either")
    f = lambda x: e.Right(x + 100)
    assert e.Either.insert(5).bind(f) == f(5)

def test_either_bind_right_identity():
    e = _imp("either")
    m = e.Right(9)
    assert m.bind(lambda x: e.Either.insert(x)) == m

def test_either_extract_dispatch():
    e = _imp("either")
    r = e.Right(4)
    l = e.Left(4)
    assert r.either(lambda x: "L", lambda x: "R") == "R"
    assert l.either(lambda x: "L", lambda x: "R") == "L"

def test_either_amap_short_circuit_positions():
    e = _imp("either")
    fail_fn = e.Left("f_fail")
    good_fn = e.Right(lambda x: x + 1)
    fail_val = e.Left("v_fail")
    good_val = e.Right(10)
    # function-side failure
    assert good_val.amap(fail_fn) == fail_fn or fail_fn.amap(good_val) == fail_fn
    # value-side failure
    res = good_fn.amap(fail_val)
    assert res.is_left()

def test_maybe_is_just_nothing():
    m = _imp("maybe")
    assert m.Just(1).is_just() is True
    assert m.Just(1).is_nothing() is False
    assert m.Nothing.is_nothing() is True
    assert m.Nothing.is_just() is False

def test_maybe_insert_is_just():
    m = _imp("maybe")
    ins = m.Maybe.insert(3)
    assert ins.is_just() is True
    assert ins == m.Just(3)

def test_maybe_functor_identity_and_composition():
    m = _imp("maybe")
    j = m.Just(4)
    assert j.map(lambda x: x) == j
    f = lambda x: x + 1
    g = lambda x: x * 3
    assert j.map(f).map(g) == j.map(lambda x: g(f(x)))

def test_maybe_map_nothing_short_circuits():
    m = _imp("maybe")
    assert m.Nothing.map(lambda x: x + 1) == m.Nothing

def test_maybe_bind_laws():
    m = _imp("maybe")
    f = lambda x: m.Just(x + 10)
    assert m.Maybe.insert(2).bind(f) == f(2)
    assert m.Just(2).bind(lambda x: m.Maybe.insert(x)) == m.Just(2)

def test_maybe_does_not_swallow_exceptions_in_map():
    m = _imp("maybe")

    def boom(x):
        raise ValueError("propagate me")

    with pytest.raises(ValueError):
        m.Just(1).map(boom)

def test_maybe_does_not_swallow_exceptions_in_bind():
    m = _imp("maybe")

    def boom(x):
        raise ValueError("propagate me")

    with pytest.raises(ValueError):
        m.Just(1).bind(boom)

def test_maybe_option_default_dispatch():
    m = _imp("maybe")
    fn = m.Nothing
    # maybe(default, fn) returns default on Nothing
    assert m.Nothing.maybe("default", lambda x: x) == "default"
    assert m.Just(5).maybe("default", lambda x: x + 1) == 6

def test_list_map():
    lm = _imp("list")
    x = lm.ListMonad(1, 2, 3)
    mapped = x.map(lambda v: v * 10)
    assert list(mapped) == [10, 20, 30]

def test_list_monoid_identity_left_and_right():
    lm = _imp("list")
    x = lm.ListMonad(1, 2, 3)
    ident = x.identity_element()
    assert list(x + ident) == [1, 2, 3]
    assert list(ident + x) == [1, 2, 3]

def test_list_concatenation():
    lm = _imp("list")
    a = lm.ListMonad(1, 2)
    b = lm.ListMonad(3, 4)
    assert list(a + b) == [1, 2, 3, 4]

def test_list_bind_flattens():
    lm = _imp("list")
    x = lm.ListMonad(1, 2, 3)
    res = x.bind(lambda v: lm.ListMonad(v, v))
    assert list(res) == [1, 1, 2, 2, 3, 3]

def test_io_is_lazy():
    io = _imp("io")
    log = []
    comp = io.IO(lambda: log.append("ran") or 42)
    # map should NOT execute yet
    mapped = comp.map(lambda x: x + 1)
    assert log == []
    result = mapped.run()
    assert result == 43
    assert log == ["ran"]

def test_io_insert_run():
    io = _imp("io")
    assert io.IO.insert(99).run() == 99

def test_io_bind_lazy_and_correct():
    io = _imp("io")
    log = []
    comp = io.IO(lambda: log.append("a") or 5)
    bound = comp.bind(lambda x: io.IO(lambda: log.append("b") or x * 2))
    assert log == []
    assert bound.run() == 10

def test_curry_basic():
    tools = _imp("tools")

    @tools.curry(2)
    def add(a, b):
        return a + b

    assert add(1)(2) == 3
    assert add(1, 2) == 3

def test_curry_three_args_partial():
    tools = _imp("tools")

    @tools.curry(3)
    def f(a, b, c):
        return a + b + c

    assert f(1)(2)(3) == 6
    assert f(1, 2)(3) == 6
    assert f(1)(2, 3) == 6
