"""Tests for Ambeo Soundbar number entities."""

from unittest.mock import AsyncMock, MagicMock

from custom_components.ambeo_soundbar.api.const import Capability
from custom_components.ambeo_soundbar.number import (
    CenterSpeakerLevel,
    CenterVolume,
    NativeVolume,
    SideFiringLevel,
    SubWooferVolume,
    UpFiringLevel,
    VoiceEnhancementLevel,
    async_setup_entry,
)


def _make_coordinator(
    data=None, capabilities=None, has_subwoofer=False, volume_max=100
):
    coordinator = MagicMock()
    coordinator.data = data if data is not None else {}
    coordinator.has_capability = MagicMock(
        side_effect=lambda cap: cap in (capabilities or [])
    )
    coordinator.has_subwoofer = AsyncMock(return_value=has_subwoofer)
    coordinator.get_volume_max = MagicMock(return_value=volume_max)
    coordinator.get_subwoofer_min_value = MagicMock(return_value=-10)
    coordinator.get_subwoofer_max_value = MagicMock(return_value=10)
    coordinator.async_set_volume = AsyncMock()
    coordinator.async_set_subwoofer_volume = AsyncMock()
    coordinator.async_set_voice_enhancement_level = AsyncMock()
    coordinator.async_set_center_volume = AsyncMock()
    coordinator.async_set_center_speaker_level = AsyncMock()
    coordinator.async_set_side_firing_level = AsyncMock()
    coordinator.async_set_up_firing_level = AsyncMock()
    return coordinator


def _make_device():
    device = MagicMock()
    device.serial = "SN123456"
    return device


class TestNativeVolume:
    """Tests for the NativeVolume number entity."""

    def test_native_value_scales_volume(self):
        """Scale the percent volume to native units using volume_max."""
        coordinator = _make_coordinator(data={"volume": 50}, volume_max=100)
        entity = NativeVolume(coordinator, _make_device())
        assert entity.native_value == 50

    def test_native_value_rounds(self):
        """Round the scaled result to the nearest integer."""
        coordinator = _make_coordinator(data={"volume": 35}, volume_max=50)
        entity = NativeVolume(coordinator, _make_device())
        # 35 * 50 / 100 = 17.5 → 18 (banker's rounding: rounds to even)
        assert entity.native_value == 18

    def test_native_value_none_when_no_data(self):
        """Return None when volume key is absent from coordinator data."""
        coordinator = _make_coordinator(data={})
        entity = NativeVolume(coordinator, _make_device())
        assert entity.native_value is None

    def test_native_max_value(self):
        """Delegate native_max_value to coordinator.get_volume_max."""
        coordinator = _make_coordinator(volume_max=80)
        entity = NativeVolume(coordinator, _make_device())
        assert entity.native_max_value == 80

    async def test_set_native_value_converts_to_percent(self):
        """Convert native units back to percent before calling the coordinator."""
        coordinator = _make_coordinator(volume_max=100)
        entity = NativeVolume(coordinator, _make_device())
        await entity.async_set_native_value(75)
        coordinator.async_set_volume.assert_awaited_once_with(75)

    async def test_set_native_value_rounds(self):
        """Round the percent conversion result before calling the coordinator."""
        coordinator = _make_coordinator(volume_max=50)
        entity = NativeVolume(coordinator, _make_device())
        # 17 * 100 / 50 = 34
        await entity.async_set_native_value(17)
        coordinator.async_set_volume.assert_awaited_once_with(34)


class TestSubWooferVolume:
    """Tests for the SubWooferVolume number entity."""

    def test_native_min_value(self):
        """Delegate native_min_value to coordinator.get_subwoofer_min_value."""
        coordinator = _make_coordinator()
        entity = SubWooferVolume(coordinator, _make_device())
        assert entity.native_min_value == -10

    def test_native_max_value(self):
        """Delegate native_max_value to coordinator.get_subwoofer_max_value."""
        coordinator = _make_coordinator()
        entity = SubWooferVolume(coordinator, _make_device())
        assert entity.native_max_value == 10

    def test_native_value_from_data(self):
        """Return the subwoofer_volume value from coordinator data."""
        coordinator = _make_coordinator(data={"subwoofer_volume": -3})
        entity = SubWooferVolume(coordinator, _make_device())
        assert entity.native_value == -3

    def test_native_value_none_when_missing(self):
        """Return None when subwoofer_volume key is absent."""
        coordinator = _make_coordinator(data={})
        entity = SubWooferVolume(coordinator, _make_device())
        assert entity.native_value is None


class TestVoiceEnhancementLevel:
    """Tests for the VoiceEnhancementLevel number entity."""

    async def test_set_native_value_casts_to_int(self):
        """Cast the float value to int before calling the coordinator."""
        coordinator = _make_coordinator()
        entity = VoiceEnhancementLevel(coordinator, _make_device())
        await entity.async_set_native_value(2.0)
        coordinator.async_set_voice_enhancement_level.assert_awaited_once_with(2)


class TestCenterVolume:
    """Tests for the CenterVolume number entity."""

    async def test_set_native_value_casts_to_int(self):
        """Cast the float value to int before calling the coordinator."""
        coordinator = _make_coordinator()
        entity = CenterVolume(coordinator, _make_device())
        await entity.async_set_native_value(3.0)
        coordinator.async_set_center_volume.assert_awaited_once_with(3)


class TestSpeakerLevels:
    """Tests for CenterSpeakerLevel, SideFiringLevel and UpFiringLevel number entities."""

    async def test_center_speaker_level_set(self):
        """Call async_set_center_speaker_level with the int value."""
        coordinator = _make_coordinator()
        entity = CenterSpeakerLevel(coordinator, _make_device())
        await entity.async_set_native_value(6.0)
        coordinator.async_set_center_speaker_level.assert_awaited_once_with(6)

    async def test_side_firing_level_set(self):
        """Call async_set_side_firing_level with the int value."""
        coordinator = _make_coordinator()
        entity = SideFiringLevel(coordinator, _make_device())
        await entity.async_set_native_value(-4.0)
        coordinator.async_set_side_firing_level.assert_awaited_once_with(-4)

    async def test_up_firing_level_set(self):
        """Call async_set_up_firing_level with the int value."""
        coordinator = _make_coordinator()
        entity = UpFiringLevel(coordinator, _make_device())
        await entity.async_set_native_value(0.0)
        coordinator.async_set_up_firing_level.assert_awaited_once_with(0)


class TestNumberSetupEntry:
    """Tests for number platform setup entry."""

    async def test_adds_native_volume_when_capable(self):
        """Add NativeVolume when device reports NATIVE_VOLUME capability."""
        coordinator = _make_coordinator(capabilities=[Capability.NATIVE_VOLUME])
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert any(isinstance(e, NativeVolume) for e in added)

    async def test_adds_subwoofer_volume_when_capable_and_present(self):
        """Add SubWooferVolume when device has SUBWOOFER capability and a subwoofer is connected."""
        coordinator = _make_coordinator(
            capabilities=[Capability.SUBWOOFER], has_subwoofer=True
        )
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert any(isinstance(e, SubWooferVolume) for e in added)

    async def test_no_subwoofer_volume_when_not_present(self):
        """Omit SubWooferVolume when no subwoofer is physically connected."""
        coordinator = _make_coordinator(
            capabilities=[Capability.SUBWOOFER], has_subwoofer=False
        )
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert not any(isinstance(e, SubWooferVolume) for e in added)

    async def test_adds_voice_enhancement_level_when_capable(self):
        """Add VoiceEnhancementLevel when device reports VOICE_ENHANCEMENT_LEVEL capability."""
        coordinator = _make_coordinator(
            capabilities=[Capability.VOICE_ENHANCEMENT_LEVEL]
        )
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert any(isinstance(e, VoiceEnhancementLevel) for e in added)

    async def test_adds_speaker_levels_when_capable(self):
        """Add the three speaker level entities when their capabilities are present."""
        coordinator = _make_coordinator(
            capabilities=[
                Capability.CENTER_SPEAKER_LEVEL,
                Capability.SIDE_FIRING_LEVEL,
                Capability.UP_FIRING_LEVEL,
            ]
        )
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        types = [type(e) for e in added]
        assert CenterSpeakerLevel in types
        assert SideFiringLevel in types
        assert UpFiringLevel in types

    async def test_adds_center_volume_when_capable(self):
        """Add CenterVolume when device reports CENTER_VOLUME capability."""
        coordinator = _make_coordinator(capabilities=[Capability.CENTER_VOLUME])
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert any(isinstance(e, CenterVolume) for e in added)

    async def test_no_entities_when_no_capabilities(self):
        """Add no entities when device has no relevant capabilities."""
        coordinator = _make_coordinator()
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert not added
