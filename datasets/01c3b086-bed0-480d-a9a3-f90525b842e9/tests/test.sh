#!/bin/bash
# Harbor verifier for a commit0 task (runs inside the pre-built ECR image).
# Scope: the official commit0 test-id set (parity with pipeline_results).
# Writes a continuous reward (fraction passed) to /logs/verifier/reward.json.
#
# Lineage-defensive: commit0 images come in two flavors — an ubuntu image with the repo
# venv at /testbed/.venv, and a python-slim image using system site-packages. We activate
# the venv if it exists, else fall back to system python. We run pytest IN PLACE on the
# agent-edited tree (NOT commit0's reset+/patch.diff model — Harbor agents edit in place).
set -uo pipefail
mkdir -p /logs/verifier
cd /testbed

if [ -f /testbed/.venv/bin/activate ]; then
  source /testbed/.venv/bin/activate
fi

# Ensure pytest-json-report is available (don't upgrade pinned pytest/pytest-asyncio).
python -m pip install --quiet --no-cache-dir pytest-json-report >/dev/null 2>&1 || true

TEST_IDS="$(tr '\n' ' ' < /tests/test_ids.txt)"

pytest $TEST_IDS \
  --json-report --json-report-file=/logs/verifier/pytest_report.json \
  --continue-on-collection-errors \
  >/logs/verifier/pytest.log 2>&1 || true

python - <<'PY'
import json, pathlib
reward, passed, total = 0.0, 0, 0
try:
    r = json.loads(pathlib.Path('/logs/verifier/pytest_report.json').read_text())
    s = r.get('summary', {})
    total = s.get('total') or s.get('collected') or 0
    passed = s.get('passed', 0)
    reward = (passed / total) if total else 0.0
except Exception:
    reward = 0.0
resolved = 1 if (total and passed == total) else 0
pathlib.Path('/logs/verifier/reward.json').write_text(
    json.dumps({"reward": reward, "resolved": resolved,
                "passed": passed, "total": total}))
PY
