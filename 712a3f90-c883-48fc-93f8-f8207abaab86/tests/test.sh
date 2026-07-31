#!/bin/bash
# Harbor verifier for a commit0 Rust task (runs inside the pre-built image).
# Scope: the official commit0 test-id set (line-separated cargo test names of
# the form `<module_path>::<test_name>`). Writes reward.json (fraction of
# expected IDs that passed). Run command uses libtest's JSON formatter, which
# is unstable and requires `-Z unstable-options` under nightly. To stay on
# stable, we use `--format=pretty` and parse the standard `test <name> ... ok/FAILED`
# lines (cargo test's stable on-by-default format).
set -uo pipefail
mkdir -p /logs/verifier
cd /testbed

cargo test --no-fail-fast -- --format=pretty \
  > /logs/verifier/cargo_test.log 2>&1 || true

python3 - <<'PY'
import json, pathlib, re
log_path = pathlib.Path('/logs/verifier/cargo_test.log')
expected = {l.strip() for l in pathlib.Path('/tests/test_ids.txt').read_text().splitlines() if l.strip()}
results: dict[str, str] = {}
if log_path.exists():
    line_re = re.compile(r'^test (\S+) \.\.\. (ok|FAILED|ignored)\b')
    for line in log_path.read_text(errors='replace').splitlines():
        m = line_re.match(line)
        if not m:
            continue
        name, status = m.group(1), m.group(2)
        if name in expected:
            results[name] = status
total = len(expected)
passed = sum(1 for tid in expected if results.get(tid) == 'ok')
reward = (passed / total) if total else 0.0
resolved = 1 if (total and passed == total) else 0
pathlib.Path('/logs/verifier/reward.json').write_text(
    json.dumps({"reward": reward, "resolved": resolved,
                "passed": passed, "total": total}))
PY
