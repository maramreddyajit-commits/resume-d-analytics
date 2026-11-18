#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON_BIN="${PYTHON_BIN:-python}"
if [[ ! -f projects/churniq/data/raw.csv ]]; then "$PYTHON_BIN" scripts/download_telco.py; fi
if [[ ! -f projects/marketscope/data/retail.xlsx ]]; then "$PYTHON_BIN" scripts/download_retail.py; fi
make metrics PYTHON="$PYTHON_BIN"
make test PYTHON="$PYTHON_BIN"
