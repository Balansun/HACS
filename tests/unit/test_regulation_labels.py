"""Unit tests for expert / status LED select label mapping."""

from tests.unit.balansun_import import load_module

labels = load_module("regulation_labels.py")


def test_expert_regulation_label_round_trip():
    assert labels.expert_regulation_label(0) == labels.EXPERT_REGULATION_LABEL_INTEGRAL
    assert labels.expert_regulation_label(1) == labels.EXPERT_REGULATION_LABEL_PID
    assert labels.expert_regulation_label(2) == labels.EXPERT_REGULATION_LABEL_PID
    assert labels.expert_regulation_label(None) == labels.EXPERT_REGULATION_LABEL_INTEGRAL
    assert (
        labels.expert_regulation_value(labels.EXPERT_REGULATION_LABEL_INTEGRAL) == 0
    )
    assert labels.expert_regulation_value(labels.EXPERT_REGULATION_LABEL_PID) == 1


def test_status_led_mode_labels():
    assert labels.status_led_mode_label("off") == "Off"
    assert labels.status_led_mode_api_value("Dual GPIO") == "dual_gpio"
    assert labels.status_led_mode_label("rgb_ws2812") == "RGB (WS2812)"
