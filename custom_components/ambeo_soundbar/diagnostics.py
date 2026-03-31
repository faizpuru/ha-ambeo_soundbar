"""Diagnostics support for Ambeo Soundbar."""

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

TO_REDACT = {"serial", "host", "unique_id"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    device = data["device"]

    diagnostics = {
        "device": {
            "serial": device.serial,
            "name": device.name,
            "manufacturer": device.manufacturer,
            "model": device.model,
            "firmware_version": device.version,
            "host": device.host,
            "port": device.port,
        },
        "capabilities": {
            "supported_features": coordinator.api.capabilities,
            "supports_debounce": coordinator.support_debounce_mode(),
        },
        "current_state": coordinator.data or {},
        "config": {
            "entry_id": entry.entry_id,
            "title": entry.title,
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
        "integration_version": entry.version,
    }

    return async_redact_data(diagnostics, TO_REDACT)
