import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory


from .const import DOMAIN, Capability
from .entity import AmbeoBaseSwitch


_LOGGER = logging.getLogger(__name__)


class SubWooferStatus(AmbeoBaseSwitch):
    def __init__(self, coordinator, device):
        """Initialize the Subwoofer  switch."""
        super().__init__(coordinator, device, "Subwoofer Status")

    @property
    def is_on(self):
        """Determine if the switch is currently on or off."""
        if self.coordinator.data and "subwoofer_status" in self.coordinator.data:
            return self.coordinator.data["subwoofer_status"]
        return None

    async def async_turn_on(self):
        """Turn the Subwoofer on."""
        await self.coordinator.async_set_subwoofer_status(True)

    async def async_turn_off(self):
        """Turn the Subwoofer off."""
        await self.coordinator.async_set_subwoofer_status(False)


class VoiceEnhancementMode(AmbeoBaseSwitch):
    def __init__(self, coordinator, device):
        """Initialize the Voice Enhancement switch."""
        super().__init__(coordinator, device, "Voice Enhancement")

    @property
    def is_on(self):
        """Determine if the switch is currently on or off."""
        if self.coordinator.data and "voice_enhancement" in self.coordinator.data:
            return self.coordinator.data["voice_enhancement"]
        return None

    async def async_turn_on(self):
        """Turn the voice enhancement feature on."""
        await self.coordinator.async_set_voice_enhancement(True)

    async def async_turn_off(self):
        """Turn the voice enhancement feature off."""
        await self.coordinator.async_set_voice_enhancement(False)


class SoundFeedback(AmbeoBaseSwitch):
    def __init__(self, coordinator, device):
        """Initialize the Sound Feedback switch."""
        super().__init__(coordinator, device, "Sound Feedback")

    @property
    def is_on(self):
        """Determine if the switch is currently on or off."""
        if self.coordinator.data and "sound_feedback" in self.coordinator.data:
            return self.coordinator.data["sound_feedback"]
        return None

    async def async_turn_on(self):
        """Turn the sound feedback feature on."""
        await self.coordinator.async_set_sound_feedback(True)

    async def async_turn_off(self):
        """Turn the sound feedback feature off."""
        await self.coordinator.async_set_sound_feedback(False)


class AmbeoMode(AmbeoBaseSwitch):
    def __init__(self, coordinator, device):
        """Initialize the Ambeo Mode switch."""
        super().__init__(coordinator, device, "Ambeo Mode")

    @property
    def is_on(self):
        """Determine if the switch is currently on or off."""
        if self.coordinator.data and "ambeo_mode" in self.coordinator.data:
            return self.coordinator.data["ambeo_mode"]
        return None

    async def async_turn_on(self):
        """Turn the Ambeo mode feature on."""
        await self.coordinator.async_set_ambeo_mode(True)

    async def async_turn_off(self):
        """Turn the Ambeo mode feature off."""
        await self.coordinator.async_set_ambeo_mode(False)


class NightMode(AmbeoBaseSwitch):
    def __init__(self, coordinator, device):
        """Initialize the Night Mode switch."""
        super().__init__(coordinator, device, "Night Mode")

    @property
    def is_on(self):
        """Determine if the switch is currently on or off."""
        if self.coordinator.data and "night_mode" in self.coordinator.data:
            return self.coordinator.data["night_mode"]
        return None

    async def async_turn_on(self):
        """Turn the night mode feature on."""
        await self.coordinator.async_set_night_mode(True)

    async def async_turn_off(self):
        """Turn the night mode feature off."""
        await self.coordinator.async_set_night_mode(False)


class AmbeoBluetoothPairing(AmbeoBaseSwitch):
    """Switch for Bluetooth pairing."""

    def __init__(self, coordinator, device):
        """Initialize the switch entity."""
        super().__init__(coordinator, device, "Ambeo Bluetooth Pairing")

    @property
    def entity_category(self) -> EntityCategory:
        """Return the entity category."""
        return EntityCategory.CONFIG

    @property
    def is_on(self):
        """Determine if the switch is currently on or off."""
        if self.coordinator.data and "bluetooth_pairing" in self.coordinator.data:
            return self.coordinator.data["bluetooth_pairing"]
        return None

    async def async_turn_on(self):
        """Turn the bluetooth pairing feature on."""
        await self.coordinator.async_set_bluetooth_pairing_state(True)

    async def async_turn_off(self):
        """Turn the bluetooth pairing feature off."""
        await self.coordinator.async_set_bluetooth_pairing_state(False)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Set up the switch entities from a config entry created in the integrations UI."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    ambeo_device = hass.data[DOMAIN][config_entry.entry_id]["device"]
    entities = [NightMode(coordinator, ambeo_device), AmbeoMode(
        coordinator, ambeo_device), SoundFeedback(coordinator, ambeo_device)]
    if coordinator.has_capability(Capability.VOICE_ENHANCEMENT_TOGGLE):
        entities.append(VoiceEnhancementMode(coordinator, ambeo_device))
    if coordinator.has_capability(Capability.BLUETOOTH_PAIRING):
        entities.append(AmbeoBluetoothPairing(coordinator, ambeo_device))
    if coordinator.has_capability(Capability.SUBWOOFER) and await coordinator.has_subwoofer():
        entities.append(SubWooferStatus(coordinator, ambeo_device))
    async_add_entities(entities)
