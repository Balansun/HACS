# HACS — CI helpers

| Script | Purpose |
|--------|---------|
| [`ci_prerelease_tag.sh`](ci_prerelease_tag.sh) | Nightly tag from commit SHA (`scripts/hacs_version_resolve.py`). |
| [`release_notes_template.sh`](release_notes_template.sh) | GitHub Release body for stable and pre-releases. |

**Local nightly tag** (same format as GitHub Actions on `main`):

```bash
./.ci/ci_prerelease_tag.sh "$(git rev-parse HEAD)"
```

**Patch manifest + verify** (matches Release workflow build):

```bash
TAG="$(./.ci/ci_prerelease_tag.sh HEAD)"
export BALANSUN_HACS_VERSION="${TAG#v}"
python3 scripts/set_manifest_version.py
RELEASE_TAG_NAME="$TAG" python3 scripts/verify_release_version.py
./scripts/build-release.sh
```
