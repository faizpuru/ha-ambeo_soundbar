"""Generic API base class for Ambeo Soundbar integration."""

import json
import logging
import time

import aiohttp

from ..const import BRIGHTNESS_RANGE_DEFAULT
from ..exceptions import AmbeoConnectionError

_LOGGER = logging.getLogger(__name__)


class AmbeoApi:
    """Base API class for Ambeo Soundbar devices."""

    capabilities = []

    def __init__(self, ip, port, timeout: int, session: aiohttp.ClientSession):
        """Initialize the API with the given IP, port, session, and Home Assistant instance."""
        self.session = session
        self.port = port
        self.set_endpoint(ip)
        self.timeout = timeout

    def set_endpoint(self, host):
        """Set the API endpoint host."""
        self.ip = host
        self.endpoint = f"http://{host}:{self.port}/api"

    async def fetch_data(self, url):
        """Fetch data from a given URL."""
        full_url = f"{self.endpoint}/{url}"
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
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
                f"Client error during HTTP request for url: {full_url}. Exception: {e}"
            ) from e
        except TimeoutError as e:
            raise AmbeoConnectionError(
                f"Timeout error while fetching data from url: {full_url}"
            ) from e
        except Exception as e:
            raise AmbeoConnectionError(
                f"Unexpected exception with url: {full_url}. Exception: {e}"
            ) from e

    def extract_data(self, json_data, key_path):
        """Extract data from JSON using a specified key path."""
        try:
            for key in key_path:
                json_data = json_data[key]
            return json_data
        except KeyError as e:
            _LOGGER.error("Missing key '%s' in JSON data", e)
            return None
        except Exception as e:
            _LOGGER.error("Exception extracting data: %s", e)
            return None

    def generate_nocache(self):
        """Generate a nocache parameter to prevent caching."""
        return int(time.time() * 1000)

    async def execute_request(
        self, function, path, role=None, value=None, from_idx=None, to_idx=None
    ):
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
        value = await self.execute_request("getData", path, role)
        if value is not None:
            return self.extract_data(value, ["value", data_type])
        return None

    async def set_value(self, path, data_type, value):
        """Set a value of a specified type at a specified path."""
        await self.execute_request(
            "setData", path, "value", json.dumps({"type": data_type, data_type: value})
        )

    def has_capability(self, capa):
        """Check if the device has a specific capability."""
        return capa in self.capabilities

    def support_debounce_mode(self):
        """Check if debounce mode is supported."""
        return False

    def get_volume_step(self):
        """Get the volume step size."""
        return 0.01

    # Subwoofer range (defaults for Popcorn).
    def get_subwoofer_min_value(self):
        """Get the subwoofer minimum value."""
        return -10

    def get_subwoofer_max_value(self):
        """Get the subwoofer maximum value."""
        return 10

    # Name.
    async def get_name(self):
        """Get the device name."""
        return await self.get_value("systemmanager:/deviceName", "string_")

    # Serial.
    async def get_serial(self):
        """Get the device serial number."""
        return await self.get_value("settings:/system/serialNumber", "string_")

    # Version.
    async def get_version(self):
        """Get the firmware version."""
        return await self.get_value(
            "ui:settings/firmwareUpdate/currentVersion", "string_"
        )

    # Model.
    async def get_model(self):
        """Get the device model."""
        return await self.get_value("settings:/system/productName", "string_")

    # Volume.
    async def get_volume(self):
        """Get the current volume."""
        return await self.get_value("player:volume", "i32_")

    async def set_volume(self, volume):
        """Set the volume."""
        await self.set_value("player:volume", "i32_", volume)

    # Mute.
    async def is_mute(self):
        """Check if the device is muted."""
        return await self.get_value("settings:/mediaPlayer/mute", "bool_")

    async def set_mute(self, mute):
        """Set the mute state."""
        await self.set_value("settings:/mediaPlayer/mute", "bool_", mute)

    # Night mode.
    async def get_night_mode(self):
        """Get the night mode state."""

    async def set_night_mode(self, night_mode):
        """Set the night mode state."""

    # Voice enhancement.
    async def get_voice_enhancement(self):
        """Get the voice enhancement state."""

    async def set_voice_enhancement(self, voice_enhancement_mode):
        """Set the voice enhancement mode."""

    # Subwoofer.
    async def has_subwoofer(self) -> bool:
        """Check if a subwoofer is connected."""
        raise NotImplementedError

    async def get_subwoofer_status(self):
        """Get the subwoofer enabled status."""

    async def set_subwoofer_status(self, status):
        """Set the subwoofer enabled status."""

    async def get_subwoofer_volume(self):
        """Get the subwoofer volume."""

    async def set_subwoofer_volume(self, volume):
        """Set the subwoofer volume."""

    # Ambeo mode.
    async def get_ambeo_mode(self):
        """Get the Ambeo mode state."""

    async def set_ambeo_mode(self, ambeo_mode):
        """Set the Ambeo mode state."""

    # Sound feedback.
    async def get_sound_feedback(self):
        """Get the sound feedback state."""

    async def set_sound_feedback(self, state):
        """Set the sound feedback state."""

    # Ambeo logo.
    async def get_logo_state(self):
        """Get the Ambeo logo state."""

    async def change_logo_state(self, value):
        """Change the Ambeo logo state."""

    async def set_logo_brightness(self, brightness):
        """Set the Ambeo logo brightness."""

    async def get_logo_brightness(self):
        """Get the Ambeo logo brightness."""

    def get_logo_brightness_range(self):
        """Get the Ambeo logo brightness range."""
        return BRIGHTNESS_RANGE_DEFAULT

    # LED bar.
    async def get_led_bar_brightness(self):
        """Get the LED bar brightness."""

    async def set_led_bar_brightness(self, brightness):
        """Set the LED bar brightness."""

    def get_led_bar_brightness_range(self):
        """Get the LED bar brightness range."""
        return BRIGHTNESS_RANGE_DEFAULT

    # Ambeo display.
    async def set_display_brightness(self, brightness):
        """Set the display brightness."""

    async def get_display_brightness(self):
        """Get the display brightness."""

    def get_display_brightness_range(self):
        """Get the display brightness range."""
        return BRIGHTNESS_RANGE_DEFAULT

    # Codec LED.
    async def get_codec_led_brightness(self):
        """Get the codec LED brightness."""

    async def set_codec_led_brightness(self, brightness):
        """Set the codec LED brightness."""

    def get_codec_led_brightness_range(self):
        """Get the codec LED brightness range."""
        return BRIGHTNESS_RANGE_DEFAULT

    # Sources.
    async def get_current_source(self):
        """Get the current audio source."""

    async def get_all_sources(self):
        """Get all available audio sources."""

    async def set_source(self, source_id):
        """Set the audio source."""

    # Presets.
    async def get_current_preset(self):
        """Get the current audio preset."""

    async def set_preset(self, preset):
        """Set the audio preset."""

    async def get_all_presets(self):
        """Get all available audio presets."""

    async def play(self):
        """Send play command."""
        await self.execute_request(
            "setData",
            "popcorn:multiPurposeButtonActivate",
            "activate",
            json.dumps({"type": "bool_", "bool_": True}),
        )

    async def pause(self):
        """Send pause command."""
        await self.execute_request(
            "setData",
            "popcorn:multiPurposeButtonActivate",
            "activate",
            json.dumps({"type": "bool_", "bool_": True}),
        )

    async def next(self):
        """Skip to the next track."""
        await self.execute_request(
            "setData",
            "player:player/control",
            "activate",
            json.dumps({"control": "next"}),
        )

    async def previous(self):
        """Go back to the previous track."""
        await self.execute_request(
            "setData",
            "player:player/control",
            "activate",
            json.dumps({"control": "previous"}),
        )

    async def get_play_time(self):
        """Get the current play time in milliseconds."""
        return await self.get_value("player:player/data/playTime", "i64_")

    async def player_data(self):
        """Get the current player data."""
        data = await self.execute_request("getData", "player:player/data/value", "@all")
        if data:
            return self.extract_data(data, ["value", "playLogicData"])
        return None

    # Power off (standby).
    async def stand_by(self):
        """Put the device into standby mode."""

    # Power on (wake).
    async def wake(self):
        """Wake the device from standby."""

    # Reboot.
    async def reboot(self):
        """Reboot the device."""
        await self.execute_request(
            "setData",
            "ui:/settings/system/restart",
            "activate",
            json.dumps({"type": "bool_", "bool_": True}),
        )

    async def get_state(self):
        """Get the current device state."""
        power_target = await self.get_value("powermanager:target", "powerTarget")
        if power_target:
            return power_target["target"]
        return None

    # Bluetooth pairing.
    async def get_bluetooth_pairing_state(self):
        """Get the Bluetooth pairing state."""

    async def set_bluetooth_pairing_state(self, state):
        """Set the Bluetooth pairing state."""

    # Voice enhancement level.
    async def get_voice_enhancement_level(self):
        """Get the voice enhancement level."""

    async def set_voice_enhancement_level(self, level):
        """Set the voice enhancement level."""

    # Speaker levels.
    async def get_center_speaker_level(self):
        """Get the center speaker level."""

    async def set_center_speaker_level(self, level):
        """Set the center speaker level."""

    async def get_side_firing_level(self):
        """Get the side firing level."""

    async def set_side_firing_level(self, level):
        """Set the side firing level."""

    async def get_up_firing_level(self):
        """Get the up firing level."""

    async def set_up_firing_level(self, level):
        """Set the up firing level."""

    # Eco mode.
    async def get_eco_mode(self):
        """Get the eco mode state."""

    async def set_eco_mode(self, mode):
        """Set the eco mode state."""

    # Expert settings.
    async def reset_expert_settings(self):
        """Reset expert settings."""
