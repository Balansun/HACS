#!/usr/bin/env python3
"""Set manifest.json version for CI release builds (does not commit)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "custom_components" / "balansun" / "manifest.json"


def main() -> None:
    ver = (sys.argv[1] if len(sys.argv) > 1 else "").strip() or os.environ.get(
        "BALANSUN_HACS_VERSION", ""
    ).strip()
    if not ver:
        print("ERROR: pass version argument or set BALANSUN_HACS_VERSION", file=sys.stderr)
        raise SystemExit(2)

    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data["version"] = ver
    MANIFEST.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"OK: manifest.json version={ver}")


if __name__ == "__main__":
    main()
