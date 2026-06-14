#!/usr/bin/env python3
"""Fail if git tag version does not match custom_components/balansun/manifest.json."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "custom_components" / "balansun" / "manifest.json"
# Stable vX.Y.Z and CI nightly vX.Y.Z-nightly.<sha> (manifest patched at build time).
TAG_RE = re.compile(r"^v(?P<ver>\d+\.\d+\.\d+(?:[-+].*)?)$")


def tag_version() -> str:
    raw = (
        os.environ.get("RELEASE_TAG_NAME", "").strip()
        or os.environ.get("GITHUB_REF_NAME", "").strip()
    )
    if not raw:
        print("ERROR: set RELEASE_TAG_NAME or GITHUB_REF_NAME (e.g. v0.1.0)", file=sys.stderr)
        raise SystemExit(2)
    m = TAG_RE.match(raw)
    if not m:
        print(f"ERROR: tag {raw!r} is not vX.Y.Z", file=sys.stderr)
        raise SystemExit(1)
    return m.group("ver")


def manifest_version() -> str:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ver = data.get("version")
    if not isinstance(ver, str) or not ver:
        print("ERROR: manifest.json missing version", file=sys.stderr)
        raise SystemExit(1)
    return ver


def main() -> None:
    tag_ver = tag_version()
    man_ver = manifest_version()
    if tag_ver != man_ver:
        print(
            f"ERROR: tag version {tag_ver!r} != manifest.json version {man_ver!r}\n"
            "Bump custom_components/balansun/manifest.json before tagging.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    print(f"OK: release tag v{tag_ver} matches manifest.json")


if __name__ == "__main__":
    main()
