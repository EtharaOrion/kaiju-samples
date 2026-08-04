#!/bin/bash
# Harbor verifier for a kaiju TypeScript task (runs inside the pre-built image).
# Scope: the official test-id set (line-separated ids of the form
# `<relative_spec_file> > <jest fullName>`). Runs the repo's jest suite with the
# machine-readable --json reporter and scores reward.json as the fraction of
# expected IDs that passed — same philosophy as the Go/Rust verifiers.
set -uo pipefail
mkdir -p /logs/verifier
cd /testbed

npx jest --json --outputFile=/logs/verifier/jest_report.json --ci \
  > /logs/verifier/jest.log 2>&1 || true

python3 - <<'PY'
import json, os, pathlib
expected = {l.strip() for l in pathlib.Path('/tests/test_ids.txt').read_text().splitlines() if l.strip()}
results: dict[str, str] = {}
try:
    r = json.loads(pathlib.Path('/logs/verifier/jest_report.json').read_text())
    for tr in r.get('testResults', []):
        f = tr.get('testFilePath') or tr.get('name') or ''
        rel = os.path.relpath(f, '/testbed') if f else ''
        for ar in tr.get('assertionResults', []) or tr.get('testResults', []):
            full = ar.get('fullName') or ' '.join(
                (ar.get('ancestorTitles') or []) + [ar.get('title') or ''])
            tid = f"{rel} > {full}".strip()
            if tid in expected:
                results[tid] = ar.get('status', '')
except Exception:
    pass
total = len(expected)
passed = sum(1 for tid in expected if results.get(tid) == 'passed')
reward = (passed / total) if total else 0.0
resolved = 1 if (total and passed == total) else 0
pathlib.Path('/logs/verifier/reward.json').write_text(
    json.dumps({"reward": reward, "resolved": resolved,
                "passed": passed, "total": total}))
PY
