"""
Behavioral verification for the restored `riker` Rust actor-system crate.

TRUTH.md describes a Rust crate whose stubbed function bodies must be restored so
that the crate compiles and its integration/unit `fail_to_pass` test-suite passes.

Since the "solution module" is a Rust crate (not an importable Python module), the
only faithful way to assert on *real outputs* / *real behavior* is to drive the
crate's own build + test harness through `cargo` and assert on concrete results:

  * the crate library + test targets compile,
  * no `STUB: not implemented` panic remains on any exercised path,
  * every named `fail_to_pass` behavioral cluster actually passes.

A stubbed / broken solution will fail to compile or will panic with the STUB
message (or the specific behavioral test will fail), causing these tests to FAIL.
A correct general implementation makes them PASS.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest


# --------------------------------------------------------------------------- #
# Locate the crate and cargo toolchain.
# --------------------------------------------------------------------------- #
def _find_crate_root() -> Path:
    # Explicit override wins.
    env = os.environ.get("RIKER_DIR") or os.environ.get("CRATE_DIR")
    if env:
        p = Path(env).expanduser().resolve()
        if (p / "Cargo.toml").is_file():
            return p

    # Search from CWD and this file's location upward + a couple levels down.
    candidates = []
    here = Path(__file__).resolve().parent
    for base in {Path.cwd().resolve(), here, *here.parents}:
        candidates.append(base)

    seen = set()
    for base in candidates:
        for depth_dir in [base, *[d for d in base.iterdir() if d.is_dir()]] if base.is_dir() else []:
            if depth_dir in seen:
                continue
            seen.add(depth_dir)
            cargo = depth_dir / "Cargo.toml"
            if cargo.is_file():
                # Confirm it's the riker crate by its module layout from TRUTH.md.
                if (depth_dir / "src" / "actor.rs").is_file() and (
                    depth_dir / "src" / "kernel.rs"
                ).is_file():
                    return depth_dir
    # Fallback: nearest Cargo.toml at CWD.
    if (Path.cwd() / "Cargo.toml").is_file():
        return Path.cwd().resolve()
    return None  # type: ignore[return-value]


CRATE_ROOT = _find_crate_root()
CARGO = shutil.which("cargo")

_STUB_MARKER = "STUB: not implemented"

# Behavioral clusters from TRUTH.md success criteria.
FAIL_TO_PASS = [
    "actor_create",
    "actor_stop",
    "actor_tell",
    "actor_try_tell",
    "channel_dead_letters",
    "channel_publish",
    "channel_publish_subscribe_all",
    "channel_system_events",
    "logging_stdlog",
    "system_create_with_slog",
    "schedule_at_time",
    "schedule_once",
    "schedule_repeat",
    "select_all_children_of_child",
    "select_child",
    "select_child_of_child",
    "select_from_context",
    "select_paths",
    "supervision_escalate_failed_actor",
    "supervision_restart_failed_actor",
    "system_builder",
    "system_create",
    "system_futures_exec",
    "system_futures_panic",
    "system_load_app_config",
    "system_shutdown",
]


pytestmark = pytest.mark.skipif(
    CARGO is None or CRATE_ROOT is None,
    reason="cargo toolchain and/or the riker crate could not be located",
)


def _run_cargo(args, timeout):
    """Run cargo in the crate root, returning CompletedProcess with captured output."""
    cmd = [CARGO, *args]
    return subprocess.run(
        cmd,
        cwd=str(CRATE_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
        env={**os.environ, "RUST_BACKTRACE": "1", "CARGO_TERM_COLOR": "never"},
    )


# --------------------------------------------------------------------------- #
# Session-scoped build so individual behavioral tests are fast and independent.
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def built_crate():
    # Compile library + all test targets. A stubbed crate that doesn't compile
    # (e.g. missing constructors / trait bodies) fails right here.
    proc = _run_cargo(["build", "--tests"], timeout=1800)
    if proc.returncode != 0:
        pytest.fail(
            "crate failed to build library + test targets:\n" + proc.stdout[-8000:]
        )
    return True


@pytest.fixture(scope="session")
def full_test_run(built_crate):
    """
    Run the whole test suite once, single-threaded to respect the
    single-message-at-a-time / global logger-install invariants, capturing all
    stdout so we can inspect for STUB panics and per-test pass/fail lines.
    """
    proc = _run_cargo(
        ["test", "--", "--test-threads=1", "--nocapture"],
        timeout=2400,
    )
    return proc


# --------------------------------------------------------------------------- #
# Contract-level assertions.
# --------------------------------------------------------------------------- #








# --------------------------------------------------------------------------- #
# Cluster-focused robustness checks (invariants that a weak/overfit solution
# would violate even if a single frozen test happened to pass).
# --------------------------------------------------------------------------- #


def test_no_stub_panics_reachable(full_test_run):
    """
    No `STUB: not implemented` panic may fire on any exercised path.
    (Cheat surface: leaving reachable STUB panics behind untested conditions.)
    """
    out = full_test_run.stdout
    assert _STUB_MARKER not in out, (
        "A reachable STUB panic was triggered during the test run:\n"
        + out[-8000:]
    )

def test_overall_suite_passes(full_test_run):
    """
    The full suite must pass. libtest prints 'test result: ok.' per binary and a
    non-zero exit code on any failure. We assert the aggregate success.
    """
    out = full_test_run.stdout
    assert full_test_run.returncode == 0, (
        "cargo test reported failures:\n" + out[-12000:]
    )
    # Sanity: at least one test binary reported an ok result summary.
    assert "test result: ok" in out, (
        "No successful test-result summary was found in output:\n" + out[-8000:]
    )
    # No failed-line markers should be present.
    assert "test result: FAILED" not in out, (
        "A test binary reported FAILED:\n" + out[-12000:]
    )

def test_supervision_cluster_both_present_and_pass(built_crate):
    """
    Supervision restart AND escalate must both genuinely pass — an escalate
    no-op that merely lets a test finish would leave one failing. Running them
    together also exercises the tree-climbing (escalate applies the *parent's*
    strategy) invariant from TRUTH.md pitfalls.
    """
    proc = _run_cargo(
        ["test", "supervision_", "--", "--test-threads=1"],
        timeout=1200,
    )
    out = proc.stdout
    assert _STUB_MARKER not in out, out[-6000:]
    assert proc.returncode == 0, "supervision cluster failed:\n" + out[-10000:]
    # Both restart and escalate variants should appear as passing.
    assert "restart_failed_actor" in out and "escalate_failed_actor" in out, (
        "expected both restart and escalate supervision tests to run:\n"
        + out[-6000:]
    )

def test_scheduling_cluster_all_variants(built_crate):
    """
    One-shot, repeat, and at-time scheduling must each pass — TRUTH.md forbids
    delivering immediately regardless of delay/interval or cancellation.
    """
    proc = _run_cargo(
        ["test", "schedule_", "--", "--test-threads=1"],
        timeout=1200,
    )
    out = proc.stdout
    assert _STUB_MARKER not in out, out[-6000:]
    assert proc.returncode == 0, "scheduling cluster failed:\n" + out[-10000:]
    for variant in ("schedule_once", "schedule_repeat", "schedule_at_time"):
        assert variant in out, f"expected {variant} to run:\n" + out[-6000:]

def test_futures_panic_isolation(built_crate):
    """
    A panicking future must be contained by the executor (not crash the pool or
    poison shared locks). system_futures_panic AND system_futures_exec must both
    pass together, proving genuine panic isolation rather than synchronous
    caller-side execution.
    """
    proc = _run_cargo(
        ["test", "system_futures", "--", "--test-threads=1"],
        timeout=1200,
    )
    out = proc.stdout
    assert _STUB_MARKER not in out, out[-6000:]
    assert proc.returncode == 0, "futures cluster failed:\n" + out[-10000:]
    assert "system_futures_exec" in out and "system_futures_panic" in out, (
        "expected both futures exec and panic tests to run:\n" + out[-6000:]
    )
