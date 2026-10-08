"""Tests for the Ambeo Soundbar diagnostics."""

import json
from unittest.mock import MagicMock

from homeassistant.components.diagnostics import REDACTED
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ambeo_soundbar import AmbeoData, AmbeoDevice
from custom_components.ambeo_soundbar.api import AmbeoPopcorn, StateKey
from custom_components.ambeo_soundbar.const import CONFIG_HOST, DOMAIN
from custom_components.ambeo_soundbar.coordinator import AmbeoCoordinator
from custom_components.ambeo_soundbar.diagnostics import (
    async_get_config_entry_diagnostics,
)


async def test_diagnostics(hass):
    """Redact private values and return serializable data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Living room",
        data={CONFIG_HOST: "192.168.1.100"},
        options={CONFIG_HOST: "192.168.1.101"},
        unique_id="SN123",
    )
    coordinator = MagicMock(spec=AmbeoCoordinator)
    coordinator.api = MagicMock(spec=AmbeoPopcorn)
    coordinator.api.capabilities = AmbeoPopcorn.capabilities
    coordinator.data = {StateKey.VOLUME: 20, StateKey.MUTED: False}
    device = AmbeoDevice(
        "SN123", "Living room", "Sennheiser", "AMBEO Soundbar Plus", "1.0", "h", 80
    )
    entry.runtime_data = AmbeoData(coordinator=coordinator, device=device)

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["device"]["serial"] == REDACTED
    assert diagnostics["device"]["host"] == REDACTED
    assert diagnostics["device"]["model"] == "AMBEO Soundbar Plus"
    assert diagnostics["config"]["data"][CONFIG_HOST] == REDACTED
    assert diagnostics["config"]["options"][CONFIG_HOST] == REDACTED
    features = diagnostics["capabilities"]["supported_features"]
    assert features == sorted(AmbeoPopcorn.capabilities)
    assert diagnostics["current_state"] == {"volume": 20, "muted": False}
    json.dumps(diagnostics)


async def test_diagnostics_without_data(hass):
    """Return an empty state before the first refresh."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONFIG_HOST: "192.168.1.100"})
    coordinator = MagicMock(spec=AmbeoCoordinator)
    coordinator.api = MagicMock(spec=AmbeoPopcorn)
    coordinator.api.capabilities = frozenset()
    coordinator.data = None
    device = AmbeoDevice("SN123", None, "Sennheiser", None, None, "h", 80)
    entry.runtime_data = AmbeoData(coordinator=coordinator, device=device)

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["current_state"] == {}
    assert diagnostics["capabilities"]["supported_features"] == []
