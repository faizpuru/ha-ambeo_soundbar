"""Tests for the entity names and identifiers of the Ambeo Soundbar integration."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.helpers import entity_registry as er
from pyambeo import DeviceInfo, Preset, Source
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ambeo_soundbar.const import CONFIG_HOST, DOMAIN

# entity_id, unique_id and name of every entity, all capabilities enabled.
# Unique IDs and entity IDs must not change, or existing setups lose their entities.
EXPECTED_ENTITIES = [
    ("binary_sensor.living_room_eco_mode", "SN123456_eco_mode", "Eco Mode"),
    (
        "button.living_room_reset_expert_settings",
        "SN123456_reset_expert_settings",
        "Reset Expert Settings",
    ),
    ("button.living_room_restart", "SN123456_ambeo_reboot", "Restart"),
    ("image.living_room_picture", "SN123456_product_picture", "Picture"),
    ("light.living_room_codec_led", "SN123456_codec_led", "Codec LED"),
    ("light.living_room_display", "SN123456_ambeo_max_display", "Display"),
    ("light.living_room_led_bar", "SN123456_led_bar", "LED Bar"),
    ("light.living_room_logo", "SN123456_ambeo_logo", "Logo"),
    ("light.living_room_logo_2", "SN123456_ambeo_max_logo", "Logo"),
    ("media_player.living_room", "SN123456_player", None),
    ("number.living_room_center_volume", "SN123456_center_volume", "Center Volume"),
    (
        "number.living_room_speaker_level_center",
        "SN123456_speaker_level_-_center",
        "Speaker Level - Center",
    ),
    (
        "number.living_room_speaker_level_side_firing",
        "SN123456_speaker_level_-_side_firing",
        "Speaker Level - Side Firing",
    ),
    (
        "number.living_room_speaker_level_up_firing",
        "SN123456_speaker_level_-_up_firing",
        "Speaker Level - Up Firing",
    ),
    (
        "number.living_room_subwoofer_volume",
        "SN123456_subwoofer_volume",
        "Subwoofer Volume",
    ),
    (
        "number.living_room_voice_enhancement_level",
        "SN123456_voice_enhancement_level",
        "Voice Enhancement Level",
    ),
    ("number.living_room_volume_native", "SN123456_native_volume", "Volume (native)"),
    ("select.living_room_ambeo_mode", "SN123456_ambeo_mode_level", "Ambeo Mode"),
    ("select.living_room_sound_mode", "SN123456_sound_mode", "Sound Mode"),
    ("select.living_room_source", "SN123456_source", "Source"),
    ("sensor.living_room_audio_codec", "SN123456_audio_codec", "Audio Codec"),
    ("sensor.living_room_decoder_status", "SN123456_decoder_status", "Decoder Status"),
    ("switch.living_room_ambeo_mode", "SN123456_ambeo_mode", "Ambeo Mode"),
    (
        "switch.living_room_bluetooth_pairing",
        "SN123456_ambeo_bluetooth_pairing",
        "Bluetooth Pairing",
    ),
    ("switch.living_room_night_mode", "SN123456_night_mode", "Night Mode"),
    ("switch.living_room_sound_feedback", "SN123456_sound_feedback", "Sound Feedback"),
    (
        "switch.living_room_subwoofer_status",
        "SN123456_subwoofer_status",
        "Subwoofer Status",
    ),
    (
        "switch.living_room_voice_enhancement",
        "SN123456_voice_enhancement",
        "Voice Enhancement",
    ),
]


def _mock_api():
    """Return a soundbar API mock with every capability."""
    api = MagicMock()
    api.info = DeviceInfo("AMBEO Soundbar Plus", "Living Room", "SN123456", "1.0.134")
    api.sources = [Source("hdmi1", "HDMI 1")]
    api.presets = [Preset("music", "Music")]
    api.fetch_state = AsyncMock(return_value={})
    api.subscribed_paths.return_value = []
    api.has_capability.return_value = True
    api.has_subwoofer = AsyncMock(return_value=True)
    api.get_range.return_value = None
    api.get_volume_step.return_value = 0.01
    api.get_display_volume_max.return_value = 100
    api.fetch_image_url = AsyncMock(
        return_value="http://192.168.1.100:80/assets/images/Soundbar_M_black.png"
    )
    for method in (
        "get_led_bar_brightness_range",
        "get_codec_led_brightness_range",
        "get_logo_brightness_range",
        "get_display_brightness_range",
    ):
        getattr(api, method).return_value = (1, 100)
    return api


async def _setup(hass):
    """Set up the integration with every capability."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id="SN123456", data={CONFIG_HOST: "192.168.1.100"}
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.ambeo_soundbar.AmbeoSoundbar.connect",
        AsyncMock(return_value=_mock_api()),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


async def test_entity_names_and_ids(hass):
    """Keep the entity IDs, unique IDs and English names stable."""
    entry = await _setup(hass)

    entities = sorted(
        (entity.entity_id, entity.unique_id, entity.original_name)
        for entity in er.async_entries_for_config_entry(
            er.async_get(hass), entry.entry_id
        )
    )
    assert entities == EXPECTED_ENTITIES


async def test_entity_names_in_french(hass):
    """Translate the names of new entities on a French setup."""
    hass.config.language = "fr"
    await _setup(hass)

    state = hass.states.get("switch.living_room_mode_nuit")
    assert state.attributes["friendly_name"] == "Living Room Mode nuit"
    state = hass.states.get("button.living_room_redemarrer")
    assert state.attributes["friendly_name"] == "Living Room Redémarrer"


async def test_existing_entity_ids_kept_in_french(hass):
    """Keep the entity IDs of entities registered before the translation."""
    hass.config.language = "fr"
    er.async_get(hass).async_get_or_create(
        "switch",
        DOMAIN,
        "SN123456_night_mode",
        suggested_object_id="living_room_night_mode",
    )
    await _setup(hass)

    state = hass.states.get("switch.living_room_night_mode")
    assert state.attributes["friendly_name"] == "Living Room Mode nuit"
