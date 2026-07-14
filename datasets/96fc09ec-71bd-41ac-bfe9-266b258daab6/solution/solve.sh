#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e 472c9d38c9fc523599f37ca3207279e5ab10f74f^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/Zahgon/distribution 472c9d38c9fc523599f37ca3207279e5ab10f74f
fi
git reset --hard 472c9d38c9fc523599f37ca3207279e5ab10f74f
echo "Reset to reference commit 472c9d38c9fc523599f37ca3207279e5ab10f74f"
