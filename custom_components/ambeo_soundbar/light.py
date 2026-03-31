import math

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.util.color import brightness_to_value
from homeassistant.components.light import ATTR_BRIGHTNESS

from .const import (
    DOMAIN,
    DEFAULT_BRIGHTNESS,
    BRIGHTNESS_SCALE,
    BRIGHTNESS_SCALE_AMBEO_MAX_LOGO,
    BRIGHTNESS_SCALE_AMBEO_MAX_DISPLAY,
    DEFAULT_BRIGHTNESS_AMBEO_MAX,
    Capability,
)
from .entity import BaseLight


class LEDBar(BaseLight):
    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "LED Bar", "led_bar",
                         BRIGHTNESS_SCALE, "led_bar_brightness",
                         "async_set_led_bar_brightness", DEFAULT_BRIGHTNESS)


class CodecLED(BaseLight):
    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Codec LED", "codec_led",
                         BRIGHTNESS_SCALE, "codec_led_brightness",
                         "async_set_codec_led_brightness", DEFAULT_BRIGHTNESS)


class AmbeoMaxLogo(BaseLight):
    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Ambeo Max Logo", "ambeo_max_logo",
                         BRIGHTNESS_SCALE_AMBEO_MAX_LOGO, "logo_brightness",
                         "async_set_logo_brightness", DEFAULT_BRIGHTNESS_AMBEO_MAX)


class AmbeoMaxDisplay(BaseLight):
    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Ambeo Max Display", "ambeo_max_display",
                         BRIGHTNESS_SCALE_AMBEO_MAX_DISPLAY, "display_brightness",
                         "async_set_display_brightness", DEFAULT_BRIGHTNESS_AMBEO_MAX)


class AmbeoLogo(BaseLight):
    """Special light with on/off state separate from brightness."""

    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Ambeo Logo", "ambeo_logo",
                         BRIGHTNESS_SCALE, "logo_brightness",
                         "async_set_logo_brightness", DEFAULT_BRIGHTNESS)

    @property
    def is_on(self):
        """Check if the Ambeo Logo light is on."""
        if self.coordinator.data:
            return (
                self.coordinator.data.get("logo_state", False)
                and self.coordinator.data.get("logo_brightness", 0) > 0
            )
        return False

    async def async_turn_on(self, **kwargs):
        """Turn on the Ambeo Logo light with specified brightness, if provided."""
        if ATTR_BRIGHTNESS in kwargs:
            brightness = math.floor(brightness_to_value(BRIGHTNESS_SCALE, kwargs[ATTR_BRIGHTNESS]))
            await self.coordinator.async_set_logo_brightness(brightness)

        logo_state = self.coordinator.data.get("logo_state", False) if self.coordinator.data else False
        if not logo_state:
            await self.coordinator.async_change_logo_state(True)

    async def async_turn_off(self, **kwargs):
        """Turn off the Ambeo Logo light."""
        await self.coordinator.async_change_logo_state(False)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Set up lights from a config entry created in the integrations UI."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    ambeo_device = hass.data[DOMAIN][config_entry.entry_id]["device"]
    entities = []
    if coordinator.has_capability(Capability.AMBEO_LOGO):
        entities.append(AmbeoLogo(coordinator, ambeo_device))
    if coordinator.has_capability(Capability.LED_BAR):
        entities.append(LEDBar(coordinator, ambeo_device))
    if coordinator.has_capability(Capability.CODEC_LED):
        entities.append(CodecLED(coordinator, ambeo_device))
    if coordinator.has_capability(Capability.MAX_LOGO):
        entities.append(AmbeoMaxLogo(coordinator, ambeo_device))
    if coordinator.has_capability(Capability.MAX_DISPLAY):
        entities.append(AmbeoMaxDisplay(coordinator, ambeo_device))
    async_add_entities(entities)
