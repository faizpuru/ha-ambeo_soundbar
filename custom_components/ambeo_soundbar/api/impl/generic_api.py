import aiohttp
import asyncio
import json
import logging
import time

from homeassistant.core import HomeAssistant

from ..exceptions import AmbeoConnectionError
from ...const import TIMEOUT


_LOGGER = logging.getLogger(__name__)


class AmbeoApi:

    capabilities = []

    def __init__(self, ip, port, session: aiohttp.ClientSession, hass: HomeAssistant):
        """Initialize the API with the given IP, port, session, and Home Assistant instance."""
        self.session = session
        self.hass = hass
        self.port = port
        self.set_endpoint(ip)

    def set_endpoint(self, host):
        self.ip = host
        self.endpoint = f"http://{host}:{self.port}/api"

    async def fetch_data(self, url):
        """Fetch data from a given URL."""
        full_url = f"{self.endpoint}/{url}"
        try:
            timeout = aiohttp.ClientTimeout(total=TIMEOUT)
            _LOGGER.debug("Executing URL fetch: %s", full_url)
            async with self.session.get(full_url, timeout=timeout) as response:
                if response.status != 200:
                    _LOGGER.error(
                        "HTTP request failed with status: %s for url: %s",
                        response.status,
                        full_url,
                    )
                    return None

                json_data = await response.json()
                return json_data

        except aiohttp.ClientError as e:
            raise AmbeoConnectionError(
                f"Client error during HTTP request for url: {full_url}. Exception: {e}")
        except asyncio.TimeoutError:
            raise AmbeoConnectionError(
                f"Timeout error while fetching data from url: {full_url}")
        except Exception as e:
            raise AmbeoConnectionError(
                f"Unexpected exception with url: {full_url}. Exception: {e}")

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

    def has_capability(self, capa):
        return capa in self.capabilities

    def support_debounce_mode(self):
        return False

    def get_volume_step(self):
        return 0.01

    # NAME
    async def get_name(self):
        return await self.get_value("systemmanager:/deviceName", "string_")

     # SERIAL
    async def get_serial(self):
        return await self.get_value("settings:/system/serialNumber", "string_")

    # VERSION
    async def get_version(self):
        return await self.get_value("ui:settings/firmwareUpdate/currentVersion", "string_")

    # MODEL
    async def get_model(self):
        return await self.get_value("settings:/system/productName", "string_")

    # VOLUME
    async def get_volume(self):
        return await self.get_value("player:volume", "i32_")

    async def set_volume(self, volume):
        await self.set_value("player:volume", "i32_", volume)

    # MUTE
    async def is_mute(self):
        return await self.get_value("settings:/mediaPlayer/mute", "bool_")

    async def set_mute(self, mute):
        await self.set_value("settings:/mediaPlayer/mute", "bool_", mute)

   # NIGHT MODE
    async def get_night_mode(self):
        pass

    async def set_night_mode(self, night_mode):
        pass

    # VOICE ENHANCEMENT
    async def get_voice_enhancement(self):
        pass

    async def set_voice_enhancement(self, voice_enhancement_mode):
        pass

    # SUB_WOOFER
    async def has_subwoofer(self):
        pass

    async def get_subwoofer_status(self):
        pass

    async def set_subwoofer_status(self):
        pass

    async def get_subwoofer_volume(self):
        pass

    async def set_subwoofer_volume(self):
        pass

    # AMBEO MODE
    async def get_ambeo_mode(self):
        pass

    async def set_ambeo_mode(self, ambeo_mode):
        pass

    # SOUND FEEDBACK
    async def get_sound_feedback(self):
        pass

    async def set_sound_feedback(self, state):
        pass

    # AMBEO LOGO

    async def get_logo_state(self):
        pass

    async def change_logo_state(self, value):
        pass

    async def set_logo_brightness(self, brightness):
        pass

    async def get_logo_brightness(self):
        pass

    # LED BAR
    async def get_led_bar_brightness(self):
        pass

    async def set_led_bar_brightness(self, brightness):
        pass

    # AMBEO DISPLAY

    async def set_display_brightness(self, brightness):
        pass

    async def get_display_brightness(self):
        pass

    # CODEC LED
    async def get_codec_led_brightness(self):
        pass

    async def set_codec_led_brightness(self, brightness):
        pass

    # SOURCES:
    async def get_current_source(self):
        pass

    async def get_all_sources(self):
        pass

    async def set_source(self, source_id):
        pass

    # PRESETS:
    async def get_current_preset(self):
        pass

    async def set_preset(self, preset):
        pass

    async def get_all_presets(self):
        pass

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
        pass

    # Power on (wake)
    async def wake(self):
        pass

    # Reboot
    async def reboot(self):
        await self.execute_request("setData", "ui:/settings/system/restart", "activate", json.dumps({"type": "bool_", "bool_": True}))

    async def get_state(self):
        power_target = await self.get_value("powermanager:target", "powerTarget")
        if power_target:
            return power_target["target"]
        return None

    # Bluetooth pairing
    async def get_bluetooth_pairing_state(self):
        pass

    async def set_bluetooth_pairing_state(self, state):
        pass
