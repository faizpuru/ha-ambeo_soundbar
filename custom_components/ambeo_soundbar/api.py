import logging
import json
import async_timeout
import time

_LOGGER = logging.getLogger(__name__)
TIMEOUT = 5

class AmbeoApi:
    def __init__(self, ip, port, session, hass):
        self.session = session
        self.hass = hass
        self.ip = ip
        self.port = port
        self.endpoint = f"http://{ip}:{port}/api"

    async def fetch_data(self, url):
        full_url = f"{self.endpoint}/{url}"
        try:
            with async_timeout.timeout(TIMEOUT):
                _LOGGER.debug("Executing URL fetch: %s", full_url)
                response = await self.session.get(full_url)
                json_data = await response.json()
                return json_data
        except Exception as e:
            _LOGGER.error(f"Exception lors de la requête HTTP avec l'url: {full_url}. Exception: {e}")
            return None


    def extract_data(self, json_data, key_path):
        try:
            for key in key_path:
                json_data = json_data[key]
            return json_data
        except KeyError:
            _LOGGER.error(f"Clé '{key}' manquante dans les données JSON")
            return None
        except Exception as e:
            _LOGGER.error(f"Exception lors de l'extraction des données : {e}")
            return None
        
    def generate_nocache(self):
        return int(time.time() * 1000) 
        
    async def execute_request(self, function, path, role=None, value=None, from_idx=None, to_idx=None):
        url = f"{function}?path={path}"
        if role:
            url += f"&role={role}"
        if value is not None:
            value_json = json.dumps(value)
            url += f"&value={value_json}"
        if from_idx is not None:
            url += f"&from={from_idx}"
        if to_idx is not None:
            url += f"&to={to_idx}"
        url += f"&_nocache={self.generate_nocache()}"
        return await self.fetch_data(url)


    async def get_value(self, path, data_type):
        value = await self.execute_request("getData", path, "@all")
        if value is not None:
            return self.extract_data(value, ["value", data_type])
        return None


    async def set_value(self, path, data_type, value):
        await self.execute_request("setData", path, "value", {"type": data_type, data_type: value})
            



    ## VOLUME
    async def get_volume(self):
        return await self.get_value("player:volume", "i32_")
    async def set_volume(self, volume): 
        await self.set_value("player:volume", "i32_", volume)
    ## MUTE
    async def is_mute(self):
        return await self.get_value("settings:/mediaPlayer/mute", "bool_")

    async def set_mute(self, mute): 
        await self.set_value("settings:/mediaPlayer/mute", "bool_", mute)

    ## SERIAL
    async def get_serial(self):
        return await self.get_value("settings:/system/serialNumber", "string_")

    ## VERSION
    async def get_version(self):
        return await self.get_value("ui:settings/firmwareUpdate/currentVersion", "string_")

    ## MODEL
    async def get_model(self):
        return await self.get_value("settings:/system/productName", "string_")

    ## NIGHT MODE
    async def get_night_mode(self):
        return await self.get_value("settings:/popcorn/audio/nightModeStatus", "bool_")

    async def set_night_mode(self, night_mode): 
        await self.set_value("settings:/popcorn/audio/nightModeStatus", "bool_", night_mode)

    ## VOICE ENHANCEMENT
    async def get_voice_enhancement(self):
        return await self.get_value("settings:/popcorn/audio/voiceEnhancement", "bool_")

    async def set_voice_enhancement(self, voice_enhancement_mode): 
        await self.set_value("settings:/popcorn/audio/voiceEnhancement", "bool_", voice_enhancement_mode)
    
    ## AMBEO MODE
    async def get_ambeo_mode(self):
        return await self.get_value("settings:/popcorn/audio/ambeoModeStatus", "bool_")
    
    async def set_ambeo_mode(self, ambeo_mode): 
        await self.set_value("settings:/popcorn/audio/ambeoModeStatus", "bool_", ambeo_mode)

    ## NAME
    async def get_name(self):
        return await self.get_value("systemmanager:/deviceName", "string_")

    ## AMBEO LOGO
    async def get_ambeo_logo_brightness(self):
        return await self.get_value("ui:/settings/interface/ambeoSection/brightness", "i32_")

    async def get_ambeo_logo_state(self):
        return await self.get_value("settings:/popcorn/ui/ledStatus", "bool_")

    async def set_ambeo_logo_brightness(self, brightness):
        await self.set_value("ui:/settings/interface/ambeoSection/brightness", "i32_", brightness)

    async def change_ambeo_logo_state(self, value):
        await self.set_value("settings:/popcorn/ui/ledStatus", "bool_", value)

    ## LED BAR
    async def get_led_bar_brightness(self):
        return await self.get_value("ui:/settings/interface/ledBrightness", "i32_")

    async def set_led_bar_brightness(self, brightness):
        await self.set_value("ui:/settings/interface/ledBrightness", "i32_", brightness)

    ## CODEC LED
    async def get_codec_led_brightness(self):
        return await self.get_value("ui:/settings/interface/codecLedBrightness", "i32_")

    async def set_codec_led_brightness(self, brightness):
        await self.set_value("ui:/settings/interface/codecLedBrightness", "i32_", brightness)

    ## SOUND FEEDBACK
    async def get_sound_feedback(self):
        return await self.get_value("settings:/popcorn/ux/soundFeedbackStatus", "bool_")

    async def set_sound_feedback(self, state):
        return await self.set_value("settings:/popcorn/ux/soundFeedbackStatus", "bool_", state)

    ## SOURCES:
    async def get_current_source(self):
        return await self.get_value("popcorn:inputChange/selected", "popcornInputId")

    async def get_all_sources(self):
        data = await self.execute_request("getRows", "ui:/inputs", "@all", None, 0, 10)
        if data:
            rows = self.extract_data(data, ["rows"])
            return rows
        return None

    async def set_source(self, source_id):
        await self.execute_request("setData", f"ui:/inputs/{source_id}", "activate", {"type": "bool_", "bool_": True})
        
    ## PRESETS:
    async def get_current_preset(self):
        return await self.get_value("settings:/popcorn/audio/audioPresets/audioPreset", "popcornAudioPreset")
    async def set_preset(self, preset):
        await self.set_value("settings:/popcorn/audio/audioPresets/audioPreset", "popcornAudioPreset", preset)
    
    async def get_all_presets(self):
        data = await self.execute_request("getRows", "settings:/popcorn/audio/audioPresetValues", "@all", None, 0, 10)
        if data:
            rows = self.extract_data(data, ["rows"])
            simplified_list = [{"title": row['title'], "id": row['value']['popcornAudioPreset']} for row in rows]
            return simplified_list
        return None

    async def play(self):
        await self.execute_request("setData", "popcorn:multiPurposeButtonActivate", "activate", {"type": "bool_", "bool_": True})

    async def pause(self):
        await self.execute_request("setData", "popcorn:multiPurposeButtonActivate", "activate", {"type": "bool_", "bool_": True})

    async def next(self):
        await self.execute_request("setData", "player:player/control", "activate", {"control": "next"})

    async def previous(self):
        await self.execute_request("setData", "player:player/control", "activate", {"control": "previous"})


    async def player_data(self):
        path = "player:player/data/value"
        data = await self.execute_request("getData", path, "@all")
        if data:
            return self.extract_data(data, ["value", "playLogicData"])
        return None