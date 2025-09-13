import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import DOMAIN, Capability
from .entity import AmbeoBaseEntity
from .api.impl.generic_api import AmbeoApi


_LOGGER = logging.getLogger(__name__)


class EcoModeSensor(AmbeoBaseEntity, BinarySensorEntity):
    def __init__(self, device, api):
        """Initialize the Eco Mode sensor."""
        super().__init__(device, api, "Eco Mode", "eco_mode")
        self._is_on = None

    @property
    def is_on(self):
        """Return the current value of the sensor."""
        return self._is_on

    @property
    def available(self):
        """Return if the sensor is available."""
        return self._is_on is not None

    async def async_update(self):
        """Update the current status of the eco mode."""
        _LOGGER.debug("Updating eco mode sensor...")
        try:
            status = await self.api.get_eco_mode()
            self._is_on = status
        except Exception as e:
            _LOGGER.error("Failed to update eco mode status: %s", e)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Set up the sensor entities from a config entry created in the integrations UI."""
    ambeo_api: AmbeoApi = hass.data[DOMAIN][config_entry.entry_id]["api"]
    ambeo_device = hass.data[DOMAIN][config_entry.entry_id]["device"]
    entities = []
    if ambeo_api.has_capability(Capability.ECO_MODE):
        entities.append(EcoModeSensor(ambeo_device, ambeo_api))
    async_add_entities(entities, update_before_add=True)
