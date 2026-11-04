"""Tests for the Ambeo Soundbar integration setup."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr
from pyambeo import (
    AmbeoConnectionError,
    AmbeoUnsupportedModelError,
    DeviceInfo,
    PlayerStatus,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ambeo_soundbar import async_unload_entry
from custom_components.ambeo_soundbar.const import (
    CONFIG_CONCURRENT_REQUESTS,
    CONFIG_HOST,
    CONFIG_UPDATE_INTERVAL,
    DOMAIN,
)


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


def _mock_api(serial="SN123456"):
    """Return a soundbar API mock with no optional capability."""
    api = MagicMock()
    api.info = DeviceInfo("AMBEO Soundbar Plus", "Living Room", serial, "1.0.134")
    api.sources = []
    api.presets = []
    api.fetch_state = AsyncMock(return_value={})
    api.subscribed_paths.return_value = []
    api.has_capability.return_value = False
    api.player_status.return_value = PlayerStatus.STANDBY
    api.get_volume_step.return_value = 0.01
    api.get_display_volume_max.return_value = 100
    return api


async def test_setup_and_reload_entry(hass):
    """Set up the entry, register the device and reload on option changes."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id="SN123456", data={CONFIG_HOST: "192.168.1.100"}
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.ambeo_soundbar.AmbeoSoundbar.connect",
        AsyncMock(return_value=_mock_api()),
    ) as connect:
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state is ConfigEntryState.LOADED

        device = dr.async_get(hass).async_get_device({(DOMAIN, "SN123456")})
        assert device.name == "Living Room"
        assert device.model == "AMBEO Soundbar Plus"
        assert device.sw_version == "1.0.134"
        assert hass.states.get("media_player.living_room") is not None

        hass.config_entries.async_update_entry(
            entry, options={CONFIG_UPDATE_INTERVAL: 20}
        )
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert connect.await_count == 2
    coordinator = entry.runtime_data.coordinator
    assert coordinator.update_interval == timedelta(seconds=20)


async def test_migrate_entry(hass):
    """Move the host to data and the polling settings to options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="SN123456",
        data={CONFIG_HOST: "192.168.1.100", CONFIG_UPDATE_INTERVAL: 10},
        options={CONFIG_HOST: "192.168.1.200", CONFIG_CONCURRENT_REQUESTS: 1},
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.ambeo_soundbar.AmbeoSoundbar.connect",
        AsyncMock(return_value=_mock_api()),
    ) as connect:
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert entry.minor_version == 2
    assert entry.data == {CONFIG_HOST: "192.168.1.200"}
    assert entry.options == {CONFIG_UPDATE_INTERVAL: 10, CONFIG_CONCURRENT_REQUESTS: 1}
    assert connect.await_args.args[0] == "192.168.1.200"


async def test_migrate_entry_from_future_version(hass):
    """Refuse to downgrade an entry created by a newer version."""
    entry = MockConfigEntry(
        domain=DOMAIN, version=2, data={CONFIG_HOST: "192.168.1.100"}
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.MIGRATION_ERROR


async def test_setup_entry_without_serial(hass):
    """Fall back to the entry ID when the soundbar reports no serial."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONFIG_HOST: "192.168.1.100"})
    entry.add_to_hass(hass)
    with patch(
        "custom_components.ambeo_soundbar.AmbeoSoundbar.connect",
        AsyncMock(return_value=_mock_api(serial=None)),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert dr.async_get(hass).async_get_device({(DOMAIN, entry.entry_id)})


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
