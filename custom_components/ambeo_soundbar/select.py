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


class AmbeoModeLevel(AmbeoBaseEntity, SelectEntity):
    """Select entity for the Ambeo mode level (Light / Regular / Boost)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = list(AMBEO_MODE_LEVELS.values())

    def __init__(self, coordinator, device):
        """Initialize the Ambeo mode level select entity."""
        super().__init__(coordinator, device, "Ambeo Mode Level", "ambeo_mode_level")

    @property
    def current_option(self) -> str | None:
        """Return the currently selected option."""
        if self.coordinator.data:
            level = self.coordinator.data.get("ambeo_mode_level")
            if level is not None:
                return AMBEO_MODE_LEVELS.get(int(level))
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        level = _AMBEO_MODE_LEVEL_BY_NAME[option]
        await self.coordinator.async_set_ambeo_mode_level(level)


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
    async_add_entities(entities)
