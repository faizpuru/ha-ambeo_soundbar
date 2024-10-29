from .generic_api import AmbeoApi
import json
from ...const import AMBEO_PLUS_VOLUME_STEP, Capability


class AmbeoApiPlus(AmbeoApi):

    capabilities = [Capability.AMBEO_LOGO,
                    Capability.LED_BAR,
                    Capability.CODEC_LED,
                    Capability.VOICE_ENHANCEMENT,
                    Capability.BLUETOOTH_PAIRING]

    def has_capability(self, capa):
        return capa in self.capabilities

    def get_volume_step(self):
        return AMBEO_PLUS_VOLUME_STEP

    async def get_bluetooth_pairing_state(self):
        bluetooth_pairing_state = await self.get_value("bluetooth:state", "bluetoothState")
        if bluetooth_pairing_state:
            return bluetooth_pairing_state["pairable"]
        return None

    async def set_bluetooth_pairing_state(self, state):
        await self.execute_request("setData", "bluetooth:deviceList/discoverable", "activate", json.dumps({"type": "bool_", "bool_": state}))

    async def get_night_mode(self):
        return await self.get_value("settings:/popcorn/audio/nightModeStatus", "bool_")

    async def set_night_mode(self, night_mode):
        await self.set_value("settings:/popcorn/audio/nightModeStatus", "bool_", night_mode)

    async def get_voice_enhancement(self):
        return await self.get_value("settings:/popcorn/audio/voiceEnhancement", "bool_")

    async def set_voice_enhancement(self, voice_enhancement_mode):
        await self.set_value("settings:/popcorn/audio/voiceEnhancement", "bool_", voice_enhancement_mode)

    async def get_ambeo_mode(self):
        return await self.get_value("settings:/popcorn/audio/ambeoModeStatus", "bool_")

    async def set_ambeo_mode(self, ambeo_mode):
        await self.set_value("settings:/popcorn/audio/ambeoModeStatus", "bool_", ambeo_mode)

    async def get_sound_feedback(self):
        return await self.get_value("settings:/popcorn/ux/soundFeedbackStatus", "bool_")

    async def set_sound_feedback(self, state):
        return await self.set_value("settings:/popcorn/ux/soundFeedbackStatus", "bool_", state)

    async def get_current_source(self):
        return await self.get_value("popcorn:inputChange/selected", "popcornInputId")

    async def get_all_sources(self):
        data = await self.execute_request("getRows", "ui:/inputs", "@all", None, 0, 10)
        if data:
            rows = self.extract_data(data, ["rows"])
            return rows
        return None

    async def set_source(self, source_id):
        await self.execute_request("setData", f"ui:/inputs/{source_id}", "activate", json.dumps({"type": "bool_", "bool_": True}))

    async def get_current_preset(self):
        return await self.get_value("settings:/popcorn/audio/audioPresets/audioPreset", "popcornAudioPreset")

    async def set_preset(self, preset):
        await self.set_value("settings:/popcorn/audio/audioPresets/audioPreset", "popcornAudioPreset", preset)

    async def get_all_presets(self):
        data = await self.execute_request("getRows", "settings:/popcorn/audio/audioPresetValues", "@all", None, 0, 10)
        if data:
            rows = self.extract_data(data, ["rows"])
            simplified_list = [
                {"title": row['title'], "id": row['value']['popcornAudioPreset']} for row in rows]
            return simplified_list
        return None

    async def get_codec_led_brightness(self):
        return await self.get_value("ui:/settings/interface/codecLedBrightness", "i32_")

    async def set_codec_led_brightness(self, brightness):
        await self.set_value("ui:/settings/interface/codecLedBrightness", "i32_", brightness)

    async def get_logo_brightness(self):
        return await self.get_value("ui:/settings/interface/ambeoSection/brightness", "i32_")

    async def get_logo_state(self):
        return await self.get_value("settings:/popcorn/ui/ledStatus", "bool_")

    async def set_logo_brightness(self, brightness):
        await self.set_value("ui:/settings/interface/ambeoSection/brightness", "i32_", brightness)

    async def change_logo_state(self, value):
        await self.set_value("settings:/popcorn/ui/ledStatus", "bool_", value)

    async def get_led_bar_brightness(self):
        return await self.get_value("ui:/settings/interface/ledBrightness", "i32_")

    async def set_led_bar_brightness(self, brightness):
        await self.set_value("ui:/settings/interface/ledBrightness", "i32_", brightness)
