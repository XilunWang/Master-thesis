#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
action="$1"
exec >> reports/training-console.log 2>&1
echo "START $(date -Is) action=$action"
printf 'RUNNING %s\n' "$action" > reports/training-exit-code.txt
trap 'code=$?; printf "EXIT_CODE=%s action=%s\n" "$code" "$action" > reports/training-exit-code.txt; echo "END $(date -Is) exit=$code"' EXIT
if test "$action" = verify; then
  .venv/bin/python scripts/test-training-entry.py
else
  .venv/bin/python scripts/train-uiis.py --stage "$action" --work-dir work_dirs/uiis_baseline_r50_36e
fi
