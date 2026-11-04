"""Tests for the Ambeo Soundbar config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pyambeo import (
    AmbeoConnectionError,
    AmbeoUnsupportedModelError,
    DeviceInfo,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ambeo_soundbar.const import (
    CONFIG_CONCURRENT_REQUESTS,
    CONFIG_HOST,
    CONFIG_UPDATE_INTERVAL,
    DOMAIN,
)

MOCK_HOST = "192.168.1.100"
MOCK_NAME = "Ambeo Soundbar Plus"
MOCK_SERIAL = "SN123456"

ERRORS = [
    (AmbeoConnectionError("down"), "cannot_connect"),
    (AmbeoUnsupportedModelError("AMBEO Soundbar Ultra"), "unsupported_model"),
    (KeyError("value"), "unknown"),
]


def _patch_connect(name=MOCK_NAME, serial=MOCK_SERIAL, side_effect=None):
    """Patch AmbeoSoundbar.connect to return a soundbar with the given info."""
    api = MagicMock()
    api.info = DeviceInfo("AMBEO Soundbar Plus", name, serial, "1.0.134")
    return patch(
        "custom_components.ambeo_soundbar.config_flow.AmbeoSoundbar.connect",
        AsyncMock(return_value=api, side_effect=side_effect),
    )


@pytest.fixture
def mock_setup_entry():
    """Patch async_setup_entry to avoid full integration setup."""
    with patch(
        "custom_components.ambeo_soundbar.async_setup_entry", return_value=True
    ) as setup_entry:
        yield setup_entry


def _add_entry(hass):
    """Add a configured soundbar entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=MOCK_NAME,
        data={CONFIG_HOST: MOCK_HOST},
        unique_id=MOCK_SERIAL,
        minor_version=2,
    )
    entry.add_to_hass(hass)
    return entry


# ---------------------------------------------------------------------------
# User flow tests
# ---------------------------------------------------------------------------


async def test_user_step_success(hass, mock_setup_entry):
    """Create the entry with the host only."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with _patch_connect():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONFIG_HOST: MOCK_HOST}
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == MOCK_NAME
    assert result["data"] == {CONFIG_HOST: MOCK_HOST}
    assert result["result"].unique_id == MOCK_SERIAL


async def test_user_step_fallback_title(hass, mock_setup_entry):
    """Use a fallback title when the soundbar reports no name."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with _patch_connect(name=None):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONFIG_HOST: MOCK_HOST}
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Ambeo Soundbar"
    assert result["result"].unique_id == MOCK_SERIAL


@pytest.mark.parametrize(("side_effect", "error"), ERRORS)
async def test_user_step_error_recovers(hass, mock_setup_entry, side_effect, error):
    """Show an error, then create the entry on retry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with _patch_connect(side_effect=side_effect):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONFIG_HOST: MOCK_HOST}
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": error}

    with _patch_connect():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONFIG_HOST: MOCK_HOST}
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == MOCK_SERIAL


async def test_user_step_no_serial(hass):
    """Abort when the soundbar reports no serial number."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with _patch_connect(serial=None):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONFIG_HOST: MOCK_HOST}
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "no_serial"


async def test_user_step_already_configured(hass):
    """Abort when the soundbar is already configured."""
    _add_entry(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with _patch_connect():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONFIG_HOST: "192.168.1.200"}
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


# ---------------------------------------------------------------------------
# Reconfigure flow tests
# ---------------------------------------------------------------------------


async def test_reconfigure_success(hass, mock_setup_entry):
    """Update the host of the same soundbar."""
    entry = _add_entry(hass)

    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    with _patch_connect():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONFIG_HOST: "192.168.1.200"}
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data == {CONFIG_HOST: "192.168.1.200"}


@pytest.mark.parametrize(("side_effect", "error"), ERRORS)
async def test_reconfigure_error_recovers(hass, mock_setup_entry, side_effect, error):
    """Show an error, then update the host on retry."""
    entry = _add_entry(hass)

    result = await entry.start_reconfigure_flow(hass)
    with _patch_connect(side_effect=side_effect):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONFIG_HOST: "192.168.1.200"}
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": error}

    with _patch_connect():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONFIG_HOST: "192.168.1.200"}
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data == {CONFIG_HOST: "192.168.1.200"}


async def test_reconfigure_different_device(hass):
    """Refuse a host that answers with another serial number."""
    entry = _add_entry(hass)

    result = await entry.start_reconfigure_flow(hass)
    with _patch_connect(serial="OTHER"):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONFIG_HOST: "192.168.1.200"}
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "different_device"
    assert entry.data == {CONFIG_HOST: MOCK_HOST}


# ---------------------------------------------------------------------------
# Options flow tests
# ---------------------------------------------------------------------------


async def test_options_flow(hass, mock_setup_entry):
    """Store the polling settings in options."""
    entry = _add_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONFIG_UPDATE_INTERVAL: 20.0, CONFIG_CONCURRENT_REQUESTS: 1.0},
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options == {
        CONFIG_UPDATE_INTERVAL: 20,
        CONFIG_CONCURRENT_REQUESTS: 1,
    }
    assert entry.data == {CONFIG_HOST: MOCK_HOST}
