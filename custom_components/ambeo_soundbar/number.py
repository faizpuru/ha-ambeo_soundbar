import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.number import NumberDeviceClass


from .const import DOMAIN, Capability
from .entity import AmbeoBaseNumber


_LOGGER = logging.getLogger(__name__)


class SubWooferVolume(AmbeoBaseNumber):
    def __init__(self, coordinator, device):
        """Initialize the subwoofer volume."""
        super().__init__(coordinator, device, "Subwoofer volume")

    @property
    def native_value(self):
        """Get current value"""
        if self.coordinator.data and "subwoofer_volume" in self.coordinator.data:
            return self.coordinator.data["subwoofer_volume"]
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Update the volume of the subwoofer."""
        await self.coordinator.async_set_subwoofer_volume(value)

    @property
    def native_step(self):
        """Step"""
        return 1

    @property
    def native_min_value(self):
        """Min value """
        return self.coordinator.get_subwoofer_min_value()

    @property
    def native_max_value(self):
        """Max value"""
        return self.coordinator.get_subwoofer_max_value()

    @property
    def native_unit_of_measurement(self):
        """Unit"""
        return "dB"

    @property
    def device_class(self):
        """Device class"""
        return NumberDeviceClass.SOUND_PRESSURE


class VoiceEnhancementLevel(AmbeoBaseNumber):
    def __init__(self, coordinator, device):
        """Initialize the voice enhancement level."""
        super().__init__(coordinator, device, "Voice Enhancement Level")

    @property
    def native_value(self):
        """Get current value"""
        if self.coordinator.data and "voice_enhancement_level" in self.coordinator.data:
            return self.coordinator.data["voice_enhancement_level"]
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Update the voice enhancement level."""
        await self.coordinator.async_set_voice_enhancement_level(int(value))

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
    def __init__(self, coordinator, device):
        """Initialize the center speaker level."""
        super().__init__(coordinator, device, "Speaker Level - Center")

    @property
    def native_value(self):
        """Get current value"""
        if self.coordinator.data and "center_speaker_level" in self.coordinator.data:
            return self.coordinator.data["center_speaker_level"]
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Update the center speaker level."""
        await self.coordinator.async_set_center_speaker_level(int(value))

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

    @property
    def entity_category(self) -> EntityCategory:
        return EntityCategory.CONFIG


class SideFiringLevel(AmbeoBaseNumber):
    def __init__(self, coordinator, device):
        """Initialize the side firing speakers level."""
        super().__init__(coordinator, device, "Speaker Level - Side Firing")

    @property
    def native_value(self):
        """Get current value"""
        if self.coordinator.data and "side_firing_level" in self.coordinator.data:
            return self.coordinator.data["side_firing_level"]
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Update the side firing speakers level."""
        await self.coordinator.async_set_side_firing_level(int(value))

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

    @property
    def entity_category(self) -> EntityCategory:
        return EntityCategory.CONFIG


class UpFiringLevel(AmbeoBaseNumber):
    def __init__(self, coordinator, device):
        """Initialize the up firing speakers level."""
        super().__init__(coordinator, device, "Speaker Level - Up Firing")

    @property
    def native_value(self):
        """Get current value"""
        if self.coordinator.data and "up_firing_level" in self.coordinator.data:
            return self.coordinator.data["up_firing_level"]
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Update the up firing speakers level."""
        await self.coordinator.async_set_up_firing_level(int(value))

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

    @property
    def entity_category(self) -> EntityCategory:
        return EntityCategory.CONFIG


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Set up the switch entities from a config entry created in the integrations UI."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    ambeo_device = hass.data[DOMAIN][config_entry.entry_id]["device"]
    entities = []
    if coordinator.has_capability(Capability.SUBWOOFER) and await coordinator.has_subwoofer():
        entities.append(SubWooferVolume(coordinator, ambeo_device))
    if coordinator.has_capability(Capability.VOICE_ENHANCEMENT_LEVEL):
        entities.append(VoiceEnhancementLevel(coordinator, ambeo_device))
    if coordinator.has_capability(Capability.CENTER_SPEAKER_LEVEL):
        entities.append(CenterSpeakerLevel(coordinator, ambeo_device))
    if coordinator.has_capability(Capability.SIDE_FIRING_LEVEL):
        entities.append(SideFiringLevel(coordinator, ambeo_device))
    if coordinator.has_capability(Capability.UP_FIRING_LEVEL):
        entities.append(UpFiringLevel(coordinator, ambeo_device))
    async_add_entities(entities)
