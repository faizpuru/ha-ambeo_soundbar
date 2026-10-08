"""Ambeo Soundbar integration setup."""

import logging
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AmbeoError, AmbeoSoundbar, AmbeoUnsupportedModelError
from .const import (
    CONFIG_CONCURRENT_REQUESTS,
    CONFIG_CONCURRENT_REQUESTS_DEFAULT,
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
    concurrent_requests = entry.options.get(
        CONFIG_CONCURRENT_REQUESTS,
        entry.data.get(CONFIG_CONCURRENT_REQUESTS, CONFIG_CONCURRENT_REQUESTS_DEFAULT),
    )
    session = async_get_clientsession(hass)

    try:
        ambeo_api = await AmbeoSoundbar.connect(
            host, session, port=DEFAULT_PORT, timeout=TIMEOUT
        )
    except AmbeoUnsupportedModelError as ex:
        raise ConfigEntryError(f"Unsupported device at {host}: {ex}") from ex
    except AmbeoError as ex:
        raise ConfigEntryNotReady(f"Could not connect to {host}: {ex}") from ex

    info = ambeo_api.info
    serial = info.serial or "unknown_serial"
    name = info.name
    model = info.model
    version = info.firmware_version
    device = AmbeoDevice(serial, name, MANUFACTURER, model, version, host, DEFAULT_PORT)

    coordinator = AmbeoCoordinator(
        hass, ambeo_api, update_interval, concurrent_requests
    )
    await coordinator.async_config_entry_first_refresh()
    await coordinator.async_start_event_listener()

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
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.coordinator.async_stop()
    return unloaded
