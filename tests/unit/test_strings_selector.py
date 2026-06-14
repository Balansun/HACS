from __future__ import annotations

import json
from pathlib import Path

COMPONENT_DIR = Path(__file__).resolve().parents[2] / "custom_components" / "balansun"
SELECTOR_KEYS = ("rest_only", "companion")


def _load_json(name: str) -> dict:
    return json.loads((COMPONENT_DIR / name).read_text(encoding="utf-8"))


def test_integration_mode_selector_keys_present() -> None:
    for name in ("strings.json", "translations/en.json", "translations/fr.json"):
        data = _load_json(name)
        options = data["selector"]["integration_mode"]["options"]
        for key in SELECTOR_KEYS:
            assert key in options
            assert options[key].strip()
