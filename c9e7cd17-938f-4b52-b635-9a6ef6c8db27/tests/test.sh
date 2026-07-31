#!/bin/bash
# Harbor verifier for a commit0 Go task (runs inside the pre-built image).
# Scope: the official commit0 test-id set (line-separated full IDs of the form
# `<package_path>/<TestName>`). Writes reward.json (fraction of expected IDs
# that passed). Run command mirrors commit0's Go evaluator: `go test -json
# -count=1 ./...`. We parse the JSONL action events, attribute pass/fail per
# test ID, and intersect against the expected set.
set -uo pipefail
mkdir -p /logs/verifier
cd /testbed

go test -json -count=1 ./... \
  > /logs/verifier/go_test_events.jsonl 2>/logs/verifier/go_test_stderr.log || true

python3 - <<'PY'
import json, pathlib
events = []
log = pathlib.Path('/logs/verifier/go_test_events.jsonl')
if log.exists():
    for line in log.read_text(errors='replace').splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
expected = {l.strip() for l in pathlib.Path('/tests/test_ids.txt').read_text().splitlines() if l.strip()}
per_test = {}
for e in events:
    action = e.get('Action')
    if action not in ('pass', 'fail', 'skip'):
        continue
    test = e.get('Test'); pkg = e.get('Package', '')
    if not test:
        continue
    full = f"{pkg}/{test}"
    if full in expected:
        per_test[full] = action
    elif test in expected:
        per_test[test] = action
total = len(expected)
passed = sum(1 for tid in expected if per_test.get(tid) == 'pass')
reward = (passed / total) if total else 0.0
resolved = 1 if (total and passed == total) else 0
pathlib.Path('/logs/verifier/reward.json').write_text(
    json.dumps({"reward": reward, "resolved": resolved,
                "passed": passed, "total": total}))
PY
