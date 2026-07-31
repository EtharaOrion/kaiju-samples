from jsons._cache import *
import pytest


def test_differential_0():
    assert repr(clear()) == 'None'

def test_differential_1():
    assert repr(cached(lambda x: x + 1)(5)) == '6'

def test_differential_2():
    assert repr(cached(lambda x: x + 1)(0)) == '1'

def test_differential_3():
    assert repr(cached(len)((1, 2, 3))) == '3'

def test_differential_4():
    assert repr(cached(str)(42)) == "'42'"

def test_differential_5():
    assert repr(cached(lambda: 'const')()) == "'const'"

def test_differential_6():
    assert repr(cached(lambda x, y: x * y)(3, 4)) == '12'

def test_differential_7():
    assert repr(cached(abs)(-7)) == '7'

def test_differential_8():
    assert repr(cached(lambda s: s.upper())('hello')) == "'HELLO'"

def test_differential_9():
    assert repr(cached(lambda s: s)('')) == "''"

def test_differential_10():
    assert repr(cached(lambda x: x)('ünicøde')) == "'ünicøde'"

def test_differential_11():
    assert repr(cached(lambda x=1: x)(10)) == '10'

def test_differential_12():
    assert repr((cached(lambda x: x * 2)(21), clear())) == '(42, None)'

def test_differential_13():
    assert repr(cached(lambda t: sum(t))((1, 2, 3, 4, 5))) == '15'



# ---- LLM-authored (golden-validated) tests ----
import datetime
import uuid
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

import pytest

import jsons


# ---------------------------------------------------------------------------
# Module-level types (must be importable by fully-qualified name for verbose)
# ---------------------------------------------------------------------------

class Foo(jsons.JsonSerializable):
    def __init__(self, x):
        self.x = x

    def __eq__(self, other):
        return isinstance(other, Foo) and other.x == self.x


@dataclass
class Point:
    x: int
    y: int


class Color(Enum):
    RED = 1
    GREEN = 2


# ---------------------------------------------------------------------------
# Primitive round trips
# ---------------------------------------------------------------------------







# ---------------------------------------------------------------------------
# Collections
# ---------------------------------------------------------------------------











# ---------------------------------------------------------------------------
# Numeric / special scalar types
# ---------------------------------------------------------------------------







# ---------------------------------------------------------------------------
# Datetimes
# ---------------------------------------------------------------------------







# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------





# ---------------------------------------------------------------------------
# Dataclasses (type inference on dump)
# ---------------------------------------------------------------------------





# ---------------------------------------------------------------------------
# Key transformers (direct, discriminating)
# ---------------------------------------------------------------------------













# ---------------------------------------------------------------------------
# Custom serializers and fork isolation
# ---------------------------------------------------------------------------





# ---------------------------------------------------------------------------
# JsonSerializable mixin
# ---------------------------------------------------------------------------





# ---------------------------------------------------------------------------
# Verbose mode
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# None / Any handling
# ---------------------------------------------------------------------------





# ---------------------------------------------------------------------------
# dumps / loads (string round trip)
# ---------------------------------------------------------------------------





# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


def test_json_serializable_json_property_matches_dump():
    foo = Foo(7)
    assert foo.json == jsons.dump(foo)
    assert foo.json == {'x': 7}

def test_json_serializable_from_json():
    foo = Foo.from_json({'x': 9})
    assert isinstance(foo, Foo)
    assert foo.x == 9
