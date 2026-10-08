"""Tests for the Ambeo Soundbar coordinator."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.media_player import MediaPlayerState
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.ambeo_soundbar.api import (
    AmbeoConnectionError,
    AmbeoResponseError,
    PlayerStatus,
    Preset,
    Source,
    StateKey,
)
from custom_components.ambeo_soundbar.coordinator import AmbeoCoordinator


@pytest.fixture
def api():
    """Return a mocked soundbar."""
    api = MagicMock()
    api.sources = [Source("hdmi1", "HDMI 1")]
    api.presets = [Preset(4, "Music")]
    api.fetch_state = AsyncMock(return_value={StateKey.VOLUME: 10})
    return api


async def test_update_data(hass, api):
    """Return the fetched state and pass the concurrency limit."""
    coordinator = AmbeoCoordinator(hass, api, concurrent_requests=5)
    data = await coordinator._async_update_data()
    assert data == {"volume": 10}
    api.fetch_state.assert_awaited_once_with(5)


async def test_update_data_play_time(hass, api):
    """Timestamp the play time."""
    api.fetch_state.return_value = {StateKey.PLAY_TIME: 1000}
    coordinator = AmbeoCoordinator(hass, api)
    data = await coordinator._async_update_data()
    assert "play_time_updated_at" in data


async def test_update_data_failure(hass, api):
    """Raise UpdateFailed on API errors."""
    api.fetch_state.side_effect = AmbeoConnectionError("down")
    coordinator = AmbeoCoordinator(hass, api)
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_lookups(hass, api):
    """Resolve source and preset titles and IDs."""
    coordinator = AmbeoCoordinator(hass, api)
    assert coordinator.get_source_title("hdmi1") == "HDMI 1"
    assert coordinator.get_source_id("HDMI 1") == "hdmi1"
    assert coordinator.get_preset_title(4) == "Music"
    assert coordinator.get_preset_id("Music") == 4
    assert coordinator.get_source_title("unknown") is None


async def test_get_state(hass, api):
    """Map the player status to a media player state."""
    api.player_status = MagicMock(return_value=PlayerStatus.STANDBY)
    coordinator = AmbeoCoordinator(hass, api)
    assert coordinator.get_state() is None
    coordinator.data = {"state": "networkStandby"}
    assert coordinator.get_state() == MediaPlayerState.OFF


async def test_event_listener_applies_updates(hass, api):
    """Apply updates pushed by the device to the coordinator data."""
    received = asyncio.Event()

    async def listen(**kwargs):
        yield {StateKey.VOLUME: 30, StateKey.PLAY_TIME: 5}
        received.set()
        await asyncio.Event().wait()

    api.subscribed_paths = MagicMock(return_value=["player:volume"])
    api.listen = listen
    coordinator = AmbeoCoordinator(hass, api)
    coordinator.data = {"volume": 10, "muted": False}

    await coordinator.async_start_event_listener()
    await asyncio.wait_for(received.wait(), 1)
    await coordinator.async_stop()

    assert coordinator.data["volume"] == 30
    assert coordinator.data["muted"] is False
    assert "play_time_updated_at" in coordinator.data


async def test_command_error(hass, api):
    """Raise HomeAssistantError and skip the optimistic update on API errors."""
    api.set_night_mode = AsyncMock(side_effect=AmbeoResponseError("HTTP 500", 500))
    coordinator = AmbeoCoordinator(hass, api)
    coordinator.data = {"night_mode": False}
    with pytest.raises(HomeAssistantError):
        await coordinator.async_set_night_mode(True)
    assert coordinator.data["night_mode"] is False


async def test_command_error_without_value(hass, api):
    """Raise HomeAssistantError for commands without arguments."""
    api.reboot = AsyncMock(side_effect=AmbeoConnectionError("down"))
    coordinator = AmbeoCoordinator(hass, api)
    with pytest.raises(HomeAssistantError):
        await coordinator.async_reboot()
