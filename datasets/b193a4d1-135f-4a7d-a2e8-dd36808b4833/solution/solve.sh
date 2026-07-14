#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e 15371d5a3a0ce19572d5a5a647a936eb190cac06^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/zahgon/little-raft 15371d5a3a0ce19572d5a5a647a936eb190cac06
fi
git reset --hard 15371d5a3a0ce19572d5a5a647a936eb190cac06
echo "Reset to reference commit 15371d5a3a0ce19572d5a5a647a936eb190cac06"
