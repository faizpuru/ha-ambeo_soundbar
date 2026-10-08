"""Implementation for Ambeo Soundbar Max (Espresso)."""

import asyncio
import logging
from typing import Any

from .const import (
    AMBEO_MAX_VOLUME_STEP,
    BRIGHTNESS_RANGE_AMBEO_MAX_DISPLAY,
    BRIGHTNESS_RANGE_AMBEO_MAX_LOGO,
    EXCLUDE_SOURCES_MAX,
    MAX_SOUNDBAR,
    Capability,
    PathSub,
    StateKey,
)
from .exceptions import AmbeoError, AmbeoResponseError
from .models import Preset, Source
from .soundbar import AmbeoSoundbar
from .transport import AmbeoTransport

_LOGGER = logging.getLogger(__name__)


class AmbeoEspresso(AmbeoSoundbar):
    """Ambeo Soundbar Max."""

    models = (MAX_SOUNDBAR,)

    capabilities = frozenset(
        {
            Capability.AMBEO_MODE_LEVEL,
            Capability.CENTER_SPEAKER_LEVEL,
            Capability.DECODER_STATUS,
            Capability.MAX_DISPLAY,
            Capability.MAX_LOGO,
            Capability.NATIVE_VOLUME,
            Capability.RESET_EXPERT_SETTINGS,
            Capability.SIDE_FIRING_LEVEL,
            Capability.STANDBY,
            Capability.SUBWOOFER,
            Capability.UP_FIRING_LEVEL,
            Capability.VOICE_ENHANCEMENT_LEVEL,
        }
    )

    # brightnessSensor is subscribed separately because it maps to two keys.
    _BRIGHTNESS_PATH = "settings:/espresso/brightnessSensor"

    _SUBSCRIPTIONS = (
        PathSub("player:volume", StateKey.VOLUME, "i32_"),
        PathSub("settings:/mediaPlayer/mute", StateKey.MUTED, "bool_"),
        PathSub("espresso:nightModeUi", StateKey.NIGHT_MODE, "bool_"),
        PathSub("espresso:ambeoModeUi", StateKey.AMBEO_MODE, "bool_"),
        PathSub("settings:/espresso/soundFeedback", StateKey.SOUND_FEEDBACK, "bool_"),
        PathSub("espresso:audioInputID", StateKey.CURRENT_SOURCE, "i32_"),
        PathSub("settings:/espresso/equalizerPreset", StateKey.CURRENT_PRESET, "i32_"),
        PathSub(
            "ui:/mydevice/voiceEnhanceLevel",
            StateKey.VOICE_ENHANCEMENT_LEVEL,
            "i16_",
            Capability.VOICE_ENHANCEMENT_LEVEL,
        ),
        PathSub(
            "ui:/settings/audio/centerSettings",
            StateKey.CENTER_SPEAKER_LEVEL,
            "i16_",
            Capability.CENTER_SPEAKER_LEVEL,
        ),
        PathSub(
            "ui:/settings/audio/widthSettings",
            StateKey.SIDE_FIRING_LEVEL,
            "i16_",
            Capability.SIDE_FIRING_LEVEL,
        ),
        PathSub(
            "ui:/settings/audio/heightSettings",
            StateKey.UP_FIRING_LEVEL,
            "i16_",
            Capability.UP_FIRING_LEVEL,
        ),
        PathSub(
            "settings:/espresso/ambeoMode",
            StateKey.AMBEO_MODE_LEVEL,
            "i32_",
            Capability.AMBEO_MODE_LEVEL,
        ),
        PathSub(
            "ui:/settings/subwoofer/enabled",
            StateKey.SUBWOOFER_STATUS,
            "bool_",
            Capability.SUBWOOFER,
        ),
        PathSub(
            "ui:/settings/subwoofer/volume",
            StateKey.SUBWOOFER_VOLUME,
            "i16_",
            Capability.SUBWOOFER,
        ),
        PathSub(
            "settings:/espresso/decoderStatus",
            StateKey.DECODER_STATUS,
            "espressoDecoderStatus",
            Capability.DECODER_STATUS,
        ),
    )

    _PRESETS = (
        Preset(0, "Neutral"),
        Preset(1, "Movies"),
        Preset(2, "Sport"),
        Preset(3, "News"),
        Preset(4, "Music"),
    )

    def __init__(self, transport: AmbeoTransport, *args, **kwargs) -> None:
        """Initialize and set up instance variables."""
        super().__init__(transport, *args, **kwargs)
        self._has_subwoofer: bool | None = None
        # Logo and display brightness share one path: serialize read-modify-write.
        self._brightness_lock = asyncio.Lock()

    def get_volume_max(self) -> int:
        """Get the maximum native volume value."""
        return 50

    def get_volume_step(self) -> float:
        """Get the volume step size."""
        return AMBEO_MAX_VOLUME_STEP

    def get_subwoofer_min_value(self) -> int:
        """Get the subwoofer minimum value."""
        return -12

    def get_subwoofer_max_value(self) -> int:
        """Get the subwoofer maximum value."""
        return 12

    def get_logo_brightness_range(self) -> tuple[int, int]:
        """Get the Ambeo Max logo brightness range."""
        return BRIGHTNESS_RANGE_AMBEO_MAX_LOGO

    def get_display_brightness_range(self) -> tuple[int, int]:
        """Get the Ambeo Max display brightness range."""
        return BRIGHTNESS_RANGE_AMBEO_MAX_DISPLAY

    async def stand_by(self) -> None:
        """Put the device into standby mode."""
        await self._transport.set_value("espresso:appRequestedStandby", "bool_", True)

    async def wake(self) -> None:
        """Wake the device from standby."""
        await self._transport.set_value("espresso:appRequestedOnline", "bool_", True)

    async def get_night_mode(self) -> bool | None:
        """Get the night mode state."""
        return await self._transport.get_value("espresso:nightModeUi", "bool_")

    async def set_night_mode(self, night_mode: bool) -> None:
        """Set the night mode state."""
        await self._transport.set_value("espresso:nightModeUi", "bool_", night_mode)

    async def get_ambeo_mode(self) -> bool | None:
        """Get the Ambeo mode state."""
        return await self._transport.get_value("espresso:ambeoModeUi", "bool_")

    async def set_ambeo_mode(self, ambeo_mode: bool) -> None:
        """Set the Ambeo mode state."""
        await self._transport.set_value("espresso:ambeoModeUi", "bool_", ambeo_mode)

    async def get_sound_feedback(self) -> bool | None:
        """Get the sound feedback state."""
        return await self._transport.get_value(
            "settings:/espresso/soundFeedback", "bool_"
        )

    async def set_sound_feedback(self, state: bool) -> None:
        """Set the sound feedback state."""
        await self._transport.set_value(
            "settings:/espresso/soundFeedback", "bool_", state
        )

    async def get_current_source(self) -> int | None:
        """Get the current audio source ID."""
        return await self._transport.get_value("espresso:audioInputID", "i32_")

    async def fetch_sources(self) -> list[Source]:
        """Fetch all available audio sources."""
        input_names, inputs = await asyncio.gather(
            self._transport.get_rows("settings:/espresso/inputNames", 0, 20),
            self._transport.get_rows("espresso:", 0, 20),
        )
        input_index_map = {
            row["title"].lower(): index
            for index, row in enumerate(inputs)
            if isinstance(row.get("title"), str)
        }
        sources = []
        for name in input_names:
            title = name.get("title")
            value = name.get("value")
            label = value.get("string_") if isinstance(value, dict) else None
            if not isinstance(title, str) or label is None:
                continue
            key = title.lower()
            if key in EXCLUDE_SOURCES_MAX or key not in input_index_map:
                continue
            sources.append(Source(input_index_map[key], label))
        return sources

    async def set_source(self, source_id: int) -> None:
        """Set the audio source."""
        await self._transport.set_value("espresso:audioInputID", "i32_", source_id)

    async def get_current_preset(self) -> int | None:
        """Get the current audio preset ID."""
        return await self._transport.get_value(
            "settings:/espresso/equalizerPreset", "i32_"
        )

    async def set_preset(self, preset: int) -> None:
        """Set the audio preset."""
        await self._transport.set_value(
            "settings:/espresso/equalizerPreset", "i32_", preset
        )

    async def fetch_presets(self) -> list[Preset]:
        """Return the audio presets (fixed on this model)."""
        return list(self._PRESETS)

    async def fetch_state(self, max_concurrency: int = 3) -> dict[StateKey, Any]:
        """Fetch the full device state.

        Logo and display brightness share one path, read once per fetch.
        """
        state, brightness = await asyncio.gather(
            super().fetch_state(max_concurrency), self._fetch_brightness_state()
        )
        state.update(brightness)
        return state

    async def _fetch_brightness_state(self) -> dict[StateKey, Any]:
        """Return the logo and display brightness state values."""
        try:
            brightness = await self._get_brightness()
        except AmbeoError as e:
            _LOGGER.debug("Brightness not available: %s", e)
            return {}
        values = {
            StateKey.LOGO_BRIGHTNESS: brightness.get("ambeologo"),
            StateKey.DISPLAY_BRIGHTNESS: brightness.get("display"),
        }
        return {key: value for key, value in values.items() if value is not None}

    async def _get_brightness(self) -> dict:
        """Get the logo and display brightness values."""
        brightness = await self._transport.get_value(
            self._BRIGHTNESS_PATH, "espressoBrightness"
        )
        return brightness if isinstance(brightness, dict) else {}

    async def _set_brightness(self, key: str, brightness: int) -> None:
        """Set one brightness value, keeping the other one unchanged."""
        async with self._brightness_lock:
            current = await self._get_brightness()
            value = {
                "ambeologo": current.get("ambeologo"),
                "display": current.get("display"),
                key: brightness,
            }
            if None in value.values():
                raise AmbeoResponseError(
                    f"Missing brightness value for path: {self._BRIGHTNESS_PATH}"
                )
            await self._transport.set_value(
                self._BRIGHTNESS_PATH, "espressoBrightness", value
            )

    async def get_display_brightness(self) -> int | None:
        """Get the display brightness."""
        return (await self._get_brightness()).get("display")

    async def set_display_brightness(self, brightness: int) -> None:
        """Set the display brightness."""
        await self._set_brightness("display", brightness)

    async def get_logo_brightness(self) -> int | None:
        """Get the Ambeo logo brightness."""
        return (await self._get_brightness()).get("ambeologo")

    async def set_logo_brightness(self, brightness: int) -> None:
        """Set the Ambeo logo brightness."""
        await self._set_brightness("ambeologo", brightness)

    async def get_voice_enhancement_level(self) -> int | None:
        """Get the voice enhancement level."""
        return await self._transport.get_value("ui:/mydevice/voiceEnhanceLevel", "i16_")

    async def set_voice_enhancement_level(self, level: int) -> None:
        """Set the voice enhancement level."""
        await self._transport.set_value("ui:/mydevice/voiceEnhanceLevel", "i16_", level)

    async def get_center_speaker_level(self) -> int | None:
        """Get the center speaker level."""
        return await self._transport.get_value(
            "ui:/settings/audio/centerSettings", "i16_"
        )

    async def set_center_speaker_level(self, level: int) -> None:
        """Set the center speaker level."""
        await self._transport.set_value(
            "ui:/settings/audio/centerSettings", "i16_", level
        )

    async def get_side_firing_level(self) -> int | None:
        """Get the side firing speaker level."""
        return await self._transport.get_value(
            "ui:/settings/audio/widthSettings", "i16_"
        )

    async def set_side_firing_level(self, level: int) -> None:
        """Set the side firing speaker level."""
        await self._transport.set_value(
            "ui:/settings/audio/widthSettings", "i16_", level
        )

    async def get_up_firing_level(self) -> int | None:
        """Get the up firing speaker level."""
        return await self._transport.get_value(
            "ui:/settings/audio/heightSettings", "i16_"
        )

    async def set_up_firing_level(self, level: int) -> None:
        """Set the up firing speaker level."""
        await self._transport.set_value(
            "ui:/settings/audio/heightSettings", "i16_", level
        )

    async def get_ambeo_mode_level(self) -> int | None:
        """Get the Ambeo mode level (1=Light, 2=Regular, 3=Boost)."""
        return await self._transport.get_value("settings:/espresso/ambeoMode", "i32_")

    async def set_ambeo_mode_level(self, level: int) -> None:
        """Set the Ambeo mode level (1=Light, 2=Regular, 3=Boost)."""
        await self._transport.set_value("settings:/espresso/ambeoMode", "i32_", level)

    async def get_decoder_status(self) -> dict | None:
        """Get the current audio decoder status."""
        return await self._transport.get_value(
            "settings:/espresso/decoderStatus", "espressoDecoderStatus"
        )

    async def reset_expert_settings(self) -> None:
        """Reset expert audio settings to defaults."""
        await self._transport.activate(
            "ui:/settings/audio/resetExpertSettings", {"type": "bool_", "bool_": True}
        )

    # Subwoofer.
    async def has_subwoofer(self) -> bool:
        """Check if a subwoofer is connected."""
        if self._has_subwoofer is None:
            try:
                data = await self._transport.get_data("ui:/settings/subwoofer/enabled")
            except AmbeoResponseError:
                data = None
            self._has_subwoofer = (
                bool(data.get("modifiable", False)) if isinstance(data, dict) else False
            )
        return self._has_subwoofer

    async def get_subwoofer_volume(self) -> float | None:
        """Get the subwoofer volume."""
        return await self._transport.get_value("ui:/settings/subwoofer/volume", "i16_")

    async def set_subwoofer_volume(self, volume: float) -> None:
        """Set the subwoofer volume."""
        await self._transport.set_value(
            "ui:/settings/subwoofer/volume", "i16_", int(volume)
        )

    async def get_subwoofer_status(self) -> bool | None:
        """Get the subwoofer enabled status."""
        return await self._transport.get_value(
            "ui:/settings/subwoofer/enabled", "bool_"
        )

    async def set_subwoofer_status(self, status: bool) -> None:
        """Set the subwoofer enabled status."""
        await self._transport.set_value(
            "ui:/settings/subwoofer/enabled", "bool_", status
        )

    def subscribed_paths(self) -> list[str]:
        """Return paths to subscribe to, filtered by device capabilities."""
        paths = super().subscribed_paths()
        if self.has_capability(Capability.MAX_DISPLAY) or self.has_capability(
            Capability.MAX_LOGO
        ):
            paths.append(self._BRIGHTNESS_PATH)
        return paths

    def process_event(self, path: str, item_value: dict) -> dict[StateKey, Any]:
        """Map an event path + itemValue to state updates."""
        if path == self._BRIGHTNESS_PATH:
            brightness = item_value.get("espressoBrightness")
            if not isinstance(brightness, dict):
                return {}
            updates: dict[StateKey, Any] = {}
            if "ambeologo" in brightness:
                updates[StateKey.LOGO_BRIGHTNESS] = brightness["ambeologo"]
            if "display" in brightness:
                updates[StateKey.DISPLAY_BRIGHTNESS] = brightness["display"]
            return updates
        return super().process_event(path, item_value)
