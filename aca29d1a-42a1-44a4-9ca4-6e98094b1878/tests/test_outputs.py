import os
import re
import shutil
import subprocess
import pytest

# ---------------------------------------------------------------------------
# Helpers: locate the Rust crate and run its test suite once (cached).
# ---------------------------------------------------------------------------

REQUIRED_TESTS = [
    "basic_map",
    "timing_map",
    "big_scan",
    "bulk_load",
    "concurrent_tree",
    "test_00",
    "test_01",
    "test_02",
    "test_03",
    "leak_check",
]


def _find_crate_root():
    """Walk upward from this file (and cwd) to find the crate containing src/lib.rs."""
    candidates = []
    here = os.path.dirname(os.path.abspath(__file__))
    candidates.append(here)
    candidates.append(os.getcwd())
    seen = set()
    for start in candidates:
        d = start
        while True:
            if d in seen:
                break
            seen.add(d)
            cargo = os.path.join(d, "Cargo.toml")
            lib = os.path.join(d, "src", "lib.rs")
            if os.path.isfile(cargo) and os.path.isfile(lib):
                return d
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent
    # Fallback: search downward from cwd for src/lib.rs
    for root, dirs, files in os.walk(os.getcwd()):
        if "target" in dirs:
            dirs.remove("target")
        if "Cargo.toml" in files and os.path.isfile(os.path.join(root, "src", "lib.rs")):
            return root
    return None


CRATE_ROOT = _find_crate_root()


def _cargo_available():
    return shutil.which("cargo") is not None


_TEST_OUTPUT_CACHE = {}


def _run_cargo_tests():
    """Run the crate test suite (default + all-features) and cache combined output."""
    if "output" in _TEST_OUTPUT_CACHE:
        return _TEST_OUTPUT_CACHE["output"]

    combined = ""
    # Two invocations: default features, then all features (covers serde/timing).
    for args in (["cargo", "test"],
                 ["cargo", "test", "--all-features"]):
        try:
            proc = subprocess.run(
                args,
                cwd=CRATE_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=1800,
                text=True,
            )
            combined += proc.stdout or ""
        except subprocess.TimeoutExpired as e:
            out = e.output or ""
            if isinstance(out, bytes):
                out = out.decode("utf-8", "replace")
            combined += out
            combined += "\n<<TIMEOUT>>\n"
        combined += "\n<<END-INVOCATION>>\n"

    _TEST_OUTPUT_CACHE["output"] = combined
    return combined


def _skip_if_no_env():
    if CRATE_ROOT is None:
        pytest.skip("Could not locate the Rust crate root (src/lib.rs).")
    if not _cargo_available():
        pytest.skip("cargo toolchain not available in environment.")


def _test_passed(name, output):
    # Matches: "test <maybe::path::>name ... ok"
    pat = re.compile(r"test\s+(?:[\w:]+::)?" + re.escape(name) + r"\s+\.\.\.\s+ok")
    return bool(pat.search(output))


def _test_failed(name, output):
    pat = re.compile(r"test\s+(?:[\w:]+::)?" + re.escape(name) + r"\s+\.\.\.\s+FAILED")
    return bool(pat.search(output))


# ---------------------------------------------------------------------------
# Source-level contract checks (fast; discriminate stub vs. real).
# ---------------------------------------------------------------------------

def _read_source(relpath):
    if CRATE_ROOT is None:
        pytest.skip("Crate root not found.")
    path = os.path.join(CRATE_ROOT, relpath)
    if not os.path.isfile(path):
        pytest.skip(f"{relpath} not present.")
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()












# ---------------------------------------------------------------------------
# Behavioral checks via the real test suite (discriminate real vs. stub).
# ---------------------------------------------------------------------------


def test_lib_has_no_remaining_stub_panics():
    """A correct solution removes all 'STUB: not implemented' bodies from lib.rs."""
    src = _read_source(os.path.join("src", "lib.rs"))
    assert "STUB: not implemented" not in src, \
        "src/lib.rs still contains stubbed 'STUB: not implemented' bodies."
    # Guard against generic unimplemented placeholders too.
    assert "unimplemented!()" not in src, \
        "src/lib.rs still contains unimplemented!() placeholders."

def test_serde_has_no_remaining_stub_panics():
    src = _read_source(os.path.join("src", "serde.rs"))
    assert "STUB: not implemented" not in src, \
        "src/serde.rs still contains stubbed 'STUB: not implemented' bodies."
    assert "unimplemented!()" not in src, \
        "src/serde.rs still contains unimplemented!() placeholders."

def test_epoch_reclamation_and_rcu_machinery_present():
    """
    The solution must genuinely use epoch-based reclamation + RCU node machinery,
    not a Mutex<BTreeMap>/DashMap replacement (see 'cheat surface').
    """
    src = _read_source(os.path.join("src", "lib.rs"))
    # Real lock-free machinery must reference atomic pointers and the ebr guard.
    assert "AtomicPtr" in src, "Lock-free node slots (AtomicPtr) missing from lib.rs."
    assert "compare_exchange" in src, \
        "RCU install via compare_exchange missing from lib.rs."
    # Reject wholesale replacement with an off-the-shelf locked map.
    lowered = src.lower()
    for banned in ("mutex<", "rwlock<", "dashmap"):
        assert banned not in lowered, \
            f"Suspected cheat: internal map appears to use {banned!r} instead of the lock-free tree."

def test_suite_compiles_and_produces_test_results():
    _skip_if_no_env()
    out = _run_cargo_tests()
    assert "<<TIMEOUT>>" not in out, "cargo test timed out."
    # A correct build must produce at least one passing test-result line.
    assert re.search(r"test result:\s+ok", out), \
        "No 'test result: ok' summary produced; the suite did not pass.\n" + out[-4000:]
    # A stubbed solution panics -> FAILED lines; ensure none of the required tests failed.
    for name in REQUIRED_TESTS:
        assert not _test_failed(name, out), f"Required test '{name}' FAILED."

def test_timing_feature_tests_pass():
    """timing_map is gated on the `timing` feature; the --all-features run covers it."""
    _skip_if_no_env()
    out = _run_cargo_tests()
    assert "<<TIMEOUT>>" not in out, "cargo test timed out."
    # Must not have failed; and if present at all it must be ok.
    assert not _test_failed("timing_map", out), "timing_map FAILED under the timing feature."
    # It should appear as a passing test in the all-features run.
    assert _test_passed("timing_map", out), \
        "timing_map did not run/pass; ensure the timing feature build compiles and passes.\n" + out[-4000:]

def test_serde_feature_roundtrip_tests_pass():
    """
    With the serde feature, ConcurrentMap must serialize/deserialize to an equal map.
    We assert the crate's own serde-gated tests pass (any test compiled under --all-features
    that exercises serde) and that no test failed under the serde-enabled build.
    """
    _skip_if_no_env()
    out = _run_cargo_tests()
    assert "<<TIMEOUT>>" not in out, "cargo test timed out."
    # No failures anywhere in the all-features (serde-enabled) run.
    assert "FAILED" not in out or not re.search(r"\.\.\.\s+FAILED", out), \
        "Some test FAILED under the serde-enabled (all-features) build.\n" + out[-4000:]
    # The all-features run must still produce a passing summary.
    assert re.search(r"test result:\s+ok", out), \
        "No passing 'test result: ok' summary under the serde-enabled build."
    # Ensure serde was actually wired up in source (round-trip contract).
    src = _read_source(os.path.join("src", "serde.rs"))
    assert "Serialize" in src and "Deserialize" in src, \
        "serde.rs must implement Serialize/Deserialize for the round-trip contract."
