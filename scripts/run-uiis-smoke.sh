#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p reports work_dirs
run_dir="work_dirs/uiis_smoke_$(date +%Y%m%d_%H%M%S)"
printf '%s\n' "$run_dir" > reports/uiis-smoke-latest.txt
.venv/bin/python scripts/train-uiis-smoke.py --max-iters 50 --work-dir "$run_dir"
.venv/bin/python scripts/train-uiis-smoke.py --max-iters 100 --work-dir "$run_dir" --resume
printf 'UIIS_SMOKE_ALL_OK\n'
