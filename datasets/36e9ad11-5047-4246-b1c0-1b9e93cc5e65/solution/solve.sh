#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e bd42b38f3627e6bca7274fb4d9af2e105f75da7c^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/Zahgon/transitions bd42b38f3627e6bca7274fb4d9af2e105f75da7c
fi
git reset --hard bd42b38f3627e6bca7274fb4d9af2e105f75da7c
echo "Reset to reference commit bd42b38f3627e6bca7274fb4d9af2e105f75da7c"
