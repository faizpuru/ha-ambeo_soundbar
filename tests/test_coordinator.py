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
    AmbeoSoundbar,
    PlayerStatus,
    Preset,
    Source,
    StateKey,
)
from custom_components.ambeo_soundbar.coordinator import AmbeoCoordinator


@pytest.fixture
def api():
    """Return a mocked soundbar."""
    api = MagicMock(spec=AmbeoSoundbar)
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


@pytest.mark.parametrize(
    ("method", "api_method", "data_key"),
    [
        ("async_set_mute", "set_mute", "muted"),
        ("async_select_source", "set_source", "current_source"),
        ("async_select_sound_mode", "set_preset", "current_preset"),
        (
            "async_set_led_bar_brightness",
            "set_led_bar_brightness",
            "led_bar_brightness",
        ),
        (
            "async_set_codec_led_brightness",
            "set_codec_led_brightness",
            "codec_led_brightness",
        ),
        ("async_set_logo_brightness", "set_logo_brightness", "logo_brightness"),
        ("async_change_logo_state", "change_logo_state", "logo_state"),
        (
            "async_set_display_brightness",
            "set_display_brightness",
            "display_brightness",
        ),
        ("async_set_night_mode", "set_night_mode", "night_mode"),
        ("async_set_ambeo_mode", "set_ambeo_mode", "ambeo_mode"),
        ("async_set_sound_feedback", "set_sound_feedback", "sound_feedback"),
        ("async_set_voice_enhancement", "set_voice_enhancement", "voice_enhancement"),
        (
            "async_set_bluetooth_pairing_state",
            "set_bluetooth_pairing_state",
            "bluetooth_pairing",
        ),
        ("async_set_subwoofer_status", "set_subwoofer_status", "subwoofer_status"),
        ("async_set_subwoofer_volume", "set_subwoofer_volume", "subwoofer_volume"),
        (
            "async_set_voice_enhancement_level",
            "set_voice_enhancement_level",
            "voice_enhancement_level",
        ),
        (
            "async_set_center_speaker_level",
            "set_center_speaker_level",
            "center_speaker_level",
        ),
        ("async_set_side_firing_level", "set_side_firing_level", "side_firing_level"),
        ("async_set_up_firing_level", "set_up_firing_level", "up_firing_level"),
        ("async_set_center_volume", "set_center_volume", "center_volume"),
        ("async_set_ambeo_mode_level", "set_ambeo_mode_level", "ambeo_mode_level"),
    ],
)
async def test_setters(hass, api, method, api_method, data_key):
    """Call the matching API setter and apply an optimistic update."""
    coordinator = AmbeoCoordinator(hass, api)
    coordinator.data = {"volume": 10}
    await getattr(coordinator, method)(7)
    getattr(api, api_method).assert_awaited_once_with(7)
    assert coordinator.data[data_key] == 7
    assert coordinator.data["volume"] == 10


@pytest.mark.parametrize(
    ("method", "api_method"),
    [
        ("async_media_play", "play"),
        ("async_media_pause", "pause"),
        ("async_media_next_track", "next"),
        ("async_media_previous_track", "previous"),
        ("async_reboot", "reboot"),
    ],
)
async def test_commands(hass, api, method, api_method):
    """Forward commands without arguments to the API."""
    coordinator = AmbeoCoordinator(hass, api)
    await getattr(coordinator, method)()
    getattr(api, api_method).assert_awaited_once_with()


async def test_set_volume_and_power(hass, api):
    """Apply optimistic updates for volume and power commands."""
    coordinator = AmbeoCoordinator(hass, api)
    coordinator.data = {"muted": False}
    await coordinator.async_set_volume(12.0)
    api.set_volume.assert_awaited_once_with(12.0)
    assert coordinator.data["volume"] == 12
    await coordinator.async_turn_off()
    assert coordinator.data["state"] == "networkStandby"
    await coordinator.async_turn_on()
    assert coordinator.data["state"] == "online"


async def test_optimistic_update_without_data(hass, api):
    """Skip the optimistic update before the first refresh."""
    coordinator = AmbeoCoordinator(hass, api)
    await coordinator.async_set_night_mode(True)
    api.set_night_mode.assert_awaited_once_with(True)
    assert coordinator.data is None


async def test_reset_expert_settings_refreshes(hass, api):
    """Refresh the data after resetting the expert settings."""
    coordinator = AmbeoCoordinator(hass, api)
    coordinator.async_request_refresh = AsyncMock()
    await coordinator.async_reset_expert_settings()
    api.reset_expert_settings.assert_awaited_once_with()
    coordinator.async_request_refresh.assert_awaited_once()


async def test_event_listener_without_paths(hass, api):
    """Do not start the listener when nothing can be subscribed."""
    api.subscribed_paths = MagicMock(return_value=[])
    coordinator = AmbeoCoordinator(hass, api)
    await coordinator.async_start_event_listener()
    assert coordinator._event_listener_task is None
    await coordinator.async_stop()


async def test_event_listener_recovers(hass, api, monkeypatch):
    """Restart listening after an unexpected error."""
    monkeypatch.setattr(AmbeoCoordinator, "EVENT_LISTENER_RETRY_DELAY", 0)
    received = asyncio.Event()
    calls = 0

    async def listen(**kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("boom")
        yield {StateKey.VOLUME: 30}
        received.set()
        await asyncio.Event().wait()

    api.subscribed_paths = MagicMock(return_value=["player:volume"])
    api.listen = listen
    coordinator = AmbeoCoordinator(hass, api)
    coordinator.data = {"volume": 10}

    await coordinator.async_start_event_listener()
    await asyncio.wait_for(received.wait(), 1)
    await coordinator.async_stop()

    assert calls == 2
    assert coordinator.data["volume"] == 30


async def test_refresh_recovers(hass, api):
    """Mark the update as failed, then recover on the next refresh."""
    coordinator = AmbeoCoordinator(hass, api)
    api.fetch_state.side_effect = AmbeoConnectionError("down")
    await coordinator.async_refresh()
    assert coordinator.last_update_success is False
    api.fetch_state.side_effect = None
    await coordinator.async_refresh()
    assert coordinator.last_update_success is True
    assert coordinator.data == {"volume": 10}
