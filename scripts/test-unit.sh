#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$(pwd)"
python3 -m compileall custom_components/balansun
python3 -m pytest tests/unit --confcutdir=tests/unit -q "$@"
