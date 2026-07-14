#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e 92fac41e9a97414cd0efa5eb8613354a63230b09^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/Zahgon/str0m 92fac41e9a97414cd0efa5eb8613354a63230b09
fi
git reset --hard 92fac41e9a97414cd0efa5eb8613354a63230b09
echo "Reset to reference commit 92fac41e9a97414cd0efa5eb8613354a63230b09"
