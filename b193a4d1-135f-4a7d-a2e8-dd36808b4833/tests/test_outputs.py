# ---- pooled sound tests, attempt 0 ----
"""
Behavioral pytest suite for the restored `little-raft` Rust crate.

Since the solution is a Rust crate, these tests drive `cargo` as the real
"public API": they build the crate, run its integration test(s) (notably
`run_replicas`), and inspect the restored source for the contractual
invariants described in TRUTH.md.

A correct implementation compiles, contains no remaining STUB panics on
reachable paths, defines the complete Message enum + supporting types, and
makes the `run_replicas` convergence test pass.  A stubbed/broken solution
fails to compile, panics, or leaves STUB markers behind.
"""

import os
import re
import shutil
import subprocess
import pathlib

import pytest


# --------------------------------------------------------------------------
# Locating the crate
# --------------------------------------------------------------------------

SRC_FILE_NAMES = {
    "cluster.rs",
    "lib.rs",
    "message.rs",
    "replica.rs",
    "state_machine.rs",
    "timer.rs",
}


def _find_crate_root():
    """Return the directory containing Cargo.toml + src/ for little-raft."""
    start = pathlib.Path(__file__).resolve()
    candidates = []

    # Walk upward from this test file, then scan downward for the crate.
    search_roots = [start.parent]
    for parent in start.parents:
        search_roots.append(parent)

    seen = set()
    for root in search_roots:
        if root in seen:
            continue
        seen.add(root)
        for dirpath, dirnames, filenames in os.walk(root):
            # Skip huge/irrelevant trees to keep the search bounded.
            base = os.path.basename(dirpath)
            if base in {".git", "target", "node_modules"}:
                dirnames[:] = []
                continue
            if "Cargo.toml" in filenames:
                src_dir = os.path.join(dirpath, "src")
                if os.path.isdir(src_dir):
                    present = set(os.listdir(src_dir))
                    if {"replica.rs", "message.rs", "timer.rs"} <= present:
                        candidates.append(pathlib.Path(dirpath))
        if candidates:
            break

    if not candidates:
        return None
    # Prefer the deepest / most specific match.
    candidates.sort(key=lambda p: len(str(p)))
    return candidates[0]


CRATE_ROOT = _find_crate_root()
CARGO = shutil.which("cargo")


def _src_dir():
    assert CRATE_ROOT is not None, "little-raft crate directory not found"
    return CRATE_ROOT / "src"


def _read_src(name):
    p = _src_dir() / name
    assert p.exists(), f"expected source file missing: {name}"
    return p.read_text(encoding="utf-8", errors="replace")


def _all_src_text():
    text = []
    for name in SRC_FILE_NAMES:
        p = _src_dir() / name
        if p.exists():
            text.append(p.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(text)


def _strip_comments_and_strings(rust_text):
    """Rough removal of // line comments, /* */ block comments and string
    literals so that keyword/marker searches look only at real code."""
    # Remove block comments
    t = re.sub(r"/\*.*?\*/", " ", rust_text, flags=re.DOTALL)
    # Remove line comments
    t = re.sub(r"//[^\n]*", " ", t)
    # Remove string literals (best-effort)
    t = re.sub(r'"(?:\\.|[^"\\])*"', '""', t)
    return t


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------


@pytest.fixture(scope="session")
def crate_root():
    if CRATE_ROOT is None:
        pytest.skip("little-raft crate directory could not be located")
    return CRATE_ROOT


@pytest.fixture(scope="session")
def cargo():
    if CARGO is None:
        pytest.skip("cargo toolchain is not available in this environment")
    return CARGO


def _run_cargo(cargo_bin, crate_dir, args, timeout=1200):
    env = dict(os.environ)
    env.setdefault("CARGO_TERM_COLOR", "never")
    return subprocess.run(
        [cargo_bin, *args],
        cwd=str(crate_dir),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        text=True,
    )


# --------------------------------------------------------------------------
# Source-level contract tests (fast; no toolchain required)
# --------------------------------------------------------------------------
























# --------------------------------------------------------------------------
# Behavioral tests via the real toolchain
# --------------------------------------------------------------------------





# ---- pooled sound tests, attempt 1 ----
import os
import shutil
import subprocess

import pytest


# --------------------------------------------------------------------------
# Locate the little_raft crate sources on disk (robustly).
# --------------------------------------------------------------------------

_PRUNE = {"target", ".git", "node_modules", ".cargo", "__pycache__"}


def _candidate_bases():
    bases = []
    here = os.path.abspath(os.path.dirname(__file__))
    cwd = os.path.abspath(os.getcwd())
    for start in (here, cwd):
        p = start
        bases.append(p)
        for _ in range(8):
            parent = os.path.dirname(p)
            if parent == p:
                break
            p = parent
            bases.append(p)
    # de-dup while preserving order, prefer shortest (topmost) first
    seen = set()
    uniq = []
    for b in sorted(set(bases), key=len):
        if b not in seen:
            seen.add(b)
            uniq.append(b)
    return uniq


def _find_replica_rs():
    for base in _candidate_bases():
        if not os.path.isdir(base):
            continue
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in _PRUNE]
            if (
                os.path.basename(root) == "src"
                and "replica.rs" in files
                and "little_raft" in root.replace("\\", "/")
            ):
                return os.path.join(root, "replica.rs")
    # fallback: any src/replica.rs
    for base in _candidate_bases():
        if not os.path.isdir(base):
            continue
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in _PRUNE]
            if os.path.basename(root) == "src" and "replica.rs" in files:
                return os.path.join(root, "replica.rs")
    return None


_REPLICA_RS = _find_replica_rs()


def _require_sources():
    if _REPLICA_RS is None:
        pytest.fail("Could not locate little_raft/src/replica.rs on disk.")


def src_dir():
    _require_sources()
    return os.path.dirname(_REPLICA_RS)


def crate_dir():
    return os.path.dirname(src_dir())


def read_src(name):
    path = os.path.join(src_dir(), name)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


EXPECTED_FILES = [
    "cluster.rs",
    "lib.rs",
    "message.rs",
    "replica.rs",
    "state_machine.rs",
    "timer.rs",
]


# --------------------------------------------------------------------------
# Static / structural tests.
# These fail on an EMPTY-file stub (files present but no declarations),
# and pass on a real implementation.
# --------------------------------------------------------------------------

























# --------------------------------------------------------------------------
# The real behavioral discriminator: build + run the crate's own tests.
# On the correct implementation `cargo test` passes; on any stub that
# fails to compile or panics ("STUB: not implemented", empty enum, etc.)
# it fails. This is the ground truth for the `run_replicas` contract.
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def cargo_test_run():
    if shutil.which("cargo") is None:
        pytest.skip("cargo toolchain not available")
    crate = crate_dir()
    assert os.path.isfile(os.path.join(crate, "Cargo.toml")), (
        "expected Cargo.toml at crate root: %s" % crate
    )
    try:
        proc = subprocess.run(
            ["cargo", "test", "--no-fail-fast"],
            cwd=crate,
            capture_output=True,
            text=True,
            timeout=1200,
        )
    except subprocess.TimeoutExpired as e:
        pytest.fail("cargo test timed out (loop likely never halts): %s" % e)
    return proc


def test_replica_checks_halt(crate_root):
    """The event loop must consult halt() or the test threads never stop."""
    replica = _strip_comments_and_strings(_read_src("replica.rs"))
    assert "halt" in replica, "start() never consults halt() — loop won't terminate"

def test_replica_uses_register_leader_hook(crate_root):
    replica = _strip_comments_and_strings(_read_src("replica.rs"))
    assert "register_leader" in replica, (
        "leader-change hook register_leader is never invoked"
    )

def test_no_stub_panics_remain():
    for name in EXPECTED_FILES:
        txt = read_src(name)
        assert "STUB" not in txt, "STUB marker still present in %s" % name
        assert "not implemented" not in txt.lower(), (
            "unimplemented stub body still present in %s" % name
        )

def test_start_consults_halt():
    # start() must terminate when halt() signals; a real impl references halt.
    txt = read_src("replica.rs")
    assert "halt" in txt, "start loop must consult cluster.halt()"
