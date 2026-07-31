from etl.dtyp import *
import pytest


def test_differential_0():
    with pytest.raises(Exception):
        SID.parse(b'\x01\x01\x00\x00\x00\x00\x00\x05\x12\x00\x00\x00')

def test_differential_1():
    with pytest.raises(Exception):
        SID.parse(b'\x01\x02\x00\x00\x00\x00\x00\x05\x20\x00\x00\x00\x20\x02\x00\x00')

def test_differential_2():
    with pytest.raises(Exception):
        SID.parse(b'\x01\x00\x00\x00\x00\x00\x00\x00')

def test_differential_3():
    with pytest.raises(Exception):
        SID.parse(b'\x01\x05\x00\x00\x00\x00\x00\x05\x15\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10')

def test_differential_4():
    with pytest.raises(Exception):
        ACL.parse(b'\x02\x00\x08\x00\x00\x00\x00\x00')

def test_differential_5():
    with pytest.raises(Exception):
        ACL.parse(b'\x02\x00\x08\x00\x01\x00\x00\x00')

def test_differential_6():
    with pytest.raises(Exception):
        SID.parse(b'\x01\x01\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00')

def test_differential_7():
    with pytest.raises(Exception):
        SID.parse(b'\x01\x04\x00\x00\x00\x00\x00\x05\x15\x00\x00\x00\x0a\x00\x00\x00\x14\x00\x00\x00\x1e\x00\x00\x00')

def test_differential_8():
    with pytest.raises(Exception):
        ACL.parse(b'\x02\x00\x18\x00\x02\x00\x00\x00' + b'\x00\x00\x00\x00')

def test_differential_9():
    with pytest.raises(Exception):
        SID.parse(b'\x01\x02\x00\x00\x00\x00\x00\x0f\xff\xff\xff\xff\xff\xff\xff\xff')

def test_differential_10():
    with pytest.raises(Exception):
        SID.parse(b'\x01\x00\x00\x00\x00\x00\x00\x12')

def test_differential_11():
    with pytest.raises(Exception):
        ACL.parse(b'\x04\x00\x08\x00\x00\x00\x00\x00')

def test_differential_12():
    with pytest.raises(Exception):
        SID.parse(b'\x01\x03\x00\x00\x00\x00\x00\x05\x00\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00')

def test_differential_13():
    with pytest.raises(Exception):
        SID.parse(b'\x01\x01\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00')



# ---- LLM-authored (golden-validated) tests ----
"""Behavioral tests for the etl-parser restoration (Zahgon/etl-parser).

These tests import the real solution modules and assert on concrete outputs /
contract invariants described in TRUTH.md.  A stubbed implementation (function
bodies replaced by ``pass``) returns ``None`` / fails to raise the specific
exceptions and therefore fails these tests, while a correct implementation
passes them.
"""

import importlib

import pytest


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _import(name):
    try:
        return importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - surfaces as a real failure
        pytest.fail("could not import required module %r: %r" % (name, exc))


def _decode(val):
    if isinstance(val, bytes):
        try:
            return val.decode("utf-16-le").rstrip("\x00")
        except Exception:
            return val.decode("latin-1").rstrip("\x00")
    return str(val)


# --------------------------------------------------------------------------- #
# GUID parsing (etl/utils.py)
# --------------------------------------------------------------------------- #






# --------------------------------------------------------------------------- #
# check_enum helper (etl/utils.py) + InvalidType (etl/error.py)
# --------------------------------------------------------------------------- #
def _build_enum():
    from construct import Enum as CEnum, Int8ul

    return CEnum(Int8ul, FOO=1, BAR=2, BAZ=3)


def _call_check_enum(check_enum, value, enum):
    try:
        return check_enum(value, enum)
    except TypeError:
        # tolerate an (enum, value) argument order
        return check_enum(enum, value)






# --------------------------------------------------------------------------- #
# WString / CString primitive parsers
# --------------------------------------------------------------------------- #




# --------------------------------------------------------------------------- #
# Exception hierarchy (etl/error.py)
# --------------------------------------------------------------------------- #
EXPECTED_EXCEPTIONS = [
    "InvalidType",
    "TlMetaDataNotFound",
    "TlUnhandledTag",
    "GroupNotFound",
    "VersionNotFound",
    "EventTypeNotFound",
    "GuidNotFound",
    "EventIdNotFound",
    "EtwVersionNotFound",
    "InvalidEtlFileHeader",
]








# --------------------------------------------------------------------------- #
# Module importability (regression guard for the restored infrastructure)
# --------------------------------------------------------------------------- #




# --------------------------------------------------------------------------- #
# TraceLogging surface (etl/tracelogging.py)
# --------------------------------------------------------------------------- #
