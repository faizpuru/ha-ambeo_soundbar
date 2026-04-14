"""Light entities for Ambeo Soundbar integration."""

import math

from homeassistant.components.light import ATTR_BRIGHTNESS
from homeassistant.core import HomeAssistant
from homeassistant.util.color import brightness_to_value

from . import AmbeoConfigEntry
from .api.const import Capability
from .coordinator import AmbeoCoordinator
from .entity import BaseLight

DEFAULT_BRIGHTNESS = 50
DEFAULT_BRIGHTNESS_AMBEO_MAX = 128


class LEDBar(BaseLight):
    """Light entity for the LED bar."""

    def __init__(self, coordinator, device):
        """Initialize the LED bar light."""
        super().__init__(
            coordinator,
            device,
            "LED Bar",
            "led_bar",
            coordinator.get_led_bar_brightness_range(),
            "led_bar_brightness",
            "async_set_led_bar_brightness",
            DEFAULT_BRIGHTNESS,
        )


class CodecLED(BaseLight):
    """Light entity for the codec LED."""

    def __init__(self, coordinator: AmbeoCoordinator, device):
        """Initialize the codec LED light."""
        super().__init__(
            coordinator,
            device,
            "Codec LED",
            "codec_led",
            coordinator.get_codec_led_brightness_range(),
            "codec_led_brightness",
            "async_set_codec_led_brightness",
            DEFAULT_BRIGHTNESS,
        )


class AmbeoMaxLogo(BaseLight):
    """Light entity for the Ambeo Max logo."""

    def __init__(self, coordinator: AmbeoCoordinator, device):
        """Initialize the Ambeo Max logo light."""
        super().__init__(
            coordinator,
            device,
            "Ambeo Max Logo",
            "ambeo_max_logo",
            coordinator.get_logo_brightness_range(),
            "logo_brightness",
            "async_set_logo_brightness",
            DEFAULT_BRIGHTNESS_AMBEO_MAX,
        )


class AmbeoMaxDisplay(BaseLight):
    """Light entity for the Ambeo Max display."""

    def __init__(self, coordinator: AmbeoCoordinator, device):
        """Initialize the Ambeo Max display light."""
        super().__init__(
            coordinator,
            device,
            "Ambeo Max Display",
            "ambeo_max_display",
            coordinator.get_display_brightness_range(),
            "display_brightness",
            "async_set_display_brightness",
            DEFAULT_BRIGHTNESS_AMBEO_MAX,
        )


class AmbeoLogo(BaseLight):
    """Special light with on/off state separate from brightness."""

    def __init__(self, coordinator: AmbeoCoordinator, device):
        """Initialize the Ambeo logo light."""
        super().__init__(
            coordinator,
            device,
            "Ambeo Logo",
            "ambeo_logo",
            coordinator.get_logo_brightness_range(),
            "logo_brightness",
            "async_set_logo_brightness",
            DEFAULT_BRIGHTNESS,
        )

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
            brightness = math.floor(
                brightness_to_value(self._brightness_scale, kwargs[ATTR_BRIGHTNESS])
            )
            await self.coordinator.async_set_logo_brightness(brightness)

        logo_state = (
            self.coordinator.data.get("logo_state", False)
            if self.coordinator.data
            else False
        )
        if not logo_state:
            await self.coordinator.async_change_logo_state(True)

    async def async_turn_off(self, **kwargs):
        """Turn off the Ambeo Logo light."""
        await self.coordinator.async_change_logo_state(False)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AmbeoConfigEntry,
    async_add_entities,
):
    """Set up lights from a config entry created in the integrations UI."""
    coordinator = config_entry.runtime_data.coordinator
    ambeo_device = config_entry.runtime_data.device
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
