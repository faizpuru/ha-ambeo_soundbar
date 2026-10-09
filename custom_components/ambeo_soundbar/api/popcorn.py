"""Implementation for Ambeo Soundbar Plus and Mini (Popcorn)."""

from .const import (
    AMBEO_POPCORN_VOLUME_STEP,
    MINI_SOUNDBAR,
    PLUS_SOUNDBAR,
    Capability,
    PathSub,
    StateKey,
)
from .exceptions import AmbeoResponseError
from .models import Preset, Source
from .soundbar import AmbeoSoundbar
from .transport import AmbeoTransport


class AmbeoPopcorn(AmbeoSoundbar):
    """Ambeo Soundbar Plus and Mini."""

    models = (MINI_SOUNDBAR, PLUS_SOUNDBAR)

    capabilities = frozenset(
        {
            Capability.AMBEO_LOGO,
            Capability.BLUETOOTH_PAIRING,
            Capability.CODEC_LED,
            Capability.DECODER_STATUS,
            Capability.ECO_MODE,
            Capability.LED_BAR,
            Capability.NATIVE_VOLUME,
            Capability.SUBWOOFER,
            Capability.VOICE_ENHANCEMENT_TOGGLE,
            Capability.CENTER_VOLUME,
        }
    )

    _SUBSCRIPTIONS = (
        PathSub("player:volume", StateKey.VOLUME, "i32_"),
        PathSub("settings:/mediaPlayer/mute", StateKey.MUTED, "bool_"),
        PathSub(
            "settings:/popcorn/audio/nightModeStatus", StateKey.NIGHT_MODE, "bool_"
        ),
        PathSub(
            "settings:/popcorn/audio/ambeoModeStatus", StateKey.AMBEO_MODE, "bool_"
        ),
        PathSub(
            "settings:/popcorn/ux/soundFeedbackStatus", StateKey.SOUND_FEEDBACK, "bool_"
        ),
        PathSub(
            "popcorn:inputChange/selected", StateKey.CURRENT_SOURCE, "popcornInputId"
        ),
        PathSub(
            "settings:/popcorn/audio/audioPresets/audioPreset",
            StateKey.CURRENT_PRESET,
            "popcornAudioPreset",
        ),
        PathSub(
            "ui:/settings/interface/codecLedBrightness",
            StateKey.CODEC_LED_BRIGHTNESS,
            "i32_",
            Capability.CODEC_LED,
        ),
        PathSub(
            "ui:/settings/interface/ambeoSection/brightness",
            StateKey.LOGO_BRIGHTNESS,
            "i32_",
            Capability.AMBEO_LOGO,
        ),
        PathSub(
            "settings:/popcorn/ui/ledStatus",
            StateKey.LOGO_STATE,
            "bool_",
            Capability.AMBEO_LOGO,
        ),
        PathSub(
            "ui:/settings/interface/ledBrightness",
            StateKey.LED_BAR_BRIGHTNESS,
            "i32_",
            Capability.LED_BAR,
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
            "double_",
            Capability.SUBWOOFER,
        ),
        PathSub(
            "uipopcorn:ecoModeState", StateKey.ECO_MODE, "bool_", Capability.ECO_MODE
        ),
        PathSub(
            "imx8af:decoderAudioFormat",
            StateKey.DECODER_STATUS,
            "imx8AfAudioFormat",
            Capability.DECODER_STATUS,
        ),
        PathSub(
            "settings:/popcorn/audio/voiceEnhancement",
            StateKey.VOICE_ENHANCEMENT,
            "bool_",
            Capability.VOICE_ENHANCEMENT_TOGGLE,
        ),
        PathSub(
            "bluetooth:state",
            StateKey.BLUETOOTH_PAIRING,
            "bluetoothState",
            Capability.BLUETOOTH_PAIRING,
            "pairable",
        ),
        PathSub(
            "settings:/popcorn/audio/centerVolume",
            StateKey.CENTER_VOLUME,
            "double_",
            Capability.CENTER_VOLUME,
        ),
    )

    # Inputs not listed by the device.
    _ADDITIONAL_SOURCES = (
        Source("airplay", "AirPlay"),
        Source("googlecast", "Google Cast"),
    )

    def __init__(self, transport: AmbeoTransport, *args, **kwargs) -> None:
        """Initialize and set up instance variables."""
        super().__init__(transport, *args, **kwargs)
        self._has_subwoofer: bool | None = None

    def get_volume_step(self) -> float:
        """Get the volume step size."""
        return AMBEO_POPCORN_VOLUME_STEP

    async def _multi_purpose_button(self) -> None:
        """Press the multi-purpose button (toggles play/pause)."""
        await self._transport.activate(
            "popcorn:multiPurposeButtonActivate", {"type": "bool_", "bool_": True}
        )

    async def play(self) -> None:
        """Send play command."""
        await self._multi_purpose_button()

    async def pause(self) -> None:
        """Send pause command."""
        await self._multi_purpose_button()

    async def get_bluetooth_pairing_state(self) -> bool | None:
        """Get the Bluetooth pairing state."""
        state = await self._transport.get_value("bluetooth:state", "bluetoothState")
        if isinstance(state, dict):
            return state.get("pairable")
        return None

    async def set_bluetooth_pairing_state(self, state: bool) -> None:
        """Set the Bluetooth pairing state."""
        await self._transport.activate(
            "bluetooth:deviceList/discoverable", {"type": "bool_", "bool_": state}
        )

    async def get_night_mode(self) -> bool | None:
        """Get the night mode state."""
        return await self._transport.get_value(
            "settings:/popcorn/audio/nightModeStatus", "bool_"
        )

    async def set_night_mode(self, night_mode: bool) -> None:
        """Set the night mode state."""
        await self._transport.set_value(
            "settings:/popcorn/audio/nightModeStatus", "bool_", night_mode
        )

    async def get_voice_enhancement(self) -> bool | None:
        """Get the voice enhancement state."""
        return await self._transport.get_value(
            "settings:/popcorn/audio/voiceEnhancement", "bool_"
        )

    async def set_voice_enhancement(self, voice_enhancement_mode: bool) -> None:
        """Set the voice enhancement mode."""
        await self._transport.set_value(
            "settings:/popcorn/audio/voiceEnhancement", "bool_", voice_enhancement_mode
        )

    async def get_ambeo_mode(self) -> bool | None:
        """Get the Ambeo mode state."""
        return await self._transport.get_value(
            "settings:/popcorn/audio/ambeoModeStatus", "bool_"
        )

    async def set_ambeo_mode(self, ambeo_mode: bool) -> None:
        """Set the Ambeo mode state."""
        await self._transport.set_value(
            "settings:/popcorn/audio/ambeoModeStatus", "bool_", ambeo_mode
        )

    async def get_sound_feedback(self) -> bool | None:
        """Get the sound feedback state."""
        return await self._transport.get_value(
            "settings:/popcorn/ux/soundFeedbackStatus", "bool_"
        )

    async def set_sound_feedback(self, state: bool) -> None:
        """Set the sound feedback state."""
        await self._transport.set_value(
            "settings:/popcorn/ux/soundFeedbackStatus", "bool_", state
        )

    async def get_current_source(self) -> str | None:
        """Get the current audio source ID."""
        return await self._transport.get_value(
            "popcorn:inputChange/selected", "popcornInputId"
        )

    async def fetch_sources(self) -> list[Source]:
        """Fetch all available audio sources."""
        rows = await self._transport.get_rows("ui:/inputs", 0, 10)
        sources = [
            Source(row["id"], row["title"], row.get("path"))
            for row in rows
            if "id" in row and "title" in row
        ]
        sources.extend(self._ADDITIONAL_SOURCES)
        return sources

    async def set_source(self, source_id: str) -> None:
        """Set the audio source."""
        # The ID is not always the last segment of the path (spdif -> optical).
        path = next(
            (s.path for s in self.sources if s.id == source_id and s.path),
            f"ui:/inputs/{source_id}",
        )
        await self._transport.activate(path, {"type": "bool_", "bool_": True})

    async def get_current_preset(self) -> str | None:
        """Get the current audio preset ID."""
        return await self._transport.get_value(
            "settings:/popcorn/audio/audioPresets/audioPreset", "popcornAudioPreset"
        )

    async def set_preset(self, preset: str) -> None:
        """Set the audio preset."""
        await self._transport.set_value(
            "settings:/popcorn/audio/audioPresets/audioPreset",
            "popcornAudioPreset",
            preset,
        )

    async def fetch_presets(self) -> list[Preset]:
        """Fetch all available audio presets."""
        rows = await self._transport.get_rows(
            "settings:/popcorn/audio/audioPresetValues", 0, 10
        )
        return [
            Preset(row["value"]["popcornAudioPreset"], row["title"])
            for row in rows
            if "title" in row
            and isinstance(row.get("value"), dict)
            and "popcornAudioPreset" in row["value"]
        ]

    async def get_codec_led_brightness(self) -> int | None:
        """Get the codec LED brightness."""
        return await self._transport.get_value(
            "ui:/settings/interface/codecLedBrightness", "i32_"
        )

    async def set_codec_led_brightness(self, brightness: int) -> None:
        """Set the codec LED brightness."""
        await self._transport.set_value(
            "ui:/settings/interface/codecLedBrightness", "i32_", brightness
        )

    async def get_logo_brightness(self) -> int | None:
        """Get the Ambeo logo brightness."""
        return await self._transport.get_value(
            "ui:/settings/interface/ambeoSection/brightness", "i32_"
        )

    async def set_logo_brightness(self, brightness: int) -> None:
        """Set the Ambeo logo brightness."""
        await self._transport.set_value(
            "ui:/settings/interface/ambeoSection/brightness", "i32_", brightness
        )

    async def get_logo_state(self) -> bool | None:
        """Get the Ambeo logo state."""
        return await self._transport.get_value(
            "settings:/popcorn/ui/ledStatus", "bool_"
        )

    async def change_logo_state(self, value: bool) -> None:
        """Change the Ambeo logo state."""
        await self._transport.set_value(
            "settings:/popcorn/ui/ledStatus", "bool_", value
        )

    async def get_led_bar_brightness(self) -> int | None:
        """Get the LED bar brightness."""
        return await self._transport.get_value(
            "ui:/settings/interface/ledBrightness", "i32_"
        )

    async def set_led_bar_brightness(self, brightness: int) -> None:
        """Set the LED bar brightness."""
        await self._transport.set_value(
            "ui:/settings/interface/ledBrightness", "i32_", brightness
        )

    async def has_subwoofer(self) -> bool:
        """Check if a subwoofer is connected."""
        if self._has_subwoofer is None:
            try:
                subwoofers = await self._transport.get_value(
                    "settings:/popcorn/subwoofer/list", "popcornSubwooferList"
                )
            except AmbeoResponseError:
                subwoofers = None
            self._has_subwoofer = bool(subwoofers)
        return self._has_subwoofer

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

    async def get_subwoofer_volume(self) -> float | None:
        """Get the subwoofer volume."""
        return await self._transport.get_value(
            "ui:/settings/subwoofer/volume", "double_"
        )

    async def set_subwoofer_volume(self, volume: float) -> None:
        """Set the subwoofer volume."""
        await self._transport.set_value(
            "ui:/settings/subwoofer/volume", "double_", volume
        )

    async def get_center_volume(self) -> float | None:
        """Get the center volume."""
        return await self._transport.get_value(
            "settings:/popcorn/audio/centerVolume", "double_"
        )

    async def set_center_volume(self, volume: float) -> None:
        """Set the center volume."""
        await self._transport.set_value(
            "settings:/popcorn/audio/centerVolume", "double_", volume
        )

    async def get_decoder_status(self) -> dict | None:
        """Get the current audio decoder status."""
        return await self._transport.get_value(
            "imx8af:decoderAudioFormat", "imx8AfAudioFormat"
        )

    async def get_eco_mode(self) -> bool | None:
        """Get the eco mode state."""
        return await self._transport.get_value("uipopcorn:ecoModeState", "bool_")
