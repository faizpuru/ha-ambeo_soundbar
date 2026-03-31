"""Number entities for Ambeo Soundbar integration."""

from homeassistant.components.number import NumberDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN, Capability
from .entity import AmbeoBaseNumber


class SubWooferVolume(AmbeoBaseNumber):
    def __init__(self, coordinator, device):
        super().__init__(
            coordinator,
            device,
            "Subwoofer volume",
            "subwoofer_volume",
            "async_set_subwoofer_volume",
        )

    @property
    def native_step(self):
        return 1

    @property
    def native_min_value(self):
        return self.coordinator.get_subwoofer_min_value()

    @property
    def native_max_value(self):
        return self.coordinator.get_subwoofer_max_value()

    @property
    def native_unit_of_measurement(self):
        return "dB"

    @property
    def device_class(self):
        return NumberDeviceClass.SOUND_PRESSURE


class VoiceEnhancementLevel(AmbeoBaseNumber):
    _attr_native_step = 1
    _attr_native_min_value = 0
    _attr_native_max_value = 3
    _attr_native_unit_of_measurement = "Level"

    def __init__(self, coordinator, device):
        super().__init__(
            coordinator,
            device,
            "Voice Enhancement Level",
            "voice_enhancement_level",
            "async_set_voice_enhancement_level",
        )

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_voice_enhancement_level(int(value))


class _SpeakerLevel(AmbeoBaseNumber):
    """Base for speaker level numbers (dB, -12 to 12, CONFIG category)."""

    _attr_native_step = 1
    _attr_native_min_value = -12
    _attr_native_max_value = 12
    _attr_native_unit_of_measurement = "dB"
    _attr_device_class = NumberDeviceClass.SOUND_PRESSURE
    _attr_entity_category = EntityCategory.CONFIG

    async def async_set_native_value(self, value: float) -> None:
        await getattr(self.coordinator, self._set_method)(int(value))


class CenterSpeakerLevel(_SpeakerLevel):
    def __init__(self, coordinator, device):
        super().__init__(
            coordinator,
            device,
            "Speaker Level - Center",
            "center_speaker_level",
            "async_set_center_speaker_level",
        )


class SideFiringLevel(_SpeakerLevel):
    def __init__(self, coordinator, device):
        super().__init__(
            coordinator,
            device,
            "Speaker Level - Side Firing",
            "side_firing_level",
            "async_set_side_firing_level",
        )


class UpFiringLevel(_SpeakerLevel):
    def __init__(self, coordinator, device):
        super().__init__(
            coordinator,
            device,
            "Speaker Level - Up Firing",
            "up_firing_level",
            "async_set_up_firing_level",
        )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Set up the number entities from a config entry created in the integrations UI."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    ambeo_device = hass.data[DOMAIN][config_entry.entry_id]["device"]
    entities = []
    if (
        coordinator.has_capability(Capability.SUBWOOFER)
        and await coordinator.has_subwoofer()
    ):
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
