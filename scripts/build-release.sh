#!/usr/bin/env bash
# Package custom_components/balansun for HACS zip_release (balansun-hacs.zip).
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${OUT:-balansun-hacs.zip}"
rm -f "$OUT"
(
  cd custom_components/balansun
  zip -r "../../$OUT" . -x '*__pycache__/*' -x '*.pyc' -x '*~'
)
echo "Wrote $OUT"
chmod +x scripts/verify-release-zip.sh
./scripts/verify-release-zip.sh "$OUT"
