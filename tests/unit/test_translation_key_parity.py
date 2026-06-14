from __future__ import annotations

import json
from pathlib import Path


TRANSLATIONS_DIR = (
    Path(__file__).resolve().parents[2]
    / "custom_components"
    / "balansun"
    / "translations"
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _key_tree(obj: object) -> object:
    if isinstance(obj, dict):
        return {key: _key_tree(value) for key, value in obj.items()}
    return None


def test_en_and_fr_match_key_structure() -> None:
    en = _load_json(TRANSLATIONS_DIR / "en.json")
    fr = _load_json(TRANSLATIONS_DIR / "fr.json")

    assert _key_tree(fr) == _key_tree(en)
