"""Unit tests for BalansunWarmClimate live channel label."""

from __future__ import annotations

from unittest.mock import MagicMock

from tests.unit.balansun_import import load_action_node_climate, load_const

climate_mod = load_action_node_climate()
const = load_const()
BalansunWarmClimate = climate_mod.BalansunWarmClimate
CONF_HOST = const.CONF_HOST


def _warm_climate(channels: list[dict], channel_id: int = 0) -> BalansunWarmClimate:
    entry = MagicMock()
    entry.data = {CONF_HOST: "http://192.168.4.10"}
    entry.entry_id = "warm-entry"
    coordinator = MagicMock()
    coordinator.host = "http://192.168.4.10"
    coordinator.data = {"warm": {"channels": channels}}
    coordinator.warm_channels.return_value = channels
    return BalansunWarmClimate(entry, coordinator, channel_id)


def test_warm_climate_name_uses_live_channel_label() -> None:
    entity = _warm_climate([{"channel_id": 0, "label": "Salon", "enabled": True}])
    assert entity.name == "Salon"


def test_warm_climate_name_falls_back_when_label_missing() -> None:
    entity = _warm_climate([{"channel_id": 1, "enabled": True}], channel_id=1)
    assert entity.name == "Radiator 2"
