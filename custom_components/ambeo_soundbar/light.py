import logging
import math

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.util.color import brightness_to_value
from homeassistant.components.light import ATTR_BRIGHTNESS

from .const import DOMAIN, DEFAULT_BRIGHTNESS, BRIGHTNESS_SCALE, BRIGHTNESS_SCALE_AMBEO_MAX_LOGO, BRIGHTNESS_SCALE_AMBEO_MAX_DISPLAY, DEFAULT_BRIGHTNESS_AMBEO_MAX, Capability
from .entity import BaseLight


_LOGGER = logging.getLogger(__name__)


class LEDBar(BaseLight):
    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "LED Bar", "led_bar", BRIGHTNESS_SCALE)

    @property
    def is_on(self):
        """Check if the light is on based on brightness."""
        if self.coordinator.data and "led_bar_brightness" in self.coordinator.data:
            return self.coordinator.data["led_bar_brightness"] > 0
        return False

    @property
    def brightness(self):
        """Return the brightness of the light."""
        if self.coordinator.data and "led_bar_brightness" in self.coordinator.data:
            from homeassistant.util.color import value_to_brightness
            return value_to_brightness(self._brightness_scale, self.coordinator.data["led_bar_brightness"])
        return None

    async def async_turn_on(self, **kwargs):
        """Turn on the light with specified brightness, if provided, otherwise use default brightness."""
        try:
            if ATTR_BRIGHTNESS in kwargs:
                brightness = math.floor(brightness_to_value(
                    BRIGHTNESS_SCALE, kwargs[ATTR_BRIGHTNESS]))
            else:
                brightness = DEFAULT_BRIGHTNESS
            await self.coordinator.async_set_led_bar_brightness(brightness)
        except Exception as e:
            _LOGGER.error("Failed to turn on the light: %s", e)

    async def async_turn_off(self, **kwargs):
        """Turn off the light."""
        try:
            await self.coordinator.async_set_led_bar_brightness(0)
        except Exception as e:
            _LOGGER.error("Failed to turn off the light: %s", e)


class CodecLED(BaseLight):
    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Codec LED", "codec_led", BRIGHTNESS_SCALE)

    @property
    def is_on(self):
        """Check if the light is on based on brightness."""
        if self.coordinator.data and "codec_led_brightness" in self.coordinator.data:
            return self.coordinator.data["codec_led_brightness"] > 0
        return False

    @property
    def brightness(self):
        """Return the brightness of the light."""
        if self.coordinator.data and "codec_led_brightness" in self.coordinator.data:
            from homeassistant.util.color import value_to_brightness
            return value_to_brightness(self._brightness_scale, self.coordinator.data["codec_led_brightness"])
        return None

    async def async_turn_on(self, **kwargs):
        """Turn on the Codec LED with specified brightness, if provided, otherwise use default brightness."""
        try:
            if ATTR_BRIGHTNESS in kwargs:
                brightness = math.floor(brightness_to_value(
                    BRIGHTNESS_SCALE, kwargs[ATTR_BRIGHTNESS]))
            else:
                brightness = DEFAULT_BRIGHTNESS
            await self.coordinator.async_set_codec_led_brightness(brightness)
        except Exception as e:
            _LOGGER.error("Failed to turn on the Codec LED: %s", e)

    async def async_turn_off(self, **kwargs):
        """Turn off the Codec LED."""
        try:
            await self.coordinator.async_set_codec_led_brightness(0)
        except Exception as e:
            _LOGGER.error("Failed to turn off the Codec LED: %s", e)


class AmbeoMaxLogo(BaseLight):
    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Ambeo Max Logo",
                         "ambeo_max_logo", BRIGHTNESS_SCALE_AMBEO_MAX_LOGO)

    @property
    def is_on(self):
        """Check if the light is on based on brightness."""
        if self.coordinator.data and "logo_brightness" in self.coordinator.data:
            return self.coordinator.data["logo_brightness"] > 0
        return False

    @property
    def brightness(self):
        """Return the brightness of the light."""
        if self.coordinator.data and "logo_brightness" in self.coordinator.data:
            from homeassistant.util.color import value_to_brightness
            return value_to_brightness(self._brightness_scale, self.coordinator.data["logo_brightness"])
        return None

    async def async_turn_on(self, **kwargs):
        """Turn on the Ambeo Max Logo with specified brightness, if provided, otherwise use default brightness."""
        try:
            if ATTR_BRIGHTNESS in kwargs:
                brightness = math.floor(brightness_to_value(
                    BRIGHTNESS_SCALE_AMBEO_MAX_LOGO, kwargs[ATTR_BRIGHTNESS]))
            else:
                brightness = DEFAULT_BRIGHTNESS_AMBEO_MAX
            await self.coordinator.async_set_logo_brightness(brightness)
        except Exception as e:
            _LOGGER.error("Failed to turn on the Ambeo Max Logo: %s", e)

    async def async_turn_off(self, **kwargs):
        """Turn off the Ambeo Max Logo."""
        try:
            await self.coordinator.async_set_logo_brightness(0)
        except Exception as e:
            _LOGGER.error("Failed to turn off the Ambeo Max Logo: %s", e)


class AmbeoMaxDisplay(BaseLight):
    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Ambeo Max Display",
                         "ambeo_max_display", BRIGHTNESS_SCALE_AMBEO_MAX_DISPLAY)

    @property
    def is_on(self):
        """Check if the light is on based on brightness."""
        if self.coordinator.data and "display_brightness" in self.coordinator.data:
            return self.coordinator.data["display_brightness"] > 0
        return False

    @property
    def brightness(self):
        """Return the brightness of the light."""
        if self.coordinator.data and "display_brightness" in self.coordinator.data:
            from homeassistant.util.color import value_to_brightness
            return value_to_brightness(self._brightness_scale, self.coordinator.data["display_brightness"])
        return None

    async def async_turn_on(self, **kwargs):
        """Turn on the Ambeo Max Display with specified brightness, if provided, otherwise use default brightness."""
        try:
            if ATTR_BRIGHTNESS in kwargs:
                brightness = math.floor(brightness_to_value(
                    BRIGHTNESS_SCALE_AMBEO_MAX_DISPLAY, kwargs[ATTR_BRIGHTNESS]))
            else:
                brightness = DEFAULT_BRIGHTNESS_AMBEO_MAX
            await self.coordinator.async_set_display_brightness(brightness)
        except Exception as e:
            _LOGGER.error("Failed to turn on the Ambeo Max Display: %s", e)

    async def async_turn_off(self, **kwargs):
        """Turn off the Ambeo Max Display."""
        try:
            await self.coordinator.async_set_display_brightness(0)
        except Exception as e:
            _LOGGER.error("Failed to turn off the Ambeo Max Display: %s", e)


class AmbeoLogo(BaseLight):
    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Ambeo Logo", "ambeo_logo", BRIGHTNESS_SCALE)

    @property
    def is_on(self):
        """Check if the Ambeo Logo light is on."""
        if self.coordinator.data and "logo_state" in self.coordinator.data and "logo_brightness" in self.coordinator.data:
            return self.coordinator.data["logo_state"] and self.coordinator.data["logo_brightness"] > 0
        return False

    @property
    def brightness(self):
        """Return the brightness of the light."""
        if self.coordinator.data and "logo_brightness" in self.coordinator.data:
            from homeassistant.util.color import value_to_brightness
            return value_to_brightness(self._brightness_scale, self.coordinator.data["logo_brightness"])
        return None

    async def async_turn_on(self, **kwargs):
        """Turn on the Ambeo Logo light with specified brightness, if provided."""
        try:
            if ATTR_BRIGHTNESS in kwargs:
                brightness = math.floor(brightness_to_value(
                    BRIGHTNESS_SCALE, kwargs[ATTR_BRIGHTNESS]))
                await self.coordinator.async_set_logo_brightness(brightness)

            logo_state = self.coordinator.data.get("logo_state", False) if self.coordinator.data else False
            if not logo_state:
                await self.coordinator.async_change_logo_state(True)
        except Exception as e:
            _LOGGER.error("Failed to turn on the Ambeo Logo light: %s", e)

    async def async_turn_off(self, **kwargs):
        """Turn off the Ambeo Logo light."""
        try:
            await self.coordinator.async_change_logo_state(False)
        except Exception as e:
            _LOGGER.error("Failed to turn off the Ambeo Logo light: %s", e)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Set up lights from a config entry created in the integrations UI."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    ambeo_device = hass.data[DOMAIN][config_entry.entry_id]["device"]
    entities = []
    if (coordinator.has_capability(Capability.AMBEO_LOGO)):
        entities.append(AmbeoLogo(coordinator, ambeo_device))
    if (coordinator.has_capability(Capability.LED_BAR)):
        entities.append(LEDBar(coordinator, ambeo_device))
    if (coordinator.has_capability(Capability.CODEC_LED)):
        entities.append(CodecLED(coordinator, ambeo_device))
    if (coordinator.has_capability(Capability.MAX_LOGO)):
        entities.append(AmbeoMaxLogo(coordinator, ambeo_device))
    if (coordinator.has_capability(Capability.MAX_DISPLAY)):
        entities.append(AmbeoMaxDisplay(coordinator, ambeo_device))
    async_add_entities(entities)
