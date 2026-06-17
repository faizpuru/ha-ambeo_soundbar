"""Tests for Ambeo Soundbar select entities."""

from unittest.mock import AsyncMock, MagicMock

from custom_components.ambeo_soundbar.api.const import Capability
from custom_components.ambeo_soundbar.select import (
    AmbeoModeLevel,
    SoundModeSelect,
    SourceSelect,
    async_setup_entry,
)

SOURCES = [
    {"id": "hdmi1", "title": "HDMI 1"},
    {"id": "optical", "title": "Optical"},
    {"id": "bluetooth", "title": "Bluetooth"},
]

PRESETS = [
    {"id": "movies", "title": "Movies"},
    {"id": "music", "title": "Music"},
    {"id": "neutral", "title": "Neutral"},
]


def _make_coordinator(sources=None, presets=None, data=None, capabilities=None):
    coordinator = MagicMock()
    coordinator.sources = sources or []
    coordinator.presets = presets or []
    coordinator.data = data or {}
    coordinator.has_capability = MagicMock(
        side_effect=lambda cap: cap in (capabilities or [])
    )
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
    coordinator.async_select_source = AsyncMock()
    coordinator.async_select_sound_mode = AsyncMock()
    coordinator.async_set_ambeo_mode = AsyncMock()
    coordinator.async_set_ambeo_mode_level = AsyncMock()
    return coordinator


def _make_device():
    device = MagicMock()
    device.serial = "SN123456"
    return device


class TestSourceSelect:
    """Tests for the SourceSelect entity."""

    def test_options_are_sorted(self):
        """Sort source options alphabetically."""
        coordinator = _make_coordinator(sources=SOURCES)
        entity = SourceSelect(coordinator, _make_device())
        assert entity._attr_options == ["Bluetooth", "HDMI 1", "Optical"]

    def test_current_option_returns_title(self):
        """Resolve the current source ID to its display title."""
        coordinator = _make_coordinator(
            sources=SOURCES, data={"current_source": "optical"}
        )
        entity = SourceSelect(coordinator, _make_device())
        assert entity.current_option == "Optical"

    def test_current_option_none_when_no_data(self):
        """Return None when current_source key is absent."""
        coordinator = _make_coordinator(sources=SOURCES, data={})
        entity = SourceSelect(coordinator, _make_device())
        assert entity.current_option is None

    def test_current_option_none_when_data_is_falsy(self):
        """Return None when coordinator has no data yet."""
        coordinator = _make_coordinator(sources=SOURCES)
        coordinator.data = None
        entity = SourceSelect(coordinator, _make_device())
        assert entity.current_option is None

    async def test_select_option_calls_coordinator(self):
        """Resolve the title to an ID and call coordinator.async_select_source."""
        coordinator = _make_coordinator(
            sources=SOURCES, data={"current_source": "hdmi1"}
        )
        entity = SourceSelect(coordinator, _make_device())
        await entity.async_select_option("Optical")
        coordinator.async_select_source.assert_awaited_once_with("optical")

    async def test_select_option_unknown_title_does_nothing(self):
        """Do nothing when the selected title cannot be resolved to a source ID."""
        coordinator = _make_coordinator(sources=SOURCES)
        entity = SourceSelect(coordinator, _make_device())
        await entity.async_select_option("Unknown Source")
        coordinator.async_select_source.assert_not_awaited()

    def test_disabled_by_default(self):
        """Be disabled in the entity registry by default."""
        coordinator = _make_coordinator(sources=SOURCES)
        entity = SourceSelect(coordinator, _make_device())
        assert entity.entity_registry_enabled_default is False


class TestSoundModeSelect:
    """Tests for the SoundModeSelect entity."""

    def test_options_are_sorted(self):
        """Sort preset options alphabetically."""
        coordinator = _make_coordinator(presets=PRESETS)
        entity = SoundModeSelect(coordinator, _make_device())
        assert entity._attr_options == ["Movies", "Music", "Neutral"]

    def test_current_option_returns_title(self):
        """Resolve the current preset ID to its display title."""
        coordinator = _make_coordinator(
            presets=PRESETS, data={"current_preset": "music"}
        )
        entity = SoundModeSelect(coordinator, _make_device())
        assert entity.current_option == "Music"

    def test_current_option_none_when_no_data(self):
        """Return None when current_preset key is absent."""
        coordinator = _make_coordinator(presets=PRESETS, data={})
        entity = SoundModeSelect(coordinator, _make_device())
        assert entity.current_option is None

    def test_current_option_none_when_data_is_falsy(self):
        """Return None when coordinator has no data yet."""
        coordinator = _make_coordinator(presets=PRESETS)
        coordinator.data = None
        entity = SoundModeSelect(coordinator, _make_device())
        assert entity.current_option is None

    async def test_select_option_calls_coordinator(self):
        """Resolve the title to an ID and call coordinator.async_select_sound_mode."""
        coordinator = _make_coordinator(
            presets=PRESETS, data={"current_preset": "movies"}
        )
        entity = SoundModeSelect(coordinator, _make_device())
        await entity.async_select_option("Music")
        coordinator.async_select_sound_mode.assert_awaited_once_with("music")

    async def test_select_option_unknown_title_does_nothing(self):
        """Do nothing when the selected title cannot be resolved to a preset ID."""
        coordinator = _make_coordinator(presets=PRESETS)
        entity = SoundModeSelect(coordinator, _make_device())
        await entity.async_select_option("Unknown Preset")
        coordinator.async_select_sound_mode.assert_not_awaited()

    def test_disabled_by_default(self):
        """Be disabled in the entity registry by default."""
        coordinator = _make_coordinator(presets=PRESETS)
        entity = SoundModeSelect(coordinator, _make_device())
        assert entity.entity_registry_enabled_default is False


class TestAmbeoModeLevel:
    """Tests for the AmbeoModeLevel select entity."""

    def test_current_option_off_when_ambeo_mode_false(self):
        """Return 'Off' when ambeo_mode is False regardless of level."""
        coordinator = _make_coordinator(data={"ambeo_mode": False})
        entity = AmbeoModeLevel(coordinator, _make_device())
        assert entity.current_option == "Off"

    def test_current_option_level_name(self):
        """Return the level name when ambeo_mode is True and a level is set."""
        coordinator = _make_coordinator(
            data={"ambeo_mode": True, "ambeo_mode_level": 2}
        )
        entity = AmbeoModeLevel(coordinator, _make_device())
        assert entity.current_option == "Regular"

    def test_current_option_none_when_no_data(self):
        """Return None when coordinator has no data yet."""
        coordinator = _make_coordinator(data={})
        coordinator.data = None
        entity = AmbeoModeLevel(coordinator, _make_device())
        assert entity.current_option is None

    async def test_select_off_disables_ambeo_mode(self):
        """Call async_set_ambeo_mode(False) when 'Off' is selected."""
        coordinator = _make_coordinator(
            data={"ambeo_mode": True, "ambeo_mode_level": 3}
        )
        entity = AmbeoModeLevel(coordinator, _make_device())
        await entity.async_select_option("Off")
        coordinator.async_set_ambeo_mode.assert_awaited_once_with(False)
        coordinator.async_set_ambeo_mode_level.assert_not_awaited()

    async def test_select_level_enables_mode_and_sets_level(self):
        """Enable Ambeo mode and set the level when a non-Off option is selected."""
        coordinator = _make_coordinator(data={"ambeo_mode": False})
        entity = AmbeoModeLevel(coordinator, _make_device())
        await entity.async_select_option("Boost")
        coordinator.async_set_ambeo_mode.assert_awaited_once_with(True)
        coordinator.async_set_ambeo_mode_level.assert_awaited_once_with(3)


class TestAsyncSetupEntry:
    """Tests for select platform setup entry."""

    async def test_adds_ambeo_mode_level_when_capable(self):
        """Add AmbeoModeLevel when device reports AMBEO_MODE_LEVEL capability."""
        coordinator = _make_coordinator(capabilities=[Capability.AMBEO_MODE_LEVEL])
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert any(isinstance(e, AmbeoModeLevel) for e in added)

    async def test_no_ambeo_mode_level_when_not_capable(self):
        """Omit AmbeoModeLevel when device lacks AMBEO_MODE_LEVEL capability."""
        coordinator = _make_coordinator()
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert not any(isinstance(e, AmbeoModeLevel) for e in added)

    async def test_adds_source_select_when_sources_present(self):
        """Add SourceSelect when the device has at least one source."""
        coordinator = _make_coordinator(sources=SOURCES)
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert any(isinstance(e, SourceSelect) for e in added)

    async def test_no_source_select_when_no_sources(self):
        """Omit SourceSelect when the device has no sources."""
        coordinator = _make_coordinator(sources=[])
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert not any(isinstance(e, SourceSelect) for e in added)

    async def test_adds_sound_mode_select_when_presets_present(self):
        """Add SoundModeSelect when the device has at least one preset."""
        coordinator = _make_coordinator(presets=PRESETS)
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert any(isinstance(e, SoundModeSelect) for e in added)

    async def test_no_sound_mode_select_when_no_presets(self):
        """Omit SoundModeSelect when the device has no presets."""
        coordinator = _make_coordinator(presets=[])
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert not any(isinstance(e, SoundModeSelect) for e in added)
