import logging
from .const import DOMAIN, DEFAULT_BRIGHTNESS, BRIGHTNESS_SCALE
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.util.color import brightness_to_value
from homeassistant.components.light import ATTR_BRIGHTNESS
from .entity import BaseLight


_LOGGER = logging.getLogger(__name__)


class LEDBar(BaseLight):
    def __init__(self, device, api, config_entry):
        super().__init__(device, api, "LED Bar", "led_bar")
    async def async_turn_on(self, **kwargs):
        try:
            if ATTR_BRIGHTNESS in kwargs:
                self._brightness = brightness_to_value(BRIGHTNESS_SCALE, kwargs[ATTR_BRIGHTNESS])
            else:
                self._brightness = DEFAULT_BRIGHTNESS
            await self.api.set_led_bar_brightness(self._brightness)        
        except Exception as e:
            _LOGGER.error("Failed to turn on the light: %s", e)

    async def async_turn_off(self, **kwargs):
        """Éteindre la lumière."""
        try:
            await self.api.set_led_bar_brightness(0)  
            self._brightness = False
        except Exception as e:
            _LOGGER.error("Failed to turn off Ambeo light: %s", e)

    async def async_update(self):
        _LOGGER.info("Updating Bar Light")
        try:
            brightness = await self.api.get_led_bar_brightness()
            self._brightness = brightness
        except Exception as e: 
            _LOGGER.error("Failed to get codev light brightness: %s", e)

class CodecLED(BaseLight):
    def __init__(self, device, api, config_entry):
        super().__init__(device, api, "Codec LED", "codec_led")

    async def async_turn_on(self, **kwargs):
        try:
            if ATTR_BRIGHTNESS in kwargs:
                self._brightness = brightness_to_value(BRIGHTNESS_SCALE, kwargs[ATTR_BRIGHTNESS])
            else:
                self._brightness = DEFAULT_BRIGHTNESS
            await self.api.set_codec_led_brightness(self._brightness)        
        except Exception as e:
            _LOGGER.error("Failed to turn on the light: %s", e)

    async def async_turn_off(self, **kwargs):
        """Éteindre la lumière."""
        try:
            await self.api.set_codec_led_brightness(0)  
            self._brightness = False
        except Exception as e:
            _LOGGER.error("Failed to turn off Ambeo light: %s", e)

    async def async_update(self):
        _LOGGER.info("Updating Codec Light")
        try:
            brightness = await self.api.get_codec_led_brightness()
            self._brightness = brightness
        except Exception as e: 
            _LOGGER.error("Failed to get codev light brightness: %s", e)

class AmbeoLogo(BaseLight):
    def __init__(self, device, api, config_entry):
        super().__init__(device, api, "Ambeo Logo", "ambeo_logo")
        self._state = False

    @property
    def is_on(self):
        return self._state and self._brightness > 0

    async def async_turn_on(self, **kwargs):
        try:
            if ATTR_BRIGHTNESS in kwargs:
                self._brightness = brightness_to_value(BRIGHTNESS_SCALE, kwargs[ATTR_BRIGHTNESS])
            if not self._state:
                await self.api.change_ambeo_logo_state(True)
            await self.api.set_ambeo_logo_brightness(self._brightness)        
            self._state = True
        except Exception as e:
            _LOGGER.error("Failed to turn on the light: %s", e)

    async def async_turn_off(self, **kwargs):
        """Éteindre la lumière."""
        try:
            await self.api.change_ambeo_logo_state(False)  
            self._state = False
        except Exception as e:
            _LOGGER.error("Failed to turn off Ambeo light: %s", e)

    async def async_update(self):
        _LOGGER.info("Updating Ambeo Light")
        try:
            brightness = await self.api.get_ambeo_logo_brightness()
            status = await self.api.get_ambeo_logo_state()
            self._brightness = brightness
            self._state = status
        except Exception as e: 
            _LOGGER.error("Failed to get ambeo light brightness: %s", e)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    ambeo_api = hass.data[DOMAIN][config_entry.entry_id]["api"]
    ambeo_device = hass.data[DOMAIN][config_entry.entry_id]["device"]
    ambeo_logo = AmbeoLogo(ambeo_device, ambeo_api, config_entry)
    led_bar = LEDBar(ambeo_device, ambeo_api, config_entry)
    codec_led = CodecLED(ambeo_device, ambeo_api, config_entry)
    async_add_entities([ambeo_logo, led_bar, codec_led], update_before_add=True)