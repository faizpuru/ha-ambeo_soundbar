import logging
from .const import DOMAIN
from .entity import AmbeoBaseSwitch
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

class VoiceEnhancementMode(AmbeoBaseSwitch):
    def __init__(self, device, api):
        super().__init__(device, api, "Voice Enhancement")

    async def async_turn_on(self):
        """Turn the voice enhancement on."""
        await self.api.set_voice_enhancement(True)
        self._is_on = True

    async def async_turn_off(self):
        """Turn the voice enhancement off."""
        await self.api.set_voice_enhancement(False)
        self._is_on = False

    async def async_update(self):
        """Update the status of the voice enhancement."""
        try:
            status = await self.api.get_voice_enhancement()
            self._is_on = status
        except Exception as e:
            _LOGGER.error(f"Failed to get voice enhancement status: {e}")

class SoundFeedback(AmbeoBaseSwitch):
    def __init__(self, device, api):
        super().__init__(device, api, "Sound Feedback")

    async def async_turn_on(self):
        """Turn the sound feedback on."""
        await self.api.set_sound_feedback(True)
        self._is_on = True

    async def async_turn_off(self):
        """Turn the sound feedback off."""
        await self.api.set_sound_feedback(False)
        self._is_on = False

    async def async_update(self):
        """Update the status of the sound feedback."""
        try:
            status = await self.api.get_sound_feedback()
            self._is_on = status
        except Exception as e:
            _LOGGER.error(f"Failed to get sound feedback status: {e}")


class AmbeoMode(AmbeoBaseSwitch):
    def __init__(self, device, api):
        super().__init__(device, api, "Ambeo Mode")

    async def async_turn_on(self):
        """Turn the Ambeo mode on."""
        await self.api.set_ambeo_mode(True)
        self._is_on = True

    async def async_turn_off(self):
        """Turn the Ambeo mode off."""
        await self.api.set_ambeo_mode(False)
        self._is_on = False

    async def async_update(self):
        """Update the status of the Ambeo mode."""
        try:
            status = await self.api.get_ambeo_mode()
            self._is_on = status
        except Exception as e:
            _LOGGER.error(f"Failed to get Ambeo mode status: {e}")
            
class NightMode(AmbeoBaseSwitch):
    def __init__(self, device, api):
        super().__init__(device, api, "Night Mode")

    async def async_turn_on(self):
        """Turn the night mode on."""
        await self.api.set_night_mode(True)
        self._is_on = True

    async def async_turn_off(self):
        """Turn the night mode off."""
        await self.api.set_night_mode(False)
        self._is_on = False

    async def async_update(self):
        """Update the status of the night mode."""
        try:
            status = await self.api.get_night_mode()
            self._is_on = status
        except Exception as e:
            _LOGGER.error(f"Failed to get night mode status: {e}")


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    ambeo_api = hass.data[DOMAIN][config_entry.entry_id]["api"]
    ambeo_device = hass.data[DOMAIN][config_entry.entry_id]["device"]
    night_mode = NightMode(ambeo_device, ambeo_api)
    voice_enhancement_mode = VoiceEnhancementMode(ambeo_device, ambeo_api)
    ambeo_mode = AmbeoMode(ambeo_device, ambeo_api)
    sound_feedback = SoundFeedback(ambeo_device, ambeo_api)
    async_add_entities([night_mode, voice_enhancement_mode, ambeo_mode, sound_feedback], update_before_add=True)
