"""
Behavioral test suite for the restored `spf13/viper` Go library.

Because the "solution module" is a Go package, we exercise its REAL public API by
compiling and running Go code against it (via the `go` toolchain).  We inject a
generated in-package test file that calls the actual functions/methods and asserts
on the behavioral contract from TRUTH.md (codec registry case-insensitivity +
built-in fallback + not-found semantics, precedence, aliases, env binding,
option nil-guards, error unwrap direction, merging).

Each pytest test runs a focused Go test so a weak/stubbed implementation fails
the specific contract it violates, while a correct implementation passes all.
"""

import os
import shutil
import subprocess
import textwrap

import pytest


# --------------------------------------------------------------------------- #
# Locate the viper Go package (directory containing viper.go + encoding.go).
# --------------------------------------------------------------------------- #
def _find_pkg_dir():
    start = os.getcwd()
    for root, dirs, files in os.walk(start):
        # prune obvious noise
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "vendor/.cache")]
        if "viper.go" in files and "encoding.go" in files:
            return root
    return None


PKG_DIR = _find_pkg_dir()
GO = shutil.which("go")

GENERATED_TEST_NAME = "zz_contract_generated_test.go"

GENERATED_TEST_SRC = textwrap.dedent(
    r'''
    package viper

    import (
        "errors"
        "os"
        "strings"
        "testing"
    )

    // Codec registry: case-insensitive lookup, built-in fallbacks, not-found -> (nil, err).
    func TestContract_CodecRegistry(t *testing.T) {
        r := NewCodecRegistry()
        if r == nil {
            t.Fatal("NewCodecRegistry returned nil")
        }
        builtins := []string{"yaml", "YAML", "yml", "JSON", "json", "toml", "TOML", "dotenv", "env"}
        for _, f := range builtins {
            enc, err := r.Encoder(f)
            if err != nil || enc == nil {
                t.Fatalf("Encoder(%q) = (%v, %v); want non-nil encoder, nil error", f, enc, err)
            }
            dec, err := r.Decoder(f)
            if err != nil || dec == nil {
                t.Fatalf("Decoder(%q) = (%v, %v); want non-nil decoder, nil error", f, dec, err)
            }
        }
        // Unknown format must yield a non-nil error AND a nil codec (contract pitfall).
        if enc, err := r.Encoder("no-such-format"); err == nil || enc != nil {
            t.Fatalf("Encoder(unknown) = (%v, %v); want (nil, non-nil error)", enc, err)
        }
        if dec, err := r.Decoder("no-such-format"); err == nil || dec != nil {
            t.Fatalf("Decoder(unknown) = (%v, %v); want (nil, non-nil error)", dec, err)
        }
    }

    // Get/Set/Default precedence + case-insensitive keys.
    func TestContract_Precedence(t *testing.T) {
        v := New()
        v.SetDefault("key", "default")
        if got := v.Get("key"); got != "default" {
            t.Fatalf("default precedence: Get(key)=%v want default", got)
        }
        v.Set("key", "override")
        if got := v.Get("key"); got != "override" {
            t.Fatalf("override precedence: Get(key)=%v want override", got)
        }
        v.Set("MixedCase", "x")
        if got := v.Get("mixedcase"); got != "x" {
            t.Fatalf("case-insensitive keys: Get(mixedcase)=%v want x", got)
        }
        if got := v.Get("MIXEDCASE"); got != "x" {
            t.Fatalf("case-insensitive keys: Get(MIXEDCASE)=%v want x", got)
        }
    }

    // Aliases including a recursive cycle must resolve and terminate (no hang).
    func TestContract_Aliases(t *testing.T) {
        v := New()
        v.Set("realkey", "realvalue")
        v.RegisterAlias("aliaskey", "realkey")
        if got := v.Get("aliaskey"); got != "realvalue" {
            t.Fatalf("alias resolution: Get(aliaskey)=%v want realvalue", got)
        }
        // Recursive aliases must not loop forever.
        v.RegisterAlias("a", "b")
        v.RegisterAlias("b", "a")
        v.Set("a", "loopval")
        _ = v.Get("a")
        _ = v.Get("b")
    }

    // Environment binding with prefix.
    func TestContract_Env(t *testing.T) {
        v := New()
        v.SetEnvPrefix("spf")
        if err := v.BindEnv("id"); err != nil {
            t.Fatalf("BindEnv err: %v", err)
        }
        os.Setenv("SPF_ID", "13")
        defer os.Unsetenv("SPF_ID")
        if got := v.Get("id"); got != "13" {
            t.Fatalf("env binding: Get(id)=%v want 13", got)
        }
    }

    // Nil-guarded options must be no-ops (must NOT clobber working registries/finder).
    func TestContract_NilOptionGuards(t *testing.T) {
        v := NewWithOptions(
            WithFinder(nil),
            WithEncoderRegistry(nil),
            WithDecoderRegistry(nil),
        )
        v.SetConfigType("yaml")
        // If the codec registry had been clobbered with nil, this read would fail.
        if err := v.ReadConfig(strings.NewReader("foo: bar\nnum: 5\n")); err != nil {
            t.Fatalf("ReadConfig after nil-guarded options failed: %v", err)
        }
        if got := v.Get("foo"); got != "bar" {
            t.Fatalf("Get(foo)=%v want bar", got)
        }
        if got := v.GetInt("num"); got != 5 {
            t.Fatalf("GetInt(num)=%v want 5", got)
        }
        v.Set("x", "y")
        if got := v.Get("x"); got != "y" {
            t.Fatalf("Set/Get still broken: Get(x)=%v want y", got)
        }
    }

    // Merge semantics: unify keys, later config overrides overlapping keys.
    func TestContract_Merge(t *testing.T) {
        v := New()
        v.SetConfigType("yaml")
        if err := v.ReadConfig(strings.NewReader("a: 1\nb: 2\n")); err != nil {
            t.Fatalf("ReadConfig err: %v", err)
        }
        if err := v.MergeConfig(strings.NewReader("b: 3\nc: 4\n")); err != nil {
            t.Fatalf("MergeConfig err: %v", err)
        }
        if got := v.GetInt("a"); got != 1 {
            t.Fatalf("merge kept: GetInt(a)=%v want 1", got)
        }
        if got := v.GetInt("b"); got != 3 {
            t.Fatalf("merge override: GetInt(b)=%v want 3", got)
        }
        if got := v.GetInt("c"); got != 4 {
            t.Fatalf("merge added: GetInt(c)=%v want 4", got)
        }
    }

    // Not-found config read must produce an error that unwraps in the correct
    // direction: to FileNotFoundFromSearchError and satisfying FileLookupError.
    func TestContract_ReadInConfigNotFoundUnwrap(t *testing.T) {
        v := New()
        v.SetConfigName("definitely_not_a_real_config_zzz")
        v.AddConfigPath(t.TempDir())
        err := v.ReadInConfig()
        if err == nil {
            t.Fatal("ReadInConfig with missing file returned nil error")
        }
        var search FileNotFoundFromSearchError
        if !errors.As(err, &search) {
            t.Fatalf("error does not unwrap to FileNotFoundFromSearchError: %T %v", err, err)
        }
        var fle FileLookupError
        if !errors.As(err, &fle) {
            t.Fatalf("error does not satisfy FileLookupError: %T %v", err, err)
        }
    }
    '''
).lstrip()


# --------------------------------------------------------------------------- #
# Fixtures / helpers
# --------------------------------------------------------------------------- #
requires_go = pytest.mark.skipif(
    GO is None or PKG_DIR is None,
    reason="Go toolchain or viper package directory not found",
)


@pytest.fixture(scope="session", autouse=True)
def _inject_generated_test():
    if GO is None or PKG_DIR is None:
        yield
        return
    path = os.path.join(PKG_DIR, GENERATED_TEST_NAME)
    with open(path, "w") as fh:
        fh.write(GENERATED_TEST_SRC)
    try:
        yield
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def _run_go_test(run_pattern, timeout=180):
    proc = subprocess.run(
        [GO, "test", "-count=1", "-timeout", "90s", "-run", run_pattern, "."],
        cwd=PKG_DIR,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return proc


# --------------------------------------------------------------------------- #
# Static contract: no leftover stub placeholders.
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# Compilation.
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# Behavioral contract tests (each isolated Go test).
# --------------------------------------------------------------------------- #


@pytest.mark.skipif(PKG_DIR is None, reason="viper package directory not found")
def test_no_remaining_stub_placeholders():
    listed = [
        "encoding.go",
        "errors.go",
        "experimental.go",
        "file.go",
        "finder.go",
        "flags.go",
        "logger.go",
        "remote.go",
        os.path.join("remote", "remote.go"),
        "util.go",
        "viper.go",
    ]
    offenders = []
    for rel in listed:
        p = os.path.join(PKG_DIR, rel)
        if not os.path.isfile(p):
            continue
        with open(p, "r", errors="replace") as fh:
            if "STUB: not implemented" in fh.read():
                offenders.append(rel)
    assert not offenders, f"Files still contain stub placeholders: {offenders}"

@requires_go
def test_codec_registry_contract():
    proc = _run_go_test("TestContract_CodecRegistry")
    assert proc.returncode == 0, (
        "Codec registry contract failed (case-insensitive lookup / built-in "
        f"fallback / not-found semantics):\n{proc.stdout}\n{proc.stderr}"
    )

@requires_go
def test_precedence_and_case_insensitivity():
    proc = _run_go_test("TestContract_Precedence")
    assert proc.returncode == 0, (
        f"Get/Set/Default precedence or case-insensitivity failed:\n{proc.stdout}\n{proc.stderr}"
    )

@requires_go
def test_aliases_resolution_and_termination():
    proc = _run_go_test("TestContract_Aliases")
    assert proc.returncode == 0, (
        f"Alias resolution / recursive-alias termination failed:\n{proc.stdout}\n{proc.stderr}"
    )

@requires_go
def test_env_binding_with_prefix():
    proc = _run_go_test("TestContract_Env")
    assert proc.returncode == 0, (
        f"Environment binding with prefix failed:\n{proc.stdout}\n{proc.stderr}"
    )

@requires_go
def test_nil_option_guards_are_noops():
    proc = _run_go_test("TestContract_NilOptionGuards")
    assert proc.returncode == 0, (
        "Nil-guarded options are not no-ops (a nil registry/finder clobbered "
        f"working state):\n{proc.stdout}\n{proc.stderr}"
    )

@requires_go
def test_merge_semantics():
    proc = _run_go_test("TestContract_Merge")
    assert proc.returncode == 0, (
        f"Config merge semantics failed:\n{proc.stdout}\n{proc.stderr}"
    )

@requires_go
def test_not_found_error_unwrap_direction():
    proc = _run_go_test("TestContract_ReadInConfigNotFoundUnwrap")
    assert proc.returncode == 0, (
        "Not-found error does not unwrap to FileNotFoundFromSearchError / "
        f"FileLookupError as required:\n{proc.stdout}\n{proc.stderr}"
    )
