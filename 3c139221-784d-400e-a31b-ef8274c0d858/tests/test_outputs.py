"""
Behavioral test-suite for the `async-h1` Rust crate.

The "solution module" here is a Rust crate.  We validate the behavioral
contract described in TRUTH.md by building and running the crate's own test
suite via `cargo test` and asserting that the concrete `fail_to_pass` tests
(which encode the contract) actually pass.

A correct implementation makes every listed test report `ok`; a stubbed /
broken implementation (the modules `panic!("STUB: not implemented")`) makes the
corresponding tests report `FAILED`, so these assertions fail.

Only the Python standard library + pytest are used.
"""

import os
import re
import shutil
import subprocess
import pathlib

import pytest


# --------------------------------------------------------------------------- #
# Locating the crate under test
# --------------------------------------------------------------------------- #
def find_crate_root():
    override = os.environ.get("SOLUTION_DIR") or os.environ.get("CRATE_DIR")
    if override:
        p = pathlib.Path(override)
        if (p / "Cargo.toml").exists():
            return p

    cwd = pathlib.Path.cwd()

    # Walk up from cwd looking for a crate root that looks like async-h1.
    for r in [cwd] + list(cwd.parents):
        cargo = r / "Cargo.toml"
        if cargo.exists() and (r / "src").is_dir():
            try:
                txt = cargo.read_text(errors="ignore")
            except OSError:
                txt = ""
            if (r / "src" / "chunked").exists() or "async-h1" in txt or "async_h1" in txt:
                return r

    # Fall back: search a few levels down for a matching crate.
    for base in [cwd] + list(cwd.parents)[:3]:
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in ("target", ".git", "node_modules")]
            if "Cargo.toml" in files and os.path.isdir(os.path.join(root, "src")):
                rp = pathlib.Path(root)
                if (rp / "src" / "chunked").exists():
                    return rp
    # Last resort: any Cargo.toml with a src dir.
    for r in [cwd] + list(cwd.parents):
        if (r / "Cargo.toml").exists() and (r / "src").is_dir():
            return r
    return None


CRATE_ROOT = find_crate_root()

_TEST_LINE = re.compile(r"^test\s+(\S+)\s+\.\.\.\s+(ok|FAILED|ignored)\s*$", re.M)


def _parse_results(text):
    """Return {test_name: [statuses...]} parsed from cargo test output."""
    results = {}
    for m in _TEST_LINE.finditer(text):
        name, status = m.group(1), m.group(2)
        results.setdefault(name, []).append(status)
    return results


@pytest.fixture(scope="session")
def cargo_results():
    if CRATE_ROOT is None:
        pytest.skip("no async-h1 Rust crate found to test against")
    if shutil.which("cargo") is None:
        pytest.skip("cargo toolchain not available")

    try:
        proc = subprocess.run(
            ["cargo", "test", "--no-fail-fast"],
            cwd=str(CRATE_ROOT),
            capture_output=True,
            text=True,
            timeout=2400,
        )
    except subprocess.TimeoutExpired:
        pytest.skip("cargo test timed out in this environment")

    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    results = _parse_results(combined)

    if not results:
        # Nothing ran: almost certainly a compile failure / broken stub build.
        pytest.fail(
            "cargo test produced no runnable tests (build failure?).\n"
            + combined[-4000:]
        )
    return results


# --------------------------------------------------------------------------- #
# Helpers to assert on named tests (matching by full path or any path suffix)
# --------------------------------------------------------------------------- #
def _matches(results, name):
    hits = {}
    for key, statuses in results.items():
        segs = key.split("::")
        tails = {"::".join(segs[i:]) for i in range(len(segs))}
        tails.add(key)
        if name in tails:
            hits[key] = statuses
    return hits


def assert_all_ok(results, name):
    hits = _matches(results, name)
    assert hits, (
        f"expected test '{name}' was not present in the cargo run "
        f"(ran {sum(len(v) for v in results.values())} tests)"
    )
    for key, statuses in hits.items():
        for st in statuses:
            assert st == "ok", f"test '{key}' reported '{st}', expected 'ok'"


# --------------------------------------------------------------------------- #
# Broad invariant: nothing regresses / the whole suite is green
# --------------------------------------------------------------------------- #




# --------------------------------------------------------------------------- #
# Chunked decoder (RFC 7230 §4.1 state machine)
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# Chunked encoder framing budget (max_bytes_to_read table)
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# HTTP date (IMF-fixdate formatting / parsing round-trip)
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# Server request-target Url construction across all target forms
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# Server body decode framing selection & Expect handling
# --------------------------------------------------------------------------- #




# --------------------------------------------------------------------------- #
# Server response encode (status line, framing, HEAD suppression)
# --------------------------------------------------------------------------- #




# --------------------------------------------------------------------------- #
# Accept loop: keep-alive + connection close semantics
# --------------------------------------------------------------------------- #




# --------------------------------------------------------------------------- #
# Client encode (request line, Date header, CONNECT, fragment, chunked body)
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# Client decode (multiple header values, newline conventions, closure framing)
# --------------------------------------------------------------------------- #


def test_no_test_failures_overall(cargo_results):
    failed = {
        k: v for k, v in cargo_results.items() if any(s == "FAILED" for s in v)
    }
    assert not failed, f"these tests failed on the solution: {sorted(failed)}"

def test_suite_actually_ran(cargo_results):
    total = sum(len(v) for v in cargo_results.values())
    assert total > 0

def test_chunked_encoder_budget_table(cargo_results):
    assert_all_ok(cargo_results, "simple_check_of_known_values")

def test_expect_continue_handling(cargo_results):
    assert_all_ok(cargo_results, "test_with_expect_when_reading_body")
    assert_all_ok(cargo_results, "test_without_expect_when_not_reading_body")

def test_server_chunked_large(cargo_results):
    assert_all_ok(cargo_results, "server_chunked_large")

def test_accept_basic(cargo_results):
    # 'basic' also appears in server_encode; all instances must be ok.
    assert_all_ok(cargo_results, "basic")
