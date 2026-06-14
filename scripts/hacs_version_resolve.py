#!/usr/bin/env python3
"""Resolve HACS integration version strings and CI nightly pre-release tags.

Nightly tags: ``v0.1.0-nightly.abc1234`` (base from manifest.json + 7-char SHA).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "custom_components" / "balansun" / "manifest.json"
NIGHTLY_SLUG = "nightly"


def read_base_version() -> str | None:
    if not MANIFEST.is_file():
        return None
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ver = data.get("version")
    if not isinstance(ver, str) or not ver.strip():
        return None
    raw = ver.strip()
    # Strip any existing prerelease suffix on main (committed base is X.Y.Z).
    m = re.match(r"^(\d+\.\d+\.\d+)", raw)
    return m.group(1) if m else raw


def git_short_sha(sha: str | None) -> str | None:
    ref = (sha or os.environ.get("GITHUB_SHA") or "").strip()
    if not ref:
        return None
    if re.fullmatch(r"[0-9a-fA-F]{7,40}", ref):
        return ref[:7].lower()
    try:
        out = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--short=7", ref],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return out.strip().lower() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def prerelease_version_string(*, sha: str | None = None, base: str | None = None) -> str | None:
    """``0.1.0-nightly.abc1234`` — None if base or sha missing."""
    base_ver = (base or read_base_version() or "").strip()
    short = git_short_sha(sha)
    if not base_ver or not short:
        return None
    return f"{base_ver}-{NIGHTLY_SLUG}.{short}"


def prerelease_tag_string(*, sha: str | None = None, base: str | None = None) -> str | None:
    ver = prerelease_version_string(sha=sha, base=base)
    return f"v{ver}" if ver else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prerelease-tag", action="store_true", help="Print vX.Y.Z-nightly.<sha>")
    parser.add_argument("--prerelease", action="store_true", help="Print X.Y.Z-nightly.<sha>")
    parser.add_argument("sha", nargs="?", help="Commit SHA (default: GITHUB_SHA)")
    parser.add_argument("--base", help="Override base semver (default: manifest.json)")
    args = parser.parse_args()

    if args.prerelease_tag:
        tag = prerelease_tag_string(sha=args.sha, base=args.base)
        if not tag:
            print("hacs_version_resolve: cannot compute pre-release tag", file=sys.stderr)
            raise SystemExit(1)
        print(tag)
        return

    if args.prerelease:
        ver = prerelease_version_string(sha=args.sha, base=args.base)
        if not ver:
            print("hacs_version_resolve: cannot compute pre-release version", file=sys.stderr)
            raise SystemExit(1)
        print(ver)
        return

    base = read_base_version()
    if not base:
        print("hacs_version_resolve: manifest.json missing version", file=sys.stderr)
        raise SystemExit(1)
    print(base)


if __name__ == "__main__":
    main()
