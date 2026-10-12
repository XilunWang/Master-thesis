#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Reuse the image's large torch/CUDA packages without modifying its base environment.
# Reproduction requires Python 3.10, torch 2.1.2+cu121, torchvision 0.16.2+cu121.
export PIP_CACHE_DIR=/root/autodl-tmp/.cache/pip
/root/miniconda3/bin/python -m venv --system-site-packages .venv
.venv/bin/python -m pip install --only-binary=mmcv -r requirements.txt \
  -f https://download.openmmlab.com/mmcv/dist/cu121/torch2.1.0/index.html
mkdir -p reports
.venv/bin/python scripts/verify-env.py | tee reports/environment-check.txt
.venv/bin/python -m pip freeze > reports/environment-freeze.txt
