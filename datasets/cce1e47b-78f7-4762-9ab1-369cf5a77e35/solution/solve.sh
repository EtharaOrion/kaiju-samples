#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e dc9550b4b0d8bf409d025eba7e9b229b67af9401^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/Zahgon/jsonrpc dc9550b4b0d8bf409d025eba7e9b229b67af9401
fi
git reset --hard dc9550b4b0d8bf409d025eba7e9b229b67af9401
echo "Reset to reference commit dc9550b4b0d8bf409d025eba7e9b229b67af9401"
