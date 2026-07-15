#!/bin/bash
# Oracle solution for a commit0 task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e f6218ffa05540438f6db71051fe0ee12bfd6489c^{commit} 2>/dev/null; then
  git fetch --depth 1 https://github.com/V1ibh1vsingh/signature_pad f6218ffa05540438f6db71051fe0ee12bfd6489c
fi
git reset --hard f6218ffa05540438f6db71051fe0ee12bfd6489c
echo "Reset to reference commit f6218ffa05540438f6db71051fe0ee12bfd6489c"
