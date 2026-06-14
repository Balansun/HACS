"""Optional integration tests against action-node mock or hardware."""

from __future__ import annotations

import asyncio
import os

import aiohttp
import pytest

pytestmark = pytest.mark.hardware


def _base_url() -> str | None:
    raw = os.environ.get("BALANSUN_ACTION_URL") or os.environ.get("BALANSUN_MOCK_URL")
    if not raw:
        return None
    return raw.rstrip("/")


def test_action_node_health_role() -> None:
    base_url = _base_url()
    assert base_url is not None

    async def run() -> None:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{base_url}/api/v1/health") as resp:
                assert resp.status == 200
                body = await resp.json()
        assert body.get("role") == "action_node"

    asyncio.run(run())


def test_action_node_timed_manual_expires() -> None:
    base_url = _base_url()
    assert base_url is not None

    async def run() -> None:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.put(
                f"{base_url}/api/v1/action/command",
                json={"pilot_wire_order": "eco", "duration_sec": 2},
            ) as resp:
                assert resp.status == 200
                body = await resp.json()
                assert body.get("control_mode") == "manual"
            await asyncio.sleep(3)
            async with session.get(f"{base_url}/api/v1/action/state") as resp:
                assert resp.status == 200
                body = await resp.json()
            assert body.get("control_mode") == "auto"

    asyncio.run(run())
