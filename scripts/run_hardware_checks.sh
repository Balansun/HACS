#!/usr/bin/env bash
# HACS REST contract tests against a lab router (Path A — production firmware).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BASE="${BALANSUN_FIELD_URL:-${BALANSUN_HIL_URL:-}}"
if [[ -z "${BASE}" ]]; then
  echo "Set BALANSUN_FIELD_URL or BALANSUN_HIL_URL (e.g. http://192.168.2.159)" >&2
  exit 1
fi

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements-dev.txt
elif ! .venv/bin/python -c "import pytest" 2>/dev/null; then
  .venv/bin/pip install -q -r requirements-dev.txt
fi

export BALANSUN_FIELD_URL="${BALANSUN_FIELD_URL:-$BASE}"
export BALANSUN_HIL_URL="${BALANSUN_HIL_URL:-$BASE}"

# If PAT returns 401, tests fall back to BALANSUN_HIL_PASSWORD when set.
if [[ -z "${BALANSUN_API_BEARER_TOKEN:-}" && -z "${BALANSUN_HIL_PASSWORD:-}" ]]; then
  echo "Hint: set BALANSUN_API_BEARER_TOKEN and/or BALANSUN_HIL_PASSWORD" >&2
fi

echo "== HACS hardware REST (${BALANSUN_FIELD_URL}) =="
.venv/bin/pytest tests/test_hacs_rest_hardware.py -v -m hardware
echo "HACS hardware REST checks passed"
