"""Tests for Ambeo Soundbar switch entities."""

from unittest.mock import AsyncMock, MagicMock

from custom_components.ambeo_soundbar.api.const import Capability
from custom_components.ambeo_soundbar.switch import (
    AmbeoBluetoothPairing,
    AmbeoMode,
    NightMode,
    SoundFeedback,
    SubWooferStatus,
    VoiceEnhancementMode,
    async_setup_entry,
)


def _make_coordinator(data=None, capabilities=None, has_subwoofer=False):
    coordinator = MagicMock()
    coordinator.data = data if data is not None else {}
    coordinator.has_capability = MagicMock(
        side_effect=lambda cap: cap in (capabilities or [])
    )
    coordinator.has_subwoofer = AsyncMock(return_value=has_subwoofer)
    coordinator.async_set_night_mode = AsyncMock()
    coordinator.async_set_ambeo_mode = AsyncMock()
    coordinator.async_set_sound_feedback = AsyncMock()
    coordinator.async_set_voice_enhancement = AsyncMock()
    coordinator.async_set_subwoofer_status = AsyncMock()
    coordinator.async_set_bluetooth_pairing_state = AsyncMock()
    return coordinator


def _make_device():
    device = MagicMock()
    device.serial = "SN123456"
    return device


class TestAmbeoBaseSwitch:
    """Tests for AmbeoBaseSwitch behaviour, exercised via NightMode."""

    def test_is_on_true(self):
        """Return True when the data key holds True."""
        coordinator = _make_coordinator(data={"night_mode": True})
        entity = NightMode(coordinator, _make_device())
        assert entity.is_on is True

    def test_is_on_false(self):
        """Return False when the data key holds False."""
        coordinator = _make_coordinator(data={"night_mode": False})
        entity = NightMode(coordinator, _make_device())
        assert entity.is_on is False

    def test_is_on_none_when_key_missing(self):
        """Return None when the data key is absent."""
        coordinator = _make_coordinator(data={})
        entity = NightMode(coordinator, _make_device())
        assert entity.is_on is None

    def test_is_on_none_when_no_data(self):
        """Return None when coordinator has no data yet."""
        coordinator = _make_coordinator()
        coordinator.data = None
        entity = NightMode(coordinator, _make_device())
        assert entity.is_on is None

    async def test_turn_on(self):
        """Call the coordinator setter with True when the switch is turned on."""
        coordinator = _make_coordinator(data={"night_mode": False})
        entity = NightMode(coordinator, _make_device())
        await entity.async_turn_on()
        coordinator.async_set_night_mode.assert_awaited_once_with(True)

    async def test_turn_off(self):
        """Call the coordinator setter with False when the switch is turned off."""
        coordinator = _make_coordinator(data={"night_mode": True})
        entity = NightMode(coordinator, _make_device())
        await entity.async_turn_off()
        coordinator.async_set_night_mode.assert_awaited_once_with(False)


class TestSwitchSetupEntry:
    """Tests for switch platform setup entry."""

    async def test_always_adds_base_switches(self):
        """Always add NightMode, AmbeoMode and SoundFeedback."""
        coordinator = _make_coordinator()
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        types = [type(e) for e in added]
        assert NightMode in types
        assert AmbeoMode in types
        assert SoundFeedback in types

    async def test_adds_voice_enhancement_when_capable(self):
        """Add VoiceEnhancementMode when device reports VOICE_ENHANCEMENT_TOGGLE capability."""
        coordinator = _make_coordinator(
            capabilities=[Capability.VOICE_ENHANCEMENT_TOGGLE]
        )
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert any(isinstance(e, VoiceEnhancementMode) for e in added)

    async def test_no_voice_enhancement_when_not_capable(self):
        """Omit VoiceEnhancementMode when device lacks VOICE_ENHANCEMENT_TOGGLE capability."""
        coordinator = _make_coordinator()
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert not any(isinstance(e, VoiceEnhancementMode) for e in added)

    async def test_adds_bluetooth_when_capable(self):
        """Add AmbeoBluetoothPairing when device reports BLUETOOTH_PAIRING capability."""
        coordinator = _make_coordinator(capabilities=[Capability.BLUETOOTH_PAIRING])
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert any(isinstance(e, AmbeoBluetoothPairing) for e in added)

    async def test_adds_subwoofer_status_when_capable_and_present(self):
        """Add SubWooferStatus when device has SUBWOOFER capability and a subwoofer is connected."""
        coordinator = _make_coordinator(
            capabilities=[Capability.SUBWOOFER], has_subwoofer=True
        )
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert any(isinstance(e, SubWooferStatus) for e in added)

    async def test_no_subwoofer_status_when_not_present(self):
        """Omit SubWooferStatus when no subwoofer is physically connected."""
        coordinator = _make_coordinator(
            capabilities=[Capability.SUBWOOFER], has_subwoofer=False
        )
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert not any(isinstance(e, SubWooferStatus) for e in added)
