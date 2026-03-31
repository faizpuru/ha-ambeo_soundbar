"""API implementation for Ambeo Soundbar Plus and Mini (Popcorn)."""

import json

from ...const import AMBEO_POPCORN_VOLUME_STEP, Capability
from .generic_api import AmbeoApi


class AmbeoPopcornApi(AmbeoApi):
    """API implementation for Ambeo Soundbar Plus and Mini."""

    _has_subwoofer = None

    additional_inputs = [
        {"id": "airplay", "title": "AirPlay"},
        {"id": "googlecast", "title": "Google Cast"},
    ]

    capabilities = [
        Capability.AMBEO_LOGO,
        Capability.BLUETOOTH_PAIRING,
        Capability.CODEC_LED,
        Capability.ECO_MODE,
        Capability.LED_BAR,
        Capability.SUBWOOFER,
        Capability.VOICE_ENHANCEMENT_TOGGLE,
    ]

    def support_debounce_mode(self):
        """Check if debounce mode is supported."""
        return False

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

    async def has_subwoofer(self):
        """Check if a subwoofer is connected."""
        if self._has_subwoofer is None:
            subwoofers = await self.get_value(
                "settings:/popcorn/subwoofer/list", "popcornSubwooferList"
            )
            if subwoofers is not None:
                self._has_subwoofer = len(subwoofers) > 0
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

    async def get_eco_mode(self):
        """Get the eco mode state."""
        return await self.get_value("uipopcorn:ecoModeState", "bool_")
