from .generic_api import AmbeoApi
from ...const import EXCLUDE_SOURCES_MAX, AMBEO_MAX_VOLUME_STEP, Capability


class AmbeoEspressoApi(AmbeoApi):

    capabilities = [Capability.STANDBY,
                    Capability.MAX_LOGO,
                    Capability.MAX_DISPLAY]

    def support_debounce_mode(self):
        return True

    def has_capability(self, capa):
        return capa in self.capabilities

    def get_volume_step(self):
        return AMBEO_MAX_VOLUME_STEP

    async def stand_by(self):
        await self.set_value("espresso:appRequestedStandby", "bool_", True)

    async def wake(self):
        await self.set_value("espresso:appRequestedOnline", "bool_", True)

    async def get_night_mode(self):
        return await self.get_value("espresso:nightModeUi", "bool_", "value")

    async def set_night_mode(self, night_mode):
        await self.set_value("espresso:nightModeUi", "bool_", night_mode)

    async def get_ambeo_mode(self):
        return await self.get_value("espresso:ambeoModeUi", "bool_", "value")

    async def set_ambeo_mode(self, ambeo_mode):
        await self.set_value("espresso:ambeoModeUi", "bool_", ambeo_mode)

    async def get_sound_feedback(self):
        return await self.get_value("settings:/espresso/soundFeedback", "bool_", "value")

    async def set_sound_feedback(self, state):
        return await self.set_value("settings:/espresso/soundFeedback", "bool_", state)

    async def get_current_source(self):
        return await self.get_value("espresso:audioInputID", "i32_")

    async def get_all_sources(self):
        input_names_res = await self.execute_request("getRows", "settings:/espresso/inputNames", "@all", None, 0, 20)
        inputs_res = await self.execute_request("getRows", "espresso:", "@all", None, 0, 20)
        if input_names_res is not None and inputs_res is not None:
            input_names = self.extract_data(input_names_res, ["rows"])
            inputs = self.extract_data(inputs_res, ["rows"])
            input_index_map = {
                input["title"].lower(): index for index,
                input in enumerate(inputs)
            }
            formatted_inputs = []
            for name in input_names:
                if not name["title"].lower() in EXCLUDE_SOURCES_MAX:
                    id = input_index_map[name["title"]]
                    title = name['value']['string_']
                    formatted_inputs.append({"id": id, "title": title})
            return formatted_inputs
        return None

    async def set_source(self, source_id):
        await self.set_value("espresso:audioInputID", "i32_", source_id)

    async def get_current_preset(self):
        return await self.get_value("settings:/espresso/equalizerPreset", "i32_")

    async def set_preset(self, preset):
        await self.set_value("settings:/espresso/equalizerPreset", "i32_", preset)

    async def get_all_presets(self):
        return [
            {"title": "Neutral", "id": 0},
            {"title": "Movies", "id": 1},
            {"title": "Sport", "id": 2},
            {"title": "News", "id": 3},
            {"title": "Music", "id": 4}
        ]

    async def get_display_brightness(self):
        espressoBrightness = await self.get_value("settings:/espresso/brightnessSensor", "espressoBrightness")
        if espressoBrightness:
            return espressoBrightness["display"]
        return None

    async def set_display_brightness(self, brightness):
        logo_brightness = await self.get_logo_brightness()
        value = {
            "ambeologo": logo_brightness,
            "display": brightness
        }
        await self.set_value("settings:/espresso/brightnessSensor", "espressoBrightness", value)

    async def set_logo_brightness(self, brightness):
        display_brightness = await self.get_display_brightness()
        value = {
            "ambeologo": brightness,
            "display": display_brightness
        }
        await self.set_value("settings:/espresso/brightnessSensor", "espressoBrightness", value)

    async def get_logo_brightness(self):
        espressoBrightness = await self.get_value("settings:/espresso/brightnessSensor", "espressoBrightness")
        if espressoBrightness:
            return espressoBrightness["ambeologo"]
        return None
