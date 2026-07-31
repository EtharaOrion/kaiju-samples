"""
Behavioral test suite for the restored `Zahgon/colly` Go module.

Because the solution under test is a Go library (not a Python module), these
tests drive the real Go toolchain: they build the module, verify no stub
placeholders survive, and execute the actual colly / queue test binaries that
encode the behavioral contract from TRUTH.md.

Each test asserts a *contract* (compiles, no residual stubs, named
fail_to_pass tests pass) rather than a brittle literal, so a stubbed / broken
implementation fails while a correct colly release passes.
"""

import os
import shutil
import subprocess
import sys

import pytest


# --------------------------------------------------------------------------- #
# Discovery helpers
# --------------------------------------------------------------------------- #

def _find_repo_root():
    """Walk upward from this file (and CWD) looking for the colly module root.

    The root is identified by a go.mod plus the top-level colly.go that defines
    NewCollector.
    """
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
            gomod = os.path.join(cur, "go.mod")
            collygo = os.path.join(cur, "colly.go")
            if os.path.isfile(gomod) and os.path.isfile(collygo):
                return cur
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent

    # Fallback: breadth search downward from candidates for colly.go+go.mod.
    for start in candidates:
        for dirpath, dirnames, filenames in os.walk(start):
            # avoid vendoring / VCS noise
            dirnames[:] = [d for d in dirnames if d not in (".git", "vendor", "node_modules")]
            if "go.mod" in filenames and "colly.go" in filenames:
                # make sure colly.go references NewCollector to reduce false hits
                try:
                    with open(os.path.join(dirpath, "colly.go"), "r", errors="ignore") as fh:
                        if "NewCollector" in fh.read():
                            return dirpath
                except OSError:
                    continue
    return None


REPO_ROOT = _find_repo_root()
GO_BIN = shutil.which("go")


def _require_env():
    if REPO_ROOT is None:
        pytest.skip("colly Go module root not found")
    if GO_BIN is None:
        pytest.skip("go toolchain not available on PATH")


def _run_go(args, timeout=600):
    """Run a go command inside the repo root, returning CompletedProcess."""
    env = dict(os.environ)
    # Keep the toolchain offline-friendly if the module cache is populated.
    env.setdefault("GOFLAGS", "")
    return subprocess.run(
        [GO_BIN] + args,
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        text=True,
    )


def _iter_go_source_files():
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d not in (".git", "vendor", "node_modules")]
        for fn in filenames:
            if fn.endswith(".go"):
                yield os.path.join(dirpath, fn)


# --------------------------------------------------------------------------- #
# Structural / anti-stub contract
# --------------------------------------------------------------------------- #





# --------------------------------------------------------------------------- #
# Build / vet contract
# --------------------------------------------------------------------------- #





# --------------------------------------------------------------------------- #
# Behavioral test-binary contract (root colly package)
# --------------------------------------------------------------------------- #

def _run_named_tests(pkg, names, timeout=600):
    _require_env()
    pattern = "^(" + "|".join(names) + ")$"
    proc = _run_go(["test", "-count=1", "-run", pattern, pkg], timeout=timeout)
    return proc






























# --------------------------------------------------------------------------- #
# Limit-rule concurrency contract (run under the race detector)
# --------------------------------------------------------------------------- #



# --------------------------------------------------------------------------- #
# Queue subpackage contract
# --------------------------------------------------------------------------- #


def test_no_stub_placeholders_remain():
    """No source file may still contain the STUB sentinel or TODO panics.

    TRUTH.md: any residual 'STUB: not implemented', panic("TODO"), etc. means
    the work was not done. This catches trivial "leave the stub" cheats.
    """
    _require_env()
    offenders = []
    needles = ('STUB: not implemented', 'panic("TODO")', "panic('TODO')")
    for path in _iter_go_source_files():
        try:
            with open(path, "r", errors="ignore") as fh:
                content = fh.read()
        except OSError:
            continue
        for needle in needles:
            if needle in content:
                offenders.append((os.path.relpath(path, REPO_ROOT), needle))
    assert not offenders, f"Residual stub placeholders found: {offenders}"

def test_core_files_are_nontrivial():
    """The core library files must contain substantial implementation.

    A stub solution reduces every body to a one-liner; a real colly source is
    large. This is a coarse, non-brittle guard against emptied-out files.
    """
    _require_env()
    core = {
        "colly.go": 5000,
        "request.go": 1500,
        "response.go": 1000,
        "http_backend.go": 1500,
        "context.go": 800,
        "htmlelement.go": 1000,
        "unmarshal.go": 1000,
        "queue/queue.go": 800,
    }
    too_small = []
    for rel, min_bytes in core.items():
        path = os.path.join(REPO_ROOT, rel)
        if not os.path.isfile(path):
            too_small.append((rel, "missing"))
            continue
        size = os.path.getsize(path)
        if size < min_bytes:
            too_small.append((rel, size))
    assert not too_small, f"Core files unexpectedly small/missing: {too_small}"

def test_revisit_semantics():
    """GET dedup keyed on URL; POST dedup incorporates body; AllowURLRevisit off.

    Covers the pitfall of mis-keying dedup (TRUTH.md 'Revisit key correctness').
    """
    proc = _run_named_tests(
        "./",
        [
            "TestCollectorURLRevisit",
            "TestCollectorPostRevisit",
            "TestCollectorPostRawRevisit",
        ],
    )
    assert proc.returncode == 0, f"revisit tests failed:\n{proc.stdout}"

def test_headers_useragent_accept():
    """Accept default only when unset; user/empty override respected."""
    proc = _run_named_tests(
        "./",
        ["TestNoAcceptHeader", "TestHeaders", "TestUserAgent"],
    )
    assert proc.returncode == 0, f"header tests failed:\n{proc.stdout}"

def test_absolute_url_and_base_tag_edge_cases():
    """AbsoluteURL must handle base tags, tabs/newlines, and a lone percent."""
    proc = _run_named_tests(
        "./",
        [
            "TestBaseTag",
            "TestBaseTagRelative",
            "TestTabsAndNewlines",
            "TestLonePercent",
        ],
    )
    assert proc.returncode == 0, f"AbsoluteURL edge-case tests failed:\n{proc.stdout}"

def test_content_sniffing_and_gzip():
    """Charset detection + content-encoding decode order, incl. gzip 404."""
    proc = _run_named_tests(
        "./",
        [
            "TestCollectorContentSniffing",
            "TestParseHTTPErrorResponse",
            "TestIssue745GzipURLWith404Response",
        ],
    )
    assert proc.returncode == 0, f"content sniffing/gzip tests failed:\n{proc.stdout}"

def test_redirects_and_cookies():
    proc = _run_named_tests(
        "./",
        [
            "TestRedirect",
            "TestRedirectWithDisallowedURLs",
            "TestSetCookieRedirect",
            "TestSetCookieComplexRedirectCycle",
            "TestCollectorCookies",
            "TestIssue594",
        ],
    )
    assert proc.returncode == 0, f"redirect/cookie tests failed:\n{proc.stdout}"

def test_robots_txt():
    proc = _run_named_tests(
        "./",
        [
            "TestRobotsWhenAllowed",
            "TestRobotsWhenDisallowed",
            "TestRobotsWhenDisallowedWithQueryParameter",
            "TestIgnoreRobotsWhenDisallowed",
            "TestConnectionErrorOnRobotsTxtResultsInError",
        ],
    )
    assert proc.returncode == 0, f"robots.txt tests failed:\n{proc.stdout}"

def test_retries_and_head_checks():
    proc = _run_named_tests(
        "./",
        [
            "TestCollectorPostRetry",
            "TestCollectorGetRetry",
            "TestCollectorPostRetryUnseekable",
            "TestRedirectErrorRetry",
            "TestCollectorVisitWithCheckHead",
            "TestCheckRequestHeadersFunc",
        ],
    )
    assert proc.returncode == 0, f"retry/head tests failed:\n{proc.stdout}"

def test_context_behavior():
    proc = _run_named_tests(
        "./",
        [
            "TestContextIteration",
            "TestContextClone",
            "TestCollectorContext",
            "TestRequestContext",
        ],
    )
    assert proc.returncode == 0, f"context tests failed:\n{proc.stdout}"

def test_request_marshal_roundtrip():
    proc = _run_named_tests("./", ["TestRequestMarshalRoundtripHost"])
    assert proc.returncode == 0, f"request marshal roundtrip failed:\n{proc.stdout}"

def test_html_element_helpers():
    proc = _run_named_tests(
        "./",
        [
            "TestHTMLElement",
            "TestAttr",
            "TestChildText",
            "TestChildTexts",
            "TestChildAttr",
            "TestChildAttrs",
        ],
    )
    assert proc.returncode == 0, f"HTMLElement helper tests failed:\n{proc.stdout}"

def test_unmarshal_into_structs():
    proc = _run_named_tests(
        "./",
        [
            "TestBasicUnmarshal",
            "TestNestedUnmarshal",
            "TestNestedUnmarshalMap",
            "TestPointerSliceUnmarshall",
            "TestStructSliceUnmarshall",
        ],
    )
    assert proc.returncode == 0, f"unmarshal tests failed:\n{proc.stdout}"

def test_depth_and_request_counting():
    proc = _run_named_tests(
        "./",
        ["TestCollectorDepth", "TestCollectorRequests"],
    )
    assert proc.returncode == 0, f"depth/request-count tests failed:\n{proc.stdout}"

def test_http_tracing():
    proc = _run_named_tests(
        "./",
        [
            "TestTraceWithNoDelay",
            "TestTraceWithDelay",
            "TestCollectorVisitWithTrace",
        ],
    )
    assert proc.returncode == 0, f"HTTP tracing tests failed:\n{proc.stdout}"

def test_shared_limit_rule_no_deadlock_no_race():
    """Shared limit rules must not deadlock or race.

    Runs the concurrency tests with -race, matching TRUTH.md's requirement that
    the race detector report no data races and the shared rule not stall.
    """
    _require_env()
    names = [
        "TestSharedLimitRule_AInitThenBInit_ANotStuck",
        "TestSharedLimitRuleRace",
        "TestLimitRuleClone",
    ]
    pattern = "^(" + "|".join(names) + ")$"
    proc = _run_go(["test", "-race", "-count=1", "-run", pattern, "./"], timeout=900)
    if proc.returncode != 0 and "-race requires cgo" in proc.stdout:
        # Environment without cgo: fall back to a non-race run so the behavioral
        # deadlock/clone contract is still exercised.
        proc = _run_go(["test", "-count=1", "-run", pattern, "./"], timeout=600)
    assert proc.returncode == 0, f"shared limit-rule tests failed:\n{proc.stdout}"

def test_queue_package():
    """queue.New / AddURL / Run / Size / IsEmpty behavior."""
    proc = _run_named_tests("./queue/", ["TestQueue"])
    assert proc.returncode == 0, f"queue.TestQueue failed:\n{proc.stdout}"
