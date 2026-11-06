"""Media player entity for Ambeo Soundbar integration."""

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.components.media_player.const import (
    MediaPlayerEntityFeature,
    MediaPlayerState,
    RepeatMode,
)
from homeassistant.const import STATE_PLAYING
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from pyambeo import Capability, PlayMode

from . import AmbeoConfigEntry, AmbeoDevice
from .const import DOMAIN
from .coordinator import AmbeoCoordinator
from .entity import AmbeoBaseEntity

PARALLEL_UPDATES = 1

_LOGGER = logging.getLogger(__name__)

# Display names for service IDs, as shown by the soundbar web app.
SERVICE_NAMES = {
    "airplay": "AirPlay",
    "avs": "Alexa",
    "googlecast": "Google Cast",
}

# Play logic of the physical inputs (HDMI, optical…), which are not apps.
PHYSICAL_INPUT_PLAY_LOGIC = "imx8af:"

# Device play mode for each shuffle and repeat combination.
PLAY_MODES = {
    (False, RepeatMode.OFF): PlayMode.NORMAL,
    (True, RepeatMode.OFF): PlayMode.SHUFFLE,
    (False, RepeatMode.ONE): PlayMode.REPEAT_ONE,
    (True, RepeatMode.ONE): PlayMode.SHUFFLE_REPEAT_ONE,
    (False, RepeatMode.ALL): PlayMode.REPEAT_ALL,
    (True, RepeatMode.ALL): PlayMode.SHUFFLE_REPEAT_ALL,
}
SHUFFLE_REPEAT = {mode: key for key, mode in PLAY_MODES.items()}


class AmbeoMediaPlayer(AmbeoBaseEntity, MediaPlayerEntity):
    """Representation of an Ambeo device as a media player entity."""

    _attr_name = None

    def __init__(self, coordinator: AmbeoCoordinator, device: AmbeoDevice) -> None:
        """Initialize the Ambeo media player entity."""
        super().__init__(coordinator, device, None, "player")
        self._max_volume = 100
        self._volume_step = coordinator.get_volume_step()
        self._last_title: str | None = None

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Flag media player features that are supported."""
        features = (
            MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.VOLUME_MUTE
            | MediaPlayerEntityFeature.VOLUME_STEP
            | MediaPlayerEntityFeature.SELECT_SOURCE
            | MediaPlayerEntityFeature.SELECT_SOUND_MODE
            | MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.PAUSE
        )

        # The stream announces the other controls it accepts. Play and pause
        # stay available, as the controls are missing while switching streams.
        controls = self._get_player_data("controls", default={})
        if controls.get("next_"):
            features |= MediaPlayerEntityFeature.NEXT_TRACK
        if controls.get("previous"):
            features |= MediaPlayerEntityFeature.PREVIOUS_TRACK
        if controls.get("seekTime") and self.media_duration is not None:
            features |= MediaPlayerEntityFeature.SEEK
        if any((controls.get("playMode") or {}).values()):
            features |= (
                MediaPlayerEntityFeature.SHUFFLE_SET
                | MediaPlayerEntityFeature.REPEAT_SET
            )

        if self.coordinator.has_capability(Capability.STANDBY):
            features |= (
                MediaPlayerEntityFeature.TURN_ON | MediaPlayerEntityFeature.TURN_OFF
            )
        return features

    def _get_player_data(self, *keys: str, default: Any = None) -> Any:
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

    def _get_metadata(self, key: str) -> Any:
        """Return a metaData field from trackRoles, falling back to mediaRoles."""
        return self._get_player_data(
            "trackRoles", "mediaData", "metaData", key
        ) or self._get_player_data("mediaRoles", "mediaData", "metaData", key)

    def _is_physical_input(self) -> bool:
        """Return True when playing from a physical input rather than an app."""
        play_logic: str = self._get_metadata("playLogicPath") or ""
        return play_logic.startswith(PHYSICAL_INPUT_PLAY_LOGIC)

    @property
    def media_title(self) -> str | None:
        """Title of current playing media."""
        title: str | None = (
            self._get_player_data("trackRoles", "title")
            or self._get_player_data("trackRoles", "description")
            or self._get_player_data("mediaRoles", "title")
        )
        if title:
            self._last_title = title
            return title
        if self.coordinator.get_state() == STATE_PLAYING:
            return self._last_title
        self._last_title = None
        return None

    @property
    def media_image_url(self) -> str | None:
        """URL for image of current playing media."""
        url: str | None = self._get_player_data("trackRoles", "icon")
        if url and url.startswith(("http://", "https://")):
            return url
        return None

    @property
    def state(self) -> MediaPlayerState | None:
        """Return the state of the device."""
        return self.coordinator.get_state()

    @property
    def volume_level(self) -> float | None:
        """Return the volume level."""
        if self.coordinator.data and "volume" in self.coordinator.data:
            return float(self.coordinator.data["volume"] / self._max_volume)
        return None

    @property
    def volume_step(self) -> float:
        """Return the volume step."""
        return self._volume_step

    @property
    def media_content_id(self) -> str | None:
        """Return the media content ID of the current playing media."""
        track_id: str | None = (
            self._get_player_data("trackRoles", "mediaData", "metaData", "trackId")
            or None
        )
        return track_id

    @property
    def media_duration(self) -> int | None:
        """Return the duration of the current playing media.

        Live streams report a duration of 0 or -1000.
        """
        duration = self._get_player_data("status", "duration")
        if not isinstance(duration, (int, float)) or duration <= 0:
            return None
        return int(duration / 1000)

    @property
    def media_position(self) -> int | None:
        """Return the current playback position in seconds.

        Inputs without a duration (HDMI, optical, …) report a running
        counter rather than a track position, so it is not exposed.
        """
        if self.media_duration is None or not self.coordinator.data:
            return None
        play_time = self.coordinator.data.get("play_time")
        return int(play_time / 1000) if play_time is not None else None

    @property
    def media_position_updated_at(self) -> datetime | None:
        """Return the time at which the media position was last updated."""
        if self.media_position is None:
            return None
        updated_at: datetime | None = self.coordinator.data.get("play_time_updated_at")
        return updated_at

    @property
    def media_artist(self) -> str | None:
        """Return the artist of the current playing media."""
        artist: str | None = self._get_metadata("artist") or None
        return artist

    @property
    def media_album_name(self) -> str | None:
        """Return the album name of the current playing media."""
        album: str | None = self._get_metadata("album") or None
        return album

    @property
    def media_playlist(self) -> str | None:
        """Return the playlist or context of the current playing media."""
        playlist = self._get_metadata("playbackSourceId")
        if not isinstance(playlist, str):
            return None
        return playlist.strip() or None

    @property
    def app_id(self) -> str | None:
        """Return the ID of the app or service currently playing."""
        if self._is_physical_input():
            return None
        service_id: str | None = self._get_metadata("serviceID") or None
        return service_id

    @property
    def app_name(self) -> str | None:
        """Return the name of the app or service currently playing."""
        if self._is_physical_input():
            return None
        name: str | None = self._get_metadata("externalAppName") or self._get_metadata(
            "serviceNameOverride"
        )
        if name:
            return name
        service_id = self._get_metadata("serviceID")
        if not isinstance(service_id, str) or not service_id:
            return None
        return SERVICE_NAMES.get(service_id, service_id[:1].upper() + service_id[1:])

    def _shuffle_repeat(self) -> tuple[bool, RepeatMode] | None:
        """Return the shuffle and repeat state of the device play mode."""
        if not self.coordinator.data:
            return None
        play_mode: PlayMode | None = self.coordinator.data.get("play_mode")
        return SHUFFLE_REPEAT.get(play_mode) if play_mode else None

    @property
    def shuffle(self) -> bool | None:
        """Return True if shuffle is enabled."""
        shuffle_repeat = self._shuffle_repeat()
        return shuffle_repeat[0] if shuffle_repeat else None

    @property
    def repeat(self) -> RepeatMode | None:
        """Return the repeat mode."""
        shuffle_repeat = self._shuffle_repeat()
        return shuffle_repeat[1] if shuffle_repeat else None

    async def async_set_shuffle(self, shuffle: bool) -> None:
        """Enable or disable shuffle, keeping the repeat mode."""
        repeat = self.repeat or RepeatMode.OFF
        await self.coordinator.async_set_play_mode(PLAY_MODES[shuffle, repeat])

    async def async_set_repeat(self, repeat: RepeatMode) -> None:
        """Set the repeat mode, keeping shuffle."""
        shuffle = bool(self.shuffle)
        await self.coordinator.async_set_play_mode(
            PLAY_MODES[shuffle, RepeatMode(repeat)]
        )

    async def async_set_volume_level(self, volume: float) -> None:
        """Set the volume level."""
        await self.coordinator.async_set_volume(volume * self._max_volume)

    @property
    def is_volume_muted(self) -> bool | None:
        """Boolean indicating if volume is currently muted."""
        if self.coordinator.data and "muted" in self.coordinator.data:
            return bool(self.coordinator.data["muted"])
        return None

    async def async_mute_volume(self, mute: bool) -> None:
        """Set volume mute status."""
        await self.coordinator.async_set_mute(mute)

    async def async_turn_on(self) -> None:
        """Turn the media player on."""
        await self.coordinator.async_turn_on()

    async def async_turn_off(self) -> None:
        """Turn the media player off."""
        await self.coordinator.async_turn_off()

    @property
    def source(self) -> str | None:
        """Return the current source."""
        if self.coordinator.data and "current_source" in self.coordinator.data:
            return self.coordinator.get_source_title(
                self.coordinator.data["current_source"]
            )
        return None

    @property
    def source_list(self) -> list[str]:
        """List of available sources."""
        titles = [source.title for source in self.coordinator.sources]
        return sorted(titles)

    async def async_select_source(self, source: str) -> None:
        """Select source."""
        source_id = self.coordinator.get_source_id(source)
        if source_id is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_source",
                translation_placeholders={"source": str(source)},
            )
        await self.coordinator.async_select_source(source_id)

    @property
    def sound_mode(self) -> str | None:
        """Return the current audio preset."""
        if self.coordinator.data and "current_preset" in self.coordinator.data:
            return self.coordinator.get_preset_title(
                self.coordinator.data["current_preset"]
            )
        return None

    @property
    def sound_mode_list(self) -> list[str]:
        """List of available audio presets."""
        titles = [preset.title for preset in self.coordinator.presets]
        return sorted(titles)

    async def async_select_sound_mode(self, sound_mode: str) -> None:
        """Switch the sound mode of the entity."""
        preset_id = self.coordinator.get_preset_id(sound_mode)
        if preset_id is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_sound_mode",
                translation_placeholders={"sound_mode": str(sound_mode)},
            )
        await self.coordinator.async_select_sound_mode(preset_id)

    async def async_media_play(self) -> None:
        """Start playback."""
        await self.coordinator.async_media_play()

    async def async_media_pause(self) -> None:
        """Pause playback."""
        await self.coordinator.async_media_pause()

    async def async_media_next_track(self) -> None:
        """Skip to the next track."""
        _LOGGER.debug("Skipping to the next track")
        await self.coordinator.async_media_next_track()

    async def async_media_previous_track(self) -> None:
        """Go back to the previous track."""
        _LOGGER.debug("Going back to the previous track")
        await self.coordinator.async_media_previous_track()

    async def async_media_seek(self, position: float) -> None:
        """Seek to a position, in seconds."""
        await self.coordinator.async_media_seek(int(position * 1000))


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AmbeoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up media player from a config entry created in the integrations UI."""
    coordinator = config_entry.runtime_data.coordinator
    ambeo_device = config_entry.runtime_data.device
    ambeo_player = AmbeoMediaPlayer(coordinator, ambeo_device)
    async_add_entities([ambeo_player])
