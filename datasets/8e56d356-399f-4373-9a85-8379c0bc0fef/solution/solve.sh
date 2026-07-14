#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e e9ad559f8ba2cd192a1c6be2011f514dad46c3a2^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/Zahgon/etl-parser e9ad559f8ba2cd192a1c6be2011f514dad46c3a2
fi
git reset --hard e9ad559f8ba2cd192a1c6be2011f514dad46c3a2
echo "Reset to reference commit e9ad559f8ba2cd192a1c6be2011f514dad46c3a2"
