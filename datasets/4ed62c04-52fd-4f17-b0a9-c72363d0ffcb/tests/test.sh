#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
cd /testbed

REPORT_JSON=/logs/verifier/report.json
REPORT_TAP=/logs/verifier/report.tap
TEST_CMD_RAW="__TEST_CMD_PLACEHOLDER__"

if echo "$TEST_CMD_RAW" | grep -qE '(^| )(jest|vitest)( |$)'; then
    $TEST_CMD_RAW --json --outputFile="$REPORT_JSON" > /logs/verifier/test.log 2>&1 || true
elif echo "$TEST_CMD_RAW" | grep -qE '(^| )node( |$).* --test'; then
    $TEST_CMD_RAW --test-reporter=tap --test-reporter-destination="$REPORT_TAP" > /logs/verifier/test.log 2>&1 || true
else
    $TEST_CMD_RAW > /logs/verifier/test.log 2>&1 || true
fi

python3 - <<'PY'
import json, re, pathlib
expected = {l.strip() for l in pathlib.Path('/tests/test_ids.txt').read_text().splitlines() if l.strip()}
passed_names = set()

j = pathlib.Path('/logs/verifier/report.json')
if j.exists():
    try:
        rep = json.loads(j.read_text())
        for suite in rep.get('testResults', []):
            for a in suite.get('assertionResults', []):
                if a.get('status') == 'passed':
                    full = a.get('fullName') or a.get('title') or ''
                    passed_names.add(full)
    except Exception:
        pass

tap = pathlib.Path('/logs/verifier/report.tap')
if tap.exists():
    for line in tap.read_text(errors='replace').splitlines():
        m = re.match(r'^ok \d+ - (.+)$', line.strip())
        if m:
            passed_names.add(m.group(1).strip())

passed = 0
for tid in expected:
    bare = tid.split(' > ')[-1] if ' > ' in tid else tid
    if tid in passed_names or bare in passed_names:
        passed += 1

total = len(expected)
reward = (passed / total) if total else 0.0
resolved = 1 if (total and passed == total) else 0
pathlib.Path('/logs/verifier/reward.json').write_text(
    json.dumps({"reward": reward, "resolved": resolved,
                "passed": passed, "total": total}))
PY
