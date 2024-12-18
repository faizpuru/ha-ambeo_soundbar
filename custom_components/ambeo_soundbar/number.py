import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.number import NumberDeviceClass


from .const import DOMAIN, Capability
from .entity import AmbeoBaseNumber

from .api.impl.generic_api import AmbeoApi


_LOGGER = logging.getLogger(__name__)


class SubWooferVolume(AmbeoBaseNumber):
    def __init__(self, device, api):
        """Initialize the subwoofer volume."""
        super().__init__(device, api, "Subwoofer volume")

    async def async_set_native_value(self, value: float) -> None:
        """Update the volume of the subwoofer."""
        await self.api.set_subwoofer_volume(value)
        self._current_value = value

    async def async_update(self):
        """Update the current volume of the subwoofer."""
        try:
            volume = await self.api.get_subwoofer_volume()
            self._current_value = volume
        except Exception as e:
            _LOGGER.error(f"Failed to update subwoofer status: {e}")

    @property
    def native_step(self):
        """Step"""
        return 1

    @property
    def native_min_value(self):
        """Min value """
        return -10

    @property
    def native_max_value(self):
        """Max value"""
        return 10

    @property
    def native_unit_of_measurement(self):
        """Unit"""
        return "dB"

    @property
    def device_class(self):
        """Device class"""
        NumberDeviceClass.SOUND_PRESSURE


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Set up the switch entities from a config entry created in the integrations UI."""
    ambeo_api: AmbeoApi = hass.data[DOMAIN][config_entry.entry_id]["api"]
    ambeo_device = hass.data[DOMAIN][config_entry.entry_id]["device"]
    entities = []
    if ambeo_api.has_capability(Capability.SUBWOOFER) and await ambeo_api.has_subwoofer():
        entities.append(SubWooferVolume(ambeo_device, ambeo_api))
    async_add_entities(entities, update_before_add=True)
