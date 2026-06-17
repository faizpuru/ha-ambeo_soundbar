"""Select entities for Ambeo Soundbar integration."""

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant

from . import AmbeoConfigEntry
from .api.const import Capability
from .entity import AmbeoBaseEntity

AMBEO_MODE_LEVELS: dict[int, str] = {
    1: "Light",
    2: "Regular",
    3: "Boost",
}
_AMBEO_MODE_LEVEL_BY_NAME = {v: k for k, v in AMBEO_MODE_LEVELS.items()}
_AMBEO_OFF = "Off"


class AmbeoModeLevel(AmbeoBaseEntity, SelectEntity):
    """Select entity for the Ambeo mode level (Off / Light / Regular / Boost)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = [_AMBEO_OFF, *AMBEO_MODE_LEVELS.values()]

    def __init__(self, coordinator, device):
        """Initialize the Ambeo mode level select entity."""
        super().__init__(coordinator, device, "Ambeo Mode", "ambeo_mode_level")

    @property
    def current_option(self) -> str | None:
        """Return the currently selected option."""
        if self.coordinator.data:
            if not self.coordinator.data.get("ambeo_mode"):
                return _AMBEO_OFF
            level = self.coordinator.data.get("ambeo_mode_level")
            if level is not None:
                return AMBEO_MODE_LEVELS.get(int(level))
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option == _AMBEO_OFF:
            await self.coordinator.async_set_ambeo_mode(False)
        else:
            level = _AMBEO_MODE_LEVEL_BY_NAME[option]
            await self.coordinator.async_set_ambeo_mode(True)
            await self.coordinator.async_set_ambeo_mode_level(level)


class SourceSelect(AmbeoBaseEntity, SelectEntity):
    """Select entity for the audio source (HDMI, Optical, …)."""

    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, device):
        """Initialize the source select entity."""
        super().__init__(coordinator, device, "Source", "source")
        self._attr_options = sorted(
            s["title"] for s in coordinator.sources if "title" in s
        )

    @property
    def current_option(self) -> str | None:
        """Return the currently selected source."""
        if self.coordinator.data and "current_source" in self.coordinator.data:
            return self.coordinator.get_source_title(
                self.coordinator.data["current_source"]
            )
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected source."""
        source_id = self.coordinator.get_source_id(option)
        if source_id is not None:
            await self.coordinator.async_select_source(source_id)


class SoundModeSelect(AmbeoBaseEntity, SelectEntity):
    """Select entity for the sound mode (Movies, Music, Neutral, …)."""

    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, device):
        """Initialize the sound mode select entity."""
        super().__init__(coordinator, device, "Sound Mode", "sound_mode")
        self._attr_options = sorted(
            p["title"] for p in coordinator.presets if "title" in p
        )

    @property
    def current_option(self) -> str | None:
        """Return the currently selected sound mode."""
        if self.coordinator.data and "current_preset" in self.coordinator.data:
            return self.coordinator.get_preset_title(
                self.coordinator.data["current_preset"]
            )
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected sound mode."""
        preset_id = self.coordinator.get_preset_id(option)
        if preset_id is not None:
            await self.coordinator.async_select_sound_mode(preset_id)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AmbeoConfigEntry,
    async_add_entities,
) -> None:
    """Set up select entities from a config entry."""
    coordinator = config_entry.runtime_data.coordinator
    ambeo_device = config_entry.runtime_data.device
    entities = []
    if coordinator.has_capability(Capability.AMBEO_MODE_LEVEL):
        entities.append(AmbeoModeLevel(coordinator, ambeo_device))
    if coordinator.sources:
        entities.append(SourceSelect(coordinator, ambeo_device))
    if coordinator.presets:
        entities.append(SoundModeSelect(coordinator, ambeo_device))
    async_add_entities(entities)
