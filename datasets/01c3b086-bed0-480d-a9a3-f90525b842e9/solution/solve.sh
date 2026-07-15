#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e f00d5d7ee6aa3e61b18922597010595c32ca0dea^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/Zahgon/SpectralCluster f00d5d7ee6aa3e61b18922597010595c32ca0dea
fi
git reset --hard f00d5d7ee6aa3e61b18922597010595c32ca0dea
echo "Reset to reference commit f00d5d7ee6aa3e61b18922597010595c32ca0dea"
