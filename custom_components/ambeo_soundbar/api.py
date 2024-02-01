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


    async def get_value(self, path, data_type):
        url = f"getData?path={path}&roles=@all&_nocache={self.generate_nocache()}"
        json_data = await self.fetch_data(url)
        if json_data is not None:
            return self.extract_data(json_data, ["value", data_type])
        return None


    async def set_value(self, path, data_type, value):
        url = "setData"
        params = {
            "path": path,
            "role": "value",
            "value": json.dumps({"type": data_type, data_type: value}),
            "_nocache": self.generate_nocache()
        }
        try:
            with async_timeout.timeout(TIMEOUT):
                full_url = f"{self.endpoint}/{url}"
                _LOGGER.debug("Executing URL fetch: %s with params %s", full_url, params)
                await self.session.get(full_url, params=params)
        except Exception as e:
            _LOGGER.error(f"Exception lors de la requête HTTP : {e}")
            

    def generate_nocache(self):
        return int(time.time() * 1000)

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
        url = f"getRows?path=ui:/inputs&roles=@all&from=0&to=10&_nocache={self.generate_nocache()}"
        json_data = await self.fetch_data(url)
        rows = self.extract_data(json_data, ["rows"])
        return rows

    async def set_source(self, source_id):
        await self.fetch_data(f'setData?path=ui:/inputs/{source_id}&role=activate&value={{"type":"bool_","bool_":true}}&_nocache={self.generate_nocache()}')

    ## PRESETS:
    async def get_current_preset(self):
        return await self.get_value("settings:/popcorn/audio/audioPresets/audioPreset", "popcornAudioPreset")
    async def set_preset(self, preset):
        await self.set_value("settings:/popcorn/audio/audioPresets/audioPreset", "popcornAudioPreset", preset)
    async def get_all_presets(self):
        url = f"getRows?path=settings:/popcorn/audio/audioPresetValues&roles=@all&from=0&to=10&_nocache={self.generate_nocache()}"
        json_data = await self.fetch_data(url)
        rows = self.extract_data(json_data, ["rows"])
        simplified_list = [{"title": row['title'], "id": row['value']['popcornAudioPreset']} for row in rows]
        return simplified_list

    async def play(self):
        await self.fetch_data(f'setData?path=popcorn:multiPurposeButtonActivate&role=activate&value={{"type":"bool_","bool_":true}}&_nocache={self.generate_nocache()}')

    async def pause(self):
        await self.fetch_data(f'setData?path=popcorn:multiPurposeButtonActivate&role=activate&value={{"type":"bool_","bool_":true}}&_nocache={self.generate_nocache()}')

    async def next(self):
        await self.fetch_data(f'setData?path=player:player/control&role=activate&value={{"control":"next"}}&_nocache={self.generate_nocache()}')

    async def previous(self):
        await self.fetch_data(f'setData?path=player:player/control&role=activate&value={{"control":"previous"}}&_nocache={self.generate_nocache()}') 

    async def player_data(self):
        url = f"getData?path=player:player/data/value&roles=@all&_nocache={self.generate_nocache()}"
        json_data = await self.fetch_data(url)
        if json_data is not None:
            return self.extract_data(json_data, ["value", "playLogicData"])
        return None