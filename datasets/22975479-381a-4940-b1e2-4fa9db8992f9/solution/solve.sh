#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e b8bc4e33eb23246566f08c9efd3916ebd41c1f3f^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/Zahgon/erg b8bc4e33eb23246566f08c9efd3916ebd41c1f3f
fi
git reset --hard b8bc4e33eb23246566f08c9efd3916ebd41c1f3f
echo "Reset to reference commit b8bc4e33eb23246566f08c9efd3916ebd41c1f3f"
