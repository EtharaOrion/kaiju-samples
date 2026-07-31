"""
Behavioral test suite for the `Zahgon/rust-signals` re-implementation of
`futures-signals`.

Because the solution under test is a Rust crate (not an importable Python
module), these tests drive the *real* crate via `cargo`:

  * they compile the crate under its strict lint settings,
  * they run the crate's own behavioral test suite (which encodes the
    contract), and
  * they compile & run an *additional* Rust integration test that we write
    from scratch and place in the crate's `tests/` directory.  That extra test
    exercises contract invariants (initial-value delivery, change delivery,
    `map` and `map_ref!` semantics) that a stubbed/weak implementation cannot
    satisfy.

A stubbed solution (`panic!("STUB")` bodies) fails: it either does not compile
or panics at runtime.  A correct solution passes.
"""

import os
import re
import shutil
import subprocess
import textwrap

import pytest


# --------------------------------------------------------------------------- #
# Locating the crate
# --------------------------------------------------------------------------- #

def _find_crate_root():
    """Search upward from this file and the cwd for the crate root."""
    candidates = []
    here = os.path.dirname(os.path.abspath(__file__))
    candidates.append(here)
    candidates.append(os.getcwd())

    seen = set()
    for start in candidates:
        cur = start
        while True:
            if cur in seen:
                break
            seen.add(cur)
            cargo = os.path.join(cur, "Cargo.toml")
            atomic = os.path.join(cur, "src", "atomic.rs")
            if os.path.isfile(cargo) and os.path.isfile(atomic):
                return cur
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent
    return None


_CRATE_ROOT = _find_crate_root()
_HAS_CARGO = shutil.which("cargo") is not None


def _require_env():
    if _CRATE_ROOT is None:
        pytest.skip("could not locate the rust-signals crate root")
    if not _HAS_CARGO:
        pytest.skip("cargo toolchain not available")


def _src_files():
    src = os.path.join(_CRATE_ROOT, "src")
    out = []
    for root, _dirs, files in os.walk(src):
        for f in files:
            if f.endswith(".rs"):
                out.append(os.path.join(root, f))
    return out


def _read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _crate_import_name():
    """Package name from Cargo.toml, normalized to the Rust import identifier."""
    cargo = _read(os.path.join(_CRATE_ROOT, "Cargo.toml"))
    # Grab the [package] section's name.
    m = re.search(r"\[package\](.*?)(\n\[|\Z)", cargo, re.S)
    section = m.group(1) if m else cargo
    nm = re.search(r'name\s*=\s*"([^"]+)"', section)
    name = nm.group(1) if nm else "futures_signals"
    return name.replace("-", "_")


def _run_cargo(args, timeout=900):
    return subprocess.run(
        ["cargo"] + args,
        cwd=_CRATE_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
    )


# --------------------------------------------------------------------------- #
# Static / anti-cheat checks
# --------------------------------------------------------------------------- #







# --------------------------------------------------------------------------- #
# Build under strict lints
# --------------------------------------------------------------------------- #



# --------------------------------------------------------------------------- #
# The crate's own behavioral contract suite must pass
# --------------------------------------------------------------------------- #



# --------------------------------------------------------------------------- #
# Extra, from-scratch Rust integration test probing contract invariants
# --------------------------------------------------------------------------- #

_PROBE_NAME = "zz_contract_probe"

_PROBE_TEMPLATE = r'''
// Auto-generated behavioral probe for the rust-signals contract.
// Uses ONLY the crate's public API + std to assert:
//   * initial-value delivery on first poll,
//   * change delivery after a subsequent set,
//   * `map` combinator value semantics,
//   * `map_ref!` merge semantics (yields on any input change, reuses cached
//      values of unchanged inputs),
//   * termination (Ready(None)) once the last Mutable is dropped.

use std::pin::Pin;
use std::task::{{Context, Poll, RawWaker, RawWakerVTable, Waker}};

use {crate}::signal::{{Mutable, Signal, SignalExt}};
use {crate}::map_ref;

fn noop_raw_waker() -> RawWaker {{
    fn no_op(_: *const ()) {{}}
    fn clone(_: *const ()) -> RawWaker {{ noop_raw_waker() }}
    let vtable = &RawWakerVTable::new(clone, no_op, no_op, no_op);
    RawWaker::new(std::ptr::null(), vtable)
}}

fn noop_waker() -> Waker {{
    unsafe {{ Waker::from_raw(noop_raw_waker()) }}
}}

fn poll<S: Signal>(s: &mut Pin<Box<S>>) -> Poll<Option<S::Item>> {{
    let waker = noop_waker();
    let mut cx = Context::from_waker(&waker);
    s.as_mut().poll_change(&mut cx)
}}

#[test]
fn initial_value_is_delivered_then_pending() {{
    let m = Mutable::new(5i32);
    let mut s = Box::pin(m.signal());

    match poll(&mut s) {{
        Poll::Ready(Some(v)) => assert_eq!(v, 5, "first poll must yield current value"),
        other => panic!("expected initial value, got {{:?}}", other),
    }}
    // No change yet: must register waker and report Pending, not spin a value.
    match poll(&mut s) {{
        Poll::Pending => {{}}
        other => panic!("expected Pending with no change, got {{:?}}", other),
    }}
}}

#[test]
fn change_is_delivered_after_set() {{
    let m = Mutable::new(1i32);
    let mut s = Box::pin(m.signal());
    assert_eq!(poll(&mut s), Poll::Ready(Some(1)));
    assert_eq!(poll(&mut s), Poll::Pending);

    m.set(42);
    match poll(&mut s) {{
        Poll::Ready(Some(v)) => assert_eq!(v, 42, "must deliver latest value after set"),
        other => panic!("expected changed value 42, got {{:?}}", other),
    }}
}}

#[test]
fn map_combinator_transforms_values() {{
    let m = Mutable::new(3i32);
    let mut s = Box::pin(m.signal().map(|x| x * 10));
    assert_eq!(poll(&mut s), Poll::Ready(Some(30)));
    assert_eq!(poll(&mut s), Poll::Pending);
    m.set(7);
    assert_eq!(poll(&mut s), Poll::Ready(Some(70)));
}}

#[test]
fn map_ref_merges_and_reuses_cached_values() {{
    let a = Mutable::new(1i32);
    let b = Mutable::new(2i32);

    let mut s = Box::pin(map_ref! {{
        let x = a.signal(),
        let y = b.signal() =>
        *x + *y
    }});

    // First poll delivers combination of current values.
    assert_eq!(poll(&mut s), Poll::Ready(Some(3)));
    // No change -> Pending.
    assert_eq!(poll(&mut s), Poll::Pending);

    // Changing only `a` must re-emit using the cached value of `b`.
    a.set(10);
    match poll(&mut s) {{
        Poll::Ready(Some(v)) => assert_eq!(v, 12, "map_ref must reuse cached other input"),
        other => panic!("expected 12 after a.set(10), got {{:?}}", other),
    }}

    // Changing only `b` next.
    assert_eq!(poll(&mut s), Poll::Pending);
    b.set(100);
    match poll(&mut s) {{
        Poll::Ready(Some(v)) => assert_eq!(v, 110, "map_ref must reuse cached a input"),
        other => panic!("expected 110 after b.set(100), got {{:?}}", other),
    }}
}}

#[test]
fn signal_terminates_when_last_mutable_dropped() {{
    let m = Mutable::new(9i32);
    let mut s = Box::pin(m.signal());
    assert_eq!(poll(&mut s), Poll::Ready(Some(9)));
    drop(m);
    // After the last Mutable is gone the derived signal must terminate.
    match poll(&mut s) {{
        Poll::Ready(None) => {{}}
        other => panic!("expected termination Ready(None), got {{:?}}", other),
    }}
}}
'''


def test_no_remaining_stub_bodies():
    """A correct solution replaces every panic!("STUB ...") / todo! stub."""
    _require_env()
    offenders = []
    for path in _src_files():
        text = _read(path)
        if "STUB" in text:
            offenders.append(("STUB", path))
        # `todo!` / `unimplemented!` left on reachable paths is a stub too.
        if re.search(r"\btodo!\s*\(", text):
            offenders.append(("todo!", path))
        if re.search(r"\bunimplemented!\s*\(", text):
            offenders.append(("unimplemented!", path))
    assert not offenders, f"stub/unfinished bodies still present: {offenders}"

def test_atomic_uses_raw_box_conversion():
    """
    AtomicOption must implement the null-pointer optimization via Box raw
    pointer conversion (Box::into_raw / from_raw), not by leaking.
    """
    _require_env()
    atomic = _read(os.path.join(_CRATE_ROOT, "src", "atomic.rs"))
    assert "into_raw" in atomic, "AtomicOption should box values via into_raw"
    assert "from_raw" in atomic, "AtomicOption should reconstruct boxes via from_raw"
    # Leaking to dodge Drop correctness is a listed cheat.
    assert "mem::forget" not in atomic and "Box::leak" not in atomic, \
        "AtomicOption must not leak to avoid Drop correctness"

def test_crate_builds_under_strict_lints():
    """The crate denies warnings; a clean, complete solution must still build."""
    _require_env()
    proc = _run_cargo(["build", "--all-targets"])
    assert proc.returncode == 0, (
        "cargo build failed (strict lints / incomplete stubs):\n" + proc.stdout[-6000:]
    )

def test_full_behavioral_test_suite_passes():
    """
    Run the crate's own test suite.  These encode the diff/value/poll
    semantics of every combinator; a stub or overfit solution fails here.
    """
    _require_env()
    proc = _run_cargo(["test"])
    tail = proc.stdout[-8000:]
    assert proc.returncode == 0, "cargo test reported failures:\n" + tail
    # Sanity: make sure tests actually ran (not silently zero).
    assert "test result:" in proc.stdout, \
        "no test results detected — did the suite actually run?\n" + tail
    assert "FAILED" not in proc.stdout, "one or more tests FAILED:\n" + tail

def test_extra_contract_probe_passes():
    """
    Compile & run our own from-scratch integration test that pins down
    invariants the frozen suite might under-check (initial delivery, cached
    reuse in map_ref, pending-registration, termination on drop).
    """
    _require_env()
    crate = _crate_import_name()
    tests_dir = os.path.join(_CRATE_ROOT, "tests")
    os.makedirs(tests_dir, exist_ok=True)
    probe_path = os.path.join(tests_dir, _PROBE_NAME + ".rs")

    source = textwrap.dedent(_PROBE_TEMPLATE).format(crate=crate)
    with open(probe_path, "w", encoding="utf-8") as fh:
        fh.write(source)

    try:
        proc = _run_cargo(["test", "--test", _PROBE_NAME])
        tail = proc.stdout[-8000:]
        assert proc.returncode == 0, (
            "contract probe failed (stub or incorrect semantics):\n" + tail
        )
        assert "test result: ok" in proc.stdout, \
            "contract probe did not report ok:\n" + tail
    finally:
        try:
            os.remove(probe_path)
        except OSError:
            pass
