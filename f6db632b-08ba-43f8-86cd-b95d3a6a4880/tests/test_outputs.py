import os
import shutil
import subprocess

import pytest


# --------------------------------------------------------------------------
# Locating the Go module under test
# --------------------------------------------------------------------------
def _find_repo_root():
    """Find the directory that contains list/list.go (the module root)."""
    start = os.getcwd()

    # Walk upward from cwd.
    cur = start
    for _ in range(8):
        if os.path.exists(os.path.join(cur, "list", "list.go")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent

    # Walk downward from cwd.
    for root, dirs, files in os.walk(start):
        if os.path.basename(root) == "list" and "list.go" in files:
            candidate = os.path.dirname(root)
            if os.path.exists(os.path.join(candidate, "screenbuf", "screenbuf.go")):
                return candidate
            return candidate
    return None


@pytest.fixture(scope="session")
def go_env():
    go_bin = shutil.which("go")
    if go_bin is None:
        pytest.skip("Go toolchain not available")
    root = _find_repo_root()
    if root is None:
        pytest.skip("Could not locate promptui Go module (list/list.go not found)")
    if not os.path.isdir(os.path.join(root, "screenbuf")):
        pytest.skip("screenbuf package not found in module")
    return go_bin, root


def _run(go_bin, cwd, *args, timeout=420):
    return subprocess.run(
        [go_bin, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _run_go_snippet(go_bin, pkg_dir, filename, source, runpat):
    """Drop a temporary *_test.go file into a package dir, run it, remove it."""
    assert filename.endswith("_test.go")
    path = os.path.join(pkg_dir, filename)
    with open(path, "w") as f:
        f.write(source)
    try:
        r = _run(go_bin, pkg_dir, "test", "-run", runpat, "-count=1", "./")
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    return r


# --------------------------------------------------------------------------
# 1. The frozen tests specified by TRUTH.md must all pass.
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# 2. list.New validation + origin initialization contract.
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# 3. Navigation keeps cursor + scroll window consistent & boundary safe.
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# 4. Per-element identity for duplicate values (TestListComparion contract).
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# 5. PageDown / PageUp clamping and can-page reporting.
# --------------------------------------------------------------------------


def test_frozen_list_and_screenbuf_tests_pass(go_env):
    go_bin, root = go_env
    r = _run(
        go_bin,
        root,
        "test",
        "-count=1",
        "-run",
        "TestListNew|TestListMovement|TestListPageDown|TestListComparion|TestScreen",
        "./list/...",
        "./screenbuf/...",
    )
    assert r.returncode == 0, (
        "The graded list/screenbuf tests must pass on a correct implementation.\n"
        f"STDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"
    )

def test_list_new_contract(go_env):
    go_bin, root = go_env
    pkg = os.path.join(root, "list")
    src = r'''
package list

import "testing"

func TestZZNewContract(t *testing.T) {
	// nil input must error (not be dereferenced).
	if _, err := New(nil, 5); err == nil {
		t.Fatal("New(nil, 5) must return an error")
	}
	// size < 1 must error.
	if _, err := New([]string{"a"}, 0); err == nil {
		t.Fatal("New(items, 0) must return an error")
	}
	if _, err := New([]string{"a"}, -3); err == nil {
		t.Fatal("New(items, -3) must return an error")
	}
	// non-slice must error.
	if _, err := New("not a slice", 5); err == nil {
		t.Fatal("New(non-slice, 5) must return an error")
	}
	if _, err := New(42, 5); err == nil {
		t.Fatal("New(int, 5) must return an error")
	}
	// arbitrary element type accepted via reflection.
	type box struct{ N int }
	l, err := New([]box{{1}, {2}, {3}}, 2)
	if err != nil {
		t.Fatalf("New with custom slice type errored: %v", err)
	}
	if l == nil {
		t.Fatal("New returned nil list on success")
	}
	// origin state.
	if l.Start() != 0 {
		t.Fatalf("initial Start()=%d, want 0", l.Start())
	}
	if l.Index() != 0 {
		t.Fatalf("initial Index()=%d, want 0", l.Index())
	}
	// preserves order & length in the visible window.
	vis, active := l.Items()
	if len(vis) != 2 {
		t.Fatalf("visible len=%d, want size=2", len(vis))
	}
	if active != 0 {
		t.Fatalf("initial active=%d, want 0", active)
	}
	if vis[0].(box).N != 1 || vis[1].(box).N != 2 {
		t.Fatalf("window did not preserve order: %+v", vis)
	}
}
'''
    r = _run_go_snippet(go_bin, pkg, "zz_new_contract_test.go", src, "TestZZNewContract")
    assert r.returncode == 0, f"list.New contract failed.\n{r.stdout}\n{r.stderr}"

def test_list_navigation_windowing(go_env):
    go_bin, root = go_env
    pkg = os.path.join(root, "list")
    src = r'''
package list

import "testing"

func TestZZNavWindow(t *testing.T) {
	items := []string{"a", "b", "c", "d", "e"}
	l, err := New(items, 3)
	if err != nil {
		t.Fatal(err)
	}

	// Prev at top is a no-op.
	l.Prev()
	if l.Index() != 0 || l.Start() != 0 {
		t.Fatalf("Prev at top changed state: index=%d start=%d", l.Index(), l.Start())
	}

	// Active item must always be inside the visible window.
	l.Next() // cursor 1
	l.Next() // cursor 2
	l.Next() // cursor 3 -> window must scroll so cursor stays visible
	vis, active := l.Items()
	if active < 0 || active >= len(vis) {
		t.Fatalf("active index %d out of visible range %d", active, len(vis))
	}
	if vis[active].(string) != "d" {
		t.Fatalf("active visible item = %v, want d", vis[active])
	}
	if l.Index() != 3 {
		t.Fatalf("Index()=%d, want 3", l.Index())
	}
	if l.Start() < 0 || l.Start()+len(vis) > len(items) {
		t.Fatalf("window out of range: start=%d len=%d", l.Start(), len(vis))
	}

	// Reach the bottom, then Next is a no-op at the boundary.
	l.Next() // cursor 4 (last)
	before := l.Index()
	l.Next() // should be a no-op
	if before != 4 || l.Index() != 4 {
		t.Fatalf("Next past bottom not a no-op: %d then %d", before, l.Index())
	}

	// Items() never returns more than `size` elements.
	vis, _ = l.Items()
	if len(vis) > 3 {
		t.Fatalf("Items returned %d elements, exceeds size 3", len(vis))
	}

	// Prev walks back up, keeping cursor visible.
	l.Prev()
	vis, active = l.Items()
	if active < 0 || active >= len(vis) {
		t.Fatalf("after Prev active %d out of range %d", active, len(vis))
	}
	if vis[active].(string) != "d" {
		t.Fatalf("after Prev active item=%v, want d", vis[active])
	}
	if l.Index() != 3 {
		t.Fatalf("after Prev Index()=%d, want 3", l.Index())
	}
}
'''
    r = _run_go_snippet(go_bin, pkg, "zz_nav_window_test.go", src, "TestZZNavWindow")
    assert r.returncode == 0, f"list navigation/windowing failed.\n{r.stdout}\n{r.stderr}"

def test_list_duplicate_identity(go_env):
    go_bin, root = go_env
    pkg = os.path.join(root, "list")
    src = r'''
package list

import "testing"

func TestZZDupIdentity(t *testing.T) {
	// Three equal values must remain individually addressable.
	l, err := New([]string{"x", "x", "x"}, 3)
	if err != nil {
		t.Fatal(err)
	}
	if l.Index() != 0 {
		t.Fatalf("Index()=%d, want 0", l.Index())
	}
	l.Next()
	if l.Index() != 1 {
		t.Fatalf("after 1 Next Index()=%d, want 1 (identity lost for dup values?)", l.Index())
	}
	l.Next()
	if l.Index() != 2 {
		t.Fatalf("after 2 Next Index()=%d, want 2 (identity lost for dup values?)", l.Index())
	}
	l.Prev()
	if l.Index() != 1 {
		t.Fatalf("after Prev Index()=%d, want 1", l.Index())
	}
}
'''
    r = _run_go_snippet(go_bin, pkg, "zz_dup_identity_test.go", src, "TestZZDupIdentity")
    assert r.returncode == 0, f"duplicate-value identity failed.\n{r.stdout}\n{r.stderr}"
