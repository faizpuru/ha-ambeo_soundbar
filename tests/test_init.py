"""Tests for the Ambeo Soundbar integration setup."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ambeo_soundbar import async_unload_entry
from custom_components.ambeo_soundbar.api import (
    AmbeoConnectionError,
    AmbeoUnsupportedModelError,
)
from custom_components.ambeo_soundbar.const import CONFIG_HOST, DOMAIN


@pytest.mark.parametrize(
    ("error", "state"),
    [
        (AmbeoConnectionError("down"), ConfigEntryState.SETUP_RETRY),
        (
            AmbeoUnsupportedModelError("AMBEO Soundbar Ultra"),
            ConfigEntryState.SETUP_ERROR,
        ),
    ],
)
async def test_setup_entry_errors(hass, error, state):
    """Retry on connection errors, fail permanently on unsupported models."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONFIG_HOST: "192.168.1.100"})
    entry.add_to_hass(hass)
    with patch(
        "custom_components.ambeo_soundbar.AmbeoSoundbar.connect", side_effect=error
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert entry.state is state


@pytest.mark.parametrize("unloaded", [True, False])
async def test_unload_entry(hass, unloaded):
    """Stop the event listener only once the platforms are unloaded."""
    entry = MagicMock()
    entry.runtime_data.coordinator.async_stop = AsyncMock()
    with patch.object(
        hass.config_entries,
        "async_unload_platforms",
        AsyncMock(return_value=unloaded),
    ):
        assert await async_unload_entry(hass, entry) is unloaded
    assert entry.runtime_data.coordinator.async_stop.await_count == int(unloaded)
