import logging
from .const import DOMAIN
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

class VoiceEnhancementMode(SwitchEntity):
    def __init__(self, device, api, config_entry):
        self._name = f"{device.name} Voice Enhancement"
        self.api = api
        self._is_on = True
        self._unique_id = f"${device.serial}_voice_enhancement"
        self.ambeo_device = device

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.ambeo_device.serial)},
        }

    @property
    def unique_id(self):
        """Retourne l'identifiant unique de l'entité."""
        return self._unique_id

    @property
    def name(self):
        """If the switch is currently on or off."""
        return self._name

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        return self._is_on

    async def async_turn_on(self):
        """Turn the switch on."""
        await self.api.set_voice_enhancement(True)
        self._is_on = True

    async def async_turn_off(self):
        """Turn the switch off."""
        await self.api.set_voice_enhancement(False)
        self._is_on = False
    
    async def async_update(self):
        _LOGGER.info("Updating")
        try:
            "Get night mode"
            status = await self.api.get_voice_enhancement()
            self._is_on = status
        except Exception as e: 
            _LOGGER.error("Failed to get voice enhancement status: %s", e)

class SoundFeedback(SwitchEntity):
    def __init__(self, device, api, config_entry):
        self._name = f"{device.name} Sound Feedback"
        self.api = api
        self._is_on = True
        self._unique_id = f"${device.serial}_sound_feedback"
        self.ambeo_device = device

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.ambeo_device.serial)},
        }

    @property
    def unique_id(self):
        """Retourne l'identifiant unique de l'entité."""
        return self._unique_id

    @property
    def name(self):
        """If the switch is currently on or off."""
        return self._name

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        return self._is_on

    async def async_turn_on(self):
        """Turn the switch on."""
        await self.api.set_sound_feedback(True)
        self._is_on = True

    async def async_turn_off(self):
        """Turn the switch off."""
        await self.api.set_sound_feedback(False)
        self._is_on = False
    
    async def async_update(self):
        _LOGGER.info("Updating")
        try:
            "Get night mode"
            status = await self.api.get_sound_feedback()
            self._is_on = status
        except Exception as e: 
            _LOGGER.error("Failed to get voice enhancement status: %s", e)

class AmbeoMode(SwitchEntity):
    def __init__(self, device, api, config_entry):
        self._name = f"{device.name} Ambeo Mode"
        self.api = api
        self._is_on = True
        self._unique_id = f"${device.serial}_ambeo_mode"
        self.ambeo_device = device

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.ambeo_device.serial)},
        }


    @property
    def unique_id(self):
        """Retourne l'identifiant unique de l'entité."""
        return self._unique_id

    @property
    def name(self):
        """If the switch is currently on or off."""
        return self._name

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        return self._is_on

    async def async_turn_on(self):
        """Turn the switch on."""
        await self.api.set_ambeo_mode(True)
        self._is_on = True

    async def async_turn_off(self):
        """Turn the switch off."""
        await self.api.set_ambeo_mode(False)
        self._is_on = False
    
    async def async_update(self):
        _LOGGER.info("Updating")
        try:
            "Get night mode"
            status = await self.api.get_ambeo_mode()
            self._is_on = status
        except Exception as e: 
            _LOGGER.error("Failed to get ambeo status: %s", e)

class NightMode(SwitchEntity):
    def __init__(self, device, api, config_entry):
        self._name = f"{device.name} Night Mode"
        self.api = api
        self._is_on = True
        self._unique_id = f"${device.serial}_night_mode"
        self.ambeo_device = device

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.ambeo_device.serial)},
        }


    @property
    def unique_id(self):
        """Retourne l'identifiant unique de l'entité."""
        return self._unique_id

    @property
    def name(self):
        """If the switch is currently on or off."""
        return self._name

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        return self._is_on

    async def async_turn_on(self):
        """Turn the switch on."""
        await self.api.set_night_mode(True)
        self._is_on = True

    async def async_turn_off(self):
        """Turn the switch off."""
        await self.api.set_night_mode(False)
        self._is_on = False
    
    async def async_update(self):
        _LOGGER.info("Updating")
        try:
            "Get night mode"
            status = await self.api.get_night_mode()
            self._is_on = status
        except Exception as e: 
            _LOGGER.error("Failed to get night mode status: %s", e)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    ambeo_api = hass.data[DOMAIN][config_entry.entry_id]["api"]
    ambeo_device = hass.data[DOMAIN][config_entry.entry_id]["device"]
    night_mode = NightMode(ambeo_device, ambeo_api, config_entry)
    voice_enhancement_mode = VoiceEnhancementMode(ambeo_device, ambeo_api, config_entry)
    ambeo_mode = AmbeoMode(ambeo_device, ambeo_api, config_entry)
    sound_feedback = SoundFeedback(ambeo_device, ambeo_api, config_entry)
    async_add_entities([night_mode, voice_enhancement_mode, ambeo_mode, sound_feedback], update_before_add=True)
