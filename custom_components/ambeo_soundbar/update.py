"""Update entity for Ambeo Soundbar integration."""

from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
    UpdateEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from pyambeo import StateKey

from . import AmbeoConfigEntry, AmbeoDevice
from .coordinator import AmbeoCoordinator
from .entity import AmbeoBaseEntity

PARALLEL_UPDATES = 0


class FirmwareUpdate(AmbeoBaseEntity, UpdateEntity):
    """Firmware of the soundbar.

    Shows the update found by the soundbar and its download progress. Updates
    are installed from the Sennheiser app.
    """

    _attr_device_class = UpdateDeviceClass.FIRMWARE
    _attr_supported_features = UpdateEntityFeature.PROGRESS

    def __init__(self, coordinator: AmbeoCoordinator, device: AmbeoDevice) -> None:
        """Initialize the firmware update entity."""
        super().__init__(coordinator, device, "firmware", "firmware")

    @property
    def installed_version(self) -> str | None:
        """Return the installed firmware version."""
        version: str | None = None
        if self.coordinator.data:
            version = self.coordinator.data.get(StateKey.FIRMWARE_VERSION)
        return version or self.ambeo_device.version

    @property
    def latest_version(self) -> str | None:
        """Return the firmware version the soundbar can update to."""
        return self.coordinator.get_latest_firmware_version() or self.installed_version

    @property
    def in_progress(self) -> bool:
        """Return True while the soundbar downloads an update."""
        return self.update_percentage is not None

    @property
    def update_percentage(self) -> int | None:
        """Return the download progress of the update."""
        return self.coordinator.get_firmware_update_progress()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AmbeoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the firmware update entity from a config entry."""
    async_add_entities(
        [
            FirmwareUpdate(
                config_entry.runtime_data.coordinator, config_entry.runtime_data.device
            )
        ]
    )
