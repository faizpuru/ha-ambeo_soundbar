import logging

from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.number import NumberEntity
from homeassistant.util.color import value_to_brightness
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class AmbeoBaseEntity(CoordinatorEntity):
    """Base class for Ambeo entities."""

    def __init__(self, coordinator, device, name_suffix, unique_id_suffix):
        """Initialize the base entity."""
        super().__init__(coordinator)
        self._name = f"{device.name} {name_suffix}"
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
    def __init__(self, coordinator, device, name_suffix, unique_id_suffix, brightness_scale):
        """Initialize the light entity with specific brightness attribute."""
        super().__init__(coordinator, device, name_suffix, unique_id_suffix)
        self._brightness_scale = brightness_scale

    @property
    def supported_color_modes(self):
        """Supported color modes."""
        return {ColorMode.BRIGHTNESS}

    @property
    def color_mode(self):
        """Current color mode."""
        return ColorMode.BRIGHTNESS


class AmbeoBaseSwitch(AmbeoBaseEntity, SwitchEntity):
    """Base class for Ambeo switch entities."""

    def __init__(self, coordinator, device, feature_name):
        """Initialize the switch entity."""
        super().__init__(coordinator, device, feature_name, feature_name)


class AmbeoBaseNumber(AmbeoBaseEntity, NumberEntity):
    """Base class for Ambeo number entities."""

    def __init__(self, coordinator, device, feature_name):
        """Initialize the number entity."""
        super().__init__(coordinator, device, feature_name, feature_name)
