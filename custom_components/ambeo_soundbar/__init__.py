"""Ambeo Soundbar integration setup."""

import logging
from dataclasses import dataclass

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api.factory import AmbeoAPIFactory
from .const import (
    CONFIG_HOST,
    CONFIG_UPDATE_INTERVAL,
    CONFIG_UPDATE_INTERVAL_DEFAULT,
    DEFAULT_PORT,
    DOMAIN,
    MANUFACTURER,
    PLATFORMS,
    TIMEOUT,
)
from .coordinator import AmbeoCoordinator

_LOGGER = logging.getLogger(__name__)

type AmbeoConfigEntry = ConfigEntry["AmbeoData"]


@dataclass
class AmbeoData:
    """Runtime data stored in config entry."""

    coordinator: AmbeoCoordinator
    device: "AmbeoDevice"


class AmbeoDevice:
    """Represent an Ambeo Soundbar device."""

    def __init__(self, serial, name, manufacturer, model, version, host, port):
        """Initialize an Ambeo device."""
        self._serial = serial
        self.name = name
        self.manufacturer = manufacturer
        self.model = model
        self.version = version
        self.host = host
        self.port = port

    @property
    def serial(self):
        """Return the serial number of the device."""
        return self._serial


async def _async_entry_updated(
    hass: HomeAssistant, config_entry: AmbeoConfigEntry
) -> None:
    """Handle entry updates."""
    host = config_entry.options.get(CONFIG_HOST)
    config_entry.runtime_data.coordinator.set_endpoint(host)
    await hass.config_entries.async_reload(config_entry.entry_id)
    _LOGGER.info("Successfully updated configuration entries")


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Ambeo Soundbar integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ambeo Soundbar from a config entry."""
    _LOGGER.debug("Starting configuration of ambeo entry")
    entry.async_on_unload(entry.add_update_listener(_async_entry_updated))

    host = entry.options.get(CONFIG_HOST, entry.data.get(CONFIG_HOST))
    update_interval = entry.options.get(
        CONFIG_UPDATE_INTERVAL,
        entry.data.get(CONFIG_UPDATE_INTERVAL, CONFIG_UPDATE_INTERVAL_DEFAULT),
    )
    session = async_create_clientsession(hass)

    ambeo_api = await AmbeoAPIFactory.create_api(host, DEFAULT_PORT, TIMEOUT, session)
    try:
        serial = await ambeo_api.get_serial() or "unknown_serial"
        model = await ambeo_api.get_model()
        name = await ambeo_api.get_name()
        version = await ambeo_api.get_version()
        sources = await ambeo_api.get_all_sources() or []
        presets = await ambeo_api.get_all_presets() or []
    except aiohttp.ClientError as ex:
        raise ConfigEntryNotReady(f"Could not connect to {host}: {ex}") from ex

    device = AmbeoDevice(serial, name, MANUFACTURER, model, version, host, DEFAULT_PORT)

    coordinator = AmbeoCoordinator(hass, ambeo_api, sources, presets, update_interval)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = AmbeoData(coordinator=coordinator, device=device)
    _LOGGER.debug("Data initialized")

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, serial)},
        name=name,
        manufacturer=MANUFACTURER,
        model=model,
        sw_version=version,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: AmbeoConfigEntry) -> bool:
    """Handle integration unload."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
