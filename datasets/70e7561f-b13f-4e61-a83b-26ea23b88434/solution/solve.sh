#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e 2cbb0ab36abe206da3cce3d5c40641acc5f4132b^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/Zahgon/lego 2cbb0ab36abe206da3cce3d5c40641acc5f4132b
fi
git reset --hard 2cbb0ab36abe206da3cce3d5c40641acc5f4132b
echo "Reset to reference commit 2cbb0ab36abe206da3cce3d5c40641acc5f4132b"
