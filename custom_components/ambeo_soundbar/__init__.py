import logging
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr

from .const import DEFAULT_PORT, DOMAIN, MANUFACTURER, MAX_SOUNDBAR
from .coordinator import AmbeoCoordinator


_LOGGER = logging.getLogger(__name__)


class AmbeoDevice:
    def __init__(self, serial, name):
        self._serial = serial
        self._name = name

    @property
    def serial(self):
        return self._serial

    @property
    def name(self):
        return self._name


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    _LOGGER.debug("Démarrage de la configuration du composant ambeo")
    config = entry.data
    host = config.get("host")
    coordinator = AmbeoCoordinator(
        hass, host, DEFAULT_PORT, aiohttp.ClientSession(), 10)
    await coordinator._async_setup()
    ambeo_api = coordinator.get_api()
    serial = coordinator.get_serial()
    model = coordinator.get_model()
    name = coordinator.get_name()
    version = coordinator.get_version()
    device = AmbeoDevice(serial, name)
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.debug("Data initialized")
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "device": device
    }
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, serial)},
        name=name,
        manufacturer=MANUFACTURER,
        model=model,
        sw_version=version)

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(
            entry, ["media_player", "switch", "light", "button"]
        )
    )
    return True
