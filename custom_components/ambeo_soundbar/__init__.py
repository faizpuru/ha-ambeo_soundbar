import logging
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .const import DEFAULT_PORT, DOMAIN, MANUFACTURER
from .api.factory import AmbeoAPIFactory


_LOGGER = logging.getLogger(__name__)


class AmbeoDevice:
    def __init__(self, serial, name, manufacturer, model, version, host, port):
        self._serial = serial
        self.name = name
        self.manufacturer = manufacturer
        self.model = model
        self.version = version
        self.host = host
        self.port = port

    @property
    def serial(self):
        return self._serial


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    _LOGGER.debug("Démarrage de la configuration du composant ambeo")
    config = entry.data
    host = config.get("host")
    ambeo_api = await AmbeoAPIFactory.create_api(
        host, DEFAULT_PORT, aiohttp.ClientSession(), hass)
    serial = await ambeo_api.get_serial()
    model = await ambeo_api.get_model()
    name = await ambeo_api.get_name()
    version = await ambeo_api.get_version()
    device = AmbeoDevice(serial, name, MANUFACTURER,
                         model, version, host, DEFAULT_PORT)
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.debug("Data initialized")
    hass.data[DOMAIN][entry.entry_id] = {
        "api": ambeo_api,
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

    await hass.config_entries.async_forward_entry_setups(entry, ["media_player", "switch", "light", "button", "number"])

    return True
