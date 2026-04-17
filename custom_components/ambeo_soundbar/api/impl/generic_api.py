"""Generic API base class for Ambeo Soundbar integration."""

import json
import logging
import time
from typing import Any
from urllib.parse import quote

import aiohttp
import yarl

from ..const import BRIGHTNESS_RANGE_DEFAULT, PathSub
from ..exceptions import AmbeoConnectionError

_LOGGER = logging.getLogger(__name__)


def _extract_from_subs(
    subs: list[PathSub], path: str, item_value: dict
) -> dict[str, Any]:
    """Return coordinator updates for the first PathSub whose path matches."""
    for sub in subs:
        if sub.path == path:
            value = item_value.get(sub.type_key)
            if sub.sub_key and isinstance(value, dict):
                value = value.get(sub.sub_key)
            return {sub.data_key: value} if value is not None else {}
    return {}


class AmbeoApi:
    """Base API class for Ambeo Soundbar devices."""

    capabilities: list[str] = []

    def __init__(
        self, ip: str, port: int, timeout: int, session: aiohttp.ClientSession
    ):
        """Initialize the API with the given IP, port, session, and Home Assistant instance."""
        self.session = session
        self.port = port
        self.set_endpoint(ip)
        self.timeout = timeout

    def set_endpoint(self, host: str) -> None:
        """Set the API endpoint host."""
        self.ip = host
        self.endpoint = f"http://{host}:{self.port}/api"

    async def fetch_data(
        self, url: str, http_timeout: int | None = None, encoded: bool = False
    ):
        """Fetch data from a given URL.

        Args:
            url: Relative URL path (appended to self.endpoint).
            http_timeout: Override the default HTTP timeout (seconds).
            encoded: If True, treat the URL as already percent-encoded and pass
                it to aiohttp as a yarl.URL(…, encoded=True) to prevent
                double-encoding of special characters such as { and }.

        """
        full_url = f"{self.endpoint}/{url}"
        try:
            total = http_timeout if http_timeout is not None else self.timeout
            timeout = aiohttp.ClientTimeout(total=total)
            _LOGGER.debug("Executing URL fetch: %s", full_url)
            request_url: str | yarl.URL = (
                yarl.URL(full_url, encoded=True) if encoded else full_url
            )
            async with self.session.get(request_url, timeout=timeout) as response:
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

    async def create_event_queue(self, paths: list[str]) -> str | None:
        """Create an event subscription queue and return the queue ID."""
        subscribe_json = json.dumps(
            [{"path": p, "type": "itemWithValue"} for p in paths]
        )
        subscribe_encoded = quote(subscribe_json, safe="")
        url = f"event/modifyQueue?subscribe={subscribe_encoded}&_nocache={self.generate_nocache()}"
        result = await self.fetch_data(url, encoded=True)
        if isinstance(result, str):
            return result
        return None

    async def poll_event_queue(
        self, queue_id: str, timeout_ms: int = 30000
    ) -> list | None:
        """Poll an event queue for changes. Blocks until events arrive or timeout.

        Returns a (possibly empty) list of events, or None on any error or
        expiry — the caller should recreate the queue in that case.
        """
        queue_id_encoded = quote(queue_id, safe="")
        http_timeout = timeout_ms // 1000 + 10
        url = f"event/pollQueue?queueId={queue_id_encoded}&timeout={timeout_ms}&_nocache={self.generate_nocache()}"
        try:
            result = await self.fetch_data(url, http_timeout=http_timeout, encoded=True)
        except AmbeoConnectionError as e:
            # HTTP timeout = poll simply expired, queue is still valid on the device.
            if isinstance(e.__cause__, TimeoutError):
                return []
            # Any other error (connection refused, etc.) signals the queue is lost.
            return None
        if isinstance(result, list):
            return result
        return None

    # Common paths shared by all device models.
    # Named _BASE_SUBSCRIPTIONS to avoid shadowing by subclass _SUBSCRIPTIONS.
    _BASE_SUBSCRIPTIONS: list[PathSub] = [
        PathSub("player:player/data/value", "player_data", "playLogicData"),
        PathSub("player:player/data/playTime", "play_time", "i64_"),
        PathSub("powermanager:target", "state", "powerTarget", sub_key="target"),
    ]

    def get_subscribed_paths(self) -> list[str]:
        """Return the list of paths to subscribe to for event-driven updates."""
        return [s.path for s in self._BASE_SUBSCRIPTIONS]

    def process_event(self, path: str, item_value: dict) -> dict[str, Any]:
        """Process an event and return coordinator data key-value updates."""
        return _extract_from_subs(self._BASE_SUBSCRIPTIONS, path, item_value)

    def extract_data(self, json_data: Any, key_path: list[str]) -> Any:
        """Extract data from JSON using a specified key path."""
        try:
            for key in key_path:
                json_data = json_data[key]
            return json_data
        except KeyError as e:
            _LOGGER.error("Missing key '%s' in JSON data", e)
            return None
        except (TypeError, IndexError) as e:
            _LOGGER.error("Exception extracting data: %s", e)
            return None

    def generate_nocache(self) -> int:
        """Generate a nocache parameter to prevent caching."""
        return int(time.time() * 1000)

    async def execute_request(
        self,
        function: str,
        path: str,
        role: str | None = None,
        value: str | None = None,
        from_idx: int | None = None,
        to_idx: int | None = None,
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

    async def get_value(self, path: str, data_type: str, role: str = "@all"):
        """Get a value of a specified type from a specified path."""
        value = await self.execute_request("getData", path, role)
        if value is not None:
            return self.extract_data(value, ["value", data_type])
        return None

    async def set_value(self, path: str, data_type: str, value: Any) -> None:
        """Set a value of a specified type at a specified path."""
        await self.execute_request(
            "setData", path, "value", json.dumps({"type": data_type, data_type: value})
        )

    def has_capability(self, capa: str) -> bool:
        """Check if the device has a specific capability."""
        return capa in self.capabilities

    def support_debounce_mode(self) -> bool:
        """Check if debounce mode is supported."""
        return False

    def get_volume_step(self) -> float:
        """Get the volume step size."""
        return 0.01

    # Subwoofer range (defaults for Popcorn).
    def get_subwoofer_min_value(self) -> int:
        """Get the subwoofer minimum value."""
        return -10

    def get_subwoofer_max_value(self) -> int:
        """Get the subwoofer maximum value."""
        return 10

    # Name.
    async def get_name(self) -> str | None:
        """Get the device name."""
        return await self.get_value("systemmanager:/deviceName", "string_")

    # Serial.
    async def get_serial(self) -> str | None:
        """Get the device serial number."""
        return await self.get_value("settings:/system/serialNumber", "string_")

    # Version.
    async def get_version(self) -> str | None:
        """Get the firmware version."""
        return await self.get_value(
            "ui:settings/firmwareUpdate/currentVersion", "string_"
        )

    # Model.
    async def get_model(self) -> str | None:
        """Get the device model."""
        return await self.get_value("settings:/system/productName", "string_")

    # Volume.
    async def get_volume(self) -> int | None:
        """Get the current volume."""
        return await self.get_value("player:volume", "i32_")

    async def set_volume(self, volume: float) -> None:
        """Set the volume."""
        await self.set_value("player:volume", "i32_", volume)

    def get_volume_max(self) -> int:
        """Get the maximum native volume value."""
        return 100

    # Mute.
    async def is_mute(self) -> bool | None:
        """Check if the device is muted."""
        return await self.get_value("settings:/mediaPlayer/mute", "bool_")

    async def set_mute(self, mute: bool) -> None:
        """Set the mute state."""
        await self.set_value("settings:/mediaPlayer/mute", "bool_", mute)

    # Night mode.
    async def get_night_mode(self) -> bool | None:
        """Get the night mode state."""
        raise NotImplementedError

    async def set_night_mode(self, night_mode: bool) -> None:
        """Set the night mode state."""
        raise NotImplementedError

    # Voice enhancement.
    async def get_voice_enhancement(self) -> bool | None:
        """Get the voice enhancement state."""
        raise NotImplementedError

    async def set_voice_enhancement(self, voice_enhancement_mode: bool) -> None:
        """Set the voice enhancement mode."""
        raise NotImplementedError

    # Subwoofer.
    async def has_subwoofer(self) -> bool:
        """Check if a subwoofer is connected."""
        raise NotImplementedError

    async def get_subwoofer_status(self) -> bool | None:
        """Get the subwoofer enabled status."""
        raise NotImplementedError

    async def set_subwoofer_status(self, status: bool) -> None:
        """Set the subwoofer enabled status."""
        raise NotImplementedError

    async def get_subwoofer_volume(self) -> float | None:
        """Get the subwoofer volume."""
        raise NotImplementedError

    async def set_subwoofer_volume(self, volume: float) -> None:
        """Set the subwoofer volume."""
        raise NotImplementedError

    # Ambeo mode.
    async def get_ambeo_mode(self) -> bool | None:
        """Get the Ambeo mode state."""
        raise NotImplementedError

    async def set_ambeo_mode(self, ambeo_mode: bool) -> None:
        """Set the Ambeo mode state."""
        raise NotImplementedError

    async def get_ambeo_mode_level(self) -> int | None:
        """Get the Ambeo mode level (1=Light, 2=Regular, 3=Boost)."""
        raise NotImplementedError

    async def set_ambeo_mode_level(self, level: int) -> None:
        """Set the Ambeo mode level (1=Light, 2=Regular, 3=Boost)."""
        raise NotImplementedError

    # Sound feedback.
    async def get_sound_feedback(self) -> bool | None:
        """Get the sound feedback state."""
        raise NotImplementedError

    async def set_sound_feedback(self, state: bool) -> None:
        """Set the sound feedback state."""
        raise NotImplementedError

    # Ambeo logo.
    async def get_logo_state(self) -> bool | None:
        """Get the Ambeo logo state."""
        raise NotImplementedError

    async def change_logo_state(self, value: bool) -> None:
        """Change the Ambeo logo state."""
        raise NotImplementedError

    async def set_logo_brightness(self, brightness: int) -> None:
        """Set the Ambeo logo brightness."""
        raise NotImplementedError

    async def get_logo_brightness(self) -> int | None:
        """Get the Ambeo logo brightness."""
        raise NotImplementedError

    def get_logo_brightness_range(self) -> tuple[int, int]:
        """Get the Ambeo logo brightness range."""
        return BRIGHTNESS_RANGE_DEFAULT

    # LED bar.
    async def get_led_bar_brightness(self) -> int | None:
        """Get the LED bar brightness."""
        raise NotImplementedError

    async def set_led_bar_brightness(self, brightness: int) -> None:
        """Set the LED bar brightness."""
        raise NotImplementedError

    def get_led_bar_brightness_range(self) -> tuple[int, int]:
        """Get the LED bar brightness range."""
        return BRIGHTNESS_RANGE_DEFAULT

    # Ambeo display.
    async def set_display_brightness(self, brightness: int) -> None:
        """Set the display brightness."""
        raise NotImplementedError

    async def get_display_brightness(self) -> int | None:
        """Get the display brightness."""
        raise NotImplementedError

    def get_display_brightness_range(self) -> tuple[int, int]:
        """Get the display brightness range."""
        return BRIGHTNESS_RANGE_DEFAULT

    # Codec LED.
    async def get_codec_led_brightness(self) -> int | None:
        """Get the codec LED brightness."""
        raise NotImplementedError

    async def set_codec_led_brightness(self, brightness: int) -> None:
        """Set the codec LED brightness."""
        raise NotImplementedError

    def get_codec_led_brightness_range(self) -> tuple[int, int]:
        """Get the codec LED brightness range."""
        return BRIGHTNESS_RANGE_DEFAULT

    # Sources.
    async def get_current_source(self):
        """Get the current audio source."""
        raise NotImplementedError

    async def get_all_sources(self) -> list[dict] | None:
        """Get all available audio sources."""
        raise NotImplementedError

    async def set_source(self, source_id) -> None:
        """Set the audio source."""
        raise NotImplementedError

    # Presets.
    async def get_current_preset(self):
        """Get the current audio preset."""
        raise NotImplementedError

    async def set_preset(self, preset) -> None:
        """Set the audio preset."""
        raise NotImplementedError

    async def get_all_presets(self) -> list[dict] | None:
        """Get all available audio presets."""
        raise NotImplementedError

    async def play(self) -> None:
        """Send play command."""
        await self.execute_request(
            "setData",
            "popcorn:multiPurposeButtonActivate",
            "activate",
            json.dumps({"type": "bool_", "bool_": True}),
        )

    async def pause(self) -> None:
        """Send pause command."""
        await self.execute_request(
            "setData",
            "popcorn:multiPurposeButtonActivate",
            "activate",
            json.dumps({"type": "bool_", "bool_": True}),
        )

    async def next(self) -> None:
        """Skip to the next track."""
        await self.execute_request(
            "setData",
            "player:player/control",
            "activate",
            json.dumps({"control": "next"}),
        )

    async def previous(self) -> None:
        """Go back to the previous track."""
        await self.execute_request(
            "setData",
            "player:player/control",
            "activate",
            json.dumps({"control": "previous"}),
        )

    async def get_play_time(self) -> int | None:
        """Get the current play time in milliseconds."""
        return await self.get_value("player:player/data/playTime", "i64_")

    async def player_data(self) -> dict | None:
        """Get the current player data."""
        data = await self.execute_request("getData", "player:player/data/value", "@all")
        if data:
            return self.extract_data(data, ["value", "playLogicData"])
        return None

    # Power off (standby).
    async def stand_by(self) -> None:
        """Put the device into standby mode."""
        raise NotImplementedError

    # Power on (wake).
    async def wake(self) -> None:
        """Wake the device from standby."""
        raise NotImplementedError

    # Reboot.
    async def reboot(self) -> None:
        """Reboot the device."""
        await self.execute_request(
            "setData",
            "ui:/settings/system/restart",
            "activate",
            json.dumps({"type": "bool_", "bool_": True}),
        )

    async def get_state(self) -> str | None:
        """Get the current device state."""
        power_target = await self.get_value("powermanager:target", "powerTarget")
        if power_target:
            return power_target["target"]
        return None

    # Bluetooth pairing.
    async def get_bluetooth_pairing_state(self) -> bool | None:
        """Get the Bluetooth pairing state."""
        raise NotImplementedError

    async def set_bluetooth_pairing_state(self, state: bool) -> None:
        """Set the Bluetooth pairing state."""
        raise NotImplementedError

    # Voice enhancement level.
    async def get_voice_enhancement_level(self) -> int | None:
        """Get the voice enhancement level."""
        raise NotImplementedError

    async def set_voice_enhancement_level(self, level: int) -> None:
        """Set the voice enhancement level."""
        raise NotImplementedError

    # Speaker levels.
    async def get_center_speaker_level(self) -> int | None:
        """Get the center speaker level."""
        raise NotImplementedError

    async def set_center_speaker_level(self, level: int) -> None:
        """Set the center speaker level."""
        raise NotImplementedError

    async def get_side_firing_level(self) -> int | None:
        """Get the side firing level."""
        raise NotImplementedError

    async def set_side_firing_level(self, level: int) -> None:
        """Set the side firing level."""
        raise NotImplementedError

    async def get_up_firing_level(self) -> int | None:
        """Get the up firing level."""
        raise NotImplementedError

    async def set_up_firing_level(self, level: int) -> None:
        """Set the up firing level."""
        raise NotImplementedError

    # Eco mode.
    async def get_eco_mode(self) -> bool | None:
        """Get the eco mode state."""
        raise NotImplementedError

    async def set_eco_mode(self, mode: bool) -> None:
        """Set the eco mode state."""
        raise NotImplementedError

    # Expert settings.
    async def reset_expert_settings(self) -> None:
        """Reset expert settings."""
        raise NotImplementedError
