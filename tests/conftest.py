"""Fixtures for HACS REST hardware contract tests."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import aiohttp
import pytest


def _base_url() -> str | None:
    raw = os.environ.get("BALANSUN_FIELD_URL") or os.environ.get("BALANSUN_HIL_URL")
    if not raw:
        return None
    return raw.rstrip("/")


def pytest_collection_modifyitems(config, items):
    if _base_url() is None:
        skip = pytest.mark.skip(
            reason="Set BALANSUN_FIELD_URL or BALANSUN_HIL_URL for hardware tests"
        )
        for item in items:
            if "hardware" in item.keywords:
                item.add_marker(skip)


@pytest.fixture
def base_url() -> str:
    url = _base_url()
    assert url is not None
    return url


async def _login_with_password(base_url: str, password: str) -> dict[str, str]:
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            f"{base_url}/api/v1/auth/login",
            json={"password": password},
            headers={"Content-Type": "application/json"},
        ) as resp:
            resp.raise_for_status()
            body = await resp.json()
    login_token = body.get("token") if isinstance(body, dict) else None
    if not login_token:
        pytest.fail("auth/login did not return a token")
    return {"Authorization": f"Bearer {login_token}"}


@pytest.fixture
async def auth_headers(base_url: str) -> dict[str, str]:
    bearer = os.environ.get("BALANSUN_API_BEARER_TOKEN", "").strip()
    password = os.environ.get("BALANSUN_HIL_PASSWORD", "").strip()

    if bearer:
        headers = {"Authorization": f"Bearer {bearer}"}
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{base_url}/api/v1/health", headers=headers) as resp:
                if resp.status != 401:
                    return headers

    if password:
        return await _login_with_password(base_url, password)

    if bearer:
        pytest.fail("BALANSUN_API_BEARER_TOKEN rejected (401); set BALANSUN_HIL_PASSWORD")
    pytest.skip("Set BALANSUN_API_BEARER_TOKEN or BALANSUN_HIL_PASSWORD")


@pytest.fixture
async def rest_session(
    auth_headers: dict[str, str],
) -> AsyncIterator[aiohttp.ClientSession]:
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(headers=auth_headers, timeout=timeout) as session:
        yield session
