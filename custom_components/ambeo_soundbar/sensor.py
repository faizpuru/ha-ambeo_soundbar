"""Sensor entities for Ambeo Soundbar integration."""

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from pyambeo import Capability

from . import AmbeoConfigEntry
from .entity import AmbeoBaseEntity

_LOGGER = logging.getLogger(__name__)

# Short names for the plain codecs, as shown by the soundbar web app.
# Dolby, DTS and MPEG-H names are already descriptive and kept as is.
SHORT_CODEC_NAMES = (
    ("pcm", "PCM"),
    ("vorbis", "Vorbis"),
    ("mp3", "MP3"),
    ("flac", "FLAC"),
    ("aac", "AAC"),
    ("sbc", "SBC"),
)


def audio_codec_name(codec: str) -> str:
    """Return the display name of a decoder codec."""
    lowered = codec.lower()
    if "dolby" in lowered or "dts" in lowered or "mpeg-h" in lowered:
        return codec
    # Tidal Atmos is reported by its container.
    if lowered.startswith("e-ac-3"):
        return "Dolby Atmos"
    for needle, name in SHORT_CODEC_NAMES:
        if needle in lowered:
            return name
    return codec


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
        """Return the codec name, or None when nothing is decoded."""
        data = self.coordinator.data or {}
        # Bluetooth bypasses the decoder: the codec is in the stream URI.
        media_data = ((data.get("player_data") or {}).get("mediaRoles") or {}).get(
            "mediaData"
        ) or {}
        resources = media_data.get("resources") or [{}]
        uri = resources[0].get("uri") if isinstance(resources[0], dict) else None
        if isinstance(uri, str) and uri.startswith("bluetooth"):
            return "SBC" if uri.startswith("bluetoothsbc:") else "AAC"
        codec = (data.get("decoder_status") or {}).get("codec")
        if not isinstance(codec, str) or not codec:
            return None
        return audio_codec_name(codec)


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
