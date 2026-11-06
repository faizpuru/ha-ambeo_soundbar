"""Base entity classes for Ambeo Soundbar integration."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.light import ATTR_BRIGHTNESS, LightEntity
from homeassistant.components.light.const import ColorMode
from homeassistant.components.number import NumberEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.color import brightness_to_value, value_to_brightness

from .const import DOMAIN
from .coordinator import AmbeoCoordinator

if TYPE_CHECKING:
    from . import AmbeoDevice


@dataclass
class LightConfig:
    """Configuration for a BaseLight entity."""

    brightness_scale: tuple[int, int]
    data_key: str
    set_method: str
    default_brightness: int


_LOGGER = logging.getLogger(__name__)


class AmbeoBaseEntity(CoordinatorEntity[AmbeoCoordinator]):
    """Base class for Ambeo entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AmbeoCoordinator,
        device: AmbeoDevice,
        translation_key: str | None,
        unique_id_suffix: str,
    ) -> None:
        """Initialize the base entity."""
        super().__init__(coordinator)
        self._attr_translation_key = translation_key
        self._attr_unique_id = (
            f"{device.serial}_{unique_id_suffix.lower().replace(' ', '_')}"
        )
        self.ambeo_device = device

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(identifiers={(DOMAIN, self.ambeo_device.serial)})


class BaseLight(AmbeoBaseEntity, LightEntity):
    """Base class for brightness-based light entities."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: AmbeoCoordinator,
        device: AmbeoDevice,
        translation_key: str,
        unique_id_suffix: str,
        config: LightConfig,
    ) -> None:
        """Initialize the light entity."""
        super().__init__(coordinator, device, translation_key, unique_id_suffix)
        self._brightness_scale = config.brightness_scale
        self._data_key = config.data_key
        self._set_method = config.set_method
        self._default_brightness = config.default_brightness

    @property
    def supported_color_modes(self) -> set[ColorMode]:
        """Supported color modes."""
        return {ColorMode.BRIGHTNESS}

    @property
    def color_mode(self) -> ColorMode:
        """Current color mode."""
        return ColorMode.BRIGHTNESS

    @property
    def is_on(self) -> bool:
        """Check if the light is on based on brightness."""
        if self.coordinator.data and self._data_key in self.coordinator.data:
            return bool(self.coordinator.data[self._data_key] > 0)
        return False

    @property
    def brightness(self) -> int | None:
        """Return the brightness of the light."""
        if self.coordinator.data and self._data_key in self.coordinator.data:
            return value_to_brightness(
                self._brightness_scale, self.coordinator.data[self._data_key]
            )
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light with specified brightness, or default."""
        if ATTR_BRIGHTNESS in kwargs:
            brightness = math.floor(
                brightness_to_value(self._brightness_scale, kwargs[ATTR_BRIGHTNESS])
            )
        else:
            brightness = self._default_brightness
        await getattr(self.coordinator, self._set_method)(brightness)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        await getattr(self.coordinator, self._set_method)(0)


class AmbeoValueEntity(AmbeoBaseEntity):
    """Base class for entities bound to one state value and its setter."""

    def __init__(
        self,
        coordinator: AmbeoCoordinator,
        device: AmbeoDevice,
        translation_key: str,
        data_key: str,
        set_method: str,
        unique_id_suffix: str | None = None,
    ) -> None:
        """Initialize the entity."""
        super().__init__(
            coordinator, device, translation_key, unique_id_suffix or translation_key
        )
        self._data_key = data_key
        self._set_method = set_method

    @property
    def _value(self) -> Any:
        """Return the current state value, or None if unknown."""
        if self.coordinator.data:
            return self.coordinator.data.get(self._data_key)
        return None

    async def _async_set_value(self, value: Any) -> None:
        """Write the state value through the coordinator."""
        await getattr(self.coordinator, self._set_method)(value)


class AmbeoBaseSwitch(AmbeoValueEntity, SwitchEntity):
    """Base class for Ambeo switch entities."""

    _attr_entity_category = EntityCategory.CONFIG

    @property
    def is_on(self) -> bool | None:
        """Return True if the switch is on."""
        value = self._value
        return None if value is None else bool(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on."""
        await self._async_set_value(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off."""
        await self._async_set_value(False)


class AmbeoBaseNumber(AmbeoValueEntity, NumberEntity):
    """Base class for Ambeo number entities."""

    # Send the value as an integer.
    _integer = False

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        value: float | None = self._value
        return value

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        await self._async_set_value(int(value) if self._integer else value)
