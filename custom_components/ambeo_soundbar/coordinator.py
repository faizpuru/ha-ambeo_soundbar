import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api.impl.generic_api import AmbeoApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class AmbeoCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching Ambeo data."""

    def __init__(self, hass: HomeAssistant, api: AmbeoApi, sources: list, presets: list, update_interval_seconds: int = 10):
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

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            data = {}

            # Media Player data
            data["volume"] = await self.api.get_volume()
            data["muted"] = await self.api.is_mute()
            data["state"] = await self.api.get_state()
            data["current_source"] = await self.api.get_current_source()
            data["current_preset"] = await self.api.get_current_preset()
            data["player_data"] = await self.api.player_data()

            # Light entities data
            try:
                data["led_bar_brightness"] = await self.api.get_led_bar_brightness()
            except Exception as e:
                _LOGGER.debug("LED bar not available: %s", e)

            try:
                data["codec_led_brightness"] = await self.api.get_codec_led_brightness()
            except Exception as e:
                _LOGGER.debug("Codec LED not available: %s", e)

            try:
                data["logo_brightness"] = await self.api.get_logo_brightness()
                data["logo_state"] = await self.api.get_logo_state()
            except Exception as e:
                _LOGGER.debug("Logo not available: %s", e)

            try:
                data["display_brightness"] = await self.api.get_display_brightness()
            except Exception as e:
                _LOGGER.debug("Display not available: %s", e)

            # Switch entities data
            try:
                data["night_mode"] = await self.api.get_night_mode()
            except Exception as e:
                _LOGGER.debug("Night mode not available: %s", e)

            try:
                data["ambeo_mode"] = await self.api.get_ambeo_mode()
            except Exception as e:
                _LOGGER.debug("Ambeo mode not available: %s", e)

            try:
                data["sound_feedback"] = await self.api.get_sound_feedback()
            except Exception as e:
                _LOGGER.debug("Sound feedback not available: %s", e)

            try:
                data["voice_enhancement"] = await self.api.get_voice_enhancement()
            except Exception as e:
                _LOGGER.debug("Voice enhancement not available: %s", e)

            try:
                data["bluetooth_pairing"] = await self.api.get_bluetooth_pairing_state()
            except Exception as e:
                _LOGGER.debug("Bluetooth pairing not available: %s", e)

            try:
                data["subwoofer_status"] = await self.api.get_subwoofer_status()
            except Exception as e:
                _LOGGER.debug("Subwoofer status not available: %s", e)

            # Number entities data
            try:
                data["subwoofer_volume"] = await self.api.get_subwoofer_volume()
            except Exception as e:
                _LOGGER.debug("Subwoofer volume not available: %s", e)

            try:
                data["voice_enhancement_level"] = await self.api.get_voice_enhancement_level()
            except Exception as e:
                _LOGGER.debug("Voice enhancement level not available: %s", e)

            try:
                data["center_speaker_level"] = await self.api.get_center_speaker_level()
            except Exception as e:
                _LOGGER.debug("Center speaker level not available: %s", e)

            try:
                data["side_firing_level"] = await self.api.get_side_firing_level()
            except Exception as e:
                _LOGGER.debug("Side firing level not available: %s", e)

            try:
                data["up_firing_level"] = await self.api.get_up_firing_level()
            except Exception as e:
                _LOGGER.debug("Up firing level not available: %s", e)

            # Binary sensor data
            try:
                data["eco_mode"] = await self.api.get_eco_mode()
            except Exception as e:
                _LOGGER.debug("Eco mode not available: %s", e)

            _LOGGER.debug("Data updated successfully: %s", data)
            return data

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    async def async_set_volume(self, volume: float):
        """Set volume."""
        await self.api.set_volume(volume)
        if self.data:
            self.data["volume"] = int(volume)
            self.async_set_updated_data(self.data)

    async def async_set_mute(self, mute: bool):
        """Set mute."""
        await self.api.set_mute(mute)
        if self.data:
            self.data["muted"] = mute
            self.async_set_updated_data(self.data)

    async def async_turn_on(self):
        """Turn on."""
        await self.api.wake()
        if self.data:
            self.data["state"] = "online"
            self.async_set_updated_data(self.data)

    async def async_turn_off(self):
        """Turn off."""
        await self.api.stand_by()
        if self.data:
            self.data["state"] = "networkStandby"
            self.async_set_updated_data(self.data)

    async def async_select_source(self, source_id: str):
        """Select source."""
        await self.api.set_source(source_id)
        # Wait a bit for the source to change
        await asyncio.sleep(1)
        if self.data:
            self.data["current_source"] = source_id
            # Refresh player data to get new source content
            try:
                player_data = await self.api.player_data()
                if player_data:
                    # Preserve the current play state if it was just set
                    if "player_data" in self.data and "state" in self.data["player_data"]:
                        current_state = self.data["player_data"]["state"]
                        self.data["player_data"] = player_data
                        # Keep playing state if we were playing
                        if current_state == "playing":
                            self.data["player_data"]["state"] = "playing"
                    else:
                        self.data["player_data"] = player_data
            except Exception as e:
                _LOGGER.debug(
                    "Failed to refresh player data after source change: %s", e)
            self.async_set_updated_data(self.data)

    async def async_select_sound_mode(self, preset_id: str):
        """Select sound mode."""
        await self.api.set_preset(preset_id)
        if self.data:
            self.data["current_preset"] = preset_id
            self.async_set_updated_data(self.data)

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
        # Wait a bit for the device to change track
        await asyncio.sleep(1)
        # Refresh player data to get new track info
        try:
            player_data = await self.api.player_data()
            if self.data and player_data:
                # Preserve the current play state if it was just set
                if "player_data" in self.data and "state" in self.data["player_data"]:
                    current_state = self.data["player_data"]["state"]
                    self.data["player_data"] = player_data
                    # Keep the state as playing if we're navigating tracks
                    if current_state == "playing":
                        self.data["player_data"]["state"] = "playing"
                else:
                    self.data["player_data"] = player_data
                self.async_set_updated_data(self.data)
        except Exception as e:
            _LOGGER.debug("Failed to refresh player data after next: %s", e)

    async def async_media_previous_track(self):
        """Previous track."""
        await self.api.previous()
        # Wait a bit for the device to change track
        await asyncio.sleep(1)
        # Refresh player data to get new track info
        try:
            player_data = await self.api.player_data()
            if self.data and player_data:
                # Preserve the current play state if it was just set
                if "player_data" in self.data and "state" in self.data["player_data"]:
                    current_state = self.data["player_data"]["state"]
                    self.data["player_data"] = player_data
                    # Keep the state as playing if we're navigating tracks
                    if current_state == "playing":
                        self.data["player_data"]["state"] = "playing"
                else:
                    self.data["player_data"] = player_data
                self.async_set_updated_data(self.data)
        except Exception as e:
            _LOGGER.debug(
                "Failed to refresh player data after previous: %s", e)

    async def async_set_led_bar_brightness(self, brightness: int):
        """Set LED bar brightness."""
        await self.api.set_led_bar_brightness(brightness)
        if self.data:
            self.data["led_bar_brightness"] = brightness
            self.async_set_updated_data(self.data)

    async def async_set_codec_led_brightness(self, brightness: int):
        """Set codec LED brightness."""
        await self.api.set_codec_led_brightness(brightness)
        if self.data:
            self.data["codec_led_brightness"] = brightness
            self.async_set_updated_data(self.data)

    async def async_set_logo_brightness(self, brightness: int):
        """Set logo brightness."""
        await self.api.set_logo_brightness(brightness)
        if self.data:
            self.data["logo_brightness"] = brightness
            self.async_set_updated_data(self.data)

    async def async_change_logo_state(self, state: bool):
        """Change logo state."""
        await self.api.change_logo_state(state)
        if self.data:
            self.data["logo_state"] = state
            self.async_set_updated_data(self.data)

    async def async_set_display_brightness(self, brightness: int):
        """Set display brightness."""
        await self.api.set_display_brightness(brightness)
        if self.data:
            self.data["display_brightness"] = brightness
            self.async_set_updated_data(self.data)

    async def async_set_night_mode(self, mode: bool):
        """Set night mode."""
        await self.api.set_night_mode(mode)
        if self.data:
            self.data["night_mode"] = mode
            self.async_set_updated_data(self.data)

    async def async_set_ambeo_mode(self, mode: bool):
        """Set ambeo mode."""
        await self.api.set_ambeo_mode(mode)
        if self.data:
            self.data["ambeo_mode"] = mode
            self.async_set_updated_data(self.data)

    async def async_set_sound_feedback(self, state: bool):
        """Set sound feedback."""
        await self.api.set_sound_feedback(state)
        if self.data:
            self.data["sound_feedback"] = state
            self.async_set_updated_data(self.data)

    async def async_set_voice_enhancement(self, mode: bool):
        """Set voice enhancement."""
        await self.api.set_voice_enhancement(mode)
        if self.data:
            self.data["voice_enhancement"] = mode
            self.async_set_updated_data(self.data)

    async def async_set_bluetooth_pairing_state(self, state: bool):
        """Set bluetooth pairing state."""
        await self.api.set_bluetooth_pairing_state(state)
        if self.data:
            self.data["bluetooth_pairing"] = state
            # If activating bluetooth, refresh player data and current source
            if state:
                await asyncio.sleep(1)
                try:
                    # Get current source (likely switched to Bluetooth)
                    current_source = await self.api.get_current_source()
                    if current_source:
                        self.data["current_source"] = current_source

                    # Get player data - use real state from API (don't preserve)
                    # since we're switching to a completely different source
                    player_data = await self.api.player_data()
                    if player_data:
                        self.data["player_data"] = player_data
                except Exception as e:
                    _LOGGER.debug(
                        "Failed to refresh data after bluetooth pairing: %s", e)
            self.async_set_updated_data(self.data)

    async def async_set_subwoofer_status(self, status: bool):
        """Set subwoofer status."""
        await self.api.set_subwoofer_status(status)
        if self.data:
            self.data["subwoofer_status"] = status
            self.async_set_updated_data(self.data)

    async def async_set_subwoofer_volume(self, volume: float):
        """Set subwoofer volume."""
        await self.api.set_subwoofer_volume(volume)
        if self.data:
            self.data["subwoofer_volume"] = volume
            self.async_set_updated_data(self.data)

    async def async_set_voice_enhancement_level(self, level: int):
        """Set voice enhancement level."""
        await self.api.set_voice_enhancement_level(level)
        if self.data:
            self.data["voice_enhancement_level"] = level
            self.async_set_updated_data(self.data)

    async def async_set_center_speaker_level(self, level: int):
        """Set center speaker level."""
        await self.api.set_center_speaker_level(level)
        if self.data:
            self.data["center_speaker_level"] = level
            self.async_set_updated_data(self.data)

    async def async_set_side_firing_level(self, level: int):
        """Set side firing level."""
        await self.api.set_side_firing_level(level)
        if self.data:
            self.data["side_firing_level"] = level
            self.async_set_updated_data(self.data)

    async def async_set_up_firing_level(self, level: int):
        """Set up firing level."""
        await self.api.set_up_firing_level(level)
        if self.data:
            self.data["up_firing_level"] = level
            self.async_set_updated_data(self.data)

    async def async_reboot(self):
        """Reboot the device."""
        await self.api.reboot()
        # No state update needed for reboot

    async def async_reset_expert_settings(self):
        """Reset expert settings."""
        await self.api.reset_expert_settings()
        # Trigger a full refresh to get reset values
        await self.async_request_refresh()

    # API wrapper methods
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

    def set_endpoint(self, host: str):
        """Set the API endpoint."""
        self.api.set_endpoint(host)
