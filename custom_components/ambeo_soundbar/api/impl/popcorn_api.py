"""API implementation for Ambeo Soundbar Plus and Mini (Popcorn)."""

import json
from typing import Any

from ..const import AMBEO_POPCORN_VOLUME_STEP, Capability, PathSub
from .generic_api import AmbeoApi, _extract_from_subs


class AmbeoPopcornApi(AmbeoApi):
    """API implementation for Ambeo Soundbar Plus and Mini."""

    _SUBSCRIPTIONS: list[PathSub] = [
        PathSub("player:volume", "volume", "i32_"),
        PathSub("settings:/mediaPlayer/mute", "muted", "bool_"),
        PathSub("settings:/popcorn/audio/nightModeStatus", "night_mode", "bool_"),
        PathSub("settings:/popcorn/audio/ambeoModeStatus", "ambeo_mode", "bool_"),
        PathSub("settings:/popcorn/ux/soundFeedbackStatus", "sound_feedback", "bool_"),
        PathSub("popcorn:inputChange/selected", "current_source", "popcornInputId"),
        PathSub(
            "settings:/popcorn/audio/audioPresets/audioPreset",
            "current_preset",
            "popcornAudioPreset",
        ),
        PathSub(
            "ui:/settings/interface/codecLedBrightness",
            "codec_led_brightness",
            "i32_",
            Capability.CODEC_LED,
        ),
        PathSub(
            "ui:/settings/interface/ambeoSection/brightness",
            "logo_brightness",
            "i32_",
            Capability.AMBEO_LOGO,
        ),
        PathSub(
            "settings:/popcorn/ui/ledStatus",
            "logo_state",
            "bool_",
            Capability.AMBEO_LOGO,
        ),
        PathSub(
            "ui:/settings/interface/ledBrightness",
            "led_bar_brightness",
            "i32_",
            Capability.LED_BAR,
        ),
        PathSub(
            "ui:/settings/subwoofer/enabled",
            "subwoofer_status",
            "bool_",
            Capability.SUBWOOFER,
        ),
        PathSub(
            "ui:/settings/subwoofer/volume",
            "subwoofer_volume",
            "double_",
            Capability.SUBWOOFER,
        ),
        PathSub("uipopcorn:ecoModeState", "eco_mode", "bool_", Capability.ECO_MODE),
        PathSub(
            "imx8af:decoderAudioFormat",
            "decoder_status",
            "imx8AfAudioFormat",
            Capability.DECODER_STATUS,
        ),
        PathSub(
            "settings:/popcorn/audio/voiceEnhancement",
            "voice_enhancement",
            "bool_",
            Capability.VOICE_ENHANCEMENT_TOGGLE,
        ),
        PathSub(
            "bluetooth:state",
            "bluetooth_pairing",
            "bluetoothState",
            Capability.BLUETOOTH_PAIRING,
            "pairable",
        ),
        PathSub(
            "settings:/popcorn/audio/centerVolume",
            "center_volume",
            "double_",
            Capability.CENTER_VOLUME,
        ),
    ]

    additional_inputs = [
        {"id": "airplay", "title": "AirPlay"},
        {"id": "googlecast", "title": "Google Cast"},
    ]

    capabilities = [
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
    ]

    def __init__(self, *args, **kwargs) -> None:
        """Initialize and set up instance variables."""
        super().__init__(*args, **kwargs)
        self._has_subwoofer: bool | None = None

    def support_debounce_mode(self) -> bool:
        """Check if debounce mode is supported."""
        return False

    async def play(self) -> None:
        """Send play command."""
        await self.execute_request(
            "setData",
            "popcorn:multiPurposeButtonActivate",
            "activate",
            json.dumps({"type": "bool_", "bool_": True}),
        )

    async def pause(self) -> None:
        """Send pause command."""
        await self.execute_request(
            "setData",
            "popcorn:multiPurposeButtonActivate",
            "activate",
            json.dumps({"type": "bool_", "bool_": True}),
        )

    def get_volume_step(self):
        """Get the volume step size."""
        return AMBEO_POPCORN_VOLUME_STEP

    async def get_bluetooth_pairing_state(self):
        """Get the Bluetooth pairing state."""
        bluetooth_pairing_state = await self.get_value(
            "bluetooth:state", "bluetoothState"
        )
        if bluetooth_pairing_state:
            return bluetooth_pairing_state["pairable"]
        return None

    async def set_bluetooth_pairing_state(self, state):
        """Set the Bluetooth pairing state."""
        await self.execute_request(
            "setData",
            "bluetooth:deviceList/discoverable",
            "activate",
            json.dumps({"type": "bool_", "bool_": state}),
        )

    async def get_night_mode(self):
        """Get the night mode state."""
        return await self.get_value("settings:/popcorn/audio/nightModeStatus", "bool_")

    async def set_night_mode(self, night_mode):
        """Set the night mode state."""
        await self.set_value(
            "settings:/popcorn/audio/nightModeStatus", "bool_", night_mode
        )

    async def get_voice_enhancement(self):
        """Get the voice enhancement state."""
        return await self.get_value("settings:/popcorn/audio/voiceEnhancement", "bool_")

    async def set_voice_enhancement(self, voice_enhancement_mode):
        """Set the voice enhancement mode."""
        await self.set_value(
            "settings:/popcorn/audio/voiceEnhancement", "bool_", voice_enhancement_mode
        )

    async def get_ambeo_mode(self):
        """Get the Ambeo mode state."""
        return await self.get_value("settings:/popcorn/audio/ambeoModeStatus", "bool_")

    async def set_ambeo_mode(self, ambeo_mode):
        """Set the Ambeo mode state."""
        await self.set_value(
            "settings:/popcorn/audio/ambeoModeStatus", "bool_", ambeo_mode
        )

    async def get_sound_feedback(self):
        """Get the sound feedback state."""
        return await self.get_value("settings:/popcorn/ux/soundFeedbackStatus", "bool_")

    async def set_sound_feedback(self, state):
        """Set the sound feedback state."""
        return await self.set_value(
            "settings:/popcorn/ux/soundFeedbackStatus", "bool_", state
        )

    async def get_current_source(self):
        """Get the current audio source."""
        return await self.get_value("popcorn:inputChange/selected", "popcornInputId")

    async def get_all_sources(self):
        """Get all available audio sources."""
        data = await self.execute_request("getRows", "ui:/inputs", "@all", None, 0, 10)
        if data:
            rows = self.extract_data(data, ["rows"])
            if rows is None:
                return None
            rows.extend(self.additional_inputs)
            return rows
        return None

    async def set_source(self, source_id):
        """Set the audio source."""
        await self.execute_request(
            "setData",
            f"ui:/inputs/{source_id}",
            "activate",
            json.dumps({"type": "bool_", "bool_": True}),
        )

    async def get_current_preset(self):
        """Get the current audio preset."""
        return await self.get_value(
            "settings:/popcorn/audio/audioPresets/audioPreset", "popcornAudioPreset"
        )

    async def set_preset(self, preset):
        """Set the audio preset."""
        await self.set_value(
            "settings:/popcorn/audio/audioPresets/audioPreset",
            "popcornAudioPreset",
            preset,
        )

    async def get_all_presets(self):
        """Get all available audio presets."""
        data = await self.execute_request(
            "getRows", "settings:/popcorn/audio/audioPresetValues", "@all", None, 0, 10
        )
        if data:
            rows = self.extract_data(data, ["rows"])
            if rows is None:
                return None
            simplified_list = [
                {"title": row["title"], "id": row["value"]["popcornAudioPreset"]}
                for row in rows
            ]
            return simplified_list
        return None

    async def get_codec_led_brightness(self):
        """Get the codec LED brightness."""
        return await self.get_value("ui:/settings/interface/codecLedBrightness", "i32_")

    async def set_codec_led_brightness(self, brightness):
        """Set the codec LED brightness."""
        await self.set_value(
            "ui:/settings/interface/codecLedBrightness", "i32_", brightness
        )

    async def get_logo_brightness(self):
        """Get the Ambeo logo brightness."""
        return await self.get_value(
            "ui:/settings/interface/ambeoSection/brightness", "i32_"
        )

    async def get_logo_state(self):
        """Get the Ambeo logo state."""
        return await self.get_value("settings:/popcorn/ui/ledStatus", "bool_")

    async def set_logo_brightness(self, brightness):
        """Set the Ambeo logo brightness."""
        await self.set_value(
            "ui:/settings/interface/ambeoSection/brightness", "i32_", brightness
        )

    async def change_logo_state(self, value):
        """Change the Ambeo logo state."""
        await self.set_value("settings:/popcorn/ui/ledStatus", "bool_", value)

    async def get_led_bar_brightness(self):
        """Get the LED bar brightness."""
        return await self.get_value("ui:/settings/interface/ledBrightness", "i32_")

    async def set_led_bar_brightness(self, brightness):
        """Set the LED bar brightness."""
        await self.set_value("ui:/settings/interface/ledBrightness", "i32_", brightness)

    async def has_subwoofer(self) -> bool:
        """Check if a subwoofer is connected."""
        if self._has_subwoofer is None:
            subwoofers = await self.get_value(
                "settings:/popcorn/subwoofer/list", "popcornSubwooferList"
            )
            self._has_subwoofer = (
                len(subwoofers) > 0 if subwoofers is not None else False
            )
        return self._has_subwoofer

    async def get_subwoofer_status(self):
        """Get the subwoofer enabled status."""
        return await self.get_value("ui:/settings/subwoofer/enabled", "bool_")

    async def set_subwoofer_status(self, status):
        """Set the subwoofer enabled status."""
        await self.set_value("ui:/settings/subwoofer/enabled", "bool_", status)

    async def get_subwoofer_volume(self):
        """Get the subwoofer volume."""
        return await self.get_value("ui:/settings/subwoofer/volume", "double_")

    async def set_subwoofer_volume(self, volume):
        """Set the subwoofer volume."""
        await self.set_value("ui:/settings/subwoofer/volume", "double_", volume)

    async def get_center_volume(self):
        """Get the center volume."""
        return await self.get_value("settings:/popcorn/audio/centerVolume", "double_")

    async def set_center_volume(self, volume: float):
        """Set the center volume."""
        await self.set_value("settings:/popcorn/audio/centerVolume", "double_", volume)

    async def get_decoder_status(self) -> dict | None:
        """Get the current audio decoder status."""
        return await self.get_value("imx8af:decoderAudioFormat", "imx8AfAudioFormat")

    async def get_eco_mode(self):
        """Get the eco mode state."""
        return await self.get_value("uipopcorn:ecoModeState", "bool_")

    def get_subscribed_paths(self) -> list[str]:
        """Return paths to subscribe to, filtered by device capabilities."""
        paths = super().get_subscribed_paths()
        paths.extend(
            s.path
            for s in self._SUBSCRIPTIONS
            if s.capability is None or self.has_capability(s.capability)
        )
        return paths

    def process_event(self, path: str, item_value: dict) -> dict[str, Any]:
        """Map an event path + itemValue to coordinator data updates."""
        return super().process_event(path, item_value) or _extract_from_subs(
            self._SUBSCRIPTIONS, path, item_value
        )
