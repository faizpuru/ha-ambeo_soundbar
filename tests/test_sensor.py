"""Tests for Ambeo Soundbar sensor entities."""

from unittest.mock import MagicMock

from custom_components.ambeo_soundbar.api.const import Capability
from custom_components.ambeo_soundbar.sensor import (
    DecoderStatusSensor,
    async_setup_entry,
)


def _make_coordinator(data=None, capabilities=None):
    coordinator = MagicMock()
    coordinator.data = data if data is not None else {}
    coordinator.has_capability = MagicMock(
        side_effect=lambda cap: cap in (capabilities or [])
    )
    return coordinator


def _make_device():
    device = MagicMock()
    device.serial = "SN123456"
    return device


class TestDecoderStatusSensor:
    """Tests for the DecoderStatusSensor diagnostic sensor entity."""

    def test_native_value_channels_key(self):
        """Read channel count from the 'channels' key in decoder_status."""
        coordinator = _make_coordinator(
            data={"decoder_status": {"channels": 6, "format": "DTS"}}
        )
        entity = DecoderStatusSensor(coordinator, _make_device())
        assert entity.native_value == 6

    def test_native_value_active_channels_fallback(self):
        """Fall back to 'active_channels' when 'channels' is absent."""
        coordinator = _make_coordinator(data={"decoder_status": {"active_channels": 2}})
        entity = DecoderStatusSensor(coordinator, _make_device())
        assert entity.native_value == 2

    def test_native_value_zero_when_no_decoder_status(self):
        """Return 0 when decoder_status key is absent from coordinator data."""
        coordinator = _make_coordinator(data={})
        entity = DecoderStatusSensor(coordinator, _make_device())
        assert entity.native_value == 0

    def test_native_value_zero_when_no_data(self):
        """Return 0 when coordinator has no data yet."""
        coordinator = _make_coordinator()
        coordinator.data = None
        entity = DecoderStatusSensor(coordinator, _make_device())
        assert entity.native_value == 0

    def test_extra_state_attributes_excludes_channels(self):
        """Exclude 'channels' from extra attributes and expose remaining fields."""
        coordinator = _make_coordinator(
            data={"decoder_status": {"channels": 6, "format": "DTS", "bitrate": 1536}}
        )
        entity = DecoderStatusSensor(coordinator, _make_device())
        attrs = entity.extra_state_attributes
        assert "channels" not in attrs
        assert attrs == {"format": "DTS", "bitrate": 1536}

    def test_extra_state_attributes_excludes_active_channels(self):
        """Exclude 'active_channels' from extra attributes and expose remaining fields."""
        coordinator = _make_coordinator(
            data={"decoder_status": {"active_channels": 2, "codec": "AAC"}}
        )
        entity = DecoderStatusSensor(coordinator, _make_device())
        attrs = entity.extra_state_attributes
        assert "active_channels" not in attrs
        assert attrs == {"codec": "AAC"}

    def test_extra_state_attributes_empty_when_no_data(self):
        """Return an empty dict when decoder_status is absent."""
        coordinator = _make_coordinator(data={})
        entity = DecoderStatusSensor(coordinator, _make_device())
        assert entity.extra_state_attributes == {}


class TestSensorSetupEntry:
    """Tests for sensor platform setup entry."""

    async def test_adds_decoder_status_when_capable(self):
        """Add DecoderStatusSensor when device reports DECODER_STATUS capability."""
        coordinator = _make_coordinator(capabilities=[Capability.DECODER_STATUS])
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert any(isinstance(e, DecoderStatusSensor) for e in added)

    async def test_no_decoder_status_when_not_capable(self):
        """Add no entities when device lacks DECODER_STATUS capability."""
        coordinator = _make_coordinator()
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert not added
