"""Binary sensor entities for Ambeo Soundbar integration."""

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant

from . import AmbeoConfigEntry
from .api.const import Capability
from .entity import AmbeoBaseEntity

_LOGGER = logging.getLogger(__name__)


class EcoModeSensor(AmbeoBaseEntity, BinarySensorEntity):
    """Binary sensor representing the eco mode state."""

    def __init__(self, coordinator, device):
        """Initialize the Eco Mode sensor."""
        super().__init__(coordinator, device, "Eco Mode", "eco_mode")

    @property
    def is_on(self):
        """Return the current value of the sensor."""
        if self.coordinator.data and "eco_mode" in self.coordinator.data:
            return self.coordinator.data["eco_mode"]
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AmbeoConfigEntry,
    async_add_entities,
):
    """Set up the sensor entities from a config entry created in the integrations UI."""
    coordinator = config_entry.runtime_data.coordinator
    ambeo_device = config_entry.runtime_data.device
    entities = []
    if coordinator.has_capability(Capability.ECO_MODE):
        entities.append(EcoModeSensor(coordinator, ambeo_device))
    async_add_entities(entities)
