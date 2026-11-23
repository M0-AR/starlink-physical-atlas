#!/usr/bin/env bash
# Verify the frozen data, generated artifacts, and test suite.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -n "${PYTHON:-}" ]]; then
    :
elif [[ -x .venv/bin/python ]]; then
    PYTHON=".venv/bin/python"
else
    PYTHON="python3"
fi

"$PYTHON" - "$ROOT" <<'PY'
import csv
import hashlib
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
manifest = json.loads((root / "data" / "manifest.json").read_text(encoding="utf-8"))

for rel, meta in manifest["files"].items():
    path = root / rel
    if not path.exists():
        raise SystemExit(f"missing frozen file: {rel}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != meta["sha256"]:
        raise SystemExit(f"checksum mismatch: {rel}\n  expected {meta['sha256']}\n  actual   {digest}")

readme = (root / "README.md").read_text(encoding="utf-8")
if "{{" in readme or "}}" in readme:
    raise SystemExit("README.md contains unresolved placeholders")
if "45-claim ledger" not in readme:
    raise SystemExit("README.md does not describe the claim ledger")

with (root / "results" / "claims.csv").open(newline="", encoding="utf-8") as fh:
    claims = list(csv.DictReader(fh))
if len(claims) != 45:
    raise SystemExit(f"expected 45 claims, found {len(claims)}")
if any(row["status"] in {"contradicted", "not_tested"} for row in claims):
    raise SystemExit("ledger contains contradicted or not-tested claims")

print(f"verified {len(manifest['files'])} frozen files, {len(claims)} claims, README render")
PY

"$PYTHON" -m pytest -q
