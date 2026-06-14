"""Tests for scripts/hacs_version_resolve.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "hacs_version_resolve.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("hacs_version_resolve", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_prerelease_tag_string():
    mod = _load_module()
    tag = mod.prerelease_tag_string(sha="deadbeefcafebabe", base="0.1.0")
    assert tag == "v0.1.0-nightly.deadbee"


def test_prerelease_version_string():
    mod = _load_module()
    ver = mod.prerelease_version_string(sha="abc1234567890abcd", base="0.2.1")
    assert ver == "0.2.1-nightly.abc1234"


def test_verify_release_version_accepts_nightly_tag(tmp_path, monkeypatch):
    """Patched manifest must match vX.Y.Z-nightly.<sha> tag."""
    import subprocess

    manifest = REPO_ROOT / "custom_components" / "balansun" / "manifest.json"
    original = manifest.read_text(encoding="utf-8")
    tag = "v0.1.0-nightly.deadbee"
    ver = "0.1.0-nightly.deadbee"
    try:
        subprocess.run(
            [sys.executable, "scripts/set_manifest_version.py", ver],
            cwd=REPO_ROOT,
            check=True,
        )
        result = subprocess.run(
            [sys.executable, "scripts/verify_release_version.py"],
            cwd=REPO_ROOT,
            env={**dict(**__import__("os").environ), "RELEASE_TAG_NAME": tag},
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert "OK:" in result.stdout
    finally:
        manifest.write_text(original, encoding="utf-8")
