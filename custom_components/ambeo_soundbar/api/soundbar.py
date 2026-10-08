"""Base class for Ambeo Soundbar devices."""

import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable, Mapping
from typing import Any, ClassVar

import aiohttp

from .const import (
    BRIGHTNESS_RANGE_DEFAULT,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    OPTIONAL_FEATURES,
    Capability,
    PathSub,
    StateKey,
)
from .exceptions import (
    AmbeoError,
    AmbeoResponseError,
    AmbeoUnsupportedModelError,
)
from .models import DeviceInfo, PlayerStatus, Preset, Source
from .transport import AmbeoTransport

_LOGGER = logging.getLogger(__name__)


_MODEL_PATH = "settings:/system/productName"
_NAME_PATH = "systemmanager:/deviceName"
_SERIAL_PATH = "settings:/system/serialNumber"
_VERSION_PATH = "ui:settings/firmwareUpdate/currentVersion"

# Populated by AmbeoSoundbar.__init_subclass__ from each subclass's `models`.
_MODEL_CLASSES: dict[str, type["AmbeoSoundbar"]] = {}


def _extract_from_subs(
    subs: tuple[PathSub, ...], path: str, item_value: dict
) -> dict[StateKey, Any]:
    """Return state updates for the first PathSub whose path matches."""
    for sub in subs:
        if sub.path == path:
            value = item_value.get(sub.type_key)
            if sub.sub_key and isinstance(value, dict):
                value = value.get(sub.sub_key)
            return {sub.data_key: value} if value is not None else {}
    return {}


async def _none_on_response_error[T](coro: Awaitable[T]) -> T | None:
    """Await coro, returning None if the device answered with an error."""
    try:
        return await coro
    except AmbeoResponseError as e:
        _LOGGER.debug("Ignoring response error: %s", e)
        return None


class AmbeoSoundbar:
    """Base class for Ambeo Soundbar devices.

    Use `await AmbeoSoundbar.connect(host, session)` to get the implementation
    matching the device model.
    """

    # Device models handled by the subclass.
    models: ClassVar[tuple[str, ...]] = ()
    capabilities: ClassVar[frozenset[Capability]] = frozenset()

    # Common paths shared by all device models.
    _BASE_SUBSCRIPTIONS: ClassVar[tuple[PathSub, ...]] = (
        PathSub("player:player/data/value", StateKey.PLAYER_DATA, "playLogicData"),
        PathSub("player:player/data/playTime", StateKey.PLAY_TIME, "i64_"),
        PathSub("powermanager:target", StateKey.STATE, "powerTarget", sub_key="target"),
    )
    # Model specific paths, filtered by capability.
    _SUBSCRIPTIONS: ClassVar[tuple[PathSub, ...]] = ()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Register the subclass for its device models."""
        super().__init_subclass__(**kwargs)
        for model in cls.models:
            _MODEL_CLASSES[model] = cls

    def __init__(
        self,
        transport: AmbeoTransport,
        info: DeviceInfo,
        sources: list[Source] | None = None,
        presets: list[Preset] | None = None,
    ) -> None:
        """Initialize the soundbar."""
        self._transport = transport
        self.info = info
        self.sources: list[Source] = sources or []
        self.presets: list[Preset] = presets or []

    @classmethod
    async def connect(
        cls,
        host: str,
        session: aiohttp.ClientSession,
        *,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> "AmbeoSoundbar":
        """Connect to a soundbar and return the implementation for its model.

        Loads the device info, sources and presets. When called on a subclass,
        raises AmbeoUnsupportedModelError if the device is another model.
        """
        transport = AmbeoTransport(host, session, port, timeout)
        model = await transport.get_value(_MODEL_PATH, "string_")
        impl = _MODEL_CLASSES.get(model)
        if impl is None or not issubclass(impl, cls):
            raise AmbeoUnsupportedModelError(model)
        _LOGGER.debug("Setting up the API for %s", model)

        name, serial, version = await asyncio.gather(
            _none_on_response_error(transport.get_value(_NAME_PATH, "string_")),
            _none_on_response_error(transport.get_value(_SERIAL_PATH, "string_")),
            _none_on_response_error(transport.get_value(_VERSION_PATH, "string_")),
        )
        soundbar = impl(transport, DeviceInfo(model, name, serial, version))
        soundbar.sources = await _none_on_response_error(soundbar.fetch_sources()) or []
        soundbar.presets = await _none_on_response_error(soundbar.fetch_presets()) or []
        return soundbar

    @property
    def host(self) -> str:
        """Return the device host."""
        return self._transport.host

    @property
    def port(self) -> int:
        """Return the device port."""
        return self._transport.port

    def has_capability(self, capability: Capability | str) -> bool:
        """Check if the device has a specific capability."""
        return capability in self.capabilities

    # State.
    async def fetch_state(self, max_concurrency: int = 3) -> dict[StateKey, Any]:
        """Fetch the full device state.

        Core values are always present (None when the device does not answer
        them). Optional values are only present when available.
        Raises AmbeoConnectionError when the device cannot be reached.
        """
        core_keys = (
            StateKey.VOLUME,
            StateKey.MUTED,
            StateKey.STATE,
            StateKey.CURRENT_SOURCE,
            StateKey.CURRENT_PRESET,
            StateKey.PLAYER_DATA,
        )
        core_values = await asyncio.gather(
            _none_on_response_error(self.get_volume()),
            _none_on_response_error(self.is_mute()),
            _none_on_response_error(self.get_state()),
            _none_on_response_error(self.get_current_source()),
            _none_on_response_error(self.get_current_preset()),
            _none_on_response_error(self.player_data()),
        )
        state: dict[StateKey, Any] = dict(zip(core_keys, core_values, strict=True))

        semaphore = asyncio.Semaphore(max_concurrency)

        async def fetch_optional(api_method: str) -> Any:
            try:
                async with semaphore:
                    return await getattr(self, api_method)()
            except (AmbeoError, NotImplementedError) as e:
                _LOGGER.debug("%s not available: %s", api_method, e)
                return None

        features = [
            f
            for f in OPTIONAL_FEATURES
            if f.capability is None or self.has_capability(f.capability)
        ]
        values = await asyncio.gather(*(fetch_optional(f.api_method) for f in features))
        for feature, value in zip(features, values, strict=True):
            if value is not None:
                state[feature.data_key] = value
        return state

    def player_status(self, state: Mapping[str, Any]) -> PlayerStatus:
        """Return the effective playback status for a state snapshot."""
        power_map = {
            "playing": PlayerStatus.PLAYING,
            "paused": PlayerStatus.PAUSED,
            "stopped": PlayerStatus.IDLE,
            "online": PlayerStatus.ON,
            "networkStandby": PlayerStatus.STANDBY
            if self.has_capability(Capability.STANDBY)
            else PlayerStatus.IDLE,
        }
        power_status = power_map.get(state.get(StateKey.STATE) or "", PlayerStatus.ON)
        if power_status != PlayerStatus.ON:
            return power_status

        player_data = state.get(StateKey.PLAYER_DATA) or {}
        if player_data.get("state") == "paused":
            return PlayerStatus.PAUSED

        decoder_status = state.get(StateKey.DECODER_STATUS)
        if isinstance(decoder_status, dict):
            is_playing = (
                decoder_status.get("decoder_status", decoder_status.get("channels", 0))
                > 0
            )
            return PlayerStatus.PLAYING if is_playing else PlayerStatus.IDLE

        player_state = player_data.get("state")
        if player_state:
            return power_map.get(player_state, PlayerStatus.IDLE)
        return power_status

    # Events.
    def subscribed_paths(self) -> list[str]:
        """Return the paths to subscribe to, filtered by device capabilities."""
        paths = [s.path for s in self._BASE_SUBSCRIPTIONS]
        paths.extend(
            s.path
            for s in self._SUBSCRIPTIONS
            if s.capability is None or self.has_capability(s.capability)
        )
        return paths

    def process_event(self, path: str, item_value: dict) -> dict[StateKey, Any]:
        """Map an event path + itemValue to state updates."""
        return _extract_from_subs(
            self._BASE_SUBSCRIPTIONS, path, item_value
        ) or _extract_from_subs(self._SUBSCRIPTIONS, path, item_value)

    async def listen(
        self, *, poll_timeout_ms: int = 30000, retry_delay: float = 30
    ) -> AsyncIterator[dict[StateKey, Any]]:
        """Yield state updates pushed by the device, forever.

        The event queue is recreated when lost; queue creation failures are
        retried every `retry_delay` seconds.
        """
        paths = self.subscribed_paths()
        _LOGGER.debug("Starting event listener for %d paths", len(paths))
        while True:
            try:
                queue_id = await self._transport.create_event_queue(paths)
            except AmbeoError as e:
                _LOGGER.debug("Failed to create event queue: %s", e)
                queue_id = None
            if not queue_id:
                _LOGGER.debug("No event queue, retrying in %ss", retry_delay)
                await asyncio.sleep(retry_delay)
                continue

            _LOGGER.debug("Event queue created: %s", queue_id)
            while (
                events := await self._transport.poll_event_queue(
                    queue_id, poll_timeout_ms
                )
            ) is not None:
                updates: dict[StateKey, Any] = {}
                for event in events:
                    if not isinstance(event, dict) or event.get("itemType") != "update":
                        continue
                    path = event.get("path")
                    item_value = event.get("itemValue")
                    if path and isinstance(item_value, dict):
                        updates.update(self.process_event(path, item_value))
                if updates:
                    yield updates
            _LOGGER.debug("Poll error, recreating event queue")

    # Device info.
    async def get_name(self) -> str | None:
        """Get the device name."""
        return await self._transport.get_value(_NAME_PATH, "string_")

    # Settings ranges.
    def get_volume_step(self) -> float:
        """Get the volume step size."""
        return 0.01

    def get_volume_max(self) -> int:
        """Get the maximum native volume value."""
        return 100

    def get_subwoofer_min_value(self) -> int:
        """Get the subwoofer minimum value."""
        return -10

    def get_subwoofer_max_value(self) -> int:
        """Get the subwoofer maximum value."""
        return 10

    def get_logo_brightness_range(self) -> tuple[int, int]:
        """Get the Ambeo logo brightness range."""
        return BRIGHTNESS_RANGE_DEFAULT

    def get_led_bar_brightness_range(self) -> tuple[int, int]:
        """Get the LED bar brightness range."""
        return BRIGHTNESS_RANGE_DEFAULT

    def get_display_brightness_range(self) -> tuple[int, int]:
        """Get the display brightness range."""
        return BRIGHTNESS_RANGE_DEFAULT

    def get_codec_led_brightness_range(self) -> tuple[int, int]:
        """Get the codec LED brightness range."""
        return BRIGHTNESS_RANGE_DEFAULT

    # Volume.
    async def get_volume(self) -> int | None:
        """Get the current volume."""
        return await self._transport.get_value("player:volume", "i32_")

    async def set_volume(self, volume: float) -> None:
        """Set the volume."""
        await self._transport.set_value("player:volume", "i32_", volume)

    # Mute.
    async def is_mute(self) -> bool | None:
        """Check if the device is muted."""
        return await self._transport.get_value("settings:/mediaPlayer/mute", "bool_")

    async def set_mute(self, mute: bool) -> None:
        """Set the mute state."""
        await self._transport.set_value("settings:/mediaPlayer/mute", "bool_", mute)

    # Power.
    async def get_state(self) -> str | None:
        """Get the current power state (online, networkStandby, …)."""
        power_target = await self._transport.get_value(
            "powermanager:target", "powerTarget"
        )
        if isinstance(power_target, dict):
            return power_target.get("target")
        return None

    async def stand_by(self) -> None:
        """Put the device into standby mode."""
        raise NotImplementedError

    async def wake(self) -> None:
        """Wake the device from standby."""
        raise NotImplementedError

    async def reboot(self) -> None:
        """Reboot the device."""
        await self._transport.activate(
            "ui:/settings/system/restart", {"type": "bool_", "bool_": True}
        )

    # Playback.
    async def _player_control(self, control: str) -> None:
        """Send a player control command."""
        await self._transport.activate("player:player/control", {"control": control})

    async def play(self) -> None:
        """Send play command."""
        await self._player_control("play")

    async def pause(self) -> None:
        """Send pause command."""
        await self._player_control("pause")

    async def next(self) -> None:
        """Skip to the next track."""
        await self._player_control("next")

    async def previous(self) -> None:
        """Go back to the previous track."""
        await self._player_control("previous")

    async def get_play_time(self) -> int | None:
        """Get the current play time in milliseconds."""
        return await self._transport.get_value("player:player/data/playTime", "i64_")

    async def player_data(self) -> dict | None:
        """Get the current player data."""
        return await self._transport.get_value(
            "player:player/data/value", "playLogicData"
        )

    # Sources.
    async def fetch_sources(self) -> list[Source]:
        """Fetch all available audio sources."""
        raise NotImplementedError

    async def get_current_source(self) -> Any:
        """Get the current audio source ID."""
        raise NotImplementedError

    async def set_source(self, source_id: Any) -> None:
        """Set the audio source."""
        raise NotImplementedError

    # Presets.
    async def fetch_presets(self) -> list[Preset]:
        """Fetch all available audio presets."""
        raise NotImplementedError

    async def get_current_preset(self) -> Any:
        """Get the current audio preset ID."""
        raise NotImplementedError

    async def set_preset(self, preset: Any) -> None:
        """Set the audio preset."""
        raise NotImplementedError

    # Night mode.
    async def get_night_mode(self) -> bool | None:
        """Get the night mode state."""
        raise NotImplementedError

    async def set_night_mode(self, night_mode: bool) -> None:
        """Set the night mode state."""
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

    # Voice enhancement.
    async def get_voice_enhancement(self) -> bool | None:
        """Get the voice enhancement state."""
        raise NotImplementedError

    async def set_voice_enhancement(self, voice_enhancement_mode: bool) -> None:
        """Set the voice enhancement mode."""
        raise NotImplementedError

    async def get_voice_enhancement_level(self) -> int | None:
        """Get the voice enhancement level."""
        raise NotImplementedError

    async def set_voice_enhancement_level(self, level: int) -> None:
        """Set the voice enhancement level."""
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

    # Ambeo logo.
    async def get_logo_state(self) -> bool | None:
        """Get the Ambeo logo state."""
        raise NotImplementedError

    async def change_logo_state(self, value: bool) -> None:
        """Change the Ambeo logo state."""
        raise NotImplementedError

    async def get_logo_brightness(self) -> int | None:
        """Get the Ambeo logo brightness."""
        raise NotImplementedError

    async def set_logo_brightness(self, brightness: int) -> None:
        """Set the Ambeo logo brightness."""
        raise NotImplementedError

    # LED bar.
    async def get_led_bar_brightness(self) -> int | None:
        """Get the LED bar brightness."""
        raise NotImplementedError

    async def set_led_bar_brightness(self, brightness: int) -> None:
        """Set the LED bar brightness."""
        raise NotImplementedError

    # Ambeo display.
    async def get_display_brightness(self) -> int | None:
        """Get the display brightness."""
        raise NotImplementedError

    async def set_display_brightness(self, brightness: int) -> None:
        """Set the display brightness."""
        raise NotImplementedError

    # Codec LED.
    async def get_codec_led_brightness(self) -> int | None:
        """Get the codec LED brightness."""
        raise NotImplementedError

    async def set_codec_led_brightness(self, brightness: int) -> None:
        """Set the codec LED brightness."""
        raise NotImplementedError

    # Bluetooth pairing.
    async def get_bluetooth_pairing_state(self) -> bool | None:
        """Get the Bluetooth pairing state."""
        raise NotImplementedError

    async def set_bluetooth_pairing_state(self, state: bool) -> None:
        """Set the Bluetooth pairing state."""
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

    async def get_center_volume(self) -> float | None:
        """Get the center volume."""
        raise NotImplementedError

    async def set_center_volume(self, volume: float) -> None:
        """Set the center volume."""
        raise NotImplementedError

    # Eco mode.
    async def get_eco_mode(self) -> bool | None:
        """Get the eco mode state."""
        raise NotImplementedError

    # Decoder.
    async def get_decoder_status(self) -> dict | None:
        """Get the current audio decoder status."""
        raise NotImplementedError

    # Expert settings.
    async def reset_expert_settings(self) -> None:
        """Reset expert settings."""
        raise NotImplementedError
