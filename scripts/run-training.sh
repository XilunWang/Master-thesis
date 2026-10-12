#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
action="${1:-status}"
session=uiis-training
mkdir -p reports work_dirs
case "$action" in
  status)
    screen -ls || true
    if test -f reports/training-exit-code.txt; then cat reports/training-exit-code.txt; fi
    if test -f reports/training-console.log; then tail -n 12 reports/training-console.log; fi
    exit 0 ;;
  first|resume|verify) ;;
  *) echo 'Usage: bash scripts/run-training.sh first|resume|verify|status' >&2; exit 2 ;;
esac
if screen -ls | grep -q "[.]${session}[[:space:]]"; then
  echo 'TRAINING_ALREADY_RUNNING: screen session exists' >&2
  exit 1
fi
if ! flock -n work_dirs/uiis-training.lock true; then
  echo 'TRAINING_ALREADY_RUNNING: project lock held' >&2
  exit 1
fi
# Worker owns redirection and records exit status even on a Python failure.
screen -dmS "$session" bash scripts/training-worker.sh "$action"
echo "BACKGROUND_REQUESTED: $action; verify reports/training-console.log and screen status"
