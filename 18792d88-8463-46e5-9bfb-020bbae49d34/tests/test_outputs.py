import os
import re
import glob
import pytest


# ---------------------------------------------------------------------------
# Locate the solution's `src` directory (this is a TypeScript project; we
# verify the restored implementation at the source level, which reliably
# discriminates a real solution from the gutted `throw new Error("STUB")` one).
# ---------------------------------------------------------------------------
def _find_src_dir():
    starts = [os.getcwd(), os.path.dirname(os.path.abspath(__file__))]
    # Walk upward looking for src/execution.ts
    for start in starts:
        d = os.path.abspath(start)
        for _ in range(10):
            src = os.path.join(d, "src")
            if os.path.isfile(os.path.join(src, "execution.ts")):
                return src
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent
    # Fall back to a recursive search
    for start in starts:
        for root, dirs, files in os.walk(os.path.abspath(start)):
            # skip node_modules for speed
            if "node_modules" in root.split(os.sep):
                continue
            if os.path.basename(root) == "src" and "execution.ts" in files:
                return root
    return None


SRC_DIR = _find_src_dir()

IMPLEMENTED_FILES = [
    "ast.ts",
    "compat.ts",
    "error.ts",
    "execution.ts",
    "generate.ts",
    "inspect.ts",
    "json.ts",
    "memoize.ts",
    "non-null.ts",
    "resolve-info.ts",
    "runtime.ts",
    os.path.join("__benchmarks__", "benchmarks.ts"),
    os.path.join("__benchmarks__", "schema-few-resolvers.ts"),
    os.path.join("__benchmarks__", "schema-many-resolvers.ts"),
    os.path.join("__benchmarks__", "schema-nested-array.ts"),
]

STUB_RE = re.compile(r'throw\s+new\s+Error\(\s*["\']STUB["\']\s*\)')


def _read(rel):
    assert SRC_DIR is not None, "Could not locate the project's src/ directory"
    path = os.path.join(SRC_DIR, rel)
    assert os.path.isfile(path), "Expected implemented file missing: %s" % rel
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# Structural / location sanity
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# Core discriminator: no STUB bodies may remain in the implemented modules.
# A correct solution restores real code; the gutted repo throws Error("STUB").
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# Public API surface / behavioral contract markers
# ---------------------------------------------------------------------------






# ---------------------------------------------------------------------------
# Directive handling (@skip / @include) must reference the graphql directives
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# Error handling: originalError preservation for wrapped scalar/resolver errors
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Resolve-info enricher validation & merge semantics
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# JSON serializer must produce real serialization logic (not a stub)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Non-null propagation helpers must exist
# ---------------------------------------------------------------------------


def test_no_stub_anywhere_in_src():
    """No implementation file in src/ (excluding tests) should keep a STUB."""
    offenders = []
    for path in glob.glob(os.path.join(SRC_DIR, "**", "*.ts"), recursive=True):
        base = os.path.basename(path)
        if base.endswith(".test.ts"):
            continue
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            if STUB_RE.search(fh.read()):
                offenders.append(os.path.relpath(path, SRC_DIR))
    assert offenders == [], "STUB bodies remain in: %r" % offenders

def test_json_module_has_stringify_logic():
    content = _read("json.ts")
    assert "stringify" in content, "json.ts must provide a stringify serializer"
    # Must actually do serialization work, not just throw.
    assert not STUB_RE.search(content)

def test_non_null_module_non_trivial():
    content = _read("non-null.ts")
    assert not STUB_RE.search(content)
    assert len(content.strip()) > 0
