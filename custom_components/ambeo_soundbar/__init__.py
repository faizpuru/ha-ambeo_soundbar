import logging
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import DEFAULT_PORT, DOMAIN, MANUFACTURER, CONFIG_HOST
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


async def _async_entry_updated(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle entry updates."""
    host = config_entry.options.get(CONFIG_HOST)
    hass.data[DOMAIN][config_entry.entry_id]["api"].set_endpoint(host)
    await hass.config_entries.async_reload(config_entry.entry_id)
    _LOGGER.info("Successfully updated configuration entries")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug("Starting configuration of ambeo entry")
    entry.async_on_unload(entry.add_update_listener(_async_entry_updated))

    host = entry.options.get(CONFIG_HOST, entry.data.get(CONFIG_HOST))
    session = async_create_clientsession(hass)

    ambeo_api = await AmbeoAPIFactory.create_api(host, DEFAULT_PORT, session, hass)
    try:
        serial = await ambeo_api.get_serial()
        model = await ambeo_api.get_model()
        name = await ambeo_api.get_name()
        version = await ambeo_api.get_version()
    except aiohttp.ClientError as ex:
        raise ConfigEntryNotReady(f"Could not connect to {host}: {ex}") from ex

    device = AmbeoDevice(serial, name, MANUFACTURER,
                         model, version, host, DEFAULT_PORT)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": ambeo_api,
        "device": device
    }
    _LOGGER.debug("Data initialized")

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, serial)},
        name=name,
        manufacturer=MANUFACTURER,
        model=model,
        sw_version=version)

    await hass.config_entries.async_forward_entry_setups(
        entry, ["media_player", "switch", "light",
                "button", "number", "binary_sensor"]
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle integration unload"""
    # Unload configuration
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, ["media_player", "switch",
                "light", "button", "number", "binary_sensor"]
    )
    if unload_ok and entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
