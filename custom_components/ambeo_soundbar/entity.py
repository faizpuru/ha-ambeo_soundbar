import logging
import math

from homeassistant.components.light import LightEntity, ColorMode, ATTR_BRIGHTNESS
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.number import NumberEntity
from homeassistant.util.color import value_to_brightness, brightness_to_value
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class AmbeoBaseEntity(CoordinatorEntity):
    """Base class for Ambeo entities."""

    def __init__(self, coordinator, device, name_suffix, unique_id_suffix):
        """Initialize the base entity."""
        super().__init__(coordinator)
        self._name = f"{device.name} {name_suffix}"
        self._unique_id = f"{device.serial}_{unique_id_suffix.lower().replace(' ', '_')}"
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
    """Base class for brightness-based light entities."""

    def __init__(self, coordinator, device, name_suffix, unique_id_suffix,
                 brightness_scale, data_key, set_method, default_brightness):
        """Initialize the light entity."""
        super().__init__(coordinator, device, name_suffix, unique_id_suffix)
        self._brightness_scale = brightness_scale
        self._data_key = data_key
        self._set_method = set_method
        self._default_brightness = default_brightness

    @property
    def supported_color_modes(self):
        """Supported color modes."""
        return {ColorMode.BRIGHTNESS}

    @property
    def color_mode(self):
        """Current color mode."""
        return ColorMode.BRIGHTNESS

    @property
    def is_on(self):
        """Check if the light is on based on brightness."""
        if self.coordinator.data and self._data_key in self.coordinator.data:
            return self.coordinator.data[self._data_key] > 0
        return False

    @property
    def brightness(self):
        """Return the brightness of the light."""
        if self.coordinator.data and self._data_key in self.coordinator.data:
            return value_to_brightness(self._brightness_scale, self.coordinator.data[self._data_key])
        return None

    async def async_turn_on(self, **kwargs):
        """Turn on the light with specified brightness, or default."""
        if ATTR_BRIGHTNESS in kwargs:
            brightness = math.floor(brightness_to_value(self._brightness_scale, kwargs[ATTR_BRIGHTNESS]))
        else:
            brightness = self._default_brightness
        await getattr(self.coordinator, self._set_method)(brightness)

    async def async_turn_off(self, **kwargs):
        """Turn off the light."""
        await getattr(self.coordinator, self._set_method)(0)


class AmbeoBaseSwitch(AmbeoBaseEntity, SwitchEntity):
    """Base class for Ambeo switch entities."""

    _data_key: str | None = None
    _set_method: str | None = None

    def __init__(self, coordinator, device, feature_name, data_key=None, set_method=None):
        """Initialize the switch entity."""
        super().__init__(coordinator, device, feature_name, feature_name)
        if data_key:
            self._data_key = data_key
        if set_method:
            self._set_method = set_method

    @property
    def is_on(self):
        """Return True if the switch is on."""
        if self._data_key and self.coordinator.data and self._data_key in self.coordinator.data:
            return self.coordinator.data[self._data_key]
        return None

    async def async_turn_on(self):
        """Turn on."""
        if self._set_method:
            await getattr(self.coordinator, self._set_method)(True)

    async def async_turn_off(self):
        """Turn off."""
        if self._set_method:
            await getattr(self.coordinator, self._set_method)(False)


class AmbeoBaseNumber(AmbeoBaseEntity, NumberEntity):
    """Base class for Ambeo number entities."""

    _data_key: str | None = None
    _set_method: str | None = None

    def __init__(self, coordinator, device, feature_name, data_key=None, set_method=None):
        """Initialize the number entity."""
        super().__init__(coordinator, device, feature_name, feature_name)
        if data_key:
            self._data_key = data_key
        if set_method:
            self._set_method = set_method

    @property
    def native_value(self):
        """Return the current value."""
        if self._data_key and self.coordinator.data and self._data_key in self.coordinator.data:
            return self.coordinator.data[self._data_key]
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        if self._set_method:
            await getattr(self.coordinator, self._set_method)(value)
