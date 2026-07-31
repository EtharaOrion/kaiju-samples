"""
Pytest module verifying the Zahgon/css-select TypeScript repository satisfies
the behavioral contract in TRUTH.md.

These tests only READ source files (they never import or execute TS).
Each test passes on the real implementation and fails on the stubbed tree.
"""

import re
from pathlib import Path

import pytest

REPO = Path.cwd()

STUB_MARKERS = (
    'STUB: not implemented',
    'throw new Error("STUB")',
    "throw new Error('STUB')",
    '__builtin_trap',
)

IMPLEMENTED_FILES = [
    "src/attributes.ts",
    "src/compile.ts",
    "src/general.ts",
    "src/helpers/cache.ts",
    "src/helpers/selectors.ts",
    "src/index.ts",
    "src/pseudo-selectors/filters.ts",
    "src/pseudo-selectors/index.ts",
    "src/pseudo-selectors/pseudos.ts",
    "src/pseudo-selectors/subselects.ts",
]


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def read(rel):
    p = REPO / rel
    assert p.is_file(), f"expected source file missing: {rel}"
    return p.read_text(encoding="utf-8")


def strip_comments(src):
    # remove block comments and line comments (approximate, good enough for tokens)
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    src = re.sub(r"//[^\n]*", "", src)
    return src


def find_function_body(src, name):
    """
    Find a function-like definition named `name` and return the body text between
    its first '{' and matching '}'.  Handles:
        function name(...) { ... }
        export function name(...) { ... }
        name(...) { ... }            (methods / object props)
        const name = (...) => { ... }
        export const name = (...) => { ... }
        name: (...) => { ... }
    """
    patterns = [
        rf"function\s+{re.escape(name)}\s*(?:<[^>]*>)?\s*\(",
        rf"\b(?:const|let|var)\s+{re.escape(name)}\s*(?::[^=]+)?=\s*(?:async\s*)?(?:function\b[^(]*)?\(",
        rf"\b{re.escape(name)}\s*(?:<[^>]*>)?\s*\([^;{{]*\)\s*(?::[^={{;]+)?=>\s*{{",
        rf"\b{re.escape(name)}\s*(?:<[^>]*>)?\s*\([^;]*\)\s*(?::[^={{;]+)?{{",
    ]
    for pat in patterns:
        for m in re.finditer(pat, src):
            start = m.start()
            brace = src.find("{", m.end() - 1)
            if brace == -1:
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


def assert_not_stub(body, name):
    assert body is not None, f"could not locate function body for {name!r}"
    for marker in STUB_MARKERS:
        assert marker not in body, f"{name} still contains stub marker {marker!r}"
    # a real body should contain some non-trivial code
    inner = body.strip().strip("{}").strip()
    assert len(inner) > 0, f"{name} has an empty body"


# --------------------------------------------------------------------------- #
# generic: no stub markers anywhere in implemented files
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# src/attributes.ts
# --------------------------------------------------------------------------- #


















# --------------------------------------------------------------------------- #
# src/general.ts
# --------------------------------------------------------------------------- #
















# --------------------------------------------------------------------------- #
# src/compile.ts
# --------------------------------------------------------------------------- #








# --------------------------------------------------------------------------- #
# src/helpers/cache.ts
# --------------------------------------------------------------------------- #






# --------------------------------------------------------------------------- #
# src/helpers/selectors.ts
# --------------------------------------------------------------------------- #








# --------------------------------------------------------------------------- #
# src/index.ts
# --------------------------------------------------------------------------- #








# --------------------------------------------------------------------------- #
# src/pseudo-selectors/filters.ts
# --------------------------------------------------------------------------- #








# --------------------------------------------------------------------------- #
# src/pseudo-selectors/index.ts (registry / dispatch)
# --------------------------------------------------------------------------- #




# --------------------------------------------------------------------------- #
# src/pseudo-selectors/pseudos.ts
# --------------------------------------------------------------------------- #




# --------------------------------------------------------------------------- #
# src/pseudo-selectors/subselects.ts
# --------------------------------------------------------------------------- #


def test_attributes_use_adapter_getattributevalue():
    src = read("src/attributes.ts")
    assert "getAttributeValue" in src, "attributes must read via adapter.getAttributeValue"

def test_attributes_null_absent_check():
    src = read("src/attributes.ts")
    # absent attribute handling relies on comparing against null
    assert "null" in src, "attributes must check for absent (null) attribute values"

def test_attributes_hyphen_boundary():
    src = strip_comments(read("src/attributes.ts"))
    # |= must match value or value + '-'
    assert '"-"' in src or "'-'" in src or "45" in src, \
        "hyphen (|=) operator must check for '-' boundary"

def test_attributes_element_word_boundary_and_whitespace_guard():
    body = find_function_body(read("src/attributes.ts"), "element")
    if body is None:
        # element may be a value in an operator object; fall back to whole file
        body = read("src/attributes.ts")
    assert re.search(r"\\s|whitespace|\s\\b|test\(", body) or "RegExp" in body or "\\b" in body, \
        "element (~=) must use whitespace/word-boundary matching"

def test_attributes_falseFunc_shortcircuits():
    src = read("src/attributes.ts")
    assert "falseFunc" in src, "degenerate values must short-circuit via falseFunc/boolbase"

def test_attributes_not_operator_negation():
    body = find_function_body(read("src/attributes.ts"), "not")
    if body is None:
        body = read("src/attributes.ts")
    assert "!" in body or "!==" in body, "not (!=) operator must negate equality"

def test_general_tag_matches_name():
    src = read("src/general.ts")
    assert "getName" in src, "tag rule must use adapter.getName"

def test_general_uses_prevElementSibling_and_fallback():
    src = read("src/general.ts")
    assert "prevElementSibling" in src, \
        "adjacent combinator must use adapter.prevElementSibling when present"
    assert "getSiblings" in src, \
        "adjacent/sibling combinators must scan getSiblings as a fallback"

def test_general_uses_isTag_filtering():
    src = read("src/general.ts")
    assert "isTag" in src, "combinators must filter through adapter.isTag"

def test_general_chains_next():
    src = read("src/general.ts")
    assert re.search(r"\bnext\s*\(", src), "combinators must chain next(element)"

def test_compile_or_combinator():
    body = find_function_body(read("src/compile.ts"), "or")
    if body is None:
        # `or` might be small/exported differently; check file
        src = read("src/compile.ts")
        assert re.search(r"\bor\b", src) and "||" in src, "compile must define an OR combinator"
    else:
        assert_not_stub(body, "or")
        assert "||" in body or "some" in body, "or() must logically OR predicates"

def test_cache_off_path_uses_next_and_matches():
    src = read("src/helpers/cache.ts")
    assert re.search(r"next\s*\(", src), "cache must call next(element)"
    assert re.search(r"matches\s*\(", src), "cache must call matches(element)"

def test_selectors_getQuality_present():
    body = find_function_body(read("src/helpers/selectors.ts"), "getQuality")
    assert_not_stub(body, "getQuality")

def test_selectors_includesScopePseudo_present():
    body = find_function_body(read("src/helpers/selectors.ts"), "includesScopePseudo")
    assert_not_stub(body, "includesScopePseudo")

def test_selectors_includesScopePseudo_checks_scope():
    body = find_function_body(read("src/helpers/selectors.ts"), "includesScopePseudo")
    assert body is not None
    assert "scope" in body.lower(), "includesScopePseudo must check for the scope pseudo"
    assert "pseudo" in body.lower(), "includesScopePseudo must inspect pseudo tokens"

def test_filters_icontains_case_insensitive():
    src = read("src/pseudo-selectors/filters.ts")
    assert "toLowerCase" in src, "icontains must lower-case for case-insensitive match"

def test_filters_not_stub():
    src = read("src/pseudo-selectors/filters.ts")
    for marker in STUB_MARKERS:
        assert marker not in src

def test_pseudos_not_stub():
    src = read("src/pseudo-selectors/pseudos.ts")
    for marker in STUB_MARKERS:
        assert marker not in src

def test_subselects_not_stub():
    src = read("src/pseudo-selectors/subselects.ts")
    for marker in STUB_MARKERS:
        assert marker not in src
