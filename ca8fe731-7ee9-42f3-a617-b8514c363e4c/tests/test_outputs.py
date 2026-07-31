"""
Behavioral test suite for the Shivansh9411/goleak stub-completion task.

Because the solution under test is Go source (leaks.go, options.go, testmain.go),
these pytest tests drive the *real* implementation by generating a Go test file
that imports/exercises the package's public and package-level API, running it via
`go test`, and asserting on per-test PASS/FAIL results.

Each pytest test maps to one generated Go test that encodes a specific clause of
the behavioral contract from TRUTH.md.  A correct implementation makes them PASS;
a stub / broken implementation (e.g. Find always returning nil, cleanup leaking
into Find, missing built-in filters, wrong error strings, no exit-code rewrite)
makes the corresponding test FAIL.
"""

import os
import re
import shutil
import subprocess

import pytest


GO_TEST_SOURCE = r'''
package goleak

import (
	"bytes"
	"fmt"
	"strings"
	"testing"
	"time"
)

type truthFakeT struct {
	errors []string
	helper bool
}

func (f *truthFakeT) Error(args ...interface{}) {
	f.errors = append(f.errors, fmt.Sprint(args...))
}

func (f *truthFakeT) Helper() { f.helper = true }

type truthFakeM struct{ code int }

func (m truthFakeM) Run() int { return m.code }

// truthLeak spawns a goroutine that blocks until the returned channel is closed.
// Its top function is an anonymous closure blocked on "chan receive", so it must
// NOT be swallowed by any built-in framework filter.
func truthLeak() chan struct{} {
	done := make(chan struct{})
	started := make(chan struct{})
	go func() {
		close(started)
		<-done
	}()
	<-started
	return done
}

func TestTruthFindRejectsCleanup(t *testing.T) {
	err := Find(Cleanup(func(exitCode int) {}))
	if err == nil {
		t.Fatal("Find must reject a Cleanup option with an error")
	}
	if !strings.Contains(err.Error(), "Cleanup can only be passed to VerifyNone or VerifyTestMain") {
		t.Fatalf("wrong Cleanup rejection message: %q", err.Error())
	}
}

func TestTruthFindRejectsRunOnFailure(t *testing.T) {
	err := Find(RunOnFailure())
	if err == nil {
		t.Fatal("Find must reject a RunOnFailure option with an error")
	}
	if !strings.Contains(err.Error(), "RunOnFailure can only be passed to VerifyTestMain") {
		t.Fatalf("wrong RunOnFailure rejection message: %q", err.Error())
	}
}

func TestTruthFindCleanReturnsNil(t *testing.T) {
	if err := Find(); err != nil {
		t.Fatalf("Find on a clean goroutine set must return nil, got: %v", err)
	}
}

func TestTruthFindDetectsLeak(t *testing.T) {
	done := truthLeak()
	err := Find(maxSleep(time.Millisecond))
	close(done)
	if err == nil {
		t.Fatal("Find must return a non-nil error when a goroutine leaks")
	}
	if !strings.HasPrefix(err.Error(), "found unexpected goroutines:") {
		t.Fatalf("leak error must start with the required prefix, got: %q", err.Error())
	}
}

func TestTruthRetryBoundary(t *testing.T) {
	o := buildOpts(maxSleep(time.Microsecond))
	if !o.retry(0) {
		t.Fatal("retry(0) must return true (attempts remain)")
	}
	if o.retry(1 << 30) {
		t.Fatal("retry(i) must return false once i >= maxRetries")
	}
}

func TestTruthVerifyNoneClean(t *testing.T) {
	ft := &truthFakeT{}
	cleanupCode := -999
	VerifyNone(ft, Cleanup(func(exitCode int) { cleanupCode = exitCode }))
	if len(ft.errors) != 0 {
		t.Fatalf("VerifyNone reported errors on a clean run: %v", ft.errors)
	}
	if !ft.helper {
		t.Fatal("VerifyNone must call Helper() when available")
	}
	if cleanupCode != 0 {
		t.Fatalf("cleanup must be invoked with exit code 0, got %d", cleanupCode)
	}
}

func TestTruthVerifyNoneLeak(t *testing.T) {
	done := truthLeak()
	ft := &truthFakeT{}
	VerifyNone(ft, maxSleep(time.Millisecond))
	close(done)
	if len(ft.errors) == 0 {
		t.Fatal("VerifyNone must call t.Error when a goroutine leaks")
	}
}

func TestTruthVerifyTestMainCleanPass(t *testing.T) {
	origExit := _osExit
	origStderr := _osStderr
	defer func() { _osExit = origExit; _osStderr = origStderr }()

	exitCode := -999
	_osExit = func(c int) { exitCode = c }
	var buf bytes.Buffer
	_osStderr = &buf

	VerifyTestMain(truthFakeM{code: 0})

	if exitCode != 0 {
		t.Fatalf("clean passing run must exit 0, got %d", exitCode)
	}
	if buf.Len() != 0 {
		t.Fatalf("clean run must not write to stderr, got: %q", buf.String())
	}
}

func TestTruthVerifyTestMainLeakRewritesExit(t *testing.T) {
	origExit := _osExit
	origStderr := _osStderr
	defer func() { _osExit = origExit; _osStderr = origStderr }()

	exitCode := 0
	_osExit = func(c int) { exitCode = c }
	var buf bytes.Buffer
	_osStderr = &buf

	done := truthLeak()
	VerifyTestMain(truthFakeM{code: 0}, maxSleep(time.Millisecond))
	close(done)

	if exitCode != 1 {
		t.Fatalf("passing run with a leak must rewrite exit code to 1, got %d", exitCode)
	}
	if !strings.Contains(buf.String(), "Errors on successful test run") {
		t.Fatalf("must use successful-run wording on stderr, got: %q", buf.String())
	}
}

func TestTruthVerifyTestMainFailedNoCheck(t *testing.T) {
	origExit := _osExit
	origStderr := _osStderr
	defer func() { _osExit = origExit; _osStderr = origStderr }()

	exitCode := -999
	_osExit = func(c int) { exitCode = c }
	var buf bytes.Buffer
	_osStderr = &buf

	// A leaked goroutine is present, but the suite already failed and
	// RunOnFailure is not set, so no leak check must run and the exit code
	// must be preserved.
	done := truthLeak()
	VerifyTestMain(truthFakeM{code: 3}, maxSleep(time.Millisecond))
	close(done)

	if exitCode != 3 {
		t.Fatalf("failed run without RunOnFailure must preserve exit code 3, got %d", exitCode)
	}
	if strings.Contains(buf.String(), "unexpected goroutines") || buf.Len() != 0 {
		t.Fatalf("no leak check should run for a failed run without RunOnFailure, stderr: %q", buf.String())
	}
}
'''


GO_TEST_FILENAME = "zz_truth_generated_test.go"
_CACHE = {}


def _find_pkg_dir():
    here = os.path.dirname(os.path.abspath(__file__))
    roots = {here, os.getcwd()}
    p = here
    for _ in range(8):
        p = os.path.dirname(p)
        if not p or p == os.path.dirname(p):
            break
        roots.add(p)
    seen = set()
    for root in list(roots):
        if not root or not os.path.isdir(root):
            continue
        for dirpath, dirs, files in os.walk(root):
            # prune noisy directories
            dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "vendor")]
            key = os.path.realpath(dirpath)
            if key in seen:
                continue
            seen.add(key)
            if (
                "leaks.go" in files
                and "options.go" in files
                and "testmain.go" in files
            ):
                return dirpath
    return None


def _run_go_tests():
    if _CACHE:
        return _CACHE["result"]

    go_bin = shutil.which("go")
    pkg_dir = _find_pkg_dir()

    if go_bin is None or pkg_dir is None:
        _CACHE["result"] = {"available": False, "results": {}, "output": ""}
        return _CACHE["result"]

    test_path = os.path.join(pkg_dir, GO_TEST_FILENAME)
    env = dict(os.environ)
    env.setdefault("GO111MODULE", "on")
    env.setdefault("GOPROXY", "off")
    env.setdefault("GOFLAGS", "-mod=mod")

    output = ""
    results = {}
    try:
        with open(test_path, "w") as fh:
            fh.write(GO_TEST_SOURCE)
        proc = subprocess.run(
            [go_bin, "test", "-count=1", "-run", "^TestTruth", "-v", "."],
            cwd=pkg_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=300,
        )
        output = proc.stdout.decode("utf-8", "replace")
        for m in re.finditer(r"--- (PASS|FAIL|SKIP): (TestTruth\w+)", output):
            results[m.group(2)] = m.group(1)
    except Exception as exc:  # pragma: no cover - environment issue
        output += "\nEXCEPTION: %r" % (exc,)
    finally:
        try:
            os.remove(test_path)
        except OSError:
            pass

    _CACHE["result"] = {"available": True, "results": results, "output": output}
    return _CACHE["result"]


def _assert_go_pass(name):
    data = _run_go_tests()
    if not data["available"]:
        pytest.skip("Go toolchain or goleak package directory not available")
    results = data["results"]
    status = results.get(name)
    if status is None:
        pytest.fail(
            "Go test %s did not run (likely a build/compile failure in the "
            "solution). go test output:\n%s" % (name, data["output"])
        )
    assert status == "PASS", (
        "Go test %s reported %s.\nFull go test output:\n%s"
        % (name, status, data["output"])
    )


def test_find_rejects_cleanup_option():
    _assert_go_pass("TestTruthFindRejectsCleanup")

def test_find_rejects_run_on_failure_option():
    _assert_go_pass("TestTruthFindRejectsRunOnFailure")

def test_find_detects_leak_with_prefix():
    _assert_go_pass("TestTruthFindDetectsLeak")

def test_retry_boundary_behavior():
    _assert_go_pass("TestTruthRetryBoundary")

def test_verify_none_clean_runs_cleanup_and_helper():
    _assert_go_pass("TestTruthVerifyNoneClean")

def test_verify_none_reports_leak():
    _assert_go_pass("TestTruthVerifyNoneLeak")

def test_verify_test_main_clean_pass():
    _assert_go_pass("TestTruthVerifyTestMainCleanPass")

def test_verify_test_main_leak_rewrites_exit_code():
    _assert_go_pass("TestTruthVerifyTestMainLeakRewritesExit")

def test_verify_test_main_failed_run_skips_check():
    _assert_go_pass("TestTruthVerifyTestMainFailedNoCheck")
