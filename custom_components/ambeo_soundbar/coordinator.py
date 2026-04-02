"""Data update coordinator for Ambeo Soundbar integration."""

import asyncio
import logging
from collections.abc import Callable
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api.const import Capability
from .api.impl.generic_api import AmbeoApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class AmbeoCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching Ambeo data."""

    TRACK_CHANGE_DELAY = 1
    SOURCE_CHANGE_DELAY = 1
    BLUETOOTH_SWITCH_DELAY = 1
    END_OF_TRACK_BUFFER = 2  # Seconds after expected track end to refresh.

    def __init__(
        self,
        hass: HomeAssistant,
        api: AmbeoApi,
        sources: list,
        presets: list,
        update_interval_seconds: int = 10,
    ):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval_seconds),
        )
        self.api = api
        self.sources = sources
        self.presets = presets
        self._end_of_track_unsub: Callable[[], None] | None = None

    async def _safe_fetch(self, coro, label: str):
        """Fetch data safely, returning None on failure."""
        try:
            return await coro
        except Exception as e:
            _LOGGER.debug("%s not available: %s", label, e)
            return None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            # Core media player data (required).
            (
                volume,
                muted,
                state,
                current_source,
                current_preset,
                player_data,
            ) = await asyncio.gather(
                self.api.get_volume(),
                self.api.is_mute(),
                self.api.get_state(),
                self.api.get_current_source(),
                self.api.get_current_preset(),
                self.api.player_data(),
            )
            data = {
                "volume": volume,
                "muted": muted,
                "state": state,
                "current_source": current_source,
                "current_preset": current_preset,
                "player_data": player_data,
            }

            # Optional features fetched in parallel, filtered by capability.
            # Tuples: (data_key, api_method_name, label, required_capability or None).
            all_optional_features = [
                ("play_time", "get_play_time", "Play time", None),
                (
                    "led_bar_brightness",
                    "get_led_bar_brightness",
                    "LED bar",
                    Capability.LED_BAR,
                ),
                (
                    "codec_led_brightness",
                    "get_codec_led_brightness",
                    "Codec LED",
                    Capability.CODEC_LED,
                ),
                (
                    "logo_brightness",
                    "get_logo_brightness",
                    "Logo brightness",
                    Capability.AMBEO_LOGO,
                ),
                ("logo_state", "get_logo_state", "Logo state", Capability.AMBEO_LOGO),
                (
                    "display_brightness",
                    "get_display_brightness",
                    "Display",
                    Capability.MAX_DISPLAY,
                ),
                ("night_mode", "get_night_mode", "Night mode", None),
                ("ambeo_mode", "get_ambeo_mode", "Ambeo mode", None),
                ("sound_feedback", "get_sound_feedback", "Sound feedback", None),
                (
                    "voice_enhancement",
                    "get_voice_enhancement",
                    "Voice enhancement",
                    Capability.VOICE_ENHANCEMENT_TOGGLE,
                ),
                (
                    "bluetooth_pairing",
                    "get_bluetooth_pairing_state",
                    "Bluetooth pairing",
                    Capability.BLUETOOTH_PAIRING,
                ),
                (
                    "subwoofer_status",
                    "get_subwoofer_status",
                    "Subwoofer status",
                    Capability.SUBWOOFER,
                ),
                (
                    "subwoofer_volume",
                    "get_subwoofer_volume",
                    "Subwoofer volume",
                    Capability.SUBWOOFER,
                ),
                (
                    "voice_enhancement_level",
                    "get_voice_enhancement_level",
                    "Voice enhancement level",
                    Capability.VOICE_ENHANCEMENT_LEVEL,
                ),
                (
                    "center_speaker_level",
                    "get_center_speaker_level",
                    "Center speaker level",
                    Capability.CENTER_SPEAKER_LEVEL,
                ),
                (
                    "side_firing_level",
                    "get_side_firing_level",
                    "Side firing level",
                    Capability.SIDE_FIRING_LEVEL,
                ),
                (
                    "up_firing_level",
                    "get_up_firing_level",
                    "Up firing level",
                    Capability.UP_FIRING_LEVEL,
                ),
                ("eco_mode", "get_eco_mode", "Eco mode", Capability.ECO_MODE),
            ]

            optional_features = [
                (key, method, label)
                for key, method, label, cap in all_optional_features
                if cap is None or self.api.has_capability(cap)
            ]

            results = await asyncio.gather(
                *(
                    self._safe_fetch(getattr(self.api, method)(), label)
                    for _, method, label in optional_features
                )
            )

            for (key, _, _), value in zip(optional_features, results, strict=True):
                if value is not None:
                    data[key] = value

            if "play_time" in data:
                data["play_time_updated_at"] = dt_util.utcnow()

            _LOGGER.debug("Data updated successfully: %s", data)
            self._schedule_end_of_track_refresh(data)
            return data

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    def _schedule_end_of_track_refresh(self, data: dict[str, Any]):
        """Schedule a refresh when the current track is about to end."""
        # Cancel any previously scheduled refresh.
        if self._end_of_track_unsub:
            self._end_of_track_unsub()
            self._end_of_track_unsub = None

        player_data = data.get("player_data", {})
        if not player_data or player_data.get("state") != "playing":
            return

        play_time = data.get("play_time")
        duration = (player_data.get("status") or {}).get("duration")

        if not play_time or not duration or duration <= 0:
            return

        remaining_s = (duration - play_time) / 1000
        if remaining_s <= 0:
            return

        delay = remaining_s + self.END_OF_TRACK_BUFFER
        _LOGGER.debug("Scheduling end-of-track refresh in %.1fs", delay)

        @callback
        def _on_track_end(_now):
            """Trigger a refresh when the track should have ended."""
            self._end_of_track_unsub = None
            self.async_set_updated_data(self.data)
            self.hass.async_create_task(self.async_request_refresh())

        self._end_of_track_unsub = async_call_later(self.hass, delay, _on_track_end)

    def _optimistic_update(self, key: str, value: Any):
        """Apply an optimistic state update and notify listeners."""
        if self.data:
            self.data[key] = value
            self.async_set_updated_data(self.data)

    async def _refresh_player_data(self, context: str, preserve_state: bool = True):
        """Refresh player data and play time from the API.

        If preserve_state is True, keep the current play state when it is "playing"
        (useful for track changes). Set to False for source changes where the new
        source may have a different state.
        """
        if not self.data:
            return
        try:
            player_data, play_time = await asyncio.gather(
                self.api.player_data(),
                self._safe_fetch(self.api.get_play_time(), "Play time"),
            )
            if player_data:
                if preserve_state:
                    current_state = self.data.get("player_data", {}).get("state")
                    self.data["player_data"] = player_data
                    if current_state == "playing":
                        self.data["player_data"]["state"] = "playing"
                else:
                    self.data["player_data"] = player_data
            if play_time is not None:
                self.data["play_time"] = play_time
                self.data["play_time_updated_at"] = dt_util.utcnow()
            self.async_set_updated_data(self.data)
        except Exception as e:
            _LOGGER.debug("Failed to refresh player data after %s: %s", context, e)

    async def async_set_volume(self, volume: float):
        """Set volume."""
        await self.api.set_volume(volume)
        self._optimistic_update("volume", int(volume))

    async def async_set_mute(self, mute: bool):
        """Set mute."""
        await self.api.set_mute(mute)
        self._optimistic_update("muted", mute)

    async def async_turn_on(self):
        """Turn on."""
        await self.api.wake()
        self._optimistic_update("state", "online")

    async def async_turn_off(self):
        """Turn off."""
        await self.api.stand_by()
        self._optimistic_update("state", "networkStandby")

    async def async_select_source(self, source_id: str):
        """Select source."""
        await self.api.set_source(source_id)
        await asyncio.sleep(self.SOURCE_CHANGE_DELAY)
        self._optimistic_update("current_source", source_id)
        await self._refresh_player_data("source change", preserve_state=False)

    async def async_select_sound_mode(self, preset_id: str):
        """Select sound mode."""
        await self.api.set_preset(preset_id)
        self._optimistic_update("current_preset", preset_id)

    async def async_media_play(self):
        """Play."""
        await self.api.play()
        if self.data and "player_data" in self.data:
            self.data["player_data"]["state"] = "playing"
            self.async_set_updated_data(self.data)

    async def async_media_pause(self):
        """Pause."""
        await self.api.pause()
        if self.data and "player_data" in self.data:
            self.data["player_data"]["state"] = "paused"
            self.async_set_updated_data(self.data)

    async def async_media_next_track(self):
        """Next track."""
        await self.api.next()
        await asyncio.sleep(self.TRACK_CHANGE_DELAY)
        await self._refresh_player_data("next track")

    async def async_media_previous_track(self):
        """Previous track."""
        await self.api.previous()
        await asyncio.sleep(self.TRACK_CHANGE_DELAY)
        await self._refresh_player_data("previous track")

    async def async_set_led_bar_brightness(self, brightness: int):
        """Set LED bar brightness."""
        await self.api.set_led_bar_brightness(brightness)
        self._optimistic_update("led_bar_brightness", brightness)

    async def async_set_codec_led_brightness(self, brightness: int):
        """Set codec LED brightness."""
        await self.api.set_codec_led_brightness(brightness)
        self._optimistic_update("codec_led_brightness", brightness)

    async def async_set_logo_brightness(self, brightness: int):
        """Set logo brightness."""
        await self.api.set_logo_brightness(brightness)
        self._optimistic_update("logo_brightness", brightness)

    async def async_change_logo_state(self, state: bool):
        """Change logo state."""
        await self.api.change_logo_state(state)
        self._optimistic_update("logo_state", state)

    async def async_set_display_brightness(self, brightness: int):
        """Set display brightness."""
        await self.api.set_display_brightness(brightness)
        self._optimistic_update("display_brightness", brightness)

    async def async_set_night_mode(self, mode: bool):
        """Set night mode."""
        await self.api.set_night_mode(mode)
        self._optimistic_update("night_mode", mode)

    async def async_set_ambeo_mode(self, mode: bool):
        """Set ambeo mode."""
        await self.api.set_ambeo_mode(mode)
        self._optimistic_update("ambeo_mode", mode)

    async def async_set_sound_feedback(self, state: bool):
        """Set sound feedback."""
        await self.api.set_sound_feedback(state)
        self._optimistic_update("sound_feedback", state)

    async def async_set_voice_enhancement(self, mode: bool):
        """Set voice enhancement."""
        await self.api.set_voice_enhancement(mode)
        self._optimistic_update("voice_enhancement", mode)

    async def async_set_bluetooth_pairing_state(self, state: bool):
        """Set bluetooth pairing state."""
        await self.api.set_bluetooth_pairing_state(state)
        self._optimistic_update("bluetooth_pairing", state)
        if state and self.data:
            await asyncio.sleep(self.BLUETOOTH_SWITCH_DELAY)
            current_source, player_data = await asyncio.gather(
                self._safe_fetch(self.api.get_current_source(), "Bluetooth source"),
                self._safe_fetch(self.api.player_data(), "Bluetooth player data"),
            )
            if current_source:
                self.data["current_source"] = current_source
            if player_data:
                self.data["player_data"] = player_data
            self.async_set_updated_data(self.data)

    async def async_set_subwoofer_status(self, status: bool):
        """Set subwoofer status."""
        await self.api.set_subwoofer_status(status)
        self._optimistic_update("subwoofer_status", status)

    async def async_set_subwoofer_volume(self, volume: float):
        """Set subwoofer volume."""
        await self.api.set_subwoofer_volume(volume)
        self._optimistic_update("subwoofer_volume", volume)

    async def async_set_voice_enhancement_level(self, level: int):
        """Set voice enhancement level."""
        await self.api.set_voice_enhancement_level(level)
        self._optimistic_update("voice_enhancement_level", level)

    async def async_set_center_speaker_level(self, level: int):
        """Set center speaker level."""
        await self.api.set_center_speaker_level(level)
        self._optimistic_update("center_speaker_level", level)

    async def async_set_side_firing_level(self, level: int):
        """Set side firing level."""
        await self.api.set_side_firing_level(level)
        self._optimistic_update("side_firing_level", level)

    async def async_set_up_firing_level(self, level: int):
        """Set up firing level."""
        await self.api.set_up_firing_level(level)
        self._optimistic_update("up_firing_level", level)

    async def async_reboot(self):
        """Reboot the device."""
        await self.api.reboot()
        # No state update needed for reboot.

    async def async_reset_expert_settings(self):
        """Reset expert settings."""
        await self.api.reset_expert_settings()
        # Trigger a full refresh to get reset values.
        await self.async_request_refresh()

    # API wrapper methods.
    def has_capability(self, capability: str) -> bool:
        """Check if the device has a specific capability."""
        return self.api.has_capability(capability)

    def support_debounce_mode(self) -> bool:
        """Check if debounce mode is supported."""
        return self.api.support_debounce_mode()

    def get_volume_step(self) -> float:
        """Get the volume step."""
        return self.api.get_volume_step()

    async def has_subwoofer(self) -> bool:
        """Check if device has a subwoofer."""
        return await self.api.has_subwoofer()

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

    def set_endpoint(self, host: str):
        """Set the API endpoint."""
        self.api.set_endpoint(host)
