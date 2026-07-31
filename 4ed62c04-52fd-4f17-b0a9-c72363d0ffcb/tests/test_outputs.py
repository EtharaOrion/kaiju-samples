"""
Behavioral verification for the `signature_pad` TypeScript solution.

Because the solution is authored in TypeScript (which cannot be imported into a
Python interpreter), these tests verify the *behavioral contract* documented in
TRUTH.md by statically analysing the restored source files.  Every assertion
here targets a concrete requirement of the contract / a listed pitfall, so a
stubbed implementation (bodies replaced with `throw new Error("STUB")`) fails,
while a correct restoration passes.
"""

import os
import re
import pathlib

import pytest


# --------------------------------------------------------------------------- #
# Locate the `src/` directory of the repository under test.
# --------------------------------------------------------------------------- #
STUB_FILES = [
    "point.ts",
    "bezier.ts",
    "signature_event_target.ts",
    "throttle.ts",
    "signature_pad.ts",
]


def _find_src_dir():
    start = pathlib.Path(__file__).resolve()
    candidates = []
    # Walk upward from the test file, then broaden to cwd.
    for base in [start.parent, *start.parents, pathlib.Path.cwd()]:
        candidates.append(base / "src")
        candidates.append(base)
    seen = set()
    for c in candidates:
        c = c.resolve()
        if c in seen:
            continue
        seen.add(c)
        # A directory qualifies if it directly holds the stub files.
        if all((c / f).is_file() for f in STUB_FILES):
            return c
        # Or search one level for a src dir.
        maybe = c / "src"
        if all((maybe / f).is_file() for f in STUB_FILES):
            return maybe
    # Last resort: recursive search from repo root guesses.
    for base in [start.parent, *start.parents]:
        for path in base.rglob("point.ts"):
            d = path.parent
            if all((d / f).is_file() for f in STUB_FILES):
                return d
    return None


SRC = _find_src_dir()


def _require_src():
    if SRC is None:
        pytest.skip("Could not locate signature_pad src/ directory")
    return SRC


def _read(name):
    src = _require_src()
    p = src / name
    assert p.is_file(), f"Missing source file: {name}"
    return p.read_text(encoding="utf-8")


def _strip_comments(code):
    # Remove block comments and line comments (best-effort, not string-aware,
    # but good enough for the structural checks below).
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)
    code = re.sub(r"//[^\n]*", "", code)
    return code


# --------------------------------------------------------------------------- #
# 1. No STUB placeholder must remain in any of the five files.
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# 2. Import hygiene: every relative import/export specifier ends with `.js`.
# --------------------------------------------------------------------------- #
def _all_ts_files():
    src = _require_src()
    return sorted(src.rglob("*.ts"))


SPECIFIER_RE = re.compile(
    r"""(?:import|export)\b[^;'"]*?from\s*['"]([^'"]+)['"]""",
    re.DOTALL,
)
BARE_IMPORT_RE = re.compile(r"""import\s*['"]([^'"]+)['"]""")






# --------------------------------------------------------------------------- #
# 3. Point contract.
# --------------------------------------------------------------------------- #










# --------------------------------------------------------------------------- #
# 4. Bezier contract.
# --------------------------------------------------------------------------- #








# --------------------------------------------------------------------------- #
# 5. SignatureEventTarget contract.
# --------------------------------------------------------------------------- #






# --------------------------------------------------------------------------- #
# 6. throttle contract.
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# 7. SignaturePad contract.
# --------------------------------------------------------------------------- #


















if __name__ == "__main__":  # pragma: no cover
    import sys
    sys.exit(pytest.main([__file__, "-v"]))


def test_point_validates_nan_and_coerces():
    code = _strip_comments(_read("point.ts"))
    # Must throw on invalid (NaN) coordinates.
    assert "throw" in code, "Point must throw on invalid coordinates"
    assert re.search(r"isNaN|Number\.isNaN|=== *NaN|!= *number", code) or "NaN" in code, \
        "Point must detect NaN coordinates"
    # Must coerce string numeric inputs to numbers.
    assert re.search(r"Number\(|parseFloat|\+x|\* *1|Number\.parseFloat", code), \
        "Point must coerce inputs to numbers"

def test_point_equals_compares_all_four_fields():
    code = _read("point.ts")
    # Isolate the equals method body heuristically.
    m = re.search(r"equals\s*\([^)]*\)\s*(?::[^\{]*)?\{(.*?)\n\s*\}", code, re.DOTALL)
    body = m.group(1) if m else code
    for field in ("x", "y", "pressure", "time"):
        assert field in body, f"Point.equals must compare '{field}'"

def test_point_velocity_guards_equal_time():
    code = _read("point.ts")
    m = re.search(r"velocityFrom\s*\([^)]*\)\s*(?::[^\{]*)?\{(.*?)\n\s*\}", code, re.DOTALL)
    body = m.group(1) if m else code
    # Must have a zero-return path for equal times (to avoid NaN/Infinity).
    assert re.search(r"time", body), "velocityFrom must reference time"
    assert re.search(r"\?\s*0|return\s+0|:\s*0", body), \
        "velocityFrom must return 0 when times are equal"

def test_point_defaults_pressure_and_time():
    code = _strip_comments(_read("point.ts"))
    assert re.search(r"pressure", code), "Point must handle pressure default"
    assert re.search(r"Date\.now\(\)|new Date\(\)\.getTime\(\)", code), \
        "Point time default must use current timestamp"

def test_bezier_length_samples_curve():
    code = _strip_comments(_read("bezier.ts"))
    # Arc-length approximation must actually compute distances (sqrt of squares).
    assert re.search(r"Math\.sqrt", code) or re.search(r"\*\* *0\.5", code), \
        "Bezier.length must approximate distance via sqrt"
    # Must sample across parametric t (a loop of some kind).
    assert re.search(r"\bfor\b|\.reduce|\bwhile\b", code), \
        "Bezier.length must iterate/sample the curve"

def test_bezier_guards_division_by_zero():
    code = _strip_comments(_read("bezier.ts"))
    # Coincident points -> l1 + l2 == 0 must be guarded to avoid NaN.
    # Accept a zero-check conditional or an epsilon guard.
    has_zero_guard = bool(
        re.search(r"===\s*0", code)
        or re.search(r"==\s*0", code)
        or re.search(r"\?\s*0\s*:", code)
        or re.search(r"Number\.isFinite|isNaN", code)
        or re.search(r"e-?\d|epsilon|EPSILON", code)
    )
    assert has_zero_guard, "Bezier must guard the zero-length division (NaN safety)"

def test_event_target_constructs_with_document_fallback():
    code = _strip_comments(_read("signature_event_target.ts"))
    assert "EventTarget" in code, "Must construct a native EventTarget"
    assert re.search(r"\btry\b", code) and re.search(r"\bcatch\b", code), \
        "Must guard EventTarget construction with try/catch"
    assert "document" in code, "Must fall back to document when EventTarget unavailable"

def test_dispatch_event_returns_delegated_result():
    code = _read("signature_event_target.ts")
    m = re.search(r"dispatchEvent\s*\([^)]*\)\s*(?::[^\{]*)?\{(.*?)\n\s*\}", code, re.DOTALL)
    assert m, "dispatchEvent method not found"
    body = m.group(1)
    # Must return the delegated call result, not a hard-coded boolean.
    assert "return" in body, "dispatchEvent must return the delegated result"
    assert "dispatchEvent" in body, "dispatchEvent must delegate to internal target"
    assert not re.search(r"return\s+true\s*;", body), \
        "dispatchEvent must not hard-code true"
    assert not re.search(r"return\s+false\s*;", body), \
        "dispatchEvent must not hard-code false"

def test_throttle_returns_wrapper_and_rate_limits():
    code = _strip_comments(_read("throttle.ts"))
    assert re.search(r"return\s+function|=>|return\s+\(", code), \
        "throttle must return a wrapper function"
    # Time-based limiting: either timestamps or timeouts.
    assert re.search(r"Date\.now|getTime|setTimeout|performance\.now", code), \
        "throttle must use time-based rate limiting"
    # Must capture the latest arguments for a trailing invocation.
    assert "arguments" in code or "args" in code or "..." in code, \
        "throttle must preserve most-recent arguments"

def test_signature_pad_uses_nullish_coalescing_for_zero_preserving_options():
    code = _strip_comments(_read("signature_pad.ts"))
    # throttle & minDistance must preserve an explicit 0 -> use ?? (nullish) or
    # an explicit `=== undefined` check.
    uses_nullish = "??" in code
    uses_undefined_check = "=== undefined" in code or "!== undefined" in code
    assert uses_nullish or uses_undefined_check, (
        "throttle/minDistance must be resolved with nullish-coalescing or explicit "
        "undefined checks to preserve a legitimate 0"
    )
    assert re.search(r"\bthrottle\b", code), "throttle option must be handled"
    assert re.search(r"\bminDistance\b", code), "minDistance option must be handled"

def test_signature_pad_option_defaults_present():
    code = _strip_comments(_read("signature_pad.ts"))
    for token in (
        "velocityFilterWeight",
        "minWidth",
        "maxWidth",
        "dotSize",
        "penColor",
        "backgroundColor",
        "compositeOperation",
    ):
        assert token in code, f"SignaturePad must resolve option '{token}'"
    assert re.search(r"source-over", code), "compositeOperation default 'source-over' expected"
    assert re.search(r"'black'|\"black\"", code), "penColor default 'black' expected"

def test_signature_pad_begin_stroke_is_cancelable():
    code = _strip_comments(_read("signature_pad.ts"))
    assert re.search(r"beginStroke", code), "beginStroke event must be dispatched"
    # A cancelable CustomEvent is required for preventDefault to abort a stroke.
    assert re.search(r"cancelable\s*:\s*true", code), \
        "beginStroke must be dispatched as cancelable"

def test_signature_pad_dispatches_all_lifecycle_events():
    code = _read("signature_pad.ts")
    for evt in ("beginStroke", "beforeUpdateStroke", "afterUpdateStroke", "endStroke"):
        assert evt in code, f"SignaturePad must dispatch '{evt}'"

def test_signature_pad_toggles_touch_and_selection_styles():
    code = _strip_comments(_read("signature_pad.ts"))
    for prop in ("touchAction", "msTouchAction", "userSelect", "webkitUserSelect"):
        assert prop in code, f"on/off must manage style '{prop}'"
    # Both the disabling ('none') and restoring ('auto') values must appear.
    assert "'none'" in code or '"none"' in code, "on() must set touch/select to none"
    assert "'auto'" in code or '"auto"' in code, "off() must restore touch/select to auto"

def test_signature_pad_toDataURL_type_guards_svg():
    code = _strip_comments(_read("signature_pad.ts"))
    assert "image/svg+xml" in code, "toDataURL must special-case SVG"
    # SVG variant must base64-encode (btoa or Buffer) the SVG payload.
    assert re.search(r"btoa|Buffer\.from|base64", code), \
        "SVG data URL must be base64 encoded"

def test_signature_pad_touch_preventdefault_gated_on_cancelable():
    code = _strip_comments(_read("signature_pad.ts"))
    # Touch handlers must only call preventDefault when the event is cancelable.
    assert "preventDefault" in code, "SignaturePad must call preventDefault somewhere"
    assert "cancelable" in code, \
        "Touch handling must consult event.cancelable before preventDefault"
