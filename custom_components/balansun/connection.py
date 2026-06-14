"""Router URL normalization and setup-time connection checks."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import aiohttp

_PUBLIC_TIMEOUT = aiohttp.ClientTimeout(total=8)


def normalize_host(url: str) -> str:
    """Strip whitespace/trailing slash; require http(s) scheme."""
    host = (url or "").strip().rstrip("/")
    if not host:
        raise ValueError("empty host")
    parsed = urlparse(host)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("host must start with http:// or https://")
    if not parsed.netloc:
        raise ValueError("host must include hostname")
    return host


def resolve_api_token(
    token_raw: Any,
    *,
    existing_token: str | None,
    reconfigure: bool,
) -> str | None:
    """On reconfigure, blank input keeps the stored token; otherwise strip or None."""
    if reconfigure and not (token_raw is not None and str(token_raw).strip()):
        stored = (existing_token or "").strip()
        return stored if stored else None
    if token_raw is None:
        return None
    stripped = str(token_raw).strip()
    return stripped if stripped else None


def scan_interval_seconds(entry_options: dict[str, Any]) -> int:
    """Clamp REST poll interval from config entry options."""
    from .const import (
        CONF_SCAN_INTERVAL,
        DEFAULT_SCAN_INTERVAL,
        MAX_SCAN_INTERVAL,
        MIN_SCAN_INTERVAL,
    )

    raw = entry_options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    try:
        seconds = int(raw)
    except (TypeError, ValueError):
        seconds = DEFAULT_SCAN_INTERVAL
    return max(MIN_SCAN_INTERVAL, min(MAX_SCAN_INTERVAL, seconds))


async def async_fetch_product_profile(
    session: aiohttp.ClientSession,
    host: str,
    token: str | None,
) -> str | None:
    """Read product_profile from /api/v1/device or action_node role from /api/v1/health."""
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        async with session.get(
            f"{host}/api/v1/health",
            headers=headers,
            timeout=_PUBLIC_TIMEOUT,
        ) as resp:
            if resp.status == 200:
                body = await resp.json()
                if isinstance(body, dict) and body.get("role") == "action_node":
                    return "action_node"
    except (aiohttp.ClientError, ValueError):
        pass
    try:
        async with session.get(
            f"{host}/api/v1/device",
            headers=headers,
            timeout=_PUBLIC_TIMEOUT,
        ) as resp:
            if resp.status != 200:
                return None
            body = await resp.json()
            if not isinstance(body, dict):
                return None
            caps = body.get("capabilities")
            if isinstance(caps, dict):
                profile = caps.get("product_profile")
                if isinstance(profile, str) and profile.strip():
                    return profile.strip()
    except (aiohttp.ClientError, ValueError):
        return None
    return None


async def async_validate_router(
    session: aiohttp.ClientSession,
    host: str,
    token: str | None,
) -> tuple[dict[str, Any] | None, str | None]:
    """GET /api/v1/public; return (body, error_key)."""
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        async with session.get(
            f"{host}/api/v1/public",
            headers=headers,
            timeout=_PUBLIC_TIMEOUT,
        ) as resp:
            if resp.status == 401:
                return None, "invalid_auth"
            if resp.status != 200:
                return None, "cannot_connect"
            body = await resp.json()
            return (body if isinstance(body, dict) else {}), None
    except (aiohttp.ClientError, ValueError):
        return None, "cannot_connect"
