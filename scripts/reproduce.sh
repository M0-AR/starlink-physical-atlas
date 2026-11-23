#!/usr/bin/env bash
# Standalone reproduction entry point for environments without make.
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

run() {
    echo "+ $*"
    "$@"
}

run "$PYTHON" experiments/00_validate_sgp4.py
run "$PYTHON" experiments/01_anatomy.py
run "$PYTHON" experiments/02_service.py
run "$PYTHON" experiments/03_dynamics.py
run "$PYTHON" experiments/04_metrics.py
run "$PYTHON" experiments/05_figures.py
run "$PYTHON" experiments/06_claims.py
run "$PYTHON" -m atlas.paper
