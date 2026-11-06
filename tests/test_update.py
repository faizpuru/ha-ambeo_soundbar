"""Tests for the Ambeo Soundbar update entity."""

from unittest.mock import MagicMock

from homeassistant.components.update import UpdateDeviceClass, UpdateEntityFeature
from homeassistant.const import EntityCategory
from pyambeo import StateKey

from custom_components.ambeo_soundbar.coordinator import AmbeoCoordinator
from custom_components.ambeo_soundbar.update import FirmwareUpdate, async_setup_entry


def _make_coordinator(data=None, latest=None, progress=None):
    coordinator = MagicMock(spec=AmbeoCoordinator)
    coordinator.data = data if data is not None else {}
    coordinator.get_latest_firmware_version = MagicMock(return_value=latest)
    coordinator.get_firmware_update_progress = MagicMock(return_value=progress)
    return coordinator


def _make_device():
    device = MagicMock()
    device.serial = "SN123456"
    device.version = "1.0.100"
    return device


class TestFirmwareUpdate:
    """Tests for the FirmwareUpdate entity."""

    def test_attributes(self):
        """Describe a read-only firmware update showing its progress."""
        entity = FirmwareUpdate(_make_coordinator(), _make_device())
        assert entity.device_class == UpdateDeviceClass.FIRMWARE
        assert entity.supported_features == UpdateEntityFeature.PROGRESS
        assert entity.entity_category == EntityCategory.DIAGNOSTIC
        assert entity.unique_id == "SN123456_firmware"

    def test_up_to_date(self):
        """Report the installed version as the latest when no update is found."""
        coordinator = _make_coordinator(
            data={StateKey.FIRMWARE_VERSION: "1.0.134"}, latest="1.0.134"
        )
        entity = FirmwareUpdate(coordinator, _make_device())
        assert entity.installed_version == "1.0.134"
        assert entity.latest_version == "1.0.134"
        assert entity.in_progress is False
        assert entity.update_percentage is None

    def test_update_available(self):
        """Report the version found by the soundbar."""
        coordinator = _make_coordinator(
            data={StateKey.FIRMWARE_VERSION: "1.0.134"}, latest="1.0.140"
        )
        entity = FirmwareUpdate(coordinator, _make_device())
        assert entity.latest_version == "1.0.140"

    def test_downloading(self):
        """Show the download progress."""
        coordinator = _make_coordinator(
            data={StateKey.FIRMWARE_VERSION: "1.0.134"}, latest="1.0.140", progress=42
        )
        entity = FirmwareUpdate(coordinator, _make_device())
        assert entity.in_progress is True
        assert entity.update_percentage == 42

    def test_version_read_at_setup(self):
        """Fall back to the version read at setup when the state has none."""
        entity = FirmwareUpdate(_make_coordinator(), _make_device())
        assert entity.installed_version == "1.0.100"
        assert entity.latest_version == "1.0.100"


class TestUpdateSetupEntry:
    """Tests for update platform setup entry."""

    async def test_adds_firmware_update(self):
        """Add the firmware update entity for every model."""
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = _make_coordinator()
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert len(added) == 1
        assert isinstance(added[0], FirmwareUpdate)
