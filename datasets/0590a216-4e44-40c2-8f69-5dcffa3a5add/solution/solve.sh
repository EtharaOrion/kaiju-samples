#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e a37e959793a6b7750c0e85a1bb70e632a57b4c75^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/Zahgon/mdns-sd a37e959793a6b7750c0e85a1bb70e632a57b4c75
fi
git reset --hard a37e959793a6b7750c0e85a1bb70e632a57b4c75
echo "Reset to reference commit a37e959793a6b7750c0e85a1bb70e632a57b4c75"
