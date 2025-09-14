import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.number import NumberDeviceClass


from .const import DOMAIN, Capability
from .entity import AmbeoBaseNumber

from .api.impl.generic_api import AmbeoApi


_LOGGER = logging.getLogger(__name__)


class SubWooferVolume(AmbeoBaseNumber):
    def __init__(self, device, api):
        """Initialize the subwoofer volume."""
        super().__init__(device, api, "Subwoofer volume")

    async def async_set_native_value(self, value: float) -> None:
        """Update the volume of the subwoofer."""
        await self.api.set_subwoofer_volume(value)
        self._current_value = value

    async def async_update(self):
        """Update the current volume of the subwoofer."""
        try:
            volume = await self.api.get_subwoofer_volume()
            self._current_value = volume
        except Exception as e:
            _LOGGER.error("Failed to update subwoofer status: %s", e)

    @property
    def native_step(self):
        """Step"""
        return 1

    @property
    def native_min_value(self):
        """Min value """
        return -10

    @property
    def native_max_value(self):
        """Max value"""
        return 10

    @property
    def native_unit_of_measurement(self):
        """Unit"""
        return "dB"

    @property
    def device_class(self):
        """Device class"""
        return NumberDeviceClass.SOUND_PRESSURE


class VoiceEnhancementLevel(AmbeoBaseNumber):
    def __init__(self, device, api):
        """Initialize the voice enhancement level."""
        super().__init__(device, api, "Voice Enhancement Level")

    async def async_set_native_value(self, value: float) -> None:
        """Update the voice enhancement level."""
        await self.api.set_voice_enhancement_level(int(value))
        self._current_value = int(value)

    async def async_update(self):
        """Update the current voice enhancement level."""
        try:
            level = await self.api.get_voice_enhancement_level()
            self._current_value = level
        except Exception as e:
            _LOGGER.error("Failed to update voice enhancement level: %s", e)

    @property
    def native_step(self):
        """Step"""
        return 1

    @property
    def native_min_value(self):
        """Min value"""
        return 0

    @property
    def native_max_value(self):
        """Max value"""
        return 3

    @property
    def native_unit_of_measurement(self):
        """Unit"""
        return "Level"


class CenterSpeakerLevel(AmbeoBaseNumber):
    def __init__(self, device, api):
        """Initialize the center speaker level."""
        super().__init__(device, api, "Center Speaker Level")

    async def async_set_native_value(self, value: float) -> None:
        """Update the center speaker level."""
        await self.api.set_center_speaker_level(int(value))
        self._current_value = int(value)

    async def async_update(self):
        """Update the current center speaker level."""
        try:
            level = await self.api.get_center_speaker_level()
            self._current_value = level
        except Exception as e:
            _LOGGER.error("Failed to update center speaker level: %s", e)

    @property
    def native_step(self):
        """Step"""
        return 1

    @property
    def native_min_value(self):
        """Min value"""
        return -12

    @property
    def native_max_value(self):
        """Max value"""
        return 12

    @property
    def native_unit_of_measurement(self):
        """Unit"""
        return "dB"

    @property
    def device_class(self):
        """Device class"""
        return NumberDeviceClass.SOUND_PRESSURE


class SideFiringLevel(AmbeoBaseNumber):
    def __init__(self, device, api):
        """Initialize the side firing speakers level."""
        super().__init__(device, api, "Side Firing Speakers Level")

    async def async_set_native_value(self, value: float) -> None:
        """Update the side firing speakers level."""
        await self.api.set_side_firing_level(int(value))
        self._current_value = int(value)

    async def async_update(self):
        """Update the current side firing speakers level."""
        try:
            level = await self.api.get_side_firing_level()
            self._current_value = level
        except Exception as e:
            _LOGGER.error("Failed to update side firing speakers level: %s", e)

    @property
    def native_step(self):
        """Step"""
        return 1

    @property
    def native_min_value(self):
        """Min value"""
        return -12

    @property
    def native_max_value(self):
        """Max value"""
        return 12

    @property
    def native_unit_of_measurement(self):
        """Unit"""
        return "dB"

    @property
    def device_class(self):
        """Device class"""
        return NumberDeviceClass.SOUND_PRESSURE


class UpFiringLevel(AmbeoBaseNumber):
    def __init__(self, device, api):
        """Initialize the up firing speakers level."""
        super().__init__(device, api, "Up Firing Speakers Level")

    async def async_set_native_value(self, value: float) -> None:
        """Update the up firing speakers level."""
        await self.api.set_up_firing_level(int(value))
        self._current_value = int(value)

    async def async_update(self):
        """Update the current up firing speakers level."""
        try:
            level = await self.api.get_up_firing_level()
            self._current_value = level
        except Exception as e:
            _LOGGER.error("Failed to update up firing speakers level: %s", e)

    @property
    def native_step(self):
        """Step"""
        return 1

    @property
    def native_min_value(self):
        """Min value"""
        return -12

    @property
    def native_max_value(self):
        """Max value"""
        return 12

    @property
    def native_unit_of_measurement(self):
        """Unit"""
        return "dB"

    @property
    def device_class(self):
        """Device class"""
        return NumberDeviceClass.SOUND_PRESSURE


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Set up the switch entities from a config entry created in the integrations UI."""
    ambeo_api: AmbeoApi = hass.data[DOMAIN][config_entry.entry_id]["api"]
    ambeo_device = hass.data[DOMAIN][config_entry.entry_id]["device"]
    entities = []
    if ambeo_api.has_capability(Capability.SUBWOOFER) and await ambeo_api.has_subwoofer():
        entities.append(SubWooferVolume(ambeo_device, ambeo_api))
    if ambeo_api.has_capability(Capability.VOICE_ENHANCEMENT_LEVEL):
        entities.append(VoiceEnhancementLevel(ambeo_device, ambeo_api))
    if ambeo_api.has_capability(Capability.CENTER_SPEAKER_LEVEL):
        entities.append(CenterSpeakerLevel(ambeo_device, ambeo_api))
    if ambeo_api.has_capability(Capability.SIDE_FIRING_LEVEL):
        entities.append(SideFiringLevel(ambeo_device, ambeo_api))
    if ambeo_api.has_capability(Capability.UP_FIRING_LEVEL):
        entities.append(UpFiringLevel(ambeo_device, ambeo_api))
    async_add_entities(entities, update_before_add=True)
