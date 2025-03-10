import logging

from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.number import NumberEntity
from homeassistant.util.color import value_to_brightness
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .api.impl.generic_api import AmbeoApi

_LOGGER = logging.getLogger(__name__)


class AmbeoBaseEntity(Entity):
    """Base class for Ambeo entities."""

    def __init__(self, device, api: AmbeoApi, name_suffix, unique_id_suffix):
        """Initialize the base entity."""
        self._name = f"{device.name} {name_suffix}"
        self.api = api
        self._unique_id = f"{device.serial}_{
            unique_id_suffix.lower().replace(' ', '_')}"
        self.ambeo_device = device

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.ambeo_device.serial)},
        }

    @property
    def unique_id(self):
        """Return the unique identifier for the entity."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name


class BaseLight(AmbeoBaseEntity, LightEntity):
    def __init__(self, device, api, name_suffix, unique_id_suffix, brightness_scale):
        """Initialize the light entity with specific brightness attribute."""
        super().__init__(device, api, name_suffix, unique_id_suffix)
        self._brightness = 0  # Specific to light type entities
        self._brightness_scale = brightness_scale

    @property
    def is_on(self):
        """Check if the light is on based on brightness."""
        return self._brightness > 0

    @property
    def available(self):
        return self._brightness is not None

    @property
    def supported_color_modes(self):
        """Supported color modes."""
        return {ColorMode.BRIGHTNESS}

    @property
    def color_mode(self):
        """Current color mode."""
        return ColorMode.BRIGHTNESS

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return value_to_brightness(self._brightness_scale, self._brightness)


class AmbeoBaseSwitch(AmbeoBaseEntity, SwitchEntity):
    """The class remains largely unchanged."""

    def __init__(self, device, api, feature_name):
        """Initialize the switch entity."""
        super().__init__(device, api, feature_name, feature_name)
        self._is_on = True

    @property
    def is_on(self):
        """Determine if the switch is currently on or off."""
        return self._is_on

    @property
    def available(self):
        return self._is_on is not None


class AmbeoBaseNumber(AmbeoBaseEntity, NumberEntity):
    """Generic ambeo number."""

    def __init__(self, device, api, feature_name):
        """Initialize the number entity."""
        super().__init__(device, api, feature_name, feature_name)
        self._current_value = None

    @property
    def native_value(self):
        """Get current value"""
        return self._current_value
