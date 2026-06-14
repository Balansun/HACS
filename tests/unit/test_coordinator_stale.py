"""Coordinator stale merge and entity default tests."""

from tests.unit.balansun_import import load_entity_registry

entity_registry = load_entity_registry()
read_binary_value = entity_registry.read_binary_value


def test_vacation_missing_config_is_none():
    assert read_binary_value({"config": {}}, "vacation") is None


def test_vacation_false_when_disabled():
    assert read_binary_value({"config": {"vacation_enabled": False}}, "vacation") is False


def test_vacation_true_when_enabled():
    assert read_binary_value({"config": {"vacation_enabled": True}}, "vacation") is True


def _section_or_prior(new, prior, key):
    """Mirror BalansunCoordinator._section_or_prior (host-testable)."""
    if isinstance(new, dict) and new:
        return new
    old = prior.get(key)
    return old if isinstance(old, dict) else {}


def test_section_or_prior_keeps_snapshot():
    prior = {"snapshot": {"house_net_power_w": 1200}}
    assert _section_or_prior(None, prior, "snapshot") == {"house_net_power_w": 1200}


def test_section_or_prior_uses_new_when_present():
    prior = {"snapshot": {"house_net_power_w": 1200}}
    assert _section_or_prior({"house_net_power_w": 99}, prior, "snapshot") == {
        "house_net_power_w": 99
    }
