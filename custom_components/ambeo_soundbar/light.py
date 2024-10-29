import logging
import math

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.util.color import brightness_to_value
from homeassistant.components.light import ATTR_BRIGHTNESS

from .const import DOMAIN, DEFAULT_BRIGHTNESS, BRIGHTNESS_SCALE, BRIGHTNESS_SCALE_AMBEO_MAX_LOGO, BRIGHTNESS_SCALE_AMBEO_MAX_DISPLAY, DEFAULT_BRIGHTNESS_AMBEO_MAX, Capability
from .entity import BaseLight
from .api.impl.generic_api import AmbeoApi


_LOGGER = logging.getLogger(__name__)


class LEDBar(BaseLight):
    def __init__(self, device, api):
        super().__init__(device, api, "LED Bar", "led_bar", BRIGHTNESS_SCALE)

    async def async_turn_on(self, **kwargs):
        """Turn on the light with specified brightness, if provided, otherwise use default brightness."""
        try:
            if ATTR_BRIGHTNESS in kwargs:
                self._brightness = math.floor(brightness_to_value(
                    BRIGHTNESS_SCALE, kwargs[ATTR_BRIGHTNESS]))
            else:
                self._brightness = DEFAULT_BRIGHTNESS
            await self.api.set_led_bar_brightness(self._brightness)
        except Exception as e:
            _LOGGER.error("Failed to turn on the light: %s", e)

    async def async_turn_off(self, **kwargs):
        """Turn off the light."""
        try:
            await self.api.set_led_bar_brightness(0)
            self._brightness = False
        except Exception as e:
            _LOGGER.error("Failed to turn off the light: %s", e)

    async def async_update(self):
        """Update the LED Bar light brightness."""
        _LOGGER.info("Updating LED Bar Light")
        try:
            brightness = await self.api.get_led_bar_brightness()
            self._brightness = brightness
        except Exception as e:
            _LOGGER.error("Failed to get LED Bar light brightness: %s", e)


class CodecLED(BaseLight):
    def __init__(self, device, api):
        super().__init__(device, api, "Codec LED", "codec_led", BRIGHTNESS_SCALE)

    async def async_turn_on(self, **kwargs):
        """Turn on the Codec LED with specified brightness, if provided, otherwise use default brightness."""
        try:
            if ATTR_BRIGHTNESS in kwargs:
                self._brightness = math.floor(brightness_to_value(
                    BRIGHTNESS_SCALE, kwargs[ATTR_BRIGHTNESS]))
            else:
                self._brightness = DEFAULT_BRIGHTNESS
            await self.api.set_codec_led_brightness(self._brightness)
        except Exception as e:
            _LOGGER.error("Failed to turn on the Codec LED: %s", e)

    async def async_turn_off(self, **kwargs):
        """Turn off the Codec LED."""
        try:
            await self.api.set_codec_led_brightness(0)
            self._brightness = False
        except Exception as e:
            _LOGGER.error("Failed to turn off the Codec LED: %s", e)

    async def async_update(self):
        """Update the Codec LED brightness."""
        _LOGGER.info("Updating Codec LED")
        try:
            brightness = await self.api.get_codec_led_brightness()
            self._brightness = brightness
        except Exception as e:
            _LOGGER.error("Failed to get Codec LED brightness: %s", e)


class AmbeoMaxLogo(BaseLight):
    def __init__(self, device, api):
        super().__init__(device, api, "Ambeo Max Logo",
                         "ambeo_max_logo", BRIGHTNESS_SCALE_AMBEO_MAX_LOGO)

    async def async_turn_on(self, **kwargs):
        """Turn on the Ambeo Max Logo with specified brightness, if provided, otherwise use default brightness."""
        try:
            if ATTR_BRIGHTNESS in kwargs:
                self._brightness = math.floor(brightness_to_value(
                    BRIGHTNESS_SCALE_AMBEO_MAX_LOGO, kwargs[ATTR_BRIGHTNESS]))
            else:
                self._brightness = DEFAULT_BRIGHTNESS_AMBEO_MAX
            await self.api.set_logo_brightness(self._brightness)
        except Exception as e:
            _LOGGER.error("Failed to turn on the Ambeo Max Logo: %s", e)

    async def async_turn_off(self, **kwargs):
        """Turn off the Ambeo Max Logo."""
        try:
            await self.api.set_logo_brightness(0)
            self._brightness = 0
        except Exception as e:
            _LOGGER.error("Failed to turn off the Ambeo Max Logo: %s", e)

    async def async_update(self):
        """Update the Ambeo Max Logo brightness."""
        _LOGGER.info("Updating Ambeo Max Logo")
        try:
            brightness = await self.api.get_logo_brightness()
            self._brightness = brightness
        except Exception as e:
            _LOGGER.error("Failed to get Ambeo Max Logo brightness: %s", e)


class AmbeoMaxDisplay(BaseLight):
    def __init__(self, device, api):
        super().__init__(device, api, "Ambeo Max Display",
                         "ambeo_max_display", BRIGHTNESS_SCALE_AMBEO_MAX_DISPLAY)

    async def async_turn_on(self, **kwargs):
        """Turn on the Ambeo Max Display with specified brightness, if provided, otherwise use default brightness."""
        try:
            if ATTR_BRIGHTNESS in kwargs:
                self._brightness = math.floor(brightness_to_value(
                    BRIGHTNESS_SCALE_AMBEO_MAX_DISPLAY, kwargs[ATTR_BRIGHTNESS]))
            else:
                self._brightness = DEFAULT_BRIGHTNESS_AMBEO_MAX
            await self.api.set_display_brightness(self._brightness)
        except Exception as e:
            _LOGGER.error("Failed to turn on the Ambeo Max Display: %s", e)

    async def async_turn_off(self, **kwargs):
        """Turn off the Ambeo Max Display."""
        try:
            await self.api.set_display_brightness(0)
            self._brightness = 0
        except Exception as e:
            _LOGGER.error("Failed to turn off the Ambeo Max Display: %s", e)

    async def async_update(self):
        """Update the Ambeo Max Display brightness."""
        _LOGGER.info("Updating Ambeo Max Display")
        try:
            brightness = await self.api.get_display_brightness()
            self._brightness = brightness
        except Exception as e:
            _LOGGER.error("Failed to get Ambeo Max Display brightness: %s", e)


class AmbeoLogo(BaseLight):
    def __init__(self, device, api):
        super().__init__(device, api, "Ambeo Logo", "ambeo_logo", BRIGHTNESS_SCALE)
        self._state = False

    @property
    def is_on(self):
        """Check if the Ambeo Logo light is on."""
        return self._state and self._brightness > 0

    async def async_turn_on(self, **kwargs):
        """Turn on the Ambeo Logo light with specified brightness, if provided."""
        try:
            if ATTR_BRIGHTNESS in kwargs:
                self._brightness = math.floor(brightness_to_value(
                    BRIGHTNESS_SCALE, kwargs[ATTR_BRIGHTNESS]))
            if not self._state:
                await self.api.change_logo_state(True)
            await self.api.set_logo_brightness(self._brightness)
            self._state = True
        except Exception as e:
            _LOGGER.error("Failed to turn on the Ambeo Logo light: %s", e)

    async def async_turn_off(self, **kwargs):
        """Turn off the Ambeo Logo light."""
        try:
            await self.api.change_logo_state(False)
            self._state = False
        except Exception as e:
            _LOGGER.error("Failed to turn off the Ambeo Logo light: %s", e)

    async def async_update(self):
        """Update the Ambeo Logo light status and brightness."""
        _LOGGER.info("Updating Ambeo Logo Light")
        try:
            brightness = await self.api.get_logo_brightness()
            status = await self.api.get_logo_state()
            self._brightness = brightness
            self._state = status
        except Exception as e:
            _LOGGER.error(
                "Failed to get Ambeo Logo light brightness and status: %s", e)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Set up lights from a config entry created in the integrations UI."""
    ambeo_api: AmbeoApi = hass.data[DOMAIN][config_entry.entry_id]["api"]
    ambeo_device = hass.data[DOMAIN][config_entry.entry_id]["device"]
    entities = []
    if (ambeo_api.has_capability(Capability.AMBEO_LOGO)):
        entities.append(AmbeoLogo(ambeo_device, ambeo_api))
    if (ambeo_api.has_capability(Capability.LED_BAR)):
        entities.append(LEDBar(ambeo_device, ambeo_api))
    if (ambeo_api.has_capability(Capability.CODEC_LED)):
        entities.append(CodecLED(ambeo_device, ambeo_api))
    if (ambeo_api.has_capability(Capability.MAX_LOGO)):
        entities.append(AmbeoMaxLogo(ambeo_device, ambeo_api))
    if (ambeo_api.has_capability(Capability.MAX_DISPLAY)):
        entities.append(AmbeoMaxDisplay(ambeo_device, ambeo_api))
    async_add_entities(entities, update_before_add=True)
