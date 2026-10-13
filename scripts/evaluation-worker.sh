#!/usr/bin/env bash
set -euo pipefail
cd /root/autodl-tmp/underwater-segmentation
mkdir -p reports/uiis-baseline-36e-evaluation
exec >> reports/uiis-baseline-36e-evaluation/console.log 2>&1
trap 'code=$?; echo "EXIT_CODE=$code" > reports/uiis-baseline-36e-evaluation/exit-code.txt' EXIT
echo RUNNING > reports/uiis-baseline-36e-evaluation/exit-code.txt
date -Is
.venv/bin/python scripts/evaluate-uiis.py
date -Is
