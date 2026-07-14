#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e cc84ed92279a652b0e28ec90940fc0e1dd388492^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/Zahgon/pipefunc cc84ed92279a652b0e28ec90940fc0e1dd388492
fi
git reset --hard cc84ed92279a652b0e28ec90940fc0e1dd388492
echo "Reset to reference commit cc84ed92279a652b0e28ec90940fc0e1dd388492"
