#!/bin/bash
# Oracle solution for the task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e e9ad559f8ba2cd192a1c6be2011f514dad46c3a2^{commit} 2>/dev/null; then
  # Fast path: fetch just the reference commit by SHA. Works on GitHub, which
  # enables uploadpack.allowReachableSHA1InWant by default.
  if ! git fetch --depth 1 https://github.com/Zahgon/etl-parser e9ad559f8ba2cd192a1c6be2011f514dad46c3a2 2>/dev/null; then
    # Fallback for git hosts that do NOT advertise arbitrary SHAs in `want`
    # (allowReachableSHA1InWant off) — self-hosted mirrors etc. (C7-016). Fetch
    # the fork's branches/tags in full so the commit arrives via a reachable ref.
    echo "SHA fetch failed; falling back to full ref fetch from https://github.com/Zahgon/etl-parser" >&2
    git fetch --tags https://github.com/Zahgon/etl-parser '+refs/heads/*:refs/remotes/oracle/*'
  fi
fi
# Fail loud (set -e) if the commit is still absent after fetching.
git reset --hard e9ad559f8ba2cd192a1c6be2011f514dad46c3a2
echo "Reset to reference commit e9ad559f8ba2cd192a1c6be2011f514dad46c3a2"
