"""Tests for Ambeo Soundbar media player entity."""

from unittest.mock import AsyncMock, MagicMock

from homeassistant.const import STATE_IDLE, STATE_ON, STATE_PLAYING

from custom_components.ambeo_soundbar.api.const import Capability
from custom_components.ambeo_soundbar.media_player import (
    AmbeoMediaPlayer,
    async_setup_entry,
)

SOURCES = [
    {"id": "hdmi1", "title": "HDMI 1"},
    {"id": "optical", "title": "Optical"},
]

PRESETS = [
    {"id": "movies", "title": "Movies"},
    {"id": "music", "title": "Music"},
]


def _make_coordinator(data=None, capabilities=None, sources=None, presets=None):
    coordinator = MagicMock()
    coordinator.data = data if data is not None else {}
    coordinator.sources = sources or []
    coordinator.presets = presets or []
    coordinator.has_capability = MagicMock(
        side_effect=lambda cap: cap in (capabilities or [])
    )
    coordinator.get_volume_step = MagicMock(return_value=0.01)
    coordinator.get_volume_max = MagicMock(return_value=100)
    coordinator.get_state = MagicMock(return_value=STATE_ON)
    coordinator.get_source_title = MagicMock(
        side_effect=lambda sid: next(
            (s["title"] for s in (sources or []) if s["id"] == sid), None
        )
    )
    coordinator.get_source_id = MagicMock(
        side_effect=lambda title: next(
            (s["id"] for s in (sources or []) if s["title"] == title), None
        )
    )
    coordinator.get_preset_title = MagicMock(
        side_effect=lambda pid: next(
            (p["title"] for p in (presets or []) if p["id"] == pid), None
        )
    )
    coordinator.get_preset_id = MagicMock(
        side_effect=lambda title: next(
            (p["id"] for p in (presets or []) if p["title"] == title), None
        )
    )
    coordinator.async_set_volume = AsyncMock()
    coordinator.async_set_mute = AsyncMock()
    coordinator.async_turn_on = AsyncMock()
    coordinator.async_turn_off = AsyncMock()
    coordinator.async_select_source = AsyncMock()
    coordinator.async_select_sound_mode = AsyncMock()
    coordinator.async_media_play = AsyncMock()
    coordinator.async_media_pause = AsyncMock()
    coordinator.async_media_next_track = AsyncMock()
    coordinator.async_media_previous_track = AsyncMock()
    return coordinator


def _make_device():
    device = MagicMock()
    device.serial = "SN123456"
    return device


def _make_player(data=None, capabilities=None, sources=None, presets=None):
    coordinator = _make_coordinator(data, capabilities, sources, presets)
    return AmbeoMediaPlayer(coordinator, _make_device()), coordinator


class TestVolume:
    """Tests for volume-related properties and actions."""

    def test_volume_level(self):
        """Express volume as a 0.0–1.0 float."""
        player, _ = _make_player(data={"volume": 50})
        assert player.volume_level == 0.5

    def test_volume_level_none_when_missing(self):
        """Return None when volume is absent from coordinator data."""
        player, _ = _make_player(data={})
        assert player.volume_level is None

    def test_is_volume_muted_true(self):
        """Return True when muted flag is True."""
        player, _ = _make_player(data={"muted": True})
        assert player.is_volume_muted is True

    def test_is_volume_muted_false(self):
        """Return False when muted flag is False."""
        player, _ = _make_player(data={"muted": False})
        assert player.is_volume_muted is False

    def test_is_volume_muted_none_when_missing(self):
        """Return None when muted key is absent."""
        player, _ = _make_player(data={})
        assert player.is_volume_muted is None

    async def test_set_volume_level(self):
        """Multiply the 0.0–1.0 level by max_volume before passing to the coordinator."""
        player, coordinator = _make_player(data={"volume": 50})
        await player.async_set_volume_level(0.75)
        coordinator.async_set_volume.assert_awaited_once_with(75.0)

    async def test_mute_volume(self):
        """Forward the mute flag to coordinator.async_set_mute."""
        player, coordinator = _make_player()
        await player.async_mute_volume(True)
        coordinator.async_set_mute.assert_awaited_once_with(True)


class TestState:
    """Tests for power state properties and actions."""

    def test_state_delegates_to_coordinator(self):
        """Return whatever state the coordinator reports."""
        player, coordinator = _make_player()
        coordinator.get_state.return_value = STATE_PLAYING
        assert player.state == STATE_PLAYING

    async def test_turn_on(self):
        """Delegate turn-on to coordinator.async_turn_on."""
        player, coordinator = _make_player()
        await player.async_turn_on()
        coordinator.async_turn_on.assert_awaited_once()

    async def test_turn_off(self):
        """Delegate turn-off to coordinator.async_turn_off."""
        player, coordinator = _make_player()
        await player.async_turn_off()
        coordinator.async_turn_off.assert_awaited_once()


class TestSource:
    """Tests for input source selection."""

    def test_source_returns_title(self):
        """Resolve the current source ID to its display title."""
        player, _ = _make_player(data={"current_source": "hdmi1"}, sources=SOURCES)
        assert player.source == "HDMI 1"

    def test_source_none_when_missing(self):
        """Return None when current_source is absent from coordinator data."""
        player, _ = _make_player(data={}, sources=SOURCES)
        assert player.source is None

    def test_source_list_sorted(self):
        """Return source titles sorted alphabetically."""
        player, _ = _make_player(sources=SOURCES)
        assert player.source_list == ["HDMI 1", "Optical"]

    async def test_select_source_known(self):
        """Resolve the title to an ID and call coordinator.async_select_source."""
        player, coordinator = _make_player(sources=SOURCES)
        await player.async_select_source("Optical")
        coordinator.async_select_source.assert_awaited_once_with("optical")

    async def test_select_source_unknown_does_nothing(self):
        """Do nothing when the source title cannot be resolved to an ID."""
        player, coordinator = _make_player(sources=SOURCES)
        await player.async_select_source("ARC")
        coordinator.async_select_source.assert_not_awaited()

    async def test_select_source_none_does_nothing(self):
        """Do nothing when source is None."""
        player, coordinator = _make_player(sources=SOURCES)
        await player.async_select_source(None)
        coordinator.async_select_source.assert_not_awaited()


class TestSoundMode:
    """Tests for sound mode (preset) selection."""

    def test_sound_mode_returns_title(self):
        """Resolve the current preset ID to its display title."""
        player, _ = _make_player(data={"current_preset": "movies"}, presets=PRESETS)
        assert player.sound_mode == "Movies"

    def test_sound_mode_none_when_missing(self):
        """Return None when current_preset is absent from coordinator data."""
        player, _ = _make_player(data={}, presets=PRESETS)
        assert player.sound_mode is None

    def test_sound_mode_list_sorted(self):
        """Return preset titles sorted alphabetically."""
        player, _ = _make_player(presets=PRESETS)
        assert player.sound_mode_list == ["Movies", "Music"]

    async def test_select_sound_mode_known(self):
        """Resolve the title to an ID and call coordinator.async_select_sound_mode."""
        player, coordinator = _make_player(presets=PRESETS)
        await player.async_select_sound_mode("Music")
        coordinator.async_select_sound_mode.assert_awaited_once_with("music")

    async def test_select_sound_mode_unknown_does_nothing(self):
        """Do nothing when the preset title cannot be resolved to an ID."""
        player, coordinator = _make_player(presets=PRESETS)
        await player.async_select_sound_mode("Jazz")
        coordinator.async_select_sound_mode.assert_not_awaited()

    async def test_select_sound_mode_none_does_nothing(self):
        """Do nothing when sound_mode is None."""
        player, coordinator = _make_player(presets=PRESETS)
        await player.async_select_sound_mode(None)
        coordinator.async_select_sound_mode.assert_not_awaited()


class TestMediaInfo:
    """Tests for now-playing metadata properties."""

    def _player_with_track(self, track_title=None, media_title=None):
        player_data = {}
        if track_title:
            player_data["trackRoles"] = {"title": track_title}
        if media_title:
            player_data["mediaRoles"] = {"title": media_title}
        return _make_player(data={"player_data": player_data})

    def test_media_title_from_track_roles(self):
        """Return the track title from trackRoles when available."""
        player, _ = self._player_with_track(track_title="Song A")
        assert player.media_title == "Song A"

    def test_media_title_from_media_roles_fallback(self):
        """Fall back to mediaRoles title when trackRoles has no title."""
        player, _ = self._player_with_track(media_title="Radio Station")
        assert player.media_title == "Radio Station"

    def test_media_title_kept_while_playing(self):
        """Retain the last known title during playback when no new title arrives."""
        player, coordinator = self._player_with_track(track_title="Song A")
        _ = player.media_title  # prime _last_title
        player.coordinator.data = {"player_data": {}}
        coordinator.get_state.return_value = STATE_PLAYING
        assert player.media_title == "Song A"

    def test_media_title_none_when_stopped(self):
        """Clear the cached title when the player is no longer playing."""
        player, coordinator = self._player_with_track(track_title="Song A")
        _ = player.media_title
        player.coordinator.data = {"player_data": {}}
        coordinator.get_state.return_value = STATE_IDLE
        assert player.media_title is None

    def test_media_image_url_valid(self):
        """Return the artwork URL when it starts with http:// or https://."""
        player, _ = _make_player(
            data={
                "player_data": {"trackRoles": {"icon": "https://example.com/art.jpg"}}
            }
        )
        assert player.media_image_url == "https://example.com/art.jpg"

    def test_media_image_url_rejects_relative(self):
        """Return None when the icon URL is relative (not http/https)."""
        player, _ = _make_player(
            data={"player_data": {"trackRoles": {"icon": "/local/art.jpg"}}}
        )
        assert player.media_image_url is None

    def test_media_image_url_none_when_missing(self):
        """Return None when no icon is present in player data."""
        player, _ = _make_player(data={"player_data": {}})
        assert player.media_image_url is None

    def test_media_duration_converts_ms(self):
        """Convert duration from milliseconds to seconds."""
        player, _ = _make_player(data={"player_data": {"status": {"duration": 240000}}})
        assert player.media_duration == 240.0

    def test_media_duration_none_when_missing(self):
        """Return None when duration is absent from player data."""
        player, _ = _make_player(data={"player_data": {}})
        assert player.media_duration is None

    def test_media_position_converts_ms(self):
        """Convert play_time from milliseconds to seconds."""
        player, _ = _make_player(data={"player_data": {}, "play_time": 30000})
        assert player.media_position == 30.0

    def test_media_position_none_when_missing(self):
        """Return None when play_time is absent from coordinator data."""
        player, _ = _make_player(data={"player_data": {}})
        assert player.media_position is None

    def test_media_artist(self):
        """Return the artist from trackRoles metaData."""
        player, _ = _make_player(
            data={
                "player_data": {
                    "trackRoles": {
                        "mediaData": {
                            "metaData": {"artist": "Artist A", "album": "Album B"}
                        }
                    }
                }
            }
        )
        assert player.media_artist == "Artist A"

    def test_media_album_name(self):
        """Return the album from trackRoles metaData."""
        player, _ = _make_player(
            data={
                "player_data": {
                    "trackRoles": {
                        "mediaData": {
                            "metaData": {"artist": "Artist A", "album": "Album B"}
                        }
                    }
                }
            }
        )
        assert player.media_album_name == "Album B"


class TestSupportedFeatures:
    """Tests for the supported_features bitmask."""

    def test_includes_turn_on_off_when_standby_capable(self):
        """Include TURN_ON and TURN_OFF when device has STANDBY capability."""
        from homeassistant.components.media_player.const import MediaPlayerEntityFeature

        player, _ = _make_player(capabilities=[Capability.STANDBY])
        features = player.supported_features
        assert features & MediaPlayerEntityFeature.TURN_ON
        assert features & MediaPlayerEntityFeature.TURN_OFF

    def test_excludes_turn_on_off_without_standby(self):
        """Exclude TURN_ON and TURN_OFF when device lacks STANDBY capability."""
        from homeassistant.components.media_player.const import MediaPlayerEntityFeature

        player, _ = _make_player()
        features = player.supported_features
        assert not (features & MediaPlayerEntityFeature.TURN_ON)
        assert not (features & MediaPlayerEntityFeature.TURN_OFF)


class TestPlayback:
    """Tests for playback control actions."""

    async def test_media_play(self):
        """Delegate play to coordinator.async_media_play."""
        player, coordinator = _make_player()
        await player.async_media_play()
        coordinator.async_media_play.assert_awaited_once()

    async def test_media_pause(self):
        """Delegate pause to coordinator.async_media_pause."""
        player, coordinator = _make_player()
        await player.async_media_pause()
        coordinator.async_media_pause.assert_awaited_once()

    async def test_next_track(self):
        """Delegate next track to coordinator.async_media_next_track."""
        player, coordinator = _make_player()
        await player.async_media_next_track()
        coordinator.async_media_next_track.assert_awaited_once()

    async def test_previous_track(self):
        """Delegate previous track to coordinator.async_media_previous_track."""
        player, coordinator = _make_player()
        await player.async_media_previous_track()
        coordinator.async_media_previous_track.assert_awaited_once()


class TestMediaPlayerSetupEntry:
    """Tests for media player platform setup entry."""

    async def test_adds_media_player(self):
        """Always register exactly one AmbeoMediaPlayer entity."""
        coordinator = _make_coordinator()
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert len(added) == 1
        assert isinstance(added[0], AmbeoMediaPlayer)
