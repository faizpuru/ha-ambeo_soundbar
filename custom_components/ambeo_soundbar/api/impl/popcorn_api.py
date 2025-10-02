import json

from .generic_api import AmbeoApi
from ...const import AMBEO_POPCORN_VOLUME_STEP, Capability


class AmbeoPopcornApi(AmbeoApi):

    _has_subwoofer = None

    additional_inputs = [
        {"id": "googlecast", "title": "Google Cast"},
        {"id": "airplay", "title": "AirPlay"}
    ]

    capabilities = [Capability.AMBEO_LOGO,
                    Capability.LED_BAR,
                    Capability.CODEC_LED,
                    Capability.VOICE_ENHANCEMENT_TOGGLE,
                    Capability.BLUETOOTH_PAIRING,
                    Capability.SUBWOOFER,
                    Capability.ECO_MODE]

    def has_capability(self, capa):
        return capa in self.capabilities

    def support_debounce_mode(self):
        return False

    def get_volume_step(self):
        return AMBEO_POPCORN_VOLUME_STEP

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
            rows.extend(self.additional_inputs)
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

    async def has_subwoofer(self):
        if self._has_subwoofer is None:
            list = await self.get_value("settings:/popcorn/subwoofer/list", "popcornSubwooferList")
            if list is not None:
                self._has_subwoofer = len(list) > 0
        return self._has_subwoofer

    async def get_subwoofer_status(self):
        return await self.get_value("ui:/settings/subwoofer/enabled", "bool_")

    async def set_subwoofer_status(self, status):
        await self.set_value("ui:/settings/subwoofer/enabled", "bool_", status)

    async def get_subwoofer_volume(self):
        return await self.get_value("ui:/settings/subwoofer/volume", "double_")

    async def set_subwoofer_volume(self, volume):
        await self.set_value("ui:/settings/subwoofer/volume", "double_", volume)

    async def get_eco_mode(self):
        return await self.get_value("uipopcorn:ecoModeState", "bool_", "value")
