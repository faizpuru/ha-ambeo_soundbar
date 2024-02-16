import logging
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .api import AmbeoApi


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
    
    @property
    def max_compat(self):
        return self.model == "AMBEO Soundbar Max"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):    
    _LOGGER.debug("Démarrage de la configuration du composant ambeo")
    config = entry.data
    host = config.get("host")
    port = 80
    ambeo_api = AmbeoApi(host, port, aiohttp.ClientSession(), hass)
    serial= await ambeo_api.get_serial()
    if serial is None:
        raise ConfigEntryNotReady(f"Can't connect to host : {host}") 
    model= await ambeo_api.get_model()
    name= await ambeo_api.get_name()
    version= await ambeo_api.get_version()
    manufacturer= "Sennheiser"
    device = AmbeoDevice(serial, name, manufacturer, model, version, host, port)
    ambeo_api._ambeo_max_compat = device.max_compat
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
         manufacturer=manufacturer,
         model=model,
         sw_version=version)

    hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, "media_player"))
    hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, "switch"))
    hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, "light"))
    hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, "button"))
    return True