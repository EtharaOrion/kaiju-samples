"""
Pytest contract-verification for the `etherparse` crate reimplementation.

These tests READ the repository source files (they never compile or import the
Rust code) and assert that the behavioral contract from TRUTH.md is actually
implemented rather than left as a stub.

They are designed to PASS on a correct implementation and FAIL on the stubbed
source tree (whose placeholders look like 'STUB: not implemented',
'throw new Error("STUB")', or '__builtin_trap').
"""

import re
from pathlib import Path

import pytest

REPO = Path.cwd()
SRC = REPO / "etherparse" / "src"

STUB_MARKERS = [
    "STUB: not implemented",
    'throw new Error("STUB")',
    "__builtin_trap",
]


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def read(rel):
    p = REPO / rel
    assert p.is_file(), f"expected file to exist: {rel}"
    return p.read_text(encoding="utf-8", errors="replace")


def extract_fn_body(src, name):
    """Return the {...} body text of `fn name`, or None if not found."""
    for m in re.finditer(r"\bfn\s+" + re.escape(name) + r"\b", src):
        brace = src.find("{", m.end())
        if brace == -1:
            continue
        semi = src.find(";", m.end())
        if semi != -1 and semi < brace:
            # a declaration without a body (e.g. a trait signature)
            continue
        depth = 0
        i = brace
        while i < len(src):
            c = src[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return src[brace : i + 1]
            i += 1
    return None


def assert_fn_real(src, name, rel):
    body = extract_fn_body(src, name)
    assert body is not None, f"could not locate `fn {name}` in {rel}"
    for mk in STUB_MARKERS:
        assert mk not in body, f"`fn {name}` in {rel} still contains stub marker {mk!r}"
    # a real body has more than an empty/near-empty placeholder
    inner = body.strip().strip("{}").strip()
    assert len(inner) > 2, f"`fn {name}` in {rel} appears to have an empty body"


def all_rust_files():
    return sorted(SRC.rglob("*.rs"))


# --------------------------------------------------------------------------- #
# whole-tree: no stub markers remain
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# checksum module
# --------------------------------------------------------------------------- #
















# --------------------------------------------------------------------------- #
# bounded newtypes: range constants must be (1<<n)-1 not 1<<n
# --------------------------------------------------------------------------- #
def _find_file(basename):
    matches = list(SRC.rglob(basename))
    assert matches, f"expected source file {basename} to exist"
    return matches[0]










# --------------------------------------------------------------------------- #
# defrag: range algebra
# --------------------------------------------------------------------------- #






# --------------------------------------------------------------------------- #
# error hierarchy: Display + std-gated source correctness
# --------------------------------------------------------------------------- #










# --------------------------------------------------------------------------- #
# std-gated source(): leaf None vs wrapper nested cause
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# header read/write/round-trip: ethernet2
# --------------------------------------------------------------------------- #




# --------------------------------------------------------------------------- #
# sliced/lax packet parsing: distinct strict vs lax parsing
# --------------------------------------------------------------------------- #




# --------------------------------------------------------------------------- #
# project files: version bump + big-endian CI + Cross.toml passthrough
# --------------------------------------------------------------------------- #








# --------------------------------------------------------------------------- #
# lib.rs wiring / no_std gating
# --------------------------------------------------------------------------- #


def test_no_stub_markers_remain_in_source_tree():
    assert SRC.is_dir(), "etherparse/src directory must exist"
    offenders = []
    for f in all_rust_files():
        text = f.read_text(encoding="utf-8", errors="replace")
        for mk in STUB_MARKERS:
            if mk in text:
                offenders.append((f.relative_to(REPO), mk))
    assert not offenders, f"stub markers still present: {offenders[:20]}"

def test_checksum_add_slice_is_real():
    src = read("etherparse/src/checksum.rs")
    assert_fn_real(src, "add_slice", "etherparse/src/checksum.rs")

def test_checksum_carry_folding_present():
    src = read("etherparse/src/checksum.rs")
    # carry folding: high bits shifted (>> 16) and added back
    assert ">> 16" in src or ">>16" in src, (
        "checksum must fold carries from the high 16 bits back into the low 16"
    )

def test_ip_frag_range_merge_is_real():
    f = _find_file("ip_frag_range.rs")
    src = f.read_text(encoding="utf-8", errors="replace")
    assert_fn_real(src, "merge", str(f.relative_to(REPO)))
    # merge operates over the [start,end) bounds
    assert "start" in src and "end" in src

def test_layer_has_display():
    src = read("etherparse/src/err/layer.rs")
    assert "Layer" in src
    assert "Display" in src and "write!" in src, "Layer must implement Display"

def test_value_too_big_error_display_uses_fields():
    src = read("etherparse/src/err/value_too_big_error.rs")
    assert "Display" in src and "write!" in src, (
        "ValueTooBigError must implement Display via write! over its fields"
    )
    # message derived from actual field values, not a constant literal only
    assert re.search(r"\{[^}]*\}", src), "Display should format field values"

def test_from_slice_error_from_conversion_is_real():
    # From conversions between related error types
    src = read("etherparse/src/err/from_slice_error.rs")
    assert "From" in src, "from_slice_error must provide From conversions"
    # ensure at least one From impl body is real
    found_real = False
    for m in re.finditer(r"\bfn\s+from\b", src):
        body = extract_fn_body(src, "from")
        if body:
            found_real = True
            for mk in STUB_MARKERS:
                assert mk not in body
            break
    assert found_real, "from_slice_error must have a real `from` implementation"

def test_arp_eth_ipv4_from_error_present():
    f = _find_file("arp_eth_ipv4_from_error.rs")
    src = f.read_text(encoding="utf-8", errors="replace")
    assert "From" in src or "Error" in src
    for mk in STUB_MARKERS:
        assert mk not in src

def test_ethernet2_header_len_returns_constant_14():
    src = read("etherparse/src/link/ethernet2_header.rs")
    body = extract_fn_body(src, "header_len")
    assert body is not None
    # ethernet II header is 14 bytes
    assert "14" in body, "Ethernet2 header_len must be 14"

def test_sliced_packet_parse_entrypoints_real():
    src = read("etherparse/src/sliced_packet.rs")
    rel = "etherparse/src/sliced_packet.rs"
    real_any = False
    for name in ("from_ethernet", "from_ether_type", "from_ip"):
        body = extract_fn_body(src, name)
        if body:
            for mk in STUB_MARKERS:
                assert mk not in body
            real_any = True
    assert real_any, f"{rel} must implement strict parse entrypoints"

def test_lax_sliced_packet_exists_and_is_real():
    src = read("etherparse/src/lax_sliced_packet.rs")
    for mk in STUB_MARKERS:
        assert mk not in src
    assert "from_ethernet" in src or "from_ether_type" in src or "from_ip" in src, (
        "lax sliced packet must provide lax parse entrypoints"
    )

def test_crate_cargo_version_bumped():
    src = read("etherparse/Cargo.toml")
    assert re.search(r'version\s*=\s*"0\.20\.3"', src), (
        "etherparse/Cargo.toml version must be bumped to 0.20.3"
    )

def test_readme_version_bumped():
    src = read("README.md")
    assert "0.20.3" in src, "README.md must reference version 0.20.3"

def test_ci_has_big_endian_target():
    src = read(".github/workflows/main.yml")
    assert "powerpc64" in src, (
        "CI workflow must add a big-endian (powerpc64) test target"
    )

def test_cross_toml_proptest_cases_passthrough():
    src = read("Cross.toml")
    assert "PROPTEST_CASES" in src, (
        "Cross.toml must pass PROPTEST_CASES through to the cross environment"
    )
