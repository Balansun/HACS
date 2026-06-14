"""Self-test safety lockout helpers (firmware /health parity)."""

from __future__ import annotations

from typing import Any

from .entity_registry import capability_enabled


def _health(data: dict[str, Any]) -> dict[str, Any]:
    h = data.get("health")
    return h if isinstance(h, dict) else {}


def _status(data: dict[str, Any]) -> dict[str, Any]:
    state = data.get("state")
    if not isinstance(state, dict):
        return {}
    status = state.get("status")
    return status if isinstance(status, dict) else {}


def _self_test(data: dict[str, Any]) -> dict[str, Any]:
    st = _health(data).get("self_test")
    return st if isinstance(st, dict) else {}


def safety_lockout_active(data: dict[str, Any]) -> bool:
    """True when firmware blocks routing writes due to commissioning self-test."""
    health = _health(data)
    lockout = health.get("safety_lockout")
    if isinstance(lockout, dict) and lockout.get("active") is True:
        return True
    st = _self_test(data)
    if st.get("safety_lockout_active") is True:
        return True
    suspend = health.get("output_suspend")
    if not isinstance(suspend, dict):
        suspend = _status(data).get("output_suspend")
    if isinstance(suspend, dict):
        reason = str(suspend.get("reason") or "")
        if suspend.get("active") is True and reason == "safety_lockout":
            return True
    return False


def safety_lockout_reasons(data: dict[str, Any]) -> list[str]:
    """Human-readable lockout reasons from health JSON."""
    health = _health(data)
    lockout = health.get("safety_lockout")
    if isinstance(lockout, dict):
        reasons = lockout.get("reasons")
        if isinstance(reasons, list) and reasons:
            return [str(r) for r in reasons if r]
    st = _self_test(data)
    reasons = st.get("safety_lockout_reasons")
    if isinstance(reasons, list) and reasons:
        return [str(r) for r in reasons if r]
    if safety_lockout_active(data):
        return ["safety_lockout"]
    return []


def routing_writes_blocked(data: dict[str, Any]) -> bool:
    """Routing mutators should be unavailable / rejected when True."""
    if safety_lockout_active(data):
        return True
    return not capability_enabled(data, "surplus_regulation")
