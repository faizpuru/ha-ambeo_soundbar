"""Media player entity for Ambeo Soundbar integration."""

import asyncio
import logging

from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.components.media_player.const import MediaPlayerEntityFeature
from homeassistant.const import (
    STATE_IDLE,
    STATE_ON,
    STATE_PAUSED,
    STATE_PLAYING,
    STATE_STANDBY,
)
from homeassistant.core import HomeAssistant

from . import AmbeoConfigEntry
from .api.const import Capability
from .const import (
    CONFIG_DEBOUNCE_COOLDOWN,
    CONFIG_DEBOUNCE_COOLDOWN_DEFAULT,
)
from .entity import AmbeoBaseEntity

_LOGGER = logging.getLogger(__name__)

STATE_DICT = {
    "playing": STATE_PLAYING,
    "paused": STATE_PAUSED,
    "stopped": STATE_IDLE,
    "online": STATE_ON,
}


class DebounceManager:
    """Manages debounce state for volume changes."""

    def __init__(self) -> None:
        """Initialize with debounce inactive."""
        self._cooldown: int = 0
        self._task: asyncio.Task | None = None
        self._lock: asyncio.Lock | None = None
        self._start: float | None = None

    def configure(self, cooldown: int, support_debounce: bool) -> None:
        """Apply new cooldown setting and set up or tear down the lock."""
        self._cooldown = cooldown
        if self.active(support_debounce):
            _LOGGER.debug("Debounce mode activated")
            self._task = None
            self._start = None
            self._lock = asyncio.Lock()
        else:
            _LOGGER.debug("Debounce mode deactivated")

    def active(self, support_debounce: bool) -> bool:
        """Return whether debounce mode is currently active."""
        return support_debounce and self._cooldown > 0

    @property
    def lock(self) -> asyncio.Lock | None:
        """Return the debounce lock."""
        return self._lock

    @lock.setter
    def lock(self, value: asyncio.Lock | None) -> None:
        self._lock = value

    async def cancel(self) -> None:
        """Cancel any pending debounce task."""
        if self._task is not None and not self._task.done():
            _LOGGER.debug("[IMMEDIATE] Cancelling existing debounce task.")
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                _LOGGER.debug("[IMMEDIATE] Debounce task fully cancelled.")
            self._task = None


class AmbeoMediaPlayer(AmbeoBaseEntity, MediaPlayerEntity):
    """Representation of an Ambeo device as a media player entity."""

    async def _async_entry_updated(self, _hass, config_entry) -> None:
        """Handle config entry option updates."""
        await self._debounce.cancel()
        if self._debounce.lock is not None and self._debounce.lock.locked():
            _LOGGER.debug("Waiting for lock release during unload")
            async with self._debounce.lock:
                pass
        self._debounce.lock = None
        self._debounce.configure(
            config_entry.options.get(
                CONFIG_DEBOUNCE_COOLDOWN, CONFIG_DEBOUNCE_COOLDOWN_DEFAULT
            ),
            self.coordinator.support_debounce_mode(),
        )

    def __init__(self, coordinator, device, config_entry):
        """Initialize the Ambeo media player entity."""
        super().__init__(coordinator, device, None, "player")
        self._config_entry = config_entry
        self._debounce = DebounceManager()
        self._debounce.configure(
            config_entry.options.get(
                CONFIG_DEBOUNCE_COOLDOWN, CONFIG_DEBOUNCE_COOLDOWN_DEFAULT
            ),
            coordinator.support_debounce_mode(),
        )
        self._max_volume = 100
        self._volume_step = coordinator.get_volume_step()
        self._state_dict = {
            **STATE_DICT,
            "networkStandby": STATE_STANDBY
            if coordinator.has_capability(Capability.STANDBY)
            else STATE_IDLE,
        }

    async def async_added_to_hass(self) -> None:
        """Subscribe to events when entity is added to HA."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self._config_entry.add_update_listener(self._async_entry_updated)
        )

    async def async_will_remove_from_hass(self) -> None:
        """Clean up resources when entity is removed from HA."""
        await self._debounce.cancel()

    @property
    def debounce_mode_activated(self) -> bool:
        """Return whether debounce mode is active."""
        return self._debounce.active(self.coordinator.support_debounce_mode())

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        features = (
            MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.VOLUME_MUTE
            | MediaPlayerEntityFeature.VOLUME_STEP
            | MediaPlayerEntityFeature.SELECT_SOURCE
            | MediaPlayerEntityFeature.SELECT_SOUND_MODE
            | MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.PAUSE
            | MediaPlayerEntityFeature.NEXT_TRACK
            | MediaPlayerEntityFeature.PREVIOUS_TRACK
        )

        if self.coordinator.has_capability(Capability.STANDBY):
            features |= (
                MediaPlayerEntityFeature.TURN_ON | MediaPlayerEntityFeature.TURN_OFF
            )
        return features

    def _get_player_data(self, *keys, default=None):
        """Navigate into player_data by a chain of keys."""
        if not self.coordinator.data or "player_data" not in self.coordinator.data:
            return default
        result = self.coordinator.data["player_data"]
        for key in keys:
            if not isinstance(result, dict):
                return default
            result = result.get(key)
            if result is None:
                return default
        return result

    @property
    def media_title(self):
        """Title of current playing media."""
        return self._get_player_data("trackRoles", "title")

    @property
    def media_image_url(self):
        """URL for image of current playing media."""
        return self._get_player_data("trackRoles", "icon")

    @property
    def state(self):
        """Return the state of the device."""
        if not self.coordinator.data:
            return None

        power_state = self._state_dict.get(
            self.coordinator.data.get("state", ""), STATE_ON
        )

        if power_state == STATE_ON:
            player_state = self._get_player_data("state")
            if player_state:
                return self._state_dict.get(player_state, STATE_IDLE)

        return power_state

    @property
    def volume_level(self):
        """Return the volume level."""
        if self.coordinator.data and "volume" in self.coordinator.data:
            return self.coordinator.data["volume"] / self._max_volume
        return None

    @property
    def volume_step(self):
        """Return the volume step."""
        return self._volume_step

    @property
    def media_content_id(self):
        """Return the media content ID of the current playing media."""
        return self._get_player_data("trackRoles", "mediaData", "metaData", "trackId")

    @property
    def media_duration(self):
        """Return the duration of the current playing media."""
        duration = self._get_player_data("status", "duration")
        return duration / 1000 if duration is not None else None

    @property
    def media_position(self):
        """Return the current playback position in seconds."""
        if self.coordinator.data and "play_time" in self.coordinator.data:
            play_time = self.coordinator.data["play_time"]
            return play_time / 1000 if play_time is not None else None
        return None

    @property
    def media_position_updated_at(self):
        """Return the time at which the media position was last updated."""
        if self.coordinator.data:
            return self.coordinator.data.get("play_time_updated_at")
        return None

    @property
    def media_artist(self):
        """Return the artist of the current playing media."""
        return self._get_player_data("trackRoles", "mediaData", "metaData", "artist")

    @property
    def media_album_name(self):
        """Return the album name of the current playing media."""
        return self._get_player_data("trackRoles", "mediaData", "metaData", "album")

    async def async_set_volume_level(self, volume):
        """Set the volume level."""
        await self.coordinator.async_set_volume(volume * self._max_volume)

    @property
    def is_volume_muted(self):
        """Boolean indicating if volume is currently muted."""
        if self.coordinator.data and "muted" in self.coordinator.data:
            return self.coordinator.data["muted"]
        return None

    async def async_mute_volume(self, mute):
        """Set volume mute status."""
        await self.coordinator.async_set_mute(mute)

    async def async_turn_on(self):
        """Turn the media player on."""
        await self.coordinator.async_turn_on()

    async def async_turn_off(self):
        """Turn the media player off."""
        await self.coordinator.async_turn_off()

    @property
    def source(self):
        """Return the current source."""
        if self.coordinator.data and "current_source" in self.coordinator.data:
            return self.coordinator.get_source_title(
                self.coordinator.data["current_source"]
            )
        return None

    @property
    def source_list(self):
        """List of available sources."""
        titles = [
            entry["title"] for entry in self.coordinator.sources if "title" in entry
        ]
        return sorted(titles)

    async def async_select_source(self, source):
        """Select source."""
        if source is not None:
            source_id = self.coordinator.get_source_id(source)
            if source_id is not None:
                await self.coordinator.async_select_source(source_id)

    @property
    def sound_mode(self):
        """Return the current audio preset."""
        if self.coordinator.data and "current_preset" in self.coordinator.data:
            return self.coordinator.get_preset_title(
                self.coordinator.data["current_preset"]
            )
        return None

    @property
    def sound_mode_list(self):
        """List of available audio presets."""
        titles = [
            preset["title"] for preset in self.coordinator.presets if "title" in preset
        ]
        return sorted(titles)

    async def async_select_sound_mode(self, sound_mode):
        """Switch the sound mode of the entity."""
        if sound_mode is not None:
            preset_id = self.coordinator.get_preset_id(sound_mode)
            if preset_id is not None:
                await self.coordinator.async_select_sound_mode(preset_id)

    async def async_media_play(self):
        """Start playback."""
        await self.coordinator.async_media_play()

    async def async_media_pause(self):
        """Pause playback."""
        await self.coordinator.async_media_pause()

    async def async_media_next_track(self):
        """Skip to the next track."""
        _LOGGER.debug("Skipping to the next track")
        await self.coordinator.async_media_next_track()

    async def async_media_previous_track(self):
        """Go back to the previous track."""
        _LOGGER.debug("Going back to the previous track")
        await self.coordinator.async_media_previous_track()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AmbeoConfigEntry,
    async_add_entities,
):
    """Set up media player from a config entry created in the integrations UI."""
    coordinator = config_entry.runtime_data.coordinator
    ambeo_device = config_entry.runtime_data.device
    ambeo_player = AmbeoMediaPlayer(coordinator, ambeo_device, config_entry)
    async_add_entities([ambeo_player])
