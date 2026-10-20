"""Number entities for Ambeo Soundbar integration."""

from homeassistant.components.number import NumberDeviceClass
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from pyambeo import Capability, StateKey

from . import AmbeoConfigEntry
from .entity import AmbeoBaseNumber


class _RangedNumber(AmbeoBaseNumber):
    """Number whose bounds are reported by the soundbar.

    The class attributes are used when the soundbar does not report them.
    """

    _range_key: StateKey

    def __init__(self, *args, **kwargs):
        """Initialize the number and apply the bounds of the soundbar."""
        super().__init__(*args, **kwargs)
        bounds = self.coordinator.get_range(self._range_key)
        if bounds is None:
            return
        self._attr_native_min_value = bounds.min
        self._attr_native_max_value = bounds.max
        self._attr_native_step = bounds.step
        if bounds.unit:
            self._attr_native_unit_of_measurement = bounds.unit


class NativeVolume(AmbeoBaseNumber):
    """Number entity for the native volume value."""

    _attr_native_step = 1
    _attr_native_min_value = 0
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, device):
        """Initialize the native volume number entity."""
        super().__init__(
            coordinator,
            device,
            "Volume (native)",
            "volume",
            "async_set_volume",
            unique_id_suffix="Native Volume",
        )

    @property
    def native_max_value(self):
        """Return the maximum volume shown by the soundbar."""
        return self.coordinator.get_display_volume_max()

    @property
    def native_value(self):
        """Return the volume shown by the soundbar.

        The Max shows half of the device volume, rounded down.
        """
        if self.coordinator.data and "volume" in self.coordinator.data:
            return (
                self.coordinator.data["volume"]
                * self.coordinator.get_display_volume_max()
                // 100
            )
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the volume from the scale shown by the soundbar."""
        await self.coordinator.async_set_volume(
            round(value * 100 / self.coordinator.get_display_volume_max())
        )


class SubWooferVolume(_RangedNumber):
    """Number entity for subwoofer volume."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_step = 1
    _attr_native_min_value = -10
    _attr_native_max_value = 10
    _attr_native_unit_of_measurement = "dB"
    _attr_device_class = NumberDeviceClass.SOUND_PRESSURE
    _range_key = StateKey.SUBWOOFER_VOLUME

    def __init__(self, coordinator, device):
        """Initialize the subwoofer volume number entity."""
        super().__init__(
            coordinator,
            device,
            "Subwoofer Volume",
            "subwoofer_volume",
            "async_set_subwoofer_volume",
        )


class VoiceEnhancementLevel(_RangedNumber):
    """Number entity for the voice enhancement level."""

    _attr_entity_category = EntityCategory.CONFIG

    _attr_native_step = 1
    _attr_native_min_value = 0
    _attr_native_max_value = 3
    _attr_native_unit_of_measurement = "Level"
    _integer = True
    _range_key = StateKey.VOICE_ENHANCEMENT_LEVEL

    def __init__(self, coordinator, device):
        """Initialize the voice enhancement level number entity."""
        super().__init__(
            coordinator,
            device,
            "Voice Enhancement Level",
            "voice_enhancement_level",
            "async_set_voice_enhancement_level",
        )


class CenterVolume(_RangedNumber):
    """Number entity for the center channel volume."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_step = 1
    _attr_native_min_value = -3
    _attr_native_max_value = 6
    _attr_native_unit_of_measurement = "dB"
    _attr_device_class = NumberDeviceClass.SOUND_PRESSURE
    _integer = True
    _range_key = StateKey.CENTER_VOLUME

    def __init__(self, coordinator, device):
        """Initialize the center volume number entity."""
        super().__init__(
            coordinator,
            device,
            "Center Volume",
            "center_volume",
            "async_set_center_volume",
        )


class _SpeakerLevel(_RangedNumber):
    """Base for speaker level numbers (dB, -12 to 12, CONFIG category)."""

    _attr_native_step = 1
    _attr_native_min_value = -12
    _attr_native_max_value = 12
    _attr_native_unit_of_measurement = "dB"
    _attr_device_class = NumberDeviceClass.SOUND_PRESSURE
    _attr_entity_category = EntityCategory.CONFIG
    _integer = True


class CenterSpeakerLevel(_SpeakerLevel):
    """Number entity for the center speaker level."""

    _range_key = StateKey.CENTER_SPEAKER_LEVEL

    def __init__(self, coordinator, device):
        """Initialize the center speaker level number entity."""
        super().__init__(
            coordinator,
            device,
            "Speaker Level - Center",
            "center_speaker_level",
            "async_set_center_speaker_level",
        )


class SideFiringLevel(_SpeakerLevel):
    """Number entity for the side-firing speaker level."""

    _range_key = StateKey.SIDE_FIRING_LEVEL

    def __init__(self, coordinator, device):
        """Initialize the side-firing speaker level number entity."""
        super().__init__(
            coordinator,
            device,
            "Speaker Level - Side Firing",
            "side_firing_level",
            "async_set_side_firing_level",
        )


class UpFiringLevel(_SpeakerLevel):
    """Number entity for the up-firing speaker level."""

    _range_key = StateKey.UP_FIRING_LEVEL

    def __init__(self, coordinator, device):
        """Initialize the up-firing speaker level number entity."""
        super().__init__(
            coordinator,
            device,
            "Speaker Level - Up Firing",
            "up_firing_level",
            "async_set_up_firing_level",
        )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AmbeoConfigEntry,
    async_add_entities,
):
    """Set up the number entities from a config entry created in the integrations UI."""
    coordinator = config_entry.runtime_data.coordinator
    ambeo_device = config_entry.runtime_data.device
    entities = []
    if coordinator.has_capability(Capability.NATIVE_VOLUME):
        entities.append(NativeVolume(coordinator, ambeo_device))
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
    if coordinator.has_capability(Capability.CENTER_VOLUME):
        entities.append(CenterVolume(coordinator, ambeo_device))
    async_add_entities(entities)
