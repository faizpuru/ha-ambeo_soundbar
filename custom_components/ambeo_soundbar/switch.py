"""Switch entities for Ambeo Soundbar integration."""

from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant

from . import AmbeoConfigEntry
from .api.const import Capability
from .entity import AmbeoBaseSwitch


class NightMode(AmbeoBaseSwitch):
    """Switch entity for night mode."""

    def __init__(self, coordinator, device):
        """Initialize the night mode switch."""
        super().__init__(
            coordinator, device, "Night Mode", "night_mode", "async_set_night_mode"
        )


class AmbeoMode(AmbeoBaseSwitch):
    """Switch entity for Ambeo mode."""

    def __init__(self, coordinator, device):
        """Initialize the Ambeo mode switch."""
        super().__init__(
            coordinator, device, "Ambeo Mode", "ambeo_mode", "async_set_ambeo_mode"
        )


class SoundFeedback(AmbeoBaseSwitch):
    """Switch entity for sound feedback."""

    def __init__(self, coordinator, device):
        """Initialize the sound feedback switch."""
        super().__init__(
            coordinator,
            device,
            "Sound Feedback",
            "sound_feedback",
            "async_set_sound_feedback",
        )


class VoiceEnhancementMode(AmbeoBaseSwitch):
    """Switch entity for voice enhancement mode."""

    def __init__(self, coordinator, device):
        """Initialize the voice enhancement mode switch."""
        super().__init__(
            coordinator,
            device,
            "Voice Enhancement",
            "voice_enhancement",
            "async_set_voice_enhancement",
        )


class SubWooferStatus(AmbeoBaseSwitch):
    """Switch entity for subwoofer status."""

    def __init__(self, coordinator, device):
        """Initialize the subwoofer status switch."""
        super().__init__(
            coordinator,
            device,
            "Subwoofer Status",
            "subwoofer_status",
            "async_set_subwoofer_status",
        )


class AmbeoBluetoothPairing(AmbeoBaseSwitch):
    """Switch entity for Ambeo Bluetooth pairing mode."""

    def __init__(self, coordinator, device):
        """Initialize the Bluetooth pairing switch."""
        super().__init__(
            coordinator,
            device,
            "Ambeo Bluetooth Pairing",
            "bluetooth_pairing",
            "async_set_bluetooth_pairing_state",
        )

    @property
    def entity_category(self) -> EntityCategory:
        """Return the entity category for the Bluetooth pairing switch."""
        return EntityCategory.CONFIG


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AmbeoConfigEntry,
    async_add_entities,
):
    """Set up the switch entities from a config entry created in the integrations UI."""
    coordinator = config_entry.runtime_data.coordinator
    ambeo_device = config_entry.runtime_data.device
    entities = [
        NightMode(coordinator, ambeo_device),
        AmbeoMode(coordinator, ambeo_device),
        SoundFeedback(coordinator, ambeo_device),
    ]
    if coordinator.has_capability(Capability.VOICE_ENHANCEMENT_TOGGLE):
        entities.append(VoiceEnhancementMode(coordinator, ambeo_device))
    if coordinator.has_capability(Capability.BLUETOOTH_PAIRING):
        entities.append(AmbeoBluetoothPairing(coordinator, ambeo_device))
    if (
        coordinator.has_capability(Capability.SUBWOOFER)
        and await coordinator.has_subwoofer()
    ):
        entities.append(SubWooferStatus(coordinator, ambeo_device))
    async_add_entities(entities)
