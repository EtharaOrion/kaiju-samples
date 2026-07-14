#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e 6f2ef8700669b4d1800ce3414f067cd25695de3c^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/Zahgon/remoc 6f2ef8700669b4d1800ce3414f067cd25695de3c
fi
git reset --hard 6f2ef8700669b4d1800ce3414f067cd25695de3c
echo "Reset to reference commit 6f2ef8700669b4d1800ce3414f067cd25695de3c"
