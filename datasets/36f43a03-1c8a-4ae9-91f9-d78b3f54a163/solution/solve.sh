#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e 4c98f5a7fc6cb6ccb7cfa5be6a6424df0e3bd97f^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/Zahgon/gonum 4c98f5a7fc6cb6ccb7cfa5be6a6424df0e3bd97f
fi
git reset --hard 4c98f5a7fc6cb6ccb7cfa5be6a6424df0e3bd97f
echo "Reset to reference commit 4c98f5a7fc6cb6ccb7cfa5be6a6424df0e3bd97f"
