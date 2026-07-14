#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e 1283a410924ce9246ab7a5641e6db72bec81c330^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/Zahgon/orion 1283a410924ce9246ab7a5641e6db72bec81c330
fi
git reset --hard 1283a410924ce9246ab7a5641e6db72bec81c330
echo "Reset to reference commit 1283a410924ce9246ab7a5641e6db72bec81c330"
