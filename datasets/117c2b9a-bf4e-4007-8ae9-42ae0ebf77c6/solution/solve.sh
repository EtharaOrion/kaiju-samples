#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e 74e2c4764dfa78cf43d27e26da495291958d32b7^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/Zahgon/luqum 74e2c4764dfa78cf43d27e26da495291958d32b7
fi
git reset --hard 74e2c4764dfa78cf43d27e26da495291958d32b7
echo "Reset to reference commit 74e2c4764dfa78cf43d27e26da495291958d32b7"
