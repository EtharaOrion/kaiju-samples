#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e c9c2424e61baf2fcdb4ef6e85de9c806477b31f1^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/zahgon/rust-raknet c9c2424e61baf2fcdb4ef6e85de9c806477b31f1
fi
git reset --hard c9c2424e61baf2fcdb4ef6e85de9c806477b31f1
echo "Reset to reference commit c9c2424e61baf2fcdb4ef6e85de9c806477b31f1"
