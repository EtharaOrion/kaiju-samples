#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e b07d146bf8477ff83edcc1429ba720ad06943688^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/Zahgon/grpc-go b07d146bf8477ff83edcc1429ba720ad06943688
fi
git reset --hard b07d146bf8477ff83edcc1429ba720ad06943688
echo "Reset to reference commit b07d146bf8477ff83edcc1429ba720ad06943688"
