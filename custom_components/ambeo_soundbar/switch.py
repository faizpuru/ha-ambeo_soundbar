from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN, Capability
from .entity import AmbeoBaseSwitch


class NightMode(AmbeoBaseSwitch):
    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Night Mode",
                         "night_mode", "async_set_night_mode")


class AmbeoMode(AmbeoBaseSwitch):
    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Ambeo Mode",
                         "ambeo_mode", "async_set_ambeo_mode")


class SoundFeedback(AmbeoBaseSwitch):
    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Sound Feedback",
                         "sound_feedback", "async_set_sound_feedback")


class VoiceEnhancementMode(AmbeoBaseSwitch):
    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Voice Enhancement",
                         "voice_enhancement", "async_set_voice_enhancement")


class SubWooferStatus(AmbeoBaseSwitch):
    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Subwoofer Status",
                         "subwoofer_status", "async_set_subwoofer_status")


class AmbeoBluetoothPairing(AmbeoBaseSwitch):
    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Ambeo Bluetooth Pairing",
                         "bluetooth_pairing", "async_set_bluetooth_pairing_state")

    @property
    def entity_category(self) -> EntityCategory:
        return EntityCategory.CONFIG


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Set up the switch entities from a config entry created in the integrations UI."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    ambeo_device = hass.data[DOMAIN][config_entry.entry_id]["device"]
    entities = [
        NightMode(coordinator, ambeo_device),
        AmbeoMode(coordinator, ambeo_device),
        SoundFeedback(coordinator, ambeo_device),
    ]
    if coordinator.has_capability(Capability.VOICE_ENHANCEMENT_TOGGLE):
        entities.append(VoiceEnhancementMode(coordinator, ambeo_device))
    if coordinator.has_capability(Capability.BLUETOOTH_PAIRING):
        entities.append(AmbeoBluetoothPairing(coordinator, ambeo_device))
    if coordinator.has_capability(Capability.SUBWOOFER) and await coordinator.has_subwoofer():
        entities.append(SubWooferStatus(coordinator, ambeo_device))
    async_add_entities(entities)
