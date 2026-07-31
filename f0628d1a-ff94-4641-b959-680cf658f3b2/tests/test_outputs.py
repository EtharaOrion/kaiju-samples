"""
Behavioral pytest suite for the Go `uuid` package described in TRUTH.md.

Since the solution under test is a Go package (not a Python module), each test
compiles and runs REAL Go code that imports the actual solution package and
asserts on concrete outputs / invariants from the behavioral contract.

We inject a temporary `*_test.go` file (package `uuid`) into the solution
directory and drive it with `go test -run ...`. Tests assert the CONTRACT
(round-trips, version/variant bits, error propagation, monotonicity,
NullUUID null semantics, well-known V3/V5 vectors) rather than brittle
implementation details.
"""

import os
import shutil
import subprocess
import uuid as _pyuuid

import pytest


# --------------------------------------------------------------------------- #
# Locate the Go solution package (directory containing `package uuid` uuid.go) #
# --------------------------------------------------------------------------- #
def _find_pkg_dir():
    candidates = []
    env = os.environ.get("SOLUTION_DIR")
    if env:
        candidates.append(env)
    candidates.append(os.getcwd())
    candidates.append(os.path.dirname(os.path.abspath(__file__)))

    seen = set()
    for root in candidates:
        if not root or not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            # prune vendor/.git for speed
            dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules")]
            if "uuid.go" in filenames and "version7.go" in filenames:
                try:
                    with open(os.path.join(dirpath, "uuid.go"), "r", errors="ignore") as fh:
                        head = fh.read(4096)
                except OSError:
                    continue
                if "package uuid" in head:
                    if dirpath not in seen:
                        seen.add(dirpath)
                        return dirpath
    return None


PKG_DIR = _find_pkg_dir()
GO_BIN = shutil.which("go")


GO_TEST_SOURCE = r'''
package uuid

import (
	"bytes"
	"encoding/json"
	"testing"
)

func zzVersion(u UUID) byte  { return u[6] >> 4 }
func zzVariantOK(u UUID) bool { return (u[8] >> 6) == 0x2 } // top two bits == 10

// ---- Parsing / formatting -------------------------------------------------
func TestZZParseForms(t *testing.T) {
	canonical := "f47ac10b-58cc-4372-8567-0e02b2c3d479"
	base, err := Parse(canonical)
	if err != nil {
		t.Fatalf("Parse canonical failed: %v", err)
	}
	if got := base.String(); got != canonical {
		t.Fatalf("String() = %q want %q", got, canonical)
	}
	unhyphen := "f47ac10b58cc43728567" + "0e02b2c3d479"
	forms := []string{
		canonical,
		"{" + canonical + "}",
		"urn:uuid:" + canonical,
		unhyphen,
	}
	for _, f := range forms {
		u, err := Parse(f)
		if err != nil {
			t.Fatalf("Parse(%q) unexpected error: %v", f, err)
		}
		if u != base {
			t.Fatalf("Parse(%q) = %v, want %v", f, u, base)
		}
		// ParseBytes must agree with Parse.
		ub, err := ParseBytes([]byte(f))
		if err != nil {
			t.Fatalf("ParseBytes(%q) unexpected error: %v", f, err)
		}
		if ub != base {
			t.Fatalf("ParseBytes(%q) = %v, want %v", f, ub, base)
		}
	}
	// URN helper.
	if base.URN() != "urn:uuid:"+canonical {
		t.Fatalf("URN() = %q", base.URN())
	}
}

func TestZZParseInvalid(t *testing.T) {
	bad := []string{
		"", "not-a-uuid", "12345",
		"f47ac10b-58cc-4372-8567-0e02b2c3d47", // one short
		"g47ac10b-58cc-4372-8567-0e02b2c3d479", // bad hex
	}
	for _, s := range bad {
		u, err := Parse(s)
		if err == nil {
			t.Fatalf("Parse(%q) expected error, got %v", s, u)
		}
		if u != Nil {
			t.Fatalf("Parse(%q) should return Nil on error, got %v", s, u)
		}
	}
	// Validate mirrors Parse acceptance.
	if err := Validate("f47ac10b-58cc-4372-8567-0e02b2c3d479"); err != nil {
		t.Fatalf("Validate valid returned error: %v", err)
	}
	if err := Validate("nope"); err == nil {
		t.Fatalf("Validate invalid returned nil")
	}
}

func TestZZFromBytes(t *testing.T) {
	b := make([]byte, 16)
	for i := range b {
		b[i] = byte(i)
	}
	u, err := FromBytes(b)
	if err != nil {
		t.Fatalf("FromBytes 16: %v", err)
	}
	for i := range b {
		if u[i] != b[i] {
			t.Fatalf("FromBytes mismatch at %d", i)
		}
	}
	if _, err := FromBytes(b[:15]); err == nil {
		t.Fatalf("FromBytes(15) expected error")
	}
	if _, err := FromBytes(nil); err == nil {
		t.Fatalf("FromBytes(nil) expected error")
	}
}

// ---- Random V4 + rand source ---------------------------------------------
func TestZZRandomV4(t *testing.T) {
	u, err := NewRandom()
	if err != nil {
		t.Fatalf("NewRandom: %v", err)
	}
	if zzVersion(u) != 4 {
		t.Fatalf("V4 version nibble = %d", zzVersion(u))
	}
	if !zzVariantOK(u) {
		t.Fatalf("V4 variant bits wrong: byte8=%#x", u[8])
	}
	// New must not return Nil for a working source.
	if New() == Nil {
		t.Fatalf("New() returned Nil")
	}
}

func TestZZSetRandDeterministic(t *testing.T) {
	seed := bytes.Repeat([]byte{0xAB}, 4096)
	SetRand(bytes.NewReader(seed))
	a, err := NewRandom()
	if err != nil {
		t.Fatalf("NewRandom a: %v", err)
	}
	SetRand(bytes.NewReader(seed))
	b, err := NewRandom()
	if err != nil {
		t.Fatalf("NewRandom b: %v", err)
	}
	if a != b {
		t.Fatalf("SetRand not deterministic: %v vs %v", a, b)
	}
	// version/variant still enforced even with fixed source
	if zzVersion(a) != 4 || !zzVariantOK(a) {
		t.Fatalf("deterministic V4 wrong bits: %v", a)
	}
	// Restore default; must not panic / must produce valid uuid.
	SetRand(nil)
	if _, err := NewRandom(); err != nil {
		t.Fatalf("NewRandom after SetRand(nil): %v", err)
	}
}

func TestZZRandPool(t *testing.T) {
	EnableRandPool()
	defer DisableRandPool()
	seen := map[UUID]bool{}
	for i := 0; i < 50; i++ {
		u, err := NewRandom()
		if err != nil {
			t.Fatalf("pooled NewRandom: %v", err)
		}
		if zzVersion(u) != 4 || !zzVariantOK(u) {
			t.Fatalf("pooled V4 wrong bits: %v", u)
		}
		if seen[u] {
			t.Fatalf("pooled produced duplicate: %v", u)
		}
		seen[u] = true
	}
}

// ---- Version 1 time-based -------------------------------------------------
func TestZZVersion1(t *testing.T) {
	u, err := NewUUID()
	if err != nil {
		t.Fatalf("NewUUID: %v", err)
	}
	if zzVersion(u) != 1 {
		t.Fatalf("V1 version nibble = %d", zzVersion(u))
	}
	if !zzVariantOK(u) {
		t.Fatalf("V1 variant bits wrong: byte8=%#x", u[8])
	}
	node := u.NodeID()
	if len(node) != 6 {
		t.Fatalf("NodeID len = %d", len(node))
	}
	allZero := true
	for _, x := range node {
		if x != 0 {
			allZero = false
		}
	}
	if allZero {
		t.Fatalf("V1 node id is all zero")
	}
}

// ---- DCE / V2 -------------------------------------------------------------
func TestZZDCE(t *testing.T) {
	u, err := NewDCEPerson()
	if err != nil {
		t.Fatalf("NewDCEPerson: %v", err)
	}
	if zzVersion(u) != 2 {
		t.Fatalf("DCE version nibble = %d", zzVersion(u))
	}
	if !zzVariantOK(u) {
		t.Fatalf("DCE variant bits wrong")
	}
}

// ---- Hash V3/V5 well-known vectors ---------------------------------------
func TestZZHashVectors(t *testing.T) {
	// RFC / widely published vectors for name "python.org" in DNS namespace.
	md5 := NewMD5(NameSpaceDNS, []byte("python.org"))
	if got := md5.String(); got != "6fa459ea-ee8a-3ca4-894e-db77e160355e" {
		t.Fatalf("NewMD5 DNS python.org = %q", got)
	}
	if zzVersion(md5) != 3 || !zzVariantOK(md5) {
		t.Fatalf("MD5 wrong version/variant: %v", md5)
	}
	sha1 := NewSHA1(NameSpaceDNS, []byte("python.org"))
	if got := sha1.String(); got != "886313e1-3b8a-5372-9b90-0c9aee199e5d" {
		t.Fatalf("NewSHA1 DNS python.org = %q", got)
	}
	if zzVersion(sha1) != 5 || !zzVariantOK(sha1) {
		t.Fatalf("SHA1 wrong version/variant: %v", sha1)
	}
	// Different input -> different output (derived from data).
	other := NewMD5(NameSpaceDNS, []byte("example.com"))
	if other == md5 {
		t.Fatalf("MD5 ignored input data")
	}
}

// ---- Version 6 ------------------------------------------------------------
func TestZZVersion6(t *testing.T) {
	u, err := NewV6()
	if err != nil {
		t.Fatalf("NewV6: %v", err)
	}
	if zzVersion(u) != 6 {
		t.Fatalf("V6 version nibble = %d", zzVersion(u))
	}
	if !zzVariantOK(u) {
		t.Fatalf("V6 variant bits wrong")
	}
}

// ---- Version 7 monotonicity ----------------------------------------------
func TestZZVersion7Monotonic(t *testing.T) {
	prev, err := NewV7()
	if err != nil {
		t.Fatalf("NewV7: %v", err)
	}
	if zzVersion(prev) != 7 {
		t.Fatalf("V7 version nibble = %d", zzVersion(prev))
	}
	if !zzVariantOK(prev) {
		t.Fatalf("V7 variant bits wrong")
	}
	for i := 0; i < 2000; i++ {
		cur, err := NewV7()
		if err != nil {
			t.Fatalf("NewV7 iter %d: %v", i, err)
		}
		if bytes.Compare(cur[:], prev[:]) <= 0 {
			t.Fatalf("V7 not strictly increasing at %d: %v <= %v", i, cur, prev)
		}
		if zzVersion(cur) != 7 || !zzVariantOK(cur) {
			t.Fatalf("V7 wrong bits at %d: %v", i, cur)
		}
		prev = cur
	}
}

// ---- Marshal / binary / json ---------------------------------------------
func TestZZMarshal(t *testing.T) {
	canonical := "f47ac10b-58cc-4372-8567-0e02b2c3d479"
	u := MustParse(canonical)

	txt, err := u.MarshalText()
	if err != nil {
		t.Fatalf("MarshalText: %v", err)
	}
	if string(txt) != canonical {
		t.Fatalf("MarshalText = %q", txt)
	}

	bin, err := u.MarshalBinary()
	if err != nil {
		t.Fatalf("MarshalBinary: %v", err)
	}
	if len(bin) != 16 || !bytes.Equal(bin, u[:]) {
		t.Fatalf("MarshalBinary wrong: %v", bin)
	}

	var back UUID
	if err := back.UnmarshalBinary(bin); err != nil {
		t.Fatalf("UnmarshalBinary: %v", err)
	}
	if back != u {
		t.Fatalf("binary round trip mismatch")
	}
	// Reject non-16 length.
	if err := back.UnmarshalBinary(bin[:15]); err == nil {
		t.Fatalf("UnmarshalBinary(15) expected error")
	}
	// UnmarshalText propagates parse error.
	if err := back.UnmarshalText([]byte("garbage")); err == nil {
		t.Fatalf("UnmarshalText bad expected error")
	}

	j, err := json.Marshal(u)
	if err != nil {
		t.Fatalf("json.Marshal: %v", err)
	}
	if string(j) != "\""+canonical+"\"" {
		t.Fatalf("json = %s", j)
	}
	var ju UUID
	if err := json.Unmarshal(j, &ju); err != nil {
		t.Fatalf("json.Unmarshal: %v", err)
	}
	if ju != u {
		t.Fatalf("json round trip mismatch")
	}
}

// ---- SQL Scan / Value -----------------------------------------------------
func TestZZScanValue(t *testing.T) {
	canonical := "f47ac10b-58cc-4372-8567-0e02b2c3d479"
	u := MustParse(canonical)

	v, err := u.Value()
	if err != nil {
		t.Fatalf("Value: %v", err)
	}
	if s, ok := v.(string); !ok || s != canonical {
		t.Fatalf("Value = %v", v)
	}

	var s1 UUID
	if err := s1.Scan(canonical); err != nil {
		t.Fatalf("Scan(string): %v", err)
	}
	if s1 != u {
		t.Fatalf("Scan(string) mismatch")
	}

	var s2 UUID
	if err := s2.Scan(u[:]); err != nil {
		t.Fatalf("Scan([]byte 16): %v", err)
	}
	if s2 != u {
		t.Fatalf("Scan([]byte 16) mismatch")
	}

	var s3 UUID
	if err := s3.Scan(nil); err != nil {
		t.Fatalf("Scan(nil): %v", err)
	}
	if s3 != Nil {
		t.Fatalf("Scan(nil) should leave Nil")
	}

	var s4 UUID
	if err := s4.Scan(12345); err == nil {
		t.Fatalf("Scan(int) expected error")
	}
}

// ---- NullUUID null semantics ---------------------------------------------
func TestZZNullUUID(t *testing.T) {
	// invalid -> null everywhere
	var n NullUUID
	j, err := json.Marshal(n)
	if err != nil {
		t.Fatalf("null json marshal: %v", err)
	}
	if string(j) != "null" {
		t.Fatalf("null json = %s", j)
	}
	v, err := n.Value()
	if err != nil {
		t.Fatalf("null Value: %v", err)
	}
	if v != nil {
		t.Fatalf("null Value = %v want nil", v)
	}
	bin, err := n.MarshalBinary()
	if err != nil {
		t.Fatalf("null MarshalBinary: %v", err)
	}
	if len(bin) != 0 {
		t.Fatalf("null MarshalBinary len = %d want 0", len(bin))
	}
	txt, err := n.MarshalText()
	if err != nil {
		t.Fatalf("null MarshalText: %v", err)
	}
	if string(txt) != "null" {
		t.Fatalf("null MarshalText = %q", txt)
	}

	// Unmarshal null -> Valid=false
	var back NullUUID
	back.Valid = true
	if err := json.Unmarshal([]byte("null"), &back); err != nil {
		t.Fatalf("unmarshal null: %v", err)
	}
	if back.Valid {
		t.Fatalf("unmarshal null should set Valid=false")
	}

	// Valid delegates to inner UUID
	canonical := "f47ac10b-58cc-4372-8567-0e02b2c3d479"
	valid := NullUUID{UUID: MustParse(canonical), Valid: true}
	vj, err := json.Marshal(valid)
	if err != nil {
		t.Fatalf("valid json: %v", err)
	}
	if string(vj) != "\""+canonical+"\"" {
		t.Fatalf("valid json = %s", vj)
	}
	vv, err := valid.Value()
	if err != nil {
		t.Fatalf("valid Value: %v", err)
	}
	if s, ok := vv.(string); !ok || s != canonical {
		t.Fatalf("valid Value = %v", vv)
	}

	var scanned NullUUID
	if err := scanned.Scan(canonical); err != nil {
		t.Fatalf("NullUUID Scan string: %v", err)
	}
	if !scanned.Valid || scanned.UUID != MustParse(canonical) {
		t.Fatalf("NullUUID Scan should set Valid + value")
	}
	var scannedNil NullUUID
	if err := scannedNil.Scan(nil); err != nil {
		t.Fatalf("NullUUID Scan nil: %v", err)
	}
	if scannedNil.Valid {
		t.Fatalf("NullUUID Scan(nil) should be invalid")
	}
}

// ---- Fuzz-style safety: no panic, error on bad input ----------------------
func TestZZParseNoPanic(t *testing.T) {
	inputs := []string{"", "x", "{}", "urn:uuid:", "----", "0000",
		"f47ac10b-58cc-4372-8567-0e02b2c3d479-extra"}
	for _, s := range inputs {
		func() {
			defer func() {
				if r := recover(); r != nil {
					t.Fatalf("Parse(%q) panicked: %v", s, r)
				}
			}()
			if _, err := Parse(s); err == nil {
				t.Fatalf("Parse(%q) expected error", s)
			}
			if _, err := ParseBytes([]byte(s)); err == nil {
				t.Fatalf("ParseBytes(%q) expected error", s)
			}
		}()
	}
}
'''


requires_go = pytest.mark.skipif(
    GO_BIN is None or PKG_DIR is None,
    reason="Go toolchain or uuid package directory not found",
)


@pytest.fixture(scope="module")
def go_test_file():
    assert PKG_DIR is not None
    fname = "zz_contract_pytest_test.go"
    path = os.path.join(PKG_DIR, fname)
    with open(path, "w") as fh:
        fh.write(GO_TEST_SOURCE)
    try:
        yield path
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def _run_go(regex):
    proc = subprocess.run(
        [GO_BIN, "test", "-run", regex, "-count=1"],
        cwd=PKG_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=600,
    )
    return proc.returncode, proc.stdout.decode(errors="replace")


def _assert_go(regex):
    rc, out = _run_go(regex)
    assert rc == 0, f"go test -run {regex} failed:\n{out}"


# --------------------------------------------------------------------------- #
# Each pytest test drives one Go contract test against the real solution code #
# --------------------------------------------------------------------------- #


@requires_go
def test_parse_forms(go_test_file):
    _assert_go("TestZZParseForms")

@requires_go
def test_parse_invalid(go_test_file):
    _assert_go("TestZZParseInvalid")

@requires_go
def test_from_bytes(go_test_file):
    _assert_go("TestZZFromBytes")

@requires_go
def test_random_v4(go_test_file):
    _assert_go("TestZZRandomV4")

@requires_go
def test_setrand_deterministic(go_test_file):
    _assert_go("TestZZSetRandDeterministic")

@requires_go
def test_rand_pool(go_test_file):
    _assert_go("TestZZRandPool")

@requires_go
def test_version1(go_test_file):
    _assert_go("TestZZVersion1")

@requires_go
def test_dce(go_test_file):
    _assert_go("TestZZDCE")

@requires_go
def test_hash_vectors(go_test_file):
    _assert_go("TestZZHashVectors")

@requires_go
def test_version6(go_test_file):
    _assert_go("TestZZVersion6")

@requires_go
def test_version7_monotonic(go_test_file):
    _assert_go("TestZZVersion7Monotonic")

@requires_go
def test_marshal(go_test_file):
    _assert_go("TestZZMarshal")

@requires_go
def test_scan_value(go_test_file):
    _assert_go("TestZZScanValue")

@requires_go
def test_null_uuid(go_test_file):
    _assert_go("TestZZNullUUID")

@requires_go
def test_parse_no_panic(go_test_file):
    _assert_go("TestZZParseNoPanic")
