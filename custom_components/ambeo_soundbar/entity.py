"""Base entity classes for Ambeo Soundbar integration."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .__init__ import AmbeoDevice

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.components.number import NumberEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.color import brightness_to_value, value_to_brightness

from .const import DOMAIN
from .coordinator import AmbeoCoordinator


@dataclass
class LightConfig:
    """Configuration for a BaseLight entity."""

    brightness_scale: tuple[int, int]
    data_key: str
    set_method: str
    default_brightness: int


_LOGGER = logging.getLogger(__name__)


class AmbeoBaseEntity(CoordinatorEntity["AmbeoCoordinator"]):
    """Base class for Ambeo entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AmbeoCoordinator,
        device: AmbeoDevice,
        name_suffix: str | None,
        unique_id_suffix: str,
    ):
        """Initialize the base entity."""
        super().__init__(coordinator)
        self._attr_name = name_suffix
        self._attr_unique_id = (
            f"{device.serial}_{unique_id_suffix.lower().replace(' ', '_')}"
        )
        self.ambeo_device = device

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.ambeo_device.serial)},
        }


class BaseLight(AmbeoBaseEntity, LightEntity):
    """Base class for brightness-based light entities."""

    def __init__(
        self,
        coordinator: AmbeoCoordinator,
        device: AmbeoDevice,
        name_suffix: str,
        unique_id_suffix: str,
        config: LightConfig,
    ):
        """Initialize the light entity."""
        super().__init__(coordinator, device, name_suffix, unique_id_suffix)
        self._brightness_scale = config.brightness_scale
        self._data_key = config.data_key
        self._set_method = config.set_method
        self._default_brightness = config.default_brightness

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
            return value_to_brightness(
                self._brightness_scale, self.coordinator.data[self._data_key]
            )
        return None

    async def async_turn_on(self, **kwargs):
        """Turn on the light with specified brightness, or default."""
        if ATTR_BRIGHTNESS in kwargs:
            brightness = math.floor(
                brightness_to_value(self._brightness_scale, kwargs[ATTR_BRIGHTNESS])
            )
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

    def __init__(
        self,
        coordinator: AmbeoCoordinator,
        device,
        feature_name,
        data_key=None,
        set_method=None,
    ):
        """Initialize the switch entity."""
        super().__init__(coordinator, device, feature_name, feature_name)
        if data_key:
            self._data_key = data_key
        if set_method:
            self._set_method = set_method

    @property
    def is_on(self):
        """Return True if the switch is on."""
        if (
            self._data_key
            and self.coordinator.data
            and self._data_key in self.coordinator.data
        ):
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

    def __init__(
        self,
        coordinator: AmbeoCoordinator,
        device,
        feature_name,
        data_key=None,
        set_method=None,
    ):
        """Initialize the number entity."""
        super().__init__(coordinator, device, feature_name, feature_name)
        if data_key:
            self._data_key = data_key
        if set_method:
            self._set_method = set_method

    @property
    def native_value(self):
        """Return the current value."""
        if (
            self._data_key
            and self.coordinator.data
            and self._data_key in self.coordinator.data
        ):
            return self.coordinator.data[self._data_key]
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        if self._set_method:
            await getattr(self.coordinator, self._set_method)(value)
