"""Diagnostics support for Ambeo Soundbar."""

import logging
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

TO_REDACT = {"serial", "host", "unique_id"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    api = data["api"]
    device = data["device"]

    # Collect device information
    device_info = {
        "serial": device.serial,
        "name": device.name,
        "manufacturer": device.manufacturer,
        "model": device.model,
        "firmware_version": device.version,
        "host": device.host,
        "port": device.port,
    }

    # Collect API capabilities
    capabilities = {
        "supported_features": api.capabilities if hasattr(api, "capabilities") else [],
        "supports_debounce": api.support_debounce_mode(),
    }

    # Try to collect current state (non-blocking)
    current_state = {}
    try:
        current_state["volume"] = await api.get_volume()
    except Exception as ex:
        current_state["volume"] = f"Error: {ex}"

    try:
        current_state["mute"] = await api.is_mute()
    except Exception as ex:
        current_state["mute"] = f"Error: {ex}"

    try:
        current_state["power_state"] = await api.get_state()
    except Exception as ex:
        current_state["power_state"] = f"Error: {ex}"

    try:
        current_state["night_mode"] = await api.get_night_mode()
    except Exception as ex:
        current_state["night_mode"] = f"Error: {ex}"

    try:
        current_state["ambeo_mode"] = await api.get_ambeo_mode()
    except Exception as ex:
        current_state["ambeo_mode"] = f"Error: {ex}"

    try:
        current_state["voice_enhancement"] = await api.get_voice_enhancement()
    except Exception as ex:
        current_state["voice_enhancement"] = f"Error: {ex}"

    try:
        current_state["current_source"] = await api.get_current_source()
    except Exception as ex:
        current_state["current_source"] = f"Error: {ex}"

    # Collect configuration
    config_data = {
        "entry_id": entry.entry_id,
        "title": entry.title,
        "data": dict(entry.data),
        "options": dict(entry.options),
    }

    # Build complete diagnostics
    diagnostics = {
        "device": device_info,
        "capabilities": capabilities,
        "current_state": current_state,
        "config": config_data,
        "integration_version": entry.version,
    }

    # Redact sensitive information
    return async_redact_data(diagnostics, TO_REDACT)
