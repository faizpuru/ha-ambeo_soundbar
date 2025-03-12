import asyncio
import logging
import time
import copy

from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON, STATE_PAUSED, STATE_PLAYING, STATE_STANDBY, STATE_IDLE
from homeassistant.core import HomeAssistant

from .const import CONFIG_DEBOUNCE_COOLDOWN, DOMAIN, Capability
from .entity import AmbeoBaseEntity
from .util import find_id_by_title, find_title_by_id
from .api.impl.generic_api import AmbeoApi


_LOGGER = logging.getLogger(__name__)

STATE_DICT = {
    'playing': STATE_PLAYING,
    'paused': STATE_PAUSED,
    'stopped': STATE_IDLE,
    'online': STATE_ON
}


class AmbeoMediaPlayer(AmbeoBaseEntity, MediaPlayerEntity):
    """Representation of an Ambeo device as a media player entity."""

    async def _async_entry_updated(self, hass, config_entry) -> None:
        # Cancel existing debounce
        await self._cancel_existing_debounce()
        if self._update_lock is not None and self._update_lock.locked():
            _LOGGER.debug("Waiting for lock release during unload")
            async with self._update_lock:  # Acquire to ensure clean release
                pass
        self._update_lock = None
        # Update debounce configuration
        self.update_debounce_mode(config_entry)

    def update_debounce_mode(self, config_entry):
        self._debounce_cooldown = config_entry.options.get(
            CONFIG_DEBOUNCE_COOLDOWN)
        if self._debounce_cooldown > 0:
            _LOGGER.debug("Debounce mode activated")
            self._debounce_task = None
            self._debounce_start = None
            self._update_lock = asyncio.Lock()
        else:
            _LOGGER.debug("Debounce mode deactivated")

    def __init__(self, device, api, sources, presets, config_entry):
        super().__init__(device, api, "Player", "player")
        config_entry.async_on_unload(
            config_entry.add_update_listener(self._async_entry_updated))

        self.update_debounce_mode(config_entry)

        self._power_state = STATE_ON
        self._playing_state = STATE_IDLE
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
        self._volume_step = api.get_volume_step()
        if (api.has_capability(Capability.STANDBY)):
            STATE_DICT['networkStandby'] = STATE_STANDBY
        else:
            STATE_DICT['networkStandby'] = STATE_IDLE

    @property
    def debounce_mode_activated(self):
        return self.api.support_debounce_mode() and self._debounce_cooldown > 0

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        features = (MediaPlayerEntityFeature.VOLUME_SET
                    | MediaPlayerEntityFeature.VOLUME_MUTE
                    | MediaPlayerEntityFeature.VOLUME_STEP
                    | MediaPlayerEntityFeature.SELECT_SOURCE
                    | MediaPlayerEntityFeature.SELECT_SOUND_MODE
                    | MediaPlayerEntityFeature.PLAY
                    | MediaPlayerEntityFeature.PAUSE
                    | MediaPlayerEntityFeature.NEXT_TRACK
                    | MediaPlayerEntityFeature.PREVIOUS_TRACK)

        if self.api.has_capability(Capability.STANDBY):
            features |= (MediaPlayerEntityFeature.TURN_ON | MediaPlayerEntityFeature.TURN_OFF)
        return features

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
        if self._power_state == STATE_ON:
            return self._playing_state
        return self._power_state

    @property
    def volume_level(self):
        """Return the volume level."""
        return self._volume

    @property
    def volume_step(self):
        """Return the volume level."""
        return self._volume_step

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

    async def async_turn_on(self):
        """Turn the media player on."""
        await self.api.wake()
        self._power_state = STATE_ON

    async def async_turn_off(self):
        """Turn the media player off."""
        await self.api.stand_by()
        self._power_state = STATE_STANDBY

    @property
    def source(self):
        """Return the current source."""
        return self._current_source

    @property
    def source_id(self):
        return find_id_by_title(
            self.source, self._sources)

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

    @property
    def available(self):
        return self._volume is not None

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
        self._playing_state = STATE_PLAYING

    async def async_media_pause(self):
        """Method to pause playback."""
        await self.api.pause()
        self._playing_state = STATE_PAUSED

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
        tasks = [
            self.update_volume(),
            self.update_mute(),
            self.update_source(),
            self.update_preset(),
            self.update_state(),
            self.update_player_data(),
        ]
        await asyncio.gather(*tasks)

    async def _update_attr(self, api_method, transform, setter, error_msg):
        """Exécute une méthode API, transforme le résultat et met à jour l'attribut correspondant."""
        try:
            result = await api_method()
            setter(transform(result))
        except Exception as e:
            _LOGGER.error(error_msg, e)

    async def update_state(self):
        await self._update_attr(
            self.api.get_state,
            lambda state: STATE_DICT.get(state, state),
            lambda value: setattr(self, "_power_state", value),
            "Failed to get state: %s"
        )

    async def update_preset(self):
        await self._update_attr(
            self.api.get_current_preset,
            lambda preset_id: find_title_by_id(preset_id, self._presets),
            lambda value: setattr(self, "_current_preset", value),
            "Failed to get preset: %s"
        )

    async def update_source(self):
        await self._update_attr(
            self.api.get_current_source,
            lambda source_id: find_title_by_id(source_id, self._sources),
            lambda value: setattr(self, "_current_source", value),
            "Failed to get source: %s"
        )

    async def update_mute(self):
        await self._update_attr(
            self.api.is_mute,
            lambda muted: muted,
            lambda value: setattr(self, "_muted", value),
            "Failed to get mute: %s"
        )

    async def update_volume(self):
        await self._update_attr(
            self.api.get_volume,
            lambda volume: volume / self._max_volume,
            lambda value: setattr(self, "_volume", value),
            "Failed to get volume: %s"
        )

    def _should_debounce(self, player_state):
        """Determine if the update should be debounced."""
        return (player_state == 'stopped' and
                self._power_state != STATE_STANDBY and
                self._playing_state != STATE_IDLE)

    async def _cancel_existing_debounce(self):
        """Cancel the existing debounce task, if any."""
        if (
            hasattr(self, "_debounce_task") and 
            self._debounce_task is not None and 
            not self._debounce_task.done()
        ):
            _LOGGER.debug("[IMMEDIATE] Cancelling existing debounce task.")
            self._debounce_task.cancel()
            try:
                await self._debounce_task
            except asyncio.CancelledError:
                _LOGGER.debug("[IMMEDIATE] Debounce task fully cancelled.")
            self._debounce_task = None

    async def update_player_data(self):
        try:
            player_data = await self.api.player_data()
            player_state = player_data.get("state")
            if player_state == 'transitioning':
                _LOGGER.debug(
                    "[IMMEDIATE] Immediate update requested, state: '%s' will not be processed.", player_state)
                return
            if self.debounce_mode_activated:
                async with self._update_lock:
                    if self._should_debounce(player_state):
                        _LOGGER.debug(
                            "[TASK] Debounced update requested, state: '%s'", player_state)
                        if self._debounce_task is None:
                            self._debounce_start = time.time()
                            self._debounce_task = asyncio.create_task(
                                self._debounced_update(player_data)
                            )
                        else:
                            elapsed = time.time() - self._debounce_start
                            remaining = max(0, self._debounce_cooldown - elapsed)
                            _LOGGER.debug(
                                "[TASK] Debounce task already running... %s seconds remaining.", round(remaining, 1))
                    else:
                        _LOGGER.debug(
                            "[IMMEDIATE] Immediate update requested, state: '%s'", player_state)
                        await self._cancel_existing_debounce()
                        self._process_player_data(player_data)
            else:
                self._process_player_data(player_data)
        except Exception as e:
            _LOGGER.error("Failed to get player data: %s", e)

    async def _debounced_update(self, player_data):
        """Handle the debounced update after the cooldown delay."""
        player_data_copy = copy.deepcopy(player_data)
        try:
            await asyncio.sleep(self._debounce_cooldown)

            # Check if the debounce task was cancelled before proceeding.
            if (
                # ...dangling task when cancelled via config entry reload
                self._debounce_task is None or
                # ...dangling task when failed to cancel properly
                self._debounce_task.cancelled()
            ):
                _LOGGER.debug("Debounce update cancelled after cooldown.")
                return

            _LOGGER.debug("Cooldown passed, applying debounced update.")
            self._process_player_data(player_data_copy)
        except asyncio.CancelledError:
            _LOGGER.debug("Debounce update cancelled within cooldown window.")
        finally:
            self._debounce_task = None

    def _process_player_data(self, player_data):
        """Update entity state from player data"""
        state = player_data.get("state", None)
        if state is not None:
            self._playing_state = STATE_DICT.get(state, STATE_IDLE)

        track_roles = player_data.get("trackRoles", {})
        self._media_title = track_roles.get("title")
        self._image_url = track_roles.get("icon")
        media_data = track_roles.get("mediaData", {})
        meta_data = media_data.get("metaData", {})
        self._artist = meta_data.get("artist")
        self._album = meta_data.get("album")


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Setup media player from a config entry created in the integrations UI."""

    ambeo_api: AmbeoApi = hass.data[DOMAIN][config_entry.entry_id]["api"]
    ambeo_device = hass.data[DOMAIN][config_entry.entry_id]["device"]
    sources = await ambeo_api.get_all_sources()
    presets = await ambeo_api.get_all_presets()
    ambeo_player = AmbeoMediaPlayer(
        ambeo_device, ambeo_api, sources, presets, config_entry)
    async_add_entities([ambeo_player], update_before_add=True)
