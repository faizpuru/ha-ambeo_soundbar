import logging

from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_IDLE, STATE_ON, STATE_PAUSED, STATE_PLAYING
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .entity import AmbeoBaseEntity
from .util import find_id_by_title, find_title_by_id

_LOGGER = logging.getLogger(__name__)

STATE_DICT= {
    'playing': STATE_PLAYING,
    'paused': STATE_PAUSED,
    'stopped': STATE_IDLE
}

class AmbeoMediaPlayer(AmbeoBaseEntity, MediaPlayerEntity):
    """Representation of an Ambeo device as a media player entity."""

    def __init__(self, device, api, sources, presets):
        super().__init__(device, api, "Player", "player")
        self._state = STATE_ON
        self._current_source = None
        self._media_title = ""
        self._artist = None
        self._album = None
        self._image_url = ""
        self._volume = 0
        self._muted = False
        self._max_volume = 100
        self._sources = sources
        self._presets = presets
        self._current_preset = None


    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return (MediaPlayerEntityFeature.VOLUME_SET
                | MediaPlayerEntityFeature.VOLUME_MUTE
                | MediaPlayerEntityFeature.SELECT_SOURCE
                | MediaPlayerEntityFeature.SELECT_SOUND_MODE
                | MediaPlayerEntityFeature.PLAY
                | MediaPlayerEntityFeature.PAUSE
                | MediaPlayerEntityFeature.NEXT_TRACK
                | MediaPlayerEntityFeature.PREVIOUS_TRACK)

    @property
    def media_title(self):
        """Title of current playing media."""
        return self._media_title

    @property
    def media_image_url(self):
        """URL for image of current playing media."""
        return self._image_url

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def volume_level(self):
        """Return the volume level."""
        return self._volume

    @property
    def media_artist(self):
        """Return the artist of the current playing media."""
        return self._artist

    @property
    def media_album_name(self):
        """Return the album name of the current playing media."""
        return self._album

    async def async_set_volume_level(self, volume):
        """Sets the volume level."""
        await self.api.set_volume(volume * self._max_volume)
        self._volume = volume

    @property
    def is_volume_muted(self):
        """Boolean indicating if volume is currently muted."""
        return self._muted

    async def async_mute_volume(self, mute):
        """Sets volume mute status."""
        await self.api.set_mute(mute)
        self._muted = mute

    @property
    def source(self):
        """Return the current source."""
        return self._current_source

    @property
    def source_list(self):
        """List of available sources."""
        titles = [entry["title"] for entry in self._sources if "title" in entry]
        return sorted(titles)

    async def async_select_source(self, source):
        """Select source."""
        if source is not None:
            source_id = find_id_by_title(source, self._sources)
            if source_id is not None:
                await self.api.set_source(source_id)
                self._current_source = source

    @property
    def sound_mode(self):
        """Return the current audio preset."""
        return self._current_preset

    @property
    def sound_mode_list(self):
        """List of available audio presets."""
        titles = [preset["title"] for preset in self._presets if "title" in preset]
        return sorted(titles)


    async def async_select_sound_mode(self, sound_mode):
        """Switch the sound mode of the entity."""
        if sound_mode is not None:
            preset_id = find_id_by_title(sound_mode, self._presets)
            if preset_id is not None:
                await self.api.set_preset(preset_id)
                self._current_preset = sound_mode

    async def async_media_play(self):
        """Method to start playback."""
        await self.api.play()
        self._state = STATE_PLAYING

    async def async_media_pause(self):
        """Method to pause playback."""
        await self.api.pause()
        self._state = STATE_PAUSED

    async def async_media_next_track(self):
        """Method to skip to the next track."""
        _LOGGER.debug("Skipping to the next track")
        await self.api.next()

    async def async_media_previous_track(self):
        """Method to go back to the previous track."""
        _LOGGER.debug("Going back to the previous track")
        await self.api.previous()

    async def async_update(self):
        """Update the media player state."""
        _LOGGER.debug("Refreshing state...")
        try:
            "Get Volume"
            volume = await self.api.get_volume()
            self._volume = volume / self._max_volume
        except Exception as e: 
            _LOGGER.error("Failed to get volume: %s", e)
        try:
            "Get Muted"
            muted = await self.api.is_mute()
            self._muted = muted
        except Exception as e: 
            _LOGGER.error("Failed to get mute: %s", e)
        try:
            "Get Source"
            source_id = await self.api.get_current_source()
            self._current_source = find_title_by_id(source_id, self._sources)
        except Exception as e: 
            _LOGGER.error("Failed to get source: %s", e)
        try:
            "Get preset"
            preset_id = await self.api.get_current_preset()
            self._current_preset = find_title_by_id(preset_id, self._presets)
        except Exception as e: 
            _LOGGER.error("Failed to get preset: %s", e)
        try:
            player_data = await self.api.player_data()
            state = player_data.get("state", None)
            self._state = STATE_DICT.get(state, STATE_ON)

            track_roles = player_data.get("trackRoles", {})
            image_url = track_roles.get("icon")
            title = track_roles.get("title")
            media_data = track_roles.get("mediaData", {})
            meta_data = media_data.get("metaData", {})

            self._image_url = image_url
            self._media_title = title
            self._album = meta_data.get("album")
            self._artist = meta_data.get("artist")

        except Exception as e:
            _LOGGER.error("Failed to get player data: %s", e)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    ambeo_api = hass.data[DOMAIN][config_entry.entry_id]["api"]
    ambeo_device = hass.data[DOMAIN][config_entry.entry_id]["device"]
    sources = await ambeo_api.get_all_sources()
    presets = await ambeo_api.get_all_presets()
    ambeo_player = AmbeoMediaPlayer(ambeo_device, ambeo_api, sources, presets)
    async_add_entities([ambeo_player], update_before_add=True)
