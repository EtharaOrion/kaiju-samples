"""
Behavioral test suite for the bigcache Go fork described in TRUTH.md.

Since the solution is a Go project, these pytest tests drive the actual Go
toolchain (build + `go test`) against the re-implemented source, and assert on
concrete behavioral contracts by compiling and running small Go probe programs.

A correct implementation makes every test pass; a stubbed/broken one fails
(build errors, failing `go test`, leftover STUB markers, or wrong probe output).
"""

import os
import shutil
import subprocess
import tempfile
import textwrap

import pytest


# --------------------------------------------------------------------------- #
# Repo discovery helpers
# --------------------------------------------------------------------------- #
STUB_MARKER = "STUB: not implemented"

CORE_FILES = [
    "bigcache.go", "bytes.go", "clock.go", "config.go", "encoding.go",
    "entry_not_found_error.go", "fnv.go", "hash.go", "iterator.go",
    "logger.go", "shard.go", "stats.go", "utils.go",
]


def _find_repo_root():
    """Locate the directory holding the bigcache go.mod."""
    candidates = []
    env = os.environ.get("SOLUTION_DIR") or os.environ.get("REPO_ROOT")
    if env:
        candidates.append(env)
    here = os.path.dirname(os.path.abspath(__file__))
    candidates.append(here)
    candidates.append(os.getcwd())

    seen = set()
    for start in candidates:
        cur = os.path.abspath(start)
        for _ in range(8):
            if cur in seen:
                break
            seen.add(cur)
            gomod = os.path.join(cur, "go.mod")
            bigcache = os.path.join(cur, "bigcache.go")
            if os.path.isfile(gomod) and os.path.isfile(bigcache):
                return cur
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent
    return None


@pytest.fixture(scope="session")
def repo_root():
    root = _find_repo_root()
    if root is None:
        pytest.skip("Could not locate bigcache repo root (no go.mod + bigcache.go)")
    return root


@pytest.fixture(scope="session")
def go_bin():
    go = shutil.which("go")
    if go is None:
        pytest.skip("Go toolchain not available on PATH")
    return go


def _run(cmd, cwd, timeout=600, env=None):
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True,
        timeout=timeout, env=full_env,
    )


def _module_path(repo_root, go_bin):
    r = _run([go_bin, "list", "-m"], repo_root)
    if r.returncode == 0 and r.stdout.strip():
        return r.stdout.strip().splitlines()[0].strip()
    # fallback: parse go.mod
    with open(os.path.join(repo_root, "go.mod")) as f:
        for line in f:
            line = line.strip()
            if line.startswith("module "):
                return line.split(None, 1)[1].strip()
    return "github.com/allegro/bigcache/v3"


# --------------------------------------------------------------------------- #
# Source-level contract: no stubs remain
# --------------------------------------------------------------------------- #




# --------------------------------------------------------------------------- #
# Build must succeed for the whole module
# --------------------------------------------------------------------------- #




# --------------------------------------------------------------------------- #
# The project's own test suites (core, queue, server) must pass
# --------------------------------------------------------------------------- #








# --------------------------------------------------------------------------- #
# Behavioral probe programs compiled against the real solution module.
# These assert concrete contract invariants that frozen tests may not cover.
# --------------------------------------------------------------------------- #
def _run_probe(repo_root, go_bin, main_src, timeout=300):
    """
    Write a `main` package Go program into a temp dir inside repo_root, run it
    with `go run`, and return the completed process. Placing it inside the repo
    lets it import the module by its own package path via the module cache.
    """
    mod = _module_path(repo_root, go_bin)
    src = main_src.replace("__MODULE__", mod)
    tmpdir = tempfile.mkdtemp(prefix="bcprobe_", dir=repo_root)
    try:
        fpath = os.path.join(tmpdir, "main.go")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(src)
        return _run([go_bin, "run", fpath], repo_root, timeout=timeout)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_no_stub_markers_remain(repo_root):
    """Every previously stubbed body must be re-implemented."""
    offenders = []
    for dirpath, _dirs, files in os.walk(repo_root):
        if "/.git" in dirpath or os.sep + ".git" in dirpath:
            continue
        for name in files:
            if not name.endswith(".go"):
                continue
            path = os.path.join(dirpath, name)
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    if STUB_MARKER in f.read():
                        offenders.append(os.path.relpath(path, repo_root))
            except OSError:
                pass
    assert offenders == [], f"Stub markers still present in: {offenders}"

def test_core_package_tests_pass(repo_root, go_bin):
    r = _run([go_bin, "test", "-count=1", "."], repo_root, timeout=900)
    assert r.returncode == 0, (
        f"core `go test .` failed:\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"
    )

def test_queue_package_tests_pass(repo_root, go_bin):
    queue_dir = os.path.join(repo_root, "queue")
    if not os.path.isdir(queue_dir):
        pytest.skip("queue subpackage not present")
    r = _run([go_bin, "test", "-count=1", "./queue/..."], repo_root, timeout=900)
    assert r.returncode == 0, (
        f"queue tests failed:\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"
    )

def test_server_package_tests_pass(repo_root, go_bin):
    server_dir = os.path.join(repo_root, "server")
    if not os.path.isdir(server_dir):
        pytest.skip("server subpackage not present")
    r = _run([go_bin, "test", "-count=1", "./server/..."], repo_root, timeout=900)
    assert r.returncode == 0, (
        f"server tests failed:\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"
    )

def test_race_detector_on_concurrency(repo_root, go_bin):
    """Concurrency tests must be free of data races."""
    r = _run(
        [go_bin, "test", "-count=1", "-race", "-run",
         "Parallel|Concurrent|Append|Iterat", "."],
        repo_root, timeout=1200,
    )
    if r.returncode != 0 and "-race requires cgo" in (r.stdout + r.stderr):
        pytest.skip("race detector unavailable (cgo disabled)")
    assert r.returncode == 0, (
        f"race run failed:\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"
    )

def test_probe_get_returns_copy_and_nil_value(repo_root, go_bin):
    """
    Contract: Get returns an independent copy; nil values are storable and
    distinct from not-found; validation rejects non-power-of-two shards.
    """
    src = textwrap.dedent('''
        package main

        import (
            "context"
            "fmt"
            "os"

            bigcache "__MODULE__"
        )

        func fail(m string) { fmt.Println("FAIL:", m); os.Exit(1) }

        func main() {
            cache, err := bigcache.New(context.Background(),
                bigcache.DefaultConfig(10 * 1e9))
            if err != nil { fail("construction: " + err.Error()) }

            // Set then Get returns stored value.
            if err := cache.Set("k1", []byte("hello")); err != nil {
                fail("set k1: " + err.Error())
            }
            v, err := cache.Get("k1")
            if err != nil { fail("get k1: " + err.Error()) }
            if string(v) != "hello" { fail("get k1 wrong value") }

            // Mutating the returned slice must NOT corrupt cache internals.
            for i := range v { v[i] = 'X' }
            v2, err := cache.Get("k1")
            if err != nil { fail("get k1 again: " + err.Error()) }
            if string(v2) != "hello" {
                fail("returned slice aliases internal buffer; got " + string(v2))
            }

            // Missing key -> not found error.
            if _, err := cache.Get("nope"); err == nil {
                fail("missing key should error")
            }

            // Nil value is storable and retrievable, distinct from not-found.
            if err := cache.Set("empty", nil); err != nil {
                fail("set nil: " + err.Error())
            }
            ev, err := cache.Get("empty")
            if err != nil { fail("nil value must not be not-found: " + err.Error()) }
            if len(ev) != 0 { fail("nil value should be empty") }

            // Delete removes; deleting again is not-found.
            if err := cache.Delete("k1"); err != nil {
                fail("delete k1: " + err.Error())
            }
            if err := cache.Delete("k1"); err == nil {
                fail("second delete should be not-found")
            }

            // Invalid config: non-power-of-two shards -> error, not panic.
            badCfg := bigcache.DefaultConfig(10 * 1e9)
            badCfg.Shards = 3
            if _, err := bigcache.New(context.Background(), badCfg); err == nil {
                fail("non-power-of-two shards must error")
            }

            fmt.Println("OK")
        }
    ''')
    r = _run_probe(repo_root, go_bin, src)
    assert r.returncode == 0 and "OK" in r.stdout, (
        f"core behavior probe failed:\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"
    )

def test_probe_append_and_len(repo_root, go_bin):
    """Append concatenates onto existing entries; Len counts entries."""
    src = textwrap.dedent('''
        package main

        import (
            "context"
            "fmt"
            "os"

            bigcache "__MODULE__"
        )

        func fail(m string) { fmt.Println("FAIL:", m); os.Exit(1) }

        func main() {
            cache, err := bigcache.New(context.Background(),
                bigcache.DefaultConfig(10 * 1e9))
            if err != nil { fail(err.Error()) }

            if err := cache.Append("a", []byte("foo")); err != nil {
                fail("append new: " + err.Error())
            }
            if err := cache.Append("a", []byte("bar")); err != nil {
                fail("append existing: " + err.Error())
            }
            v, err := cache.Get("a")
            if err != nil { fail("get a: " + err.Error()) }
            if string(v) != "foobar" {
                fail("append did not concatenate; got " + string(v))
            }

            _ = cache.Set("b", []byte("x"))
            if cache.Len() < 2 { fail("Len should count >=2 entries") }

            fmt.Println("OK")
        }
    ''')
    r = _run_probe(repo_root, go_bin, src)
    assert r.returncode == 0 and "OK" in r.stdout, (
        f"append/len probe failed:\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"
    )
