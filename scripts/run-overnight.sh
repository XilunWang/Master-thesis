#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# This CPU-only supervisor runs inside its own detached screen session.
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
exec .venv/bin/python scripts/continue-overnight.py >> reports/overnight-console.log 2>&1
