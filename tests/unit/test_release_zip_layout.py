"""Release zip must match HACS zip_release extract layout (flat archive root)."""

from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ZIP_NAME = "balansun-hacs.zip"
INTEGRATION_DIR = REPO_ROOT / "custom_components" / "balansun"


def test_release_zip_hacs_layout():
    """Build balansun-hacs.zip and verify HACS extract simulation."""
    zip_path = REPO_ROOT / ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()

    result = subprocess.run(
        ["./scripts/build-release.sh"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "OK: release zip layout valid" in result.stdout
    assert zip_path.is_file()


def test_nested_balansun_zip_rejected(tmp_path: Path):
    """Regression: balansun/ prefix in zip must fail (double-directory bug)."""
    bad_zip = tmp_path / "bad-nested.zip"
    manifest = INTEGRATION_DIR / "manifest.json"
    with zipfile.ZipFile(bad_zip, "w") as zf:
        zf.write(manifest, arcname="balansun/manifest.json")

    result = subprocess.run(
        ["./scripts/verify-release-zip.sh", str(bad_zip)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "must not nest balansun/" in (result.stderr or result.stdout)
