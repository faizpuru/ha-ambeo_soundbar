import logging
import aiohttp
from .const import DOMAIN
from .api import AmbeoApi
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers import device_registry as dr


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
    def device_info(self):
        return DeviceInfo(
            identifiers={
                (DOMAIN, self.serial)
            },
            name=self.name,
            manufacturer=self.manufacturer,
            model=self.model,
            sw_version=self.version),


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):    
    _LOGGER.debug("Démarrage de la configuration du composant ambeo")
    config = entry.data
    host = config.get("host")
    port = 80
    ambeo_api = AmbeoApi(host, port, aiohttp.ClientSession(), hass)
    serial= await ambeo_api.get_serial()
    model= await ambeo_api.get_model()
    name= await ambeo_api.get_name()
    version= await ambeo_api.get_version()
    manufacturer= "Sennheiser"
    device = AmbeoDevice(serial, name, manufacturer, model, version, host, port)
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.warning("Data initialized")
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

    return True