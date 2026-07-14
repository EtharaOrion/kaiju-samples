#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e 42eb361c9c553e50b763524cf9087bb64f31af6c^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/Zahgon/nexosim 42eb361c9c553e50b763524cf9087bb64f31af6c
fi
git reset --hard 42eb361c9c553e50b763524cf9087bb64f31af6c
echo "Reset to reference commit 42eb361c9c553e50b763524cf9087bb64f31af6c"
