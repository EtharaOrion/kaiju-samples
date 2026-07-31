from blacksheep.baseapp import BaseApplication
import pytest


def test_differential_0():
    assert repr(BaseApplication(True, None).show_error_details) == 'True'

def test_differential_1():
    assert repr(BaseApplication(False, None).show_error_details) == 'False'

def test_differential_2():
    assert repr(type(BaseApplication(True, None).exceptions_handlers).__name__) == "'ExceptionHandlersDict'"

def test_differential_3():
    assert repr(BaseApplication(True, None).exceptions_handlers) == "{404: <function handle_not_found at 0xffffbb324700>, 400: <function handle_bad_request at 0xffffbad12e60>, <class 'pydantic_core._pydantic_core.ValidationError'>: <function _default_pydantic_validation_error_handler at 0xffffbad12ef0>}"

def test_differential_4():
    assert repr(isinstance(BaseApplication(False, None).exceptions_handlers, dict)) == 'False'

def test_differential_5():
    assert repr(BaseApplication(True, None).get_http_exception_handler.__name__ if hasattr(BaseApplication(True, None), 'get_http_exception_handler') else None) == "'get_http_exception_handler'"

def test_differential_6():
    assert repr(hasattr(BaseApplication(True, None), 'handle')) == 'True'

def test_differential_7():
    assert repr(hasattr(BaseApplication(False, None), 'router')) == 'True'

def test_differential_8():
    assert repr(BaseApplication(True, None).router) == 'None'

def test_differential_9():
    assert repr(len(BaseApplication(True, None).exceptions_handlers)) == '3'

def test_differential_10():
    assert repr(sorted([k for k in dir(BaseApplication(True, None)) if not k.startswith('_')])) == "['exceptions_handlers', 'get_exception_handler', 'get_http_exception_handler', 'handle', 'handle_exception', 'handle_http_exception', 'handle_internal_server_error', 'handle_request_handler_exception', 'init_exceptions_handlers', 'is_handled_exception', 'log_handled_exc', 'log_unhandled_exc', 'logger', 'router', 'show_error_details']"

def test_differential_11():
    assert repr(callable(getattr(BaseApplication(True, None), 'handle', None))) == 'True'

def test_differential_12():
    assert repr(BaseApplication(0, None).show_error_details) == '0'

def test_differential_13():
    assert repr(bool(BaseApplication(True, None).exceptions_handlers)) == 'True'



# ---- LLM-authored (golden-validated) tests ----
"""
Behavioral tests for the BlackSheep framework re-implementation.

These tests exercise the pure-Python primitives and server machinery described
in TRUTH.md.  Each test asserts a concrete contractual behavior that a correct
implementation produces but an unimplemented stub does not.
"""

import json
from urllib.parse import unquote, parse_qs

import pytest


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _as_bytes(x):
    return x.encode() if isinstance(x, str) else x


def _as_str(x):
    return x.decode() if isinstance(x, (bytes, bytearray)) else x


# ---------------------------------------------------------------------------
# URL handling
# ---------------------------------------------------------------------------
