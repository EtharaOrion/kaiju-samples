#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e 2016e44ba4a4757a996300350063b937a2ad33e8^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/Zahgon/frost 2016e44ba4a4757a996300350063b937a2ad33e8
fi
git reset --hard 2016e44ba4a4757a996300350063b937a2ad33e8
echo "Reset to reference commit 2016e44ba4a4757a996300350063b937a2ad33e8"
