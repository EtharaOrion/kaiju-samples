#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e 006adaf5b13870c6cec71a2f00fda0d12f1e3b5d^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/Zahgon/rust-signals 006adaf5b13870c6cec71a2f00fda0d12f1e3b5d
fi
git reset --hard 006adaf5b13870c6cec71a2f00fda0d12f1e3b5d
echo "Reset to reference commit 006adaf5b13870c6cec71a2f00fda0d12f1e3b5d"
