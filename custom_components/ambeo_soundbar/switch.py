import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import  EntityCategory


from .const import DOMAIN
from .entity import AmbeoBaseSwitch

_LOGGER = logging.getLogger(__name__)

class VoiceEnhancementMode(AmbeoBaseSwitch):
    def __init__(self, device, api):
        """Initialize the Voice Enhancement switch."""
        super().__init__(device, api, "Voice Enhancement")

    async def async_turn_on(self):
        """Turn the voice enhancement feature on."""
        await self.api.set_voice_enhancement(True)
        self._is_on = True

    async def async_turn_off(self):
        """Turn the voice enhancement feature off."""
        await self.api.set_voice_enhancement(False)
        self._is_on = False

    async def async_update(self):
        """Update the current status of the voice enhancement feature."""
        try:
            status = await self.api.get_voice_enhancement()
            self._is_on = status
        except Exception as e:
            _LOGGER.error(f"Failed to update voice enhancement status: {e}")

class SoundFeedback(AmbeoBaseSwitch):
    def __init__(self, device, api):
        """Initialize the Sound Feedback switch."""
        super().__init__(device, api, "Sound Feedback")

    async def async_turn_on(self):
        """Turn the sound feedback feature on."""
        await self.api.set_sound_feedback(True)
        self._is_on = True

    async def async_turn_off(self):
        """Turn the sound feedback feature off."""
        await self.api.set_sound_feedback(False)
        self._is_on = False

    async def async_update(self):
        """Update the current status of the sound feedback feature."""
        try:
            status = await self.api.get_sound_feedback()
            self._is_on = status
        except Exception as e:
            _LOGGER.error(f"Failed to update sound feedback status: {e}")


class AmbeoMode(AmbeoBaseSwitch):
    def __init__(self, device, api):
        """Initialize the Ambeo Mode switch."""
        super().__init__(device, api, "Ambeo Mode")

    async def async_turn_on(self):
        """Turn the Ambeo mode feature on."""
        await self.api.set_ambeo_mode(True)
        self._is_on = True

    async def async_turn_off(self):
        """Turn the Ambeo mode feature off."""
        await self.api.set_ambeo_mode(False)
        self._is_on = False

    async def async_update(self):
        """Update the current status of the Ambeo mode feature."""
        try:
            status = await self.api.get_ambeo_mode()
            self._is_on = status
        except Exception as e:
            _LOGGER.error(f"Failed to update Ambeo mode status: {e}")
            
class NightMode(AmbeoBaseSwitch):
    def __init__(self, device, api):
        """Initialize the Night Mode switch."""
        super().__init__(device, api, "Night Mode")

    async def async_turn_on(self):
        """Turn the night mode feature on."""
        await self.api.set_night_mode(True)
        self._is_on = True

    async def async_turn_off(self):
        """Turn the night mode feature off."""
        await self.api.set_night_mode(False)
        self._is_on = False

    async def async_update(self):
        """Update the current status of the night mode feature."""
        try:
            status = await self.api.get_night_mode()
            self._is_on = status
        except Exception as e:
            _LOGGER.error(f"Failed to update night mode status: {e}")
            
class AmbeoBluetoothPairing(AmbeoBaseSwitch):
    """The class remains largely unchanged."""
    def __init__(self, device, api):
        """Initialize the switch entity."""
        super().__init__(device, api, "Ambeo Bluetooth Pairing")
        
    @property
    def entity_category(self) -> EntityCategory:
        """Return the entity category."""
        return EntityCategory.CONFIG

    async def async_turn_on(self):
        """Turn the bluetooth pairing feature on."""
        await self.api.set_bluetooth_pairing_state(True)
        self._is_on = True

    async def async_turn_off(self):
        """Turn the bluetooth pairing feature off."""
        await self.api.set_bluetooth_pairing_state(False)
        self._is_on = False

    async def async_update(self):
        """Update the current status of the bluetooth pairing feature."""
        try:
            status = await self.api.get_bluetooth_pairing_state()
            self._is_on = status
        except Exception as e:
            _LOGGER.error(f"Failed to update bluetooth pairing status: {e}")
            

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Set up the switch entities from a config entry created in the integrations UI."""
    ambeo_api = hass.data[DOMAIN][config_entry.entry_id]["api"]
    ambeo_device = hass.data[DOMAIN][config_entry.entry_id]["device"]
    entities = [NightMode(ambeo_device, ambeo_api), AmbeoMode(ambeo_device, ambeo_api), SoundFeedback(ambeo_device, ambeo_api)]
    if not ambeo_device.max_compat:
        entities.append(VoiceEnhancementMode(ambeo_device, ambeo_api))
        entities.append(AmbeoBluetoothPairing(ambeo_device, ambeo_api))
    async_add_entities(entities, update_before_add=True)
