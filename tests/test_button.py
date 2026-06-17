"""Tests for Ambeo Soundbar button entities."""

from unittest.mock import AsyncMock, MagicMock

from homeassistant.components.button import ButtonDeviceClass
from homeassistant.const import EntityCategory

from custom_components.ambeo_soundbar.api.const import Capability
from custom_components.ambeo_soundbar.button import (
    AmbeoReboot,
    ResetExpertSettings,
    async_setup_entry,
)


def _make_coordinator(capabilities=None):
    coordinator = MagicMock()
    coordinator.has_capability = MagicMock(
        side_effect=lambda cap: cap in (capabilities or [])
    )
    coordinator.async_reboot = AsyncMock()
    coordinator.async_reset_expert_settings = AsyncMock()
    return coordinator


def _make_device():
    device = MagicMock()
    device.serial = "SN123456"
    return device


class TestAmbeoReboot:
    """Tests for the AmbeoReboot button entity."""

    async def test_press_calls_reboot(self):
        """Call coordinator.async_reboot when the button is pressed."""
        coordinator = _make_coordinator()
        entity = AmbeoReboot(coordinator, _make_device())
        await entity.async_press()
        coordinator.async_reboot.assert_awaited_once()

    def test_entity_category_is_config(self):
        """Expose the reboot button under the CONFIG entity category."""
        coordinator = _make_coordinator()
        entity = AmbeoReboot(coordinator, _make_device())
        assert entity.entity_category == EntityCategory.CONFIG

    def test_device_class_is_restart(self):
        """Use the RESTART device class for the reboot button."""
        coordinator = _make_coordinator()
        entity = AmbeoReboot(coordinator, _make_device())
        assert entity.device_class == ButtonDeviceClass.RESTART


class TestResetExpertSettings:
    """Tests for the ResetExpertSettings button entity."""

    async def test_press_calls_reset(self):
        """Call coordinator.async_reset_expert_settings when the button is pressed."""
        coordinator = _make_coordinator()
        entity = ResetExpertSettings(coordinator, _make_device())
        await entity.async_press()
        coordinator.async_reset_expert_settings.assert_awaited_once()

    def test_entity_category_is_config(self):
        """Expose the reset button under the CONFIG entity category."""
        coordinator = _make_coordinator()
        entity = ResetExpertSettings(coordinator, _make_device())
        assert entity.entity_category == EntityCategory.CONFIG


class TestButtonSetupEntry:
    """Tests for button platform setup entry."""

    async def test_always_adds_reboot(self):
        """Always add AmbeoReboot regardless of capabilities."""
        coordinator = _make_coordinator()
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert any(isinstance(e, AmbeoReboot) for e in added)

    async def test_adds_reset_when_capable(self):
        """Add ResetExpertSettings when device reports RESET_EXPERT_SETTINGS capability."""
        coordinator = _make_coordinator(capabilities=[Capability.RESET_EXPERT_SETTINGS])
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert any(isinstance(e, ResetExpertSettings) for e in added)

    async def test_no_reset_when_not_capable(self):
        """Omit ResetExpertSettings when device lacks RESET_EXPERT_SETTINGS capability."""
        coordinator = _make_coordinator()
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert not any(isinstance(e, ResetExpertSettings) for e in added)
