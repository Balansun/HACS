#!/usr/bin/env sh
# HACS integration release notes (prepend to GitHub Release body).
# Usage: ./.ci/release_notes_template.sh [TAG]
set -eu
TAG="${1:-}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CHANGELOG="${REPO_ROOT}/CHANGELOG.md"

cat <<'EOF'
## Upgrade notes

- **Home Assistant:** Requires **2026.3.0** or newer (`hacs.json`, `manifest.json`).
- **Firmware:** Full REST parity needs Balansun firmware with `GET /api/v1/telemetry/snapshot` and `POST /api/v1/triac/override` (see [MQTT/REST parity](https://balansun.clouded.fr/en/integrations/home-assistant/mqtt-rest-parity/)).
- **Integration mode:** Default **`rest_only`** (full REST entity set). **`companion`** when MQTT discovery is active: HACS adds action buttons only (**Republish MQTT discovery**, **Run self-test**, **Reboot device**) — no duplicate sensors.
- **Reload:** After upgrade, restart Home Assistant or reload the Balansun integration.

## Install

- HACS custom repository: `https://github.com/Balansun/HACS` (category **Integration**).
- When `zip_release` is enabled, pick this **release** version in HACS (not the default branch).

EOF

echo ""
echo "## Changes"
echo ""

extract_changelog_section() {
  heading="$1"
  [ -f "$CHANGELOG" ] || return 1
  awk -v heading="$heading" '
    $0 == heading { found=1; next }
    found && /^## / { exit }
    found { print }
  ' "$CHANGELOG"
}

if [ -n "$TAG" ]; then
  if extract_changelog_section "## [Unreleased]" | grep -q .; then
    extract_changelog_section "## [Unreleased]"
  elif git -C "$REPO_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    PREV_TAG="$(git -C "$REPO_ROOT" describe --tags --abbrev=0 "${TAG}^" 2>/dev/null || true)"
    if [ -n "$PREV_TAG" ]; then
      git -C "$REPO_ROOT" log --pretty='- %s' "${PREV_TAG}..${TAG}" || true
    else
      git -C "$REPO_ROOT" log --pretty='- %s' -30 "${TAG}" || true
    fi
  fi
else
  echo "- (no tag specified)"
fi

if [ -n "$TAG" ]; then
  echo ""
  echo "Tag: \`$TAG\`"
  case "$TAG" in
    *-*)
      echo ""
      echo "Published as a **GitHub prerelease** (tag contains a hyphen after the version core)."
      ;;
  esac
fi
