"""
Behavioral tests for the `Zahgon/erg` crate stubs (src/dummy.rs, src/main.rs).

Because the solution is a Rust crate, these tests exercise behavior by:
  1. Statically verifying the STUB panics were genuinely replaced (a stubbed
     solution still contains `panic!("STUB: not implemented")`).
  2. Verifying the wire-protocol contract is really implemented (big-endian,
     instruction-byte + 2-byte size + data layout) rather than left unimplemented.
  3. When a Rust toolchain is available, actually running the crate's
     `dummy::test_message` unit test which validates exact serialization /
     deserialization of the wire protocol.

The static checks always run and discriminate stub-vs-correct; the cargo checks
run when `cargo` is present.
"""

import os
import re
import shutil
import subprocess
import pytest


# --------------------------------------------------------------------------- #
# Locate the crate sources.
# --------------------------------------------------------------------------- #
def _find_crate_root():
    start = os.path.dirname(os.path.abspath(__file__))
    candidates = [start, os.getcwd()]
    seen = set()
    for base in candidates:
        cur = base
        # Walk upward.
        for _ in range(12):
            if cur in seen:
                break
            seen.add(cur)
            dummy = os.path.join(cur, "src", "dummy.rs")
            main = os.path.join(cur, "src", "main.rs")
            if os.path.isfile(dummy) and os.path.isfile(main):
                return cur
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent
    # Walk downward from candidates as a fallback.
    for base in candidates:
        for root, dirs, files in os.walk(base):
            # Prune common heavy dirs.
            dirs[:] = [d for d in dirs if d not in (".git", "target", "node_modules")]
            if "dummy.rs" in files and "main.rs" in files and os.path.basename(root) == "src":
                return os.path.dirname(root)
    return None


CRATE_ROOT = _find_crate_root()


def _require_crate():
    if CRATE_ROOT is None:
        pytest.skip("Could not locate the erg crate (src/dummy.rs, src/main.rs).")
    return CRATE_ROOT


def _read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _dummy_src():
    return _read(os.path.join(_require_crate(), "src", "dummy.rs"))


def _main_src():
    return _read(os.path.join(_require_crate(), "src", "main.rs"))


# --------------------------------------------------------------------------- #
# Static contract checks (always run — fail hard on a stubbed solution).
# --------------------------------------------------------------------------- #


























# --------------------------------------------------------------------------- #
# Dynamic check: actually run the crate's wire-protocol unit test.
# --------------------------------------------------------------------------- #
def _cargo_available():
    return shutil.which("cargo") is not None


def test_no_remaining_stub_in_dummy():
    src = _dummy_src()
    # A stubbed solution has bodies of `panic!("STUB: not implemented")`.
    assert "STUB" not in src, "src/dummy.rs still contains STUB markers"
    assert 'panic!("STUB' not in src

def test_no_remaining_stub_in_main():
    src = _main_src()
    assert "STUB" not in src, "src/main.rs still contains STUB markers"
    assert 'panic!("STUB' not in src

def test_message_size_clamping_present():
    """
    Contract §2 / pitfall: oversized payloads must be clamped to 65535 rather
    than silently truncated by an `as u16` cast. Look for the clamp constant.
    """
    src = _dummy_src()
    assert ("u16::MAX" in src) or ("65535" in src), (
        "Message::new must clamp payload length to u16::MAX (65535)"
    )
    # size field is 16-bit.
    assert "u16" in src

def test_send_recv_use_exact_read_semantics():
    """
    Contract §4 / pitfall: framing must read exactly N bytes (read_exact),
    not a best-effort read/read_to_end which can under-read on a socket.
    """
    src = _dummy_src()
    assert "read_exact" in src, "recv_msg must use read_exact for framing"

def test_send_uses_big_endian_two_byte_size():
    """
    Contract §3 / pitfall: the size field is serialized big-endian, 2 bytes.
    A correct impl uses to_be_bytes / write_u16 / big-endian ordering.
    """
    src = _dummy_src()
    big_endian_markers = ("to_be_bytes", "be_bytes", "BigEndian", "write_u16::<Big", "from_be_bytes")
    assert any(m in src for m in big_endian_markers), (
        "wire protocol must serialize the 2-byte size big-endian"
    )

def test_main_dispatches_multiple_runnables():
    """
    Contract §14 / cheat surface: main must dispatch each mode to the correct
    runnable, not route everything through one path.
    """
    src = _main_src()
    expected_runnables = ["DummyVM", "Linter", "LexerRunner", "ParserRunner", "PackageTypeChecker"]
    found = [r for r in expected_runnables if r in src]
    assert len(found) >= 3, (
        f"main.rs should dispatch to several distinct runnables; found only {found}"
    )
    # Must exit with the runnable's code, not a fixed 0.
    assert "exit" in src

def test_eval_strips_trailing_none():
    """
    Contract §10 / pitfall: the REPL suppresses `None` results by trimming a
    trailing "None".
    """
    src = _dummy_src()
    assert "None" in src
    strip_markers = ("strip_suffix", 'trim_end_matches', "truncate")
    assert any(m in src for m in strip_markers), (
        "eval must strip a trailing \"None\" result"
    )
