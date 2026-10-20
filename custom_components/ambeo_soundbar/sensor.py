"""Sensor entities for Ambeo Soundbar integration."""

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from pyambeo import Capability

from . import AmbeoConfigEntry
from .entity import AmbeoBaseEntity

_LOGGER = logging.getLogger(__name__)

# Reported when the decoder is up but receives no audio.
NO_SIGNAL = "No signal"


class DecoderStatusSensor(AmbeoBaseEntity, SensorEntity):
    """Diagnostic sensor exposing the audio decoder status."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = "channels"

    def __init__(self, coordinator, device):
        """Initialize the decoder status sensor."""
        super().__init__(coordinator, device, "Decoder Status", "decoder_status")

    @property
    def native_value(self):
        """Return the number of active channels."""
        decoder_status = (
            self.coordinator.data.get("decoder_status")
            if self.coordinator.data
            else None
        )
        if not decoder_status:
            return 0
        return decoder_status.get("channels", decoder_status.get("active_channels", 0))

    @property
    def extra_state_attributes(self):
        """Return the remaining decoder fields as attributes."""
        decoder_status = (
            self.coordinator.data.get("decoder_status")
            if self.coordinator.data
            else None
        )
        if not decoder_status:
            return {}
        return {
            k: v
            for k, v in decoder_status.items()
            if k not in ("channels", "active_channels")
        }


class AudioCodecSensor(AmbeoBaseEntity, SensorEntity):
    """Diagnostic sensor exposing the codec of the incoming audio."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device):
        """Initialize the audio codec sensor."""
        super().__init__(coordinator, device, "Audio Codec", "audio_codec")

    @property
    def native_value(self):
        """Return the codec name, NO_SIGNAL when nothing is decoded."""
        data = self.coordinator.data
        if not data or not isinstance(data.get("decoder_status"), dict):
            return None
        return self.coordinator.get_audio_codec() or NO_SIGNAL


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AmbeoConfigEntry,
    async_add_entities,
):
    """Set up diagnostic sensor entities from a config entry."""
    coordinator = config_entry.runtime_data.coordinator
    device = config_entry.runtime_data.device

    if coordinator.has_capability(Capability.DECODER_STATUS):
        async_add_entities(
            [
                DecoderStatusSensor(coordinator, device),
                AudioCodecSensor(coordinator, device),
            ]
        )
