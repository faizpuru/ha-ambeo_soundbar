"""Data update coordinator for Ambeo Soundbar integration."""

import asyncio
import contextlib
import logging
from datetime import timedelta
from typing import Any, NamedTuple

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api.const import Capability
from .api.impl.generic_api import AmbeoApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class FeatureDef(NamedTuple):
    """Definition of an optional feature fetched during coordinator update."""

    data_key: str
    api_method: str
    label: str
    capability: str | None = None


class AmbeoCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching Ambeo data."""

    # Event listener settings.
    POLL_TIMEOUT_MS = 30000
    EVENT_LISTENER_RETRY_DELAY = 30  # Seconds to wait before retrying after error.

    def __init__(
        self,
        hass: HomeAssistant,
        api: AmbeoApi,
        sources: list[dict],
        presets: list[dict],
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
        self._event_listener_task: asyncio.Task | None = None
        # Lookup dicts for O(1) source/preset resolution.
        self._source_title_by_id: dict = {
            s["id"]: s["title"] for s in sources if "id" in s and "title" in s
        }
        self._source_id_by_title: dict = {
            s["title"]: s["id"] for s in sources if "id" in s and "title" in s
        }
        self._preset_title_by_id: dict = {
            p["id"]: p["title"] for p in presets if "id" in p and "title" in p
        }
        self._preset_id_by_title: dict = {
            p["title"]: p["id"] for p in presets if "id" in p and "title" in p
        }

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
            all_optional_features = [
                FeatureDef("play_time", "get_play_time", "Play time"),
                FeatureDef(
                    "led_bar_brightness",
                    "get_led_bar_brightness",
                    "LED bar",
                    Capability.LED_BAR,
                ),
                FeatureDef(
                    "codec_led_brightness",
                    "get_codec_led_brightness",
                    "Codec LED",
                    Capability.CODEC_LED,
                ),
                FeatureDef(
                    "logo_brightness",
                    "get_logo_brightness",
                    "Logo brightness",
                    Capability.AMBEO_LOGO,
                ),
                FeatureDef(
                    "logo_state", "get_logo_state", "Logo state", Capability.AMBEO_LOGO
                ),
                FeatureDef(
                    "display_brightness",
                    "get_display_brightness",
                    "Display",
                    Capability.MAX_DISPLAY,
                ),
                FeatureDef("night_mode", "get_night_mode", "Night mode"),
                FeatureDef("ambeo_mode", "get_ambeo_mode", "Ambeo mode"),
                FeatureDef("sound_feedback", "get_sound_feedback", "Sound feedback"),
                FeatureDef(
                    "voice_enhancement",
                    "get_voice_enhancement",
                    "Voice enhancement",
                    Capability.VOICE_ENHANCEMENT_TOGGLE,
                ),
                FeatureDef(
                    "bluetooth_pairing",
                    "get_bluetooth_pairing_state",
                    "Bluetooth pairing",
                    Capability.BLUETOOTH_PAIRING,
                ),
                FeatureDef(
                    "subwoofer_status",
                    "get_subwoofer_status",
                    "Subwoofer status",
                    Capability.SUBWOOFER,
                ),
                FeatureDef(
                    "subwoofer_volume",
                    "get_subwoofer_volume",
                    "Subwoofer volume",
                    Capability.SUBWOOFER,
                ),
                FeatureDef(
                    "voice_enhancement_level",
                    "get_voice_enhancement_level",
                    "Voice enhancement level",
                    Capability.VOICE_ENHANCEMENT_LEVEL,
                ),
                FeatureDef(
                    "center_speaker_level",
                    "get_center_speaker_level",
                    "Center speaker level",
                    Capability.CENTER_SPEAKER_LEVEL,
                ),
                FeatureDef(
                    "side_firing_level",
                    "get_side_firing_level",
                    "Side firing level",
                    Capability.SIDE_FIRING_LEVEL,
                ),
                FeatureDef(
                    "up_firing_level",
                    "get_up_firing_level",
                    "Up firing level",
                    Capability.UP_FIRING_LEVEL,
                ),
                FeatureDef("eco_mode", "get_eco_mode", "Eco mode", Capability.ECO_MODE),
                FeatureDef(
                    "ambeo_mode_level",
                    "get_ambeo_mode_level",
                    "Ambeo mode level",
                    Capability.AMBEO_MODE_LEVEL,
                ),
            ]

            optional_features = [
                f
                for f in all_optional_features
                if f.capability is None or self.api.has_capability(f.capability)
            ]

            results = await asyncio.gather(
                *(
                    self._safe_fetch(getattr(self.api, f.api_method)(), f.label)
                    for f in optional_features
                )
            )

            for feature, value in zip(optional_features, results, strict=True):
                if value is not None:
                    data[feature.data_key] = value

            if "play_time" in data:
                data["play_time_updated_at"] = dt_util.utcnow()

            _LOGGER.debug("Data updated successfully: %s", data)
            return data

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def async_start_event_listener(self) -> None:
        """Start the background event listener task."""
        if not self.api.get_subscribed_paths():
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
        """Background task: subscribe to device paths and react to changes."""
        paths = self.api.get_subscribed_paths()
        _LOGGER.debug("Starting event listener for %d paths", len(paths))

        while True:
            try:
                queue_id = await self.api.create_event_queue(paths)
                if not queue_id:
                    _LOGGER.debug(
                        "Failed to create event queue, retrying in %ds",
                        self.EVENT_LISTENER_RETRY_DELAY,
                    )
                    await asyncio.sleep(self.EVENT_LISTENER_RETRY_DELAY)
                    continue

                _LOGGER.debug("Event queue created: %s", queue_id)

                while True:
                    events = await self.api.poll_event_queue(
                        queue_id, timeout_ms=self.POLL_TIMEOUT_MS
                    )
                    if events is None:
                        _LOGGER.debug("Poll error, recreating event queue")
                        break
                    for event in events:
                        if event.get("itemType") != "update":
                            continue
                        path = event.get("path")
                        item_value = event.get("itemValue")
                        if not path or not item_value:
                            continue
                        updates = self.api.process_event(path, item_value)
                        for key, value in updates.items():
                            _LOGGER.debug("Event update: %s = %r", key, value)
                            self._apply_event_update(key, value)

            except asyncio.CancelledError:
                _LOGGER.debug("Event listener cancelled")
                return
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

    async def _async_set(self, api_method: str, data_key: str, value: Any) -> None:
        """Call an API setter and apply an optimistic update."""
        await getattr(self.api, api_method)(value)
        self._optimistic_update(data_key, value)

    def _apply_event_update(self, key: str, value: Any):
        """Apply an event-driven update with special handling for player keys."""
        if not self.data:
            return
        self.data[key] = value
        if key == "play_time":
            self.data["play_time_updated_at"] = dt_util.utcnow()
        self.async_set_updated_data(self.data)

    async def async_set_volume(self, volume: float):
        """Set volume."""
        await self.api.set_volume(volume)
        self._optimistic_update("volume", int(volume))

    async def async_set_mute(self, mute: bool):
        """Set mute."""
        await self._async_set("set_mute", "muted", mute)

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
        await self._async_set("set_source", "current_source", source_id)

    async def async_select_sound_mode(self, preset_id: str):
        """Select sound mode."""
        await self._async_set("set_preset", "current_preset", preset_id)

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

    async def async_media_previous_track(self):
        """Previous track."""
        await self.api.previous()

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

    async def async_set_ambeo_mode_level(self, level: int) -> None:
        """Set the Ambeo mode level."""
        await self._async_set("set_ambeo_mode_level", "ambeo_mode_level", level)

    async def async_reboot(self):
        """Reboot the device."""
        await self.api.reboot()
        # No state update needed for reboot.

    async def async_reset_expert_settings(self):
        """Reset expert settings."""
        await self.api.reset_expert_settings()
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

    def support_debounce_mode(self) -> bool:
        """Check if debounce mode is supported."""
        return self.api.support_debounce_mode()

    def get_volume_step(self) -> float:
        """Get the volume step."""
        return self.api.get_volume_step()

    async def has_subwoofer(self) -> bool:
        """Check if device has a subwoofer."""
        return await self.api.has_subwoofer()

    def get_volume_max(self) -> int:
        """Get the maximum native volume value."""
        return self.api.get_volume_max()

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
