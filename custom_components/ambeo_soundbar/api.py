import async_timeout
import json
import logging
import time
from .const import EXCLUDE_SOURCES_MAX


_LOGGER = logging.getLogger(__name__)
TIMEOUT = 5

class AmbeoApi:
    def __init__(self, ip, port, session, hass):
        """Initialize the API with the given IP, port, session, and Home Assistant instance."""
        self.session = session
        self.hass = hass
        self.ip = ip
        self.port = port
        self.endpoint = f"http://{ip}:{port}/api"
        self._ambeo_max_compat = False

    async def fetch_data(self, url):
        """Fetch data from a given URL."""
        full_url = f"{self.endpoint}/{url}"
        try:
            with async_timeout.timeout(TIMEOUT):
                _LOGGER.debug("Executing URL fetch: %s", full_url)
                response = await self.session.get(full_url)
                json_data = await response.json()
                return json_data
        except Exception as e:
            _LOGGER.error(f"HTTP request exception with url: {full_url}. Exception: {e}")
            return None

    def extract_data(self, json_data, key_path):
        """Extract data from JSON using a specified key path."""
        try:
            for key in key_path:
                json_data = json_data[key]
            return json_data
        except KeyError:
            _LOGGER.error(f"Missing key '{key}' in JSON data")
            return None
        except Exception as e:
            _LOGGER.error(f"Exception extracting data: {e}")
            return None
        
    def generate_nocache(self):
        """Generate a nocache parameter to prevent caching."""
        return int(time.time() * 1000)
        
    async def execute_request(self, function, path, role=None, value=None, from_idx=None, to_idx=None):
        """Execute a request with the specified parameters."""
        url = f"{function}?path={path}"
        if role:
            url += f"&roles={role}"
        if value is not None:
            url += f"&value={value}"
        if from_idx is not None:
            url += f"&from={from_idx}"
        if to_idx is not None:
            url += f"&to={to_idx}"
        url += f"&_nocache={self.generate_nocache()}"
        return await self.fetch_data(url)

    async def get_value(self, path, data_type, role="@all"):
        """Get a value of a specified type from a specified path."""
        value = await self.execute_request("getData", path, "@all")
        if value is not None:
            return self.extract_data(value, ["value", data_type])
        return None

    async def set_value(self, path, data_type, value):
        """Set a value of a specified type at a specified path."""
        await self.execute_request("setData", path, "value", json.dumps({"type": data_type, data_type: value}))

    # Specific functions for interacting with the device features like volume, mute, serial, version, model, night mode, voice enhancement, Ambeo mode, name, Ambeo logo brightness and state, LED bar brightness, codec LED brightness, sound feedback, sources, presets, and player controls follow here, each implemented with appropriate get and set methods as per the device's API.

    ## NAME
    async def get_name(self):
        return await self.get_value("systemmanager:/deviceName", "string_")
    
     ## SERIAL
    async def get_serial(self):
        return await self.get_value("settings:/system/serialNumber", "string_")

    ## VERSION
    async def get_version(self):
        return await self.get_value("ui:settings/firmwareUpdate/currentVersion", "string_")

    ## MODEL
    async def get_model(self):
        return await self.get_value("settings:/system/productName", "string_")

    
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

   
   ## NIGHT MODE
    async def get_night_mode(self):
        if self._ambeo_max_compat:
            return await self.get_value("espresso:nightModeUi", "bool_", "value")
        else:
            return await self.get_value("settings:/popcorn/audio/nightModeStatus", "bool_")

    async def set_night_mode(self, night_mode):
        path =  "espresso:nightModeUi" if self._ambeo_max_compat else "settings:/popcorn/audio/nightModeStatus"
        await self.set_value(path, "bool_", night_mode)
        

    ## VOICE ENHANCEMENT
    async def get_voice_enhancement(self):
        return await self.get_value("settings:/popcorn/audio/voiceEnhancement", "bool_")

    async def set_voice_enhancement(self, voice_enhancement_mode): 
        await self.set_value("settings:/popcorn/audio/voiceEnhancement", "bool_", voice_enhancement_mode)
    
    ## AMBEO MODE
    async def get_ambeo_mode(self):
        if self._ambeo_max_compat:
            return await self.get_value("espresso:ambeoModeUi", "bool_", "value")
        else:
            return await self.get_value("settings:/popcorn/audio/ambeoModeStatus", "bool_")
    
    async def set_ambeo_mode(self, ambeo_mode): 
        path = "espresso:ambeoModeUi" if self._ambeo_max_compat else "settings:/popcorn/audio/ambeoModeStatus"
        await self.set_value(path, "bool_", ambeo_mode)
        
    ## SOUND FEEDBACK
    async def get_sound_feedback(self):
        if self._ambeo_max_compat:
            return await self.get_value("settings:/espresso/soundFeedback", "bool_", "value")
        else:
            return await self.get_value("settings:/popcorn/ux/soundFeedbackStatus", "bool_")

    async def set_sound_feedback(self, state):
        path = "settings:/espresso/soundFeedback" if self._ambeo_max_compat else "settings:/popcorn/ux/soundFeedbackStatus"
        return await self.set_value(path, "bool_", state)

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
    ## TODO: AMBEO MAX NOT COMPATIBLE
    async def get_led_bar_brightness(self):
        return await self.get_value("ui:/settings/interface/ledBrightness", "i32_")

    async def set_led_bar_brightness(self, brightness):
        await self.set_value("ui:/settings/interface/ledBrightness", "i32_", brightness)
        
    ## AMBEO MAX LOGO
    async def set_ambeo_max_logo_brightness(self, brightness):
        display_brightness = await self.get_ambeo_max_display_brightness()
        value = {
            "ambeologo": brightness,
            "display": display_brightness
        }
        await self.set_value("settings:/espresso/brightnessSensor", "espressoBrightness", value)
    async def get_ambeo_max_logo_brightness(self):
        espressoBrightness = await self.get_value("settings:/espresso/brightnessSensor", "espressoBrightness")
        if espressoBrightness:
            return espressoBrightness["ambeologo"]
        return None
    
    ## AMBEO MAX DISPLAY
    async def set_ambeo_max_display_brightness(self, brightness):
        logo_brightness = await self.get_ambeo_max_logo_brightness()
        value = {
            "ambeologo": logo_brightness,
            "display": brightness
        }
        await self.set_value("settings:/espresso/brightnessSensor", "espressoBrightness", value)
        
    async def get_ambeo_max_display_brightness(self):
        espressoBrightness = await self.get_value("settings:/espresso/brightnessSensor", "espressoBrightness")
        if espressoBrightness:
            return espressoBrightness["display"]
        return None
    
    ## CODEC LED
    ## TODO: AMBEO MAX NOT COMPATIBLE
    async def get_codec_led_brightness(self):
        return await self.get_value("ui:/settings/interface/codecLedBrightness", "i32_")

    async def set_codec_led_brightness(self, brightness):
        await self.set_value("ui:/settings/interface/codecLedBrightness", "i32_", brightness)

    ## SOURCES:    
    async def get_current_source(self):
        if self._ambeo_max_compat:
            return await self.get_value("espresso:audioInputID", "i32_")
        else:
            return await self.get_value("popcorn:inputChange/selected", "popcornInputId")

    async def get_all_sources(self):
        if self._ambeo_max_compat:
            input_names_res = await self.execute_request("getRows", "settings:/espresso/inputNames", "@all", None, 0, 20)
            inputs_res = await self.execute_request("getRows", "espresso:", "@all", None, 0, 20)
            if input_names_res is not None and inputs_res is not None:
                input_names = self.extract_data(input_names_res, ["rows"])
                inputs = self.extract_data(inputs_res, ["rows"])
                input_index_map = {
                    input["title"].lower(): index for index, 
                    input in enumerate(inputs)
                }
                formatted_inputs=[]
                for name in input_names:
                    if not name["title"].lower() in EXCLUDE_SOURCES_MAX:
                        id = input_index_map[name["title"]]
                        title = name['value']['string_']
                        formatted_inputs.append({"id": id, "title": title})
                return formatted_inputs
            return None
        else:
            data = await self.execute_request("getRows", "ui:/inputs", "@all", None, 0, 10)
            if data:
                rows = self.extract_data(data, ["rows"])
                return rows
            return None

    async def set_source(self, source_id):
        if self._ambeo_max_compat:
            await self.set_value("espresso:audioInputID", "i32_", source_id)
        else:
            await self.execute_request("setData", f"ui:/inputs/{source_id}", "activate", json.dumps({"type": "bool_", "bool_": True}))
        
    ## PRESETS:
    async def get_current_preset(self):
        if self._ambeo_max_compat:
            return await self.get_value("settings:/espresso/equalizerPreset", "i32_")
        else:
            return await self.get_value("settings:/popcorn/audio/audioPresets/audioPreset", "popcornAudioPreset")

    async def set_preset(self, preset):
        if self._ambeo_max_compat:
            await self.set_value("settings:/espresso/equalizerPreset", "i32_", preset)
        else:
            await self.set_value("settings:/popcorn/audio/audioPresets/audioPreset", "popcornAudioPreset", preset)
    
    async def get_all_presets(self):
        if self._ambeo_max_compat:
            return [
                    {"title": "Neutral", "id": 0},
                    {"title": "Movies", "id": 1},
                    {"title": "Sport", "id": 2},
                    {"title": "News", "id": 3},
                    {"title": "Music", "id": 4}
                ]
        else:
            data = await self.execute_request("getRows", "settings:/popcorn/audio/audioPresetValues", "@all", None, 0, 10)
            if data:
                rows = self.extract_data(data, ["rows"])
                simplified_list = [{"title": row['title'], "id": row['value']['popcornAudioPreset']} for row in rows]
                return simplified_list
            return None

    async def play(self):
        await self.execute_request("setData", "popcorn:multiPurposeButtonActivate", "activate", json.dumps({"type": "bool_", "bool_": True}))

    async def pause(self):
        await self.execute_request("setData", "popcorn:multiPurposeButtonActivate", "activate", json.dumps({"type": "bool_", "bool_": True}))

    async def next(self):
        await self.execute_request("setData", "player:player/control", "activate", json.dumps({"control": "next"}))

    async def previous(self):
        await self.execute_request("setData", "player:player/control", "activate", json.dumps({"control": "previous"}))

    async def player_data(self):
        data = await self.execute_request("getData", "player:player/data/value", "@all")
        if data:
            return self.extract_data(data, ["value", "playLogicData"])
        return None
    
    # Power off (standby)
    async def stand_by(self):
        if self._ambeo_max_compat:
            await self.set_value("espresso:appRequestedStandby", "bool_", True)
            
    # Power on (wake)
    async def wake(self):
        if self._ambeo_max_compat:
            await self.set_value("espresso:appRequestedOnline", "bool_", True)
            
    # Reboot
    async def reboot(self):
        await self.execute_request("setData", "ui:/settings/system/restart", "activate", json.dumps({"type": "bool_", "bool_": True}))
    
    async def get_state(self):
        power_target = await self.get_value("powermanager:target", "powerTarget")
        if power_target:
            return power_target["target"]
        return None
    
    async def start_bluetooth_pairing(self):
        if not self._ambeo_max_compat:
            await self.execute_request("setData", "bluetooth:deviceList/discoverable", "activate", json.dumps({"type": "bool_", "bool_": True}))
