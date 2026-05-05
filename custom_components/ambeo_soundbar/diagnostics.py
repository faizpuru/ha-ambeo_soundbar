"""Diagnostics support for Ambeo Soundbar."""

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import AmbeoConfigEntry

TO_REDACT = {"serial", "host", "unique_id"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: AmbeoConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data.coordinator
    device = entry.runtime_data.device

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
