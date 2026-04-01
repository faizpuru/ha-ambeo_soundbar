"""API implementation for Ambeo Soundbar Max (Espresso)."""

import asyncio

from ...const import AMBEO_MAX_VOLUME_STEP, EXCLUDE_SOURCES_MAX, Capability
from .generic_api import AmbeoApi


class AmbeoEspressoApi(AmbeoApi):
    """API implementation for Ambeo Soundbar Max."""

    capabilities = [
        Capability.CENTER_SPEAKER_LEVEL,
        Capability.MAX_DISPLAY,
        Capability.MAX_LOGO,
        Capability.RESET_EXPERT_SETTINGS,
        Capability.SIDE_FIRING_LEVEL,
        Capability.STANDBY,
        Capability.SUBWOOFER,
        Capability.UP_FIRING_LEVEL,
        Capability.VOICE_ENHANCEMENT_LEVEL,
    ]

    _has_subwoofer = None

    def support_debounce_mode(self):
        """Check if debounce mode is supported."""
        return True

    def get_volume_step(self):
        """Get the volume step size."""
        return AMBEO_MAX_VOLUME_STEP

    def get_subwoofer_min_value(self):
        """Get the subwoofer minimum value."""
        return -12

    def get_subwoofer_max_value(self):
        """Get the subwoofer maximum value."""
        return 12

    async def stand_by(self):
        """Put the device into standby mode."""
        await self.set_value("espresso:appRequestedStandby", "bool_", True)

    async def wake(self):
        """Wake the device from standby."""
        await self.set_value("espresso:appRequestedOnline", "bool_", True)

    async def get_night_mode(self):
        """Get the night mode state."""
        return await self.get_value("espresso:nightModeUi", "bool_")

    async def set_night_mode(self, night_mode):
        """Set the night mode state."""
        await self.set_value("espresso:nightModeUi", "bool_", night_mode)

    async def get_ambeo_mode(self):
        """Get the Ambeo mode state."""
        return await self.get_value("espresso:ambeoModeUi", "bool_")

    async def set_ambeo_mode(self, ambeo_mode):
        """Set the Ambeo mode state."""
        await self.set_value("espresso:ambeoModeUi", "bool_", ambeo_mode)

    async def get_sound_feedback(self):
        """Get the sound feedback state."""
        return await self.get_value("settings:/espresso/soundFeedback", "bool_")

    async def set_sound_feedback(self, state):
        """Set the sound feedback state."""
        return await self.set_value("settings:/espresso/soundFeedback", "bool_", state)

    async def get_current_source(self):
        """Get the current audio source."""
        return await self.get_value("espresso:audioInputID", "i32_")

    async def get_all_sources(self):
        """Get all available audio sources."""
        input_names_res, inputs_res = await asyncio.gather(
            self.execute_request(
                "getRows", "settings:/espresso/inputNames", "@all", None, 0, 20
            ),
            self.execute_request("getRows", "espresso:", "@all", None, 0, 20),
        )
        if input_names_res is not None and inputs_res is not None:
            input_names = self.extract_data(input_names_res, ["rows"])
            inputs = self.extract_data(inputs_res, ["rows"])
            if input_names is None or inputs is None:
                return None
            input_index_map = {
                input["title"].lower(): index for index, input in enumerate(inputs)
            }
            formatted_inputs = []
            for name in input_names:
                if name["title"].lower() not in EXCLUDE_SOURCES_MAX:
                    source_id = input_index_map[name["title"]]
                    title = name["value"]["string_"]
                    formatted_inputs.append({"id": source_id, "title": title})
            return formatted_inputs
        return None

    async def set_source(self, source_id):
        """Set the audio source."""
        await self.set_value("espresso:audioInputID", "i32_", source_id)

    async def get_current_preset(self):
        """Get the current audio preset."""
        return await self.get_value("settings:/espresso/equalizerPreset", "i32_")

    async def set_preset(self, preset):
        """Set the audio preset."""
        await self.set_value("settings:/espresso/equalizerPreset", "i32_", preset)

    async def get_all_presets(self):
        """Get all available audio presets."""
        return [
            {"title": "Neutral", "id": 0},
            {"title": "Movies", "id": 1},
            {"title": "Sport", "id": 2},
            {"title": "News", "id": 3},
            {"title": "Music", "id": 4},
        ]

    async def get_display_brightness(self):
        """Get the display brightness."""
        espressoBrightness = await self.get_value(
            "settings:/espresso/brightnessSensor", "espressoBrightness"
        )
        if espressoBrightness:
            return espressoBrightness["display"]
        return None

    async def set_display_brightness(self, brightness):
        """Set the display brightness."""
        logo_brightness = await self.get_logo_brightness()
        value = {"ambeologo": logo_brightness, "display": brightness}
        await self.set_value(
            "settings:/espresso/brightnessSensor", "espressoBrightness", value
        )

    async def set_logo_brightness(self, brightness):
        """Set the Ambeo logo brightness."""
        display_brightness = await self.get_display_brightness()
        value = {"ambeologo": brightness, "display": display_brightness}
        await self.set_value(
            "settings:/espresso/brightnessSensor", "espressoBrightness", value
        )

    async def get_logo_brightness(self):
        """Get the Ambeo logo brightness."""
        espressoBrightness = await self.get_value(
            "settings:/espresso/brightnessSensor", "espressoBrightness"
        )
        if espressoBrightness:
            return espressoBrightness["ambeologo"]
        return None

    async def get_voice_enhancement_level(self):
        """Get the voice enhancement level."""
        return await self.get_value("ui:/mydevice/voiceEnhanceLevel", "i16_")

    async def set_voice_enhancement_level(self, level):
        """Set the voice enhancement level."""
        await self.set_value("ui:/mydevice/voiceEnhanceLevel", "i16_", level)

    async def get_center_speaker_level(self):
        """Get the center speaker level."""
        return await self.get_value("ui:/settings/audio/centerSettings", "i16_")

    async def set_center_speaker_level(self, level):
        """Set the center speaker level."""
        await self.set_value("ui:/settings/audio/centerSettings", "i16_", level)

    async def get_side_firing_level(self):
        """Get the side firing speaker level."""
        return await self.get_value("ui:/settings/audio/widthSettings", "i16_")

    async def set_side_firing_level(self, level):
        """Set the side firing speaker level."""
        await self.set_value("ui:/settings/audio/widthSettings", "i16_", level)

    async def get_up_firing_level(self):
        """Get the up firing speaker level."""
        return await self.get_value("ui:/settings/audio/heightSettings", "i16_")

    async def set_up_firing_level(self, level):
        """Set the up firing speaker level."""
        await self.set_value("ui:/settings/audio/heightSettings", "i16_", level)

    async def reset_expert_settings(self):
        """Reset expert audio settings to defaults."""
        await self.execute_request(
            "setData",
            "ui:/settings/audio/resetExpertSettings",
            "activate",
            '{"type":"bool_","bool_":true}',
        )

    # Subwoofer.
    async def has_subwoofer(self) -> bool:
        """Check if a subwoofer is connected."""
        if self._has_subwoofer is None:
            data = await self.execute_request(
                "getData", "ui:/settings/subwoofer/enabled", "@all"
            )
            if data is not None:
                self._has_subwoofer = data.get("modifiable", False)
            else:
                self._has_subwoofer = False
        return self._has_subwoofer

    async def get_subwoofer_volume(self):
        """Get the subwoofer volume."""
        return await self.get_value("ui:/settings/subwoofer/volume", "i16_")

    async def set_subwoofer_volume(self, volume):
        """Set the subwoofer volume."""
        await self.set_value("ui:/settings/subwoofer/volume", "i16_", int(volume))

    async def get_subwoofer_status(self):
        """Get the subwoofer enabled status."""
        return await self.get_value("ui:/settings/subwoofer/enabled", "bool_")

    async def set_subwoofer_status(self, status):
        """Set the subwoofer enabled status."""
        await self.set_value("ui:/settings/subwoofer/enabled", "bool_", status)
