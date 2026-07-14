#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e 6b05a1f4cb412d3cfb1d512f5c308588fd83ebe7^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/Zahgon/etherparse 6b05a1f4cb412d3cfb1d512f5c308588fd83ebe7
fi
git reset --hard 6b05a1f4cb412d3cfb1d512f5c308588fd83ebe7
echo "Reset to reference commit 6b05a1f4cb412d3cfb1d512f5c308588fd83ebe7"
