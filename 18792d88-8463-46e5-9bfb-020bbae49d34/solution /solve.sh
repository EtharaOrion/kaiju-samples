#!/bin/bash
# Oracle solution for the task. The image ships the repo at the BASE (stubbed)
# commit only; the reference (solved) commit is fetched from the fork by SHA, then the
# working tree is reset to it. Needs internet access (the task sets allow_internet=true).
set -euo pipefail
cd /testbed
if ! git cat-file -e 61e5a006156f6c95e9a3246715a135da93216342^{commit} 2>/dev/null; then
  # Fast path: fetch just the reference commit by SHA. Works on GitHub, which
  # enables uploadpack.allowReachableSHA1InWant by default.
  if ! git fetch --depth 1 https://github.com/Zahgon/graphql-jit 61e5a006156f6c95e9a3246715a135da93216342 2>/dev/null; then
    # Fallback for git hosts that do NOT advertise arbitrary SHAs in `want`
    # (allowReachableSHA1InWant off) — self-hosted mirrors etc. (C7-016). Fetch
    # the fork's branches/tags in full so the commit arrives via a reachable ref.
    echo "SHA fetch failed; falling back to full ref fetch from https://github.com/Zahgon/graphql-jit" >&2
    git fetch --tags https://github.com/Zahgon/graphql-jit '+refs/heads/*:refs/remotes/oracle/*'
  fi
fi
# Fail loud (set -e) if the commit is still absent after fetching.
git reset --hard 61e5a006156f6c95e9a3246715a135da93216342
echo "Reset to reference commit 61e5a006156f6c95e9a3246715a135da93216342"
