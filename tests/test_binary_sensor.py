"""Tests for Ambeo Soundbar binary sensor entities."""

from unittest.mock import MagicMock

from custom_components.ambeo_soundbar.api.const import Capability
from custom_components.ambeo_soundbar.binary_sensor import (
    EcoModeSensor,
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


class TestEcoModeSensor:
    """Tests for the EcoModeSensor binary sensor entity."""

    def test_is_on_true(self):
        """Return True when eco_mode data is True."""
        coordinator = _make_coordinator(data={"eco_mode": True})
        entity = EcoModeSensor(coordinator, _make_device())
        assert entity.is_on is True

    def test_is_on_false(self):
        """Return False when eco_mode data is False."""
        coordinator = _make_coordinator(data={"eco_mode": False})
        entity = EcoModeSensor(coordinator, _make_device())
        assert entity.is_on is False

    def test_is_on_none_when_key_missing(self):
        """Return None when eco_mode key is absent from data."""
        coordinator = _make_coordinator(data={})
        entity = EcoModeSensor(coordinator, _make_device())
        assert entity.is_on is None

    def test_is_on_none_when_no_data(self):
        """Return None when coordinator has no data yet."""
        coordinator = _make_coordinator()
        coordinator.data = None
        entity = EcoModeSensor(coordinator, _make_device())
        assert entity.is_on is None


class TestBinarySensorSetupEntry:
    """Tests for binary sensor platform setup entry."""

    async def test_adds_eco_mode_when_capable(self):
        """Add EcoModeSensor when device reports ECO_MODE capability."""
        coordinator = _make_coordinator(capabilities=[Capability.ECO_MODE])
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert any(isinstance(e, EcoModeSensor) for e in added)

    async def test_no_eco_mode_when_not_capable(self):
        """Add no entities when device lacks ECO_MODE capability."""
        coordinator = _make_coordinator()
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert not added
