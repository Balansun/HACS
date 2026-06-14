#!/usr/bin/env bash
# Verify balansun-hacs.zip matches HACS zip_release extract layout.
# HACS runs ZipFile.extractall(config/custom_components/balansun/) — archive
# entries must be integration files at the root, not under balansun/.
set -euo pipefail

ZIP="${1:-balansun-hacs.zip}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ ! -f "$ZIP" ]]; then
  echo "ERROR: zip not found: $ZIP" >&2
  exit 1
fi

if ! command -v unzip >/dev/null 2>&1; then
  echo "ERROR: unzip required" >&2
  exit 1
fi

zip_list="$(unzip -l "$ZIP")"

case "$zip_list" in
  *balansun/manifest.json*)
    echo "ERROR: zip must not nest balansun/ (causes balansun/balansun/ on install)" >&2
    exit 1
    ;;
esac

case "$zip_list" in
  *custom_components/*)
    echo "ERROR: zip must not include custom_components/ prefix" >&2
    exit 1
    ;;
esac

case "$zip_list" in
  *" manifest.json"*) ;;
  *)
    echo "ERROR: zip missing manifest.json at archive root" >&2
    exit 1
    ;;
esac

case "$zip_list" in
  *" __init__.py"*) ;;
  *)
    echo "ERROR: zip missing __init__.py at archive root" >&2
    exit 1
    ;;
esac

case "$zip_list" in
  *brand/icon.png*) ;;
  *)
    echo "ERROR: zip missing brand/icon.png" >&2
    exit 1
    ;;
esac

case "$zip_list" in
  *__pycache__*)
    echo "ERROR: zip contains __pycache__" >&2
    exit 1
    ;;
esac

# Simulate HACS extractall into config/custom_components/balansun/
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
install_dir="$tmpdir/custom_components/balansun"
mkdir -p "$install_dir"
unzip -q "$ZIP" -d "$install_dir"

if [[ ! -f "$install_dir/manifest.json" ]]; then
  echo "ERROR: after extract, manifest.json missing at custom_components/balansun/" >&2
  exit 1
fi

if [[ -f "$install_dir/balansun/manifest.json" ]]; then
  echo "ERROR: after extract, nested balansun/balansun/manifest.json detected" >&2
  exit 1
fi

if [[ ! -f "$install_dir/__init__.py" ]]; then
  echo "ERROR: after extract, __init__.py missing at custom_components/balansun/" >&2
  exit 1
fi

echo "OK: release zip layout valid ($ZIP)"
