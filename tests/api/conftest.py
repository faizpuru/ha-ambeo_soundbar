"""Fixtures for the Ambeo API tests (no Home Assistant involved)."""

import re
from typing import Any

import aiohttp
import pytest
from aioresponses import aioresponses

HOST = "ambeo.test"
# aioresponses normalizes URLs: default port dropped, query params sorted.
BASE = f"http://{HOST}/api"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations():
    """Override the integration-level autouse fixture: no hass needed here."""


@pytest.fixture
def mock_http():
    """Mock aiohttp requests."""
    with aioresponses() as m:
        yield m


@pytest.fixture
async def session():
    """Return an aiohttp session."""
    async with aiohttp.ClientSession() as s:
        yield s


def url_for(function: str, path: str | None = None) -> re.Pattern:
    """Return a URL pattern matching a request to the device API."""
    pattern = f"^{re.escape(BASE)}/{re.escape(function)}\\?"
    if path is not None:
        pattern += f"(.*&)?path={re.escape(path)}(&|$)"
    return re.compile(pattern)


def mock_value(m: aioresponses, path: str, data_type: str, value: Any) -> None:
    """Mock a getData response for a path."""
    m.get(
        url_for("getData", path),
        payload={"value": {"type": data_type, data_type: value}},
        repeat=True,
    )


def mock_rows(m: aioresponses, path: str, rows: list[dict]) -> None:
    """Mock a getRows response for a path."""
    m.get(url_for("getRows", path), payload={"rows": rows}, repeat=True)


def mock_device_info(m: aioresponses, model: str) -> None:
    """Mock the device info paths."""
    mock_value(m, "settings:/system/productName", "string_", model)
    mock_value(m, "systemmanager:/deviceName", "string_", "Living room")
    mock_value(m, "settings:/system/serialNumber", "string_", "SN123")
    mock_value(m, "ui:settings/firmwareUpdate/currentVersion", "string_", "1.2.3")
