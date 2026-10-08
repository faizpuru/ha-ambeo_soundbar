"""Tests for the Ambeo Soundbar config flow."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ambeo_soundbar.api import (
    AmbeoConnectionError,
    AmbeoUnsupportedModelError,
)
from custom_components.ambeo_soundbar.config_flow import validate_connection
from custom_components.ambeo_soundbar.const import (
    CONFIG_HOST,
    CONFIG_UPDATE_INTERVAL,
    CONFIG_UPDATE_INTERVAL_DEFAULT,
    DOMAIN,
)

MOCK_HOST = "192.168.1.100"
MOCK_NAME = "Ambeo Soundbar Plus"
MOCK_SERIAL = "SN123456"


def _patch_validate_connection(name=MOCK_NAME, serial=MOCK_SERIAL, error=None):
    """Patch validate_connection to return given values."""
    return patch(
        "custom_components.ambeo_soundbar.config_flow.validate_connection",
        return_value=(name, serial, error),
    )


def _patch_setup_entry():
    """Patch async_setup_entry to avoid full integration setup."""
    return patch(
        "custom_components.ambeo_soundbar.async_setup_entry",
        return_value=True,
    )


# ---------------------------------------------------------------------------
# Config flow tests
# ---------------------------------------------------------------------------


async def test_user_step_shows_form(hass):
    """Test that the user step shows the setup form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_user_step_success(hass):
    """Test successful config flow from user step."""
    with _patch_validate_connection(), _patch_setup_entry():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONFIG_HOST: MOCK_HOST},
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == MOCK_NAME
    assert result["data"][CONFIG_HOST] == MOCK_HOST


async def test_user_step_cannot_connect(hass):
    """Test config flow shows error when connection fails."""
    with _patch_validate_connection(name=None, serial=None, error="cannot_connect"):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONFIG_HOST: MOCK_HOST},
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_step_already_configured(hass):
    """Test config flow aborts when device is already configured."""
    with _patch_validate_connection(), _patch_setup_entry():
        # First setup
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONFIG_HOST: MOCK_HOST}
        )

    with _patch_validate_connection():
        # Second attempt with same serial
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONFIG_HOST: MOCK_HOST}
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_user_step_fallback_title(hass):
    """Test that config flow uses fallback title when name is None."""
    with _patch_validate_connection(name=None), _patch_setup_entry():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONFIG_HOST: MOCK_HOST},
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Ambeo Soundbar"


async def test_user_step_custom_update_interval(hass):
    """Test that a custom update interval is stored in data."""
    with _patch_validate_connection(), _patch_setup_entry():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONFIG_HOST: MOCK_HOST, CONFIG_UPDATE_INTERVAL: 30},
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONFIG_UPDATE_INTERVAL] == 30


# ---------------------------------------------------------------------------
# Options flow tests
# ---------------------------------------------------------------------------


async def _setup_entry(hass, options=None):
    """Create a config entry with mocked runtime_data and return it."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=MOCK_NAME,
        data={
            CONFIG_HOST: MOCK_HOST,
            CONFIG_UPDATE_INTERVAL: CONFIG_UPDATE_INTERVAL_DEFAULT,
        },
        options=options or {},
        unique_id=MOCK_SERIAL,
    )
    entry.add_to_hass(hass)

    mock_coordinator = MagicMock()

    mock_data = MagicMock()
    mock_data.coordinator = mock_coordinator
    entry.runtime_data = mock_data

    return entry


async def test_options_flow_shows_form(hass):
    """Test that the options flow shows the settings form."""
    entry = await _setup_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"


async def test_options_flow_success(hass):
    """Test successful options flow update."""
    entry = await _setup_entry(hass)

    with _patch_validate_connection():
        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {CONFIG_HOST: "192.168.1.200", CONFIG_UPDATE_INTERVAL: 20},
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONFIG_HOST] == "192.168.1.200"
    assert result["data"][CONFIG_UPDATE_INTERVAL] == 20


async def test_options_flow_cannot_connect(hass):
    """Test options flow shows error when connection fails."""
    entry = await _setup_entry(hass)

    with _patch_validate_connection(name=None, serial=None, error="cannot_connect"):
        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {CONFIG_HOST: "bad-host", CONFIG_UPDATE_INTERVAL: 10},
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_options_flow_different_device(hass):
    """Refuse a host that answers with another serial number."""
    entry = await _setup_entry(hass)

    with _patch_validate_connection(serial="OTHER"):
        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {CONFIG_HOST: "192.168.1.200", CONFIG_UPDATE_INTERVAL: 20},
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "different_device"}


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (AmbeoUnsupportedModelError("AMBEO Soundbar Ultra"), "unsupported_model"),
        (AmbeoConnectionError("down"), "cannot_connect"),
        (KeyError("value"), "unknown"),
    ],
)
async def test_validate_connection_errors(hass, error, expected):
    """Map connect() errors to config flow error codes."""
    with patch(
        "custom_components.ambeo_soundbar.config_flow.AmbeoSoundbar.connect",
        side_effect=error,
    ):
        assert await validate_connection(hass, MOCK_HOST) == (None, None, expected)
