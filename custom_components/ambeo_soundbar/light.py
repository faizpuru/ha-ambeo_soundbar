import logging
import math
from .const import DOMAIN, DEFAULT_BRIGHTNESS
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.util.color import value_to_brightness, brightness_to_value
from homeassistant.components.light import LightEntity, COLOR_MODE_BRIGHTNESS, ATTR_BRIGHTNESS

BRIGHTNESS_SCALE = (0, 100)


_LOGGER = logging.getLogger(__name__)


class BaseLight(LightEntity):
    def __init__(self, device, api, name_suffix, unique_id_suffix):
        self._name = f"{device.name} {name_suffix}"
        self.api = api
        self._brightness = 0
        self._unique_id = f"${device.serial}_{unique_id_suffix}"
        self.ambeo_device = device

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.ambeo_device.serial)},
        }

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._brightness > 0

    @property
    def supported_color_modes(self):
        return {COLOR_MODE_BRIGHTNESS}

    @property
    def color_mode(self):
        return COLOR_MODE_BRIGHTNESS

    @property
    def brightness(self):
        return value_to_brightness(BRIGHTNESS_SCALE, self._brightness)

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