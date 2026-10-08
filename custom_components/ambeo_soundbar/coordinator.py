"""Data update coordinator for Ambeo Soundbar integration."""

import asyncio
import contextlib
import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.media_player import MediaPlayerState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import AmbeoError, AmbeoSoundbar, PlayerStatus, StateKey
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_HA_STATE_BY_STATUS = {
    PlayerStatus.PLAYING: MediaPlayerState.PLAYING,
    PlayerStatus.PAUSED: MediaPlayerState.PAUSED,
    PlayerStatus.IDLE: MediaPlayerState.IDLE,
    PlayerStatus.ON: MediaPlayerState.ON,
    PlayerStatus.STANDBY: MediaPlayerState.OFF,
}


class AmbeoCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching Ambeo data."""

    # Event listener settings.
    POLL_TIMEOUT_MS = 30000
    EVENT_LISTENER_RETRY_DELAY = 30  # Seconds to wait before retrying after error.

    def __init__(
        self,
        hass: HomeAssistant,
        api: AmbeoSoundbar,
        update_interval_seconds: int = 30,
        concurrent_requests: int = 3,
    ):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval_seconds),
        )
        self.api = api
        self.sources = api.sources
        self.presets = api.presets
        self._event_listener_task: asyncio.Task | None = None
        self._concurrent_requests = concurrent_requests
        # Lookup dicts for O(1) source/preset resolution.
        self._source_title_by_id = {s.id: s.title for s in self.sources}
        self._source_id_by_title = {s.title: s.id for s in self.sources}
        self._preset_title_by_id = {p.id: p.title for p in self.presets}
        self._preset_id_by_title = {p.title: p.id for p in self.presets}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            data: dict[str, Any] = await self.api.fetch_state(self._concurrent_requests)
        except AmbeoError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        if StateKey.PLAY_TIME in data:
            data["play_time_updated_at"] = dt_util.utcnow()
        _LOGGER.debug("Data updated successfully: %s", data)
        return data

    async def async_start_event_listener(self) -> None:
        """Start the background event listener task."""
        if not self.api.subscribed_paths():
            return
        self._event_listener_task = self.hass.async_create_background_task(
            self._run_event_listener(),
            name=f"{DOMAIN}_event_listener",
        )

    async def async_stop(self) -> None:
        """Cancel the event listener background task."""
        if self._event_listener_task and not self._event_listener_task.done():
            self._event_listener_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._event_listener_task
        self._event_listener_task = None

    async def _run_event_listener(self) -> None:
        """Background task: apply state updates pushed by the device."""
        while True:
            try:
                async for updates in self.api.listen(
                    poll_timeout_ms=self.POLL_TIMEOUT_MS,
                    retry_delay=self.EVENT_LISTENER_RETRY_DELAY,
                ):
                    _LOGGER.debug("Event updates: %r", updates)
                    self._apply_event_updates(updates)
            except Exception as e:  # noqa: BLE001
                _LOGGER.debug(
                    "Event listener error: %s, retrying in %ds",
                    e,
                    self.EVENT_LISTENER_RETRY_DELAY,
                )
                await asyncio.sleep(self.EVENT_LISTENER_RETRY_DELAY)

    def _optimistic_update(self, key: str, value: Any):
        """Apply an optimistic state update and notify listeners."""
        if self.data:
            self.data[key] = value
            self.async_set_updated_data(self.data)

    async def _async_call(self, api_method: str, *args: Any) -> None:
        """Call an API command, converting API errors to HomeAssistantError."""
        try:
            await getattr(self.api, api_method)(*args)
        except AmbeoError as err:
            raise HomeAssistantError(f"Error calling {api_method}: {err}") from err

    async def _async_set(self, api_method: str, data_key: str, value: Any) -> None:
        """Call an API setter and apply an optimistic update."""
        await self._async_call(api_method, value)
        self._optimistic_update(data_key, value)

    def _apply_event_updates(self, updates: dict[str, Any]):
        """Apply event-driven updates with special handling for player keys."""
        if not self.data:
            return
        self.data.update(updates)
        if StateKey.PLAY_TIME in updates:
            self.data["play_time_updated_at"] = dt_util.utcnow()
        self.async_set_updated_data(self.data)

    async def async_set_volume(self, volume: float):
        """Set volume."""
        await self._async_call("set_volume", volume)
        self._optimistic_update("volume", int(volume))

    async def async_set_mute(self, mute: bool):
        """Set mute."""
        await self._async_set("set_mute", "muted", mute)

    async def async_turn_on(self):
        """Turn on."""
        await self._async_call("wake")
        self._optimistic_update("state", "online")

    async def async_turn_off(self):
        """Turn off."""
        await self._async_call("stand_by")
        self._optimistic_update("state", "networkStandby")

    async def async_select_source(self, source_id: str):
        """Select source."""
        await self._async_set("set_source", "current_source", source_id)

    async def async_select_sound_mode(self, preset_id: str):
        """Select sound mode."""
        await self._async_set("set_preset", "current_preset", preset_id)

    async def async_media_play(self):
        """Play."""
        await self._async_call("play")

    async def async_media_pause(self):
        """Pause."""
        await self._async_call("pause")

    async def async_media_next_track(self):
        """Next track."""
        await self._async_call("next")

    async def async_media_previous_track(self):
        """Previous track."""
        await self._async_call("previous")

    async def async_set_led_bar_brightness(self, brightness: int):
        """Set LED bar brightness."""
        await self._async_set(
            "set_led_bar_brightness", "led_bar_brightness", brightness
        )

    async def async_set_codec_led_brightness(self, brightness: int):
        """Set codec LED brightness."""
        await self._async_set(
            "set_codec_led_brightness", "codec_led_brightness", brightness
        )

    async def async_set_logo_brightness(self, brightness: int):
        """Set logo brightness."""
        await self._async_set("set_logo_brightness", "logo_brightness", brightness)

    async def async_change_logo_state(self, state: bool):
        """Change logo state."""
        await self._async_set("change_logo_state", "logo_state", state)

    async def async_set_display_brightness(self, brightness: int):
        """Set display brightness."""
        await self._async_set(
            "set_display_brightness", "display_brightness", brightness
        )

    async def async_set_night_mode(self, mode: bool):
        """Set night mode."""
        await self._async_set("set_night_mode", "night_mode", mode)

    async def async_set_ambeo_mode(self, mode: bool):
        """Set ambeo mode."""
        await self._async_set("set_ambeo_mode", "ambeo_mode", mode)

    async def async_set_sound_feedback(self, state: bool):
        """Set sound feedback."""
        await self._async_set("set_sound_feedback", "sound_feedback", state)

    async def async_set_voice_enhancement(self, mode: bool):
        """Set voice enhancement."""
        await self._async_set("set_voice_enhancement", "voice_enhancement", mode)

    async def async_set_bluetooth_pairing_state(self, state: bool):
        """Set bluetooth pairing state."""
        await self._async_set("set_bluetooth_pairing_state", "bluetooth_pairing", state)

    async def async_set_subwoofer_status(self, status: bool):
        """Set subwoofer status."""
        await self._async_set("set_subwoofer_status", "subwoofer_status", status)

    async def async_set_subwoofer_volume(self, volume: float):
        """Set subwoofer volume."""
        await self._async_set("set_subwoofer_volume", "subwoofer_volume", volume)

    async def async_set_voice_enhancement_level(self, level: int):
        """Set voice enhancement level."""
        await self._async_set(
            "set_voice_enhancement_level", "voice_enhancement_level", level
        )

    async def async_set_center_speaker_level(self, level: int):
        """Set center speaker level."""
        await self._async_set("set_center_speaker_level", "center_speaker_level", level)

    async def async_set_side_firing_level(self, level: int):
        """Set side firing level."""
        await self._async_set("set_side_firing_level", "side_firing_level", level)

    async def async_set_up_firing_level(self, level: int):
        """Set up firing level."""
        await self._async_set("set_up_firing_level", "up_firing_level", level)

    async def async_set_center_volume(self, volume: float):
        """Set center volume."""
        await self._async_set("set_center_volume", "center_volume", volume)

    async def async_set_ambeo_mode_level(self, level: int) -> None:
        """Set the Ambeo mode level."""
        await self._async_set("set_ambeo_mode_level", "ambeo_mode_level", level)

    async def async_reboot(self):
        """Reboot the device."""
        await self._async_call("reboot")
        # No state update needed for reboot.

    async def async_reset_expert_settings(self):
        """Reset expert settings."""
        await self._async_call("reset_expert_settings")
        # Trigger a full refresh to get reset values.
        await self.async_request_refresh()

    # Lookup helpers.
    def get_source_title(self, source_id) -> str | None:
        """Return the display title for a source ID."""
        return self._source_title_by_id.get(source_id)

    def get_source_id(self, title: str):
        """Return the source ID for a display title."""
        return self._source_id_by_title.get(title)

    def get_preset_title(self, preset_id) -> str | None:
        """Return the display title for a preset ID."""
        return self._preset_title_by_id.get(preset_id)

    def get_preset_id(self, title: str):
        """Return the preset ID for a display title."""
        return self._preset_id_by_title.get(title)

    # API wrapper methods.
    def has_capability(self, capability: str) -> bool:
        """Check if the device has a specific capability."""
        return self.api.has_capability(capability)

    def get_volume_step(self) -> float:
        """Get the volume step."""
        return self.api.get_volume_step()

    async def has_subwoofer(self) -> bool:
        """Check if device has a subwoofer."""
        return await self.api.has_subwoofer()

    def get_volume_max(self) -> int:
        """Get the maximum native volume value."""
        return self.api.get_volume_max()

    def get_state(self) -> str | None:
        """Return the effective HA state, accounting for eco mode and player state."""
        if not self.data:
            return None
        return _HA_STATE_BY_STATUS[self.api.player_status(self.data)]

    def get_subwoofer_min_value(self) -> int:
        """Get subwoofer minimum value."""
        return self.api.get_subwoofer_min_value()

    def get_subwoofer_max_value(self) -> int:
        """Get subwoofer maximum value."""
        return self.api.get_subwoofer_max_value()

    def get_led_bar_brightness_range(self):
        """Get the LED bar brightness range."""
        return self.api.get_led_bar_brightness_range()

    def get_codec_led_brightness_range(self):
        """Get the codec LED brightness range."""
        return self.api.get_codec_led_brightness_range()

    def get_logo_brightness_range(self):
        """Get the logo brightness range."""
        return self.api.get_logo_brightness_range()

    def get_display_brightness_range(self):
        """Get the display brightness range."""
        return self.api.get_display_brightness_range()
