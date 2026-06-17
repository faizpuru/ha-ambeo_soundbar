"""Tests for Ambeo Soundbar light entities."""

from unittest.mock import AsyncMock, MagicMock

from custom_components.ambeo_soundbar.api.const import Capability
from custom_components.ambeo_soundbar.light import (
    AmbeoLogo,
    AmbeoMaxDisplay,
    AmbeoMaxLogo,
    CodecLED,
    LEDBar,
    async_setup_entry,
)

BRIGHTNESS_RANGE = (0, 100)


def _make_coordinator(data=None, capabilities=None):
    coordinator = MagicMock()
    coordinator.data = data if data is not None else {}
    coordinator.has_capability = MagicMock(
        side_effect=lambda cap: cap in (capabilities or [])
    )
    coordinator.get_led_bar_brightness_range = MagicMock(return_value=BRIGHTNESS_RANGE)
    coordinator.get_codec_led_brightness_range = MagicMock(
        return_value=BRIGHTNESS_RANGE
    )
    coordinator.get_logo_brightness_range = MagicMock(return_value=BRIGHTNESS_RANGE)
    coordinator.get_display_brightness_range = MagicMock(return_value=BRIGHTNESS_RANGE)
    coordinator.async_set_led_bar_brightness = AsyncMock()
    coordinator.async_set_codec_led_brightness = AsyncMock()
    coordinator.async_set_logo_brightness = AsyncMock()
    coordinator.async_set_display_brightness = AsyncMock()
    coordinator.async_change_logo_state = AsyncMock()
    return coordinator


def _make_device():
    device = MagicMock()
    device.serial = "SN123456"
    return device


class TestBaseLight:
    """Tests for BaseLight behaviour, exercised via LEDBar."""

    def test_is_on_true_when_brightness_positive(self):
        """Return True when the brightness data value is greater than zero."""
        coordinator = _make_coordinator(data={"led_bar_brightness": 50})
        entity = LEDBar(coordinator, _make_device())
        assert entity.is_on is True

    def test_is_on_false_when_brightness_zero(self):
        """Return False when brightness is zero."""
        coordinator = _make_coordinator(data={"led_bar_brightness": 0})
        entity = LEDBar(coordinator, _make_device())
        assert entity.is_on is False

    def test_is_on_false_when_no_data(self):
        """Return False when the brightness key is absent."""
        coordinator = _make_coordinator(data={})
        entity = LEDBar(coordinator, _make_device())
        assert entity.is_on is False

    def test_brightness_returns_scaled_value(self):
        """Return 255 (full HA brightness) when device brightness is at maximum."""
        coordinator = _make_coordinator(data={"led_bar_brightness": 100})
        entity = LEDBar(coordinator, _make_device())
        assert entity.brightness == 255

    def test_brightness_none_when_key_missing(self):
        """Return None when brightness key is absent from data."""
        coordinator = _make_coordinator(data={})
        entity = LEDBar(coordinator, _make_device())
        assert entity.brightness is None

    async def test_turn_on_without_brightness_uses_default(self):
        """Set brightness to the entity's default when turned on without a brightness arg."""
        coordinator = _make_coordinator(data={"led_bar_brightness": 0})
        entity = LEDBar(coordinator, _make_device())
        await entity.async_turn_on()
        coordinator.async_set_led_bar_brightness.assert_awaited_once_with(50)

    async def test_turn_on_with_brightness(self):
        """Scale and apply the provided HA brightness value to the device range."""
        coordinator = _make_coordinator(data={"led_bar_brightness": 0})
        entity = LEDBar(coordinator, _make_device())
        await entity.async_turn_on(brightness=128)
        coordinator.async_set_led_bar_brightness.assert_awaited_once()
        value = coordinator.async_set_led_bar_brightness.call_args[0][0]
        assert 48 <= value <= 52  # ~50% of 0-100 range

    async def test_turn_off_sets_brightness_zero(self):
        """Set brightness to zero when the light is turned off."""
        coordinator = _make_coordinator(data={"led_bar_brightness": 80})
        entity = LEDBar(coordinator, _make_device())
        await entity.async_turn_off()
        coordinator.async_set_led_bar_brightness.assert_awaited_once_with(0)


class TestAmbeoLogo:
    """Tests for the AmbeoLogo light entity, which combines state and brightness."""

    def test_is_on_requires_state_and_brightness(self):
        """Return True only when both logo_state is True and brightness is positive."""
        coordinator = _make_coordinator(
            data={"logo_state": True, "logo_brightness": 50}
        )
        entity = AmbeoLogo(coordinator, _make_device())
        assert entity.is_on is True

    def test_is_on_false_when_state_off(self):
        """Return False when logo_state is False even if brightness is positive."""
        coordinator = _make_coordinator(
            data={"logo_state": False, "logo_brightness": 50}
        )
        entity = AmbeoLogo(coordinator, _make_device())
        assert entity.is_on is False

    def test_is_on_false_when_brightness_zero(self):
        """Return False when brightness is zero even if logo_state is True."""
        coordinator = _make_coordinator(data={"logo_state": True, "logo_brightness": 0})
        entity = AmbeoLogo(coordinator, _make_device())
        assert entity.is_on is False

    def test_is_on_false_when_no_data(self):
        """Return False when coordinator has no data yet."""
        coordinator = _make_coordinator()
        coordinator.data = None
        entity = AmbeoLogo(coordinator, _make_device())
        assert entity.is_on is False

    async def test_turn_on_activates_logo_state_when_off(self):
        """Set logo_state to True when turning on a currently-off logo."""
        coordinator = _make_coordinator(
            data={"logo_state": False, "logo_brightness": 50}
        )
        entity = AmbeoLogo(coordinator, _make_device())
        await entity.async_turn_on()
        coordinator.async_change_logo_state.assert_awaited_once_with(True)

    async def test_turn_on_does_not_toggle_state_when_already_on(self):
        """Skip the logo_state call when the logo is already on."""
        coordinator = _make_coordinator(
            data={"logo_state": True, "logo_brightness": 50}
        )
        entity = AmbeoLogo(coordinator, _make_device())
        await entity.async_turn_on()
        coordinator.async_change_logo_state.assert_not_awaited()

    async def test_turn_on_with_brightness_sets_it(self):
        """Set logo brightness when a brightness value is provided."""
        coordinator = _make_coordinator(
            data={"logo_state": True, "logo_brightness": 50}
        )
        entity = AmbeoLogo(coordinator, _make_device())
        await entity.async_turn_on(brightness=255)
        coordinator.async_set_logo_brightness.assert_awaited_once()

    async def test_turn_off_sets_logo_state_false(self):
        """Set logo_state to False when the logo is turned off."""
        coordinator = _make_coordinator(
            data={"logo_state": True, "logo_brightness": 50}
        )
        entity = AmbeoLogo(coordinator, _make_device())
        await entity.async_turn_off()
        coordinator.async_change_logo_state.assert_awaited_once_with(False)


class TestLightSetupEntry:
    """Tests for light platform setup entry."""

    async def test_adds_ambeo_logo_when_capable(self):
        """Add AmbeoLogo when device reports AMBEO_LOGO capability."""
        coordinator = _make_coordinator(capabilities=[Capability.AMBEO_LOGO])
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert any(isinstance(e, AmbeoLogo) for e in added)

    async def test_adds_led_bar_when_capable(self):
        """Add LEDBar when device reports LED_BAR capability."""
        coordinator = _make_coordinator(capabilities=[Capability.LED_BAR])
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert any(isinstance(e, LEDBar) for e in added)

    async def test_adds_codec_led_when_capable(self):
        """Add CodecLED when device reports CODEC_LED capability."""
        coordinator = _make_coordinator(capabilities=[Capability.CODEC_LED])
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert any(isinstance(e, CodecLED) for e in added)

    async def test_adds_max_logo_when_capable(self):
        """Add AmbeoMaxLogo when device reports MAX_LOGO capability."""
        coordinator = _make_coordinator(capabilities=[Capability.MAX_LOGO])
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert any(isinstance(e, AmbeoMaxLogo) for e in added)

    async def test_adds_max_display_when_capable(self):
        """Add AmbeoMaxDisplay when device reports MAX_DISPLAY capability."""
        coordinator = _make_coordinator(capabilities=[Capability.MAX_DISPLAY])
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert any(isinstance(e, AmbeoMaxDisplay) for e in added)

    async def test_no_lights_when_no_capabilities(self):
        """Add no light entities when device has no relevant capabilities."""
        coordinator = _make_coordinator()
        config_entry = MagicMock()
        config_entry.runtime_data.coordinator = coordinator
        config_entry.runtime_data.device = _make_device()
        added = []
        await async_setup_entry(MagicMock(), config_entry, added.extend)
        assert not added
