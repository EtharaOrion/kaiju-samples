#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e b6aa0421ec818a31c7f26ada8f6cef2558c768bf^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/Zahgon/Clarabel.rs b6aa0421ec818a31c7f26ada8f6cef2558c768bf
fi
git reset --hard b6aa0421ec818a31c7f26ada8f6cef2558c768bf
echo "Reset to reference commit b6aa0421ec818a31c7f26ada8f6cef2558c768bf"
