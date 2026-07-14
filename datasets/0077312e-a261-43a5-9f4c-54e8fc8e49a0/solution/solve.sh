#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e 0cba399419ac5bc738a2986874f7c5ee3b7b7e70^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/Zahgon/opentelemetry-collector 0cba399419ac5bc738a2986874f7c5ee3b7b7e70
fi
git reset --hard 0cba399419ac5bc738a2986874f7c5ee3b7b7e70
echo "Reset to reference commit 0cba399419ac5bc738a2986874f7c5ee3b7b7e70"
