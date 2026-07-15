#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e 609a5b2011b25bcba177a0132865f2bb49e369d3^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/Zahgon/refactor 609a5b2011b25bcba177a0132865f2bb49e369d3
fi
git reset --hard 609a5b2011b25bcba177a0132865f2bb49e369d3
echo "Reset to reference commit 609a5b2011b25bcba177a0132865f2bb49e369d3"
