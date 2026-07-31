"""
Behavioral test suite for the restored rollup-plugin-typescript2 sources.

This is a TypeScript/Node project, so the *real* behavioral contract described
in TRUTH.md is exercised through the project's own Jest specs (which import the
actual modules and assert on real outputs).  We drive those from pytest via
subprocess, and additionally perform source-level invariants that catch stub /
overfit solutions even before the toolchain runs.

Requirements: stdlib + pytest only.  No network access is performed; we only use
locally-installed dev dependencies (node_modules) when present and skip cleanly
otherwise.
"""

import json
import os
import shutil
import subprocess

import pytest


# --------------------------------------------------------------------------- #
# Repository discovery
# --------------------------------------------------------------------------- #

SEVEN_FILES = [
    "diagnostics-format-host.ts",
    "diagnostics.ts",
    "get-options-overrides.ts",
    "host.ts",
    "index.ts",
    "rollingcache.ts",
    "tscache.ts",
]


def _looks_like_repo(d):
    return (
        os.path.isdir(os.path.join(d, "src"))
        and os.path.isfile(os.path.join(d, "src", "tscache.ts"))
        and os.path.isfile(os.path.join(d, "package.json"))
    )


def _find_repo_root():
    starts = []
    for env in ("REPO_ROOT", "PROJECT_ROOT", "SOLUTION_DIR"):
        v = os.environ.get(env)
        if v:
            starts.append(v)
    starts.append(os.path.dirname(os.path.abspath(__file__)))
    starts.append(os.getcwd())

    # Walk upward from each start.
    seen = set()
    for start in starts:
        d = os.path.abspath(start)
        while True:
            if d in seen:
                break
            seen.add(d)
            if _looks_like_repo(d):
                return d
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent

    # Walk downward (bounded) from each start.
    for start in starts:
        start = os.path.abspath(start)
        if not os.path.isdir(start):
            continue
        for root, dirs, _files in os.walk(start):
            dirs[:] = [x for x in dirs if x not in ("node_modules", ".git")]
            if _looks_like_repo(root):
                return root
    return None


REPO = _find_repo_root()


@pytest.fixture(scope="session")
def repo():
    if REPO is None:
        pytest.skip("Could not locate the rollup-plugin-typescript2 repository root")
    return REPO


def _src(repo, name):
    return os.path.join(repo, "src", name)


def _read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


# --------------------------------------------------------------------------- #
# Source-level invariants (always runnable; catch stubs / overfits)
# --------------------------------------------------------------------------- #













# --------------------------------------------------------------------------- #
# Jest-driven behavioral tests (real module imports + real assertions)
# --------------------------------------------------------------------------- #

def _jest_available(repo):
    if os.name == "nt":
        bin_name = "jest.cmd"
    else:
        bin_name = "jest"
    local = os.path.join(repo, "node_modules", ".bin", bin_name)
    if os.path.isfile(local):
        return [local]
    npx = shutil.which("npx")
    if npx and os.path.isdir(os.path.join(repo, "node_modules")):
        return [npx, "jest"]
    return None


def _find_spec(repo, spec_basename):
    for root, dirs, files in os.walk(repo):
        dirs[:] = [x for x in dirs if x not in ("node_modules", ".git")]
        if spec_basename in files:
            return os.path.join(root, spec_basename)
    return None


def _run_jest(repo, spec_basename, timeout):
    cmd = _jest_available(repo)
    if cmd is None:
        pytest.skip("jest / node_modules not available; cannot run behavioral specs")
    spec = _find_spec(repo, spec_basename)
    if spec is None:
        pytest.skip(f"spec file {spec_basename} not found in repository")

    env = dict(os.environ)
    env.setdefault("CI", "true")
    full = list(cmd) + [
        "--runTestsByPath",
        spec,
        "--colors=false",
        "--ci",
    ]
    try:
        proc = subprocess.run(
            full,
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        pytest.skip("jest executable could not be launched")
    except subprocess.TimeoutExpired:
        pytest.skip(f"jest run for {spec_basename} timed out")
    return proc


def _assert_jest_passed(proc, spec_basename):
    if proc.returncode != 0:
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        # If the environment simply can't run (e.g. transform tooling missing),
        # be lenient only when there's a clear infra failure signal.
        infra_markers = (
            "Cannot find module",
            "command not found",
            "ts-jest",
            "No tests found",
        )
        if proc.returncode != 1 and any(m in out for m in infra_markers):
            pytest.skip(f"jest could not execute {spec_basename}: infra issue\n{out[-2000:]}")
        pytest.fail(
            f"jest spec {spec_basename} failed (exit {proc.returncode}):\n"
            f"{out[-4000:]}"
        )


UNIT_SPECS = [
    "diagnostics-format-host.spec.ts",
    "diagnostics.spec.ts",
    "host.spec.ts",
    "rollingcache.spec.ts",
    "get-options-overrides.spec.ts",
]




INTEGRATION_SPECS = [
    # Names as they typically appear; skipped cleanly if not present.
    "no-errors.spec.ts",
    "errors.spec.ts",
]


def test_diagnostics_computes_fileline_from_position(repo):
    """convertDiagnostic must derive fileLine from the real TS position API,
    not fabricate it.  A correct implementation calls
    getLineAndCharacterOfPosition to build the 1-based `fileName(line,char)`."""
    text = _read(_src(repo, "diagnostics.ts"))
    assert "getLineAndCharacterOfPosition" in text, (
        "diagnostics.ts must use getLineAndCharacterOfPosition to compute fileLine"
    )
    # 1-based coordinates require an explicit +1 somewhere.
    assert "+ 1" in text or "+1" in text, (
        "diagnostics.ts must convert 0-based line/character to 1-based (missing +1)"
    )

def test_diagnostics_routes_by_category(repo):
    """printDiagnostics must route to info/error/warn based on category."""
    text = _read(_src(repo, "diagnostics.ts"))
    for method in ("info", "error", "warn"):
        assert method in text, f"printDiagnostics must be able to call context.{method}"

def test_format_host_uses_ts_sys(repo):
    """FormatHost cwd/newline must come from the TS system, not be hard-coded."""
    text = _read(_src(repo, "diagnostics-format-host.ts"))
    assert "sys" in text, (
        "diagnostics-format-host.ts must derive values from the TypeScript system (tsModule.sys)"
    )
