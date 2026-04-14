"""Common fixtures for Ambeo Soundbar tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    return enable_custom_integrations


@pytest.fixture
def mock_api():
    """Return a mocked Ambeo API."""
    api = MagicMock()
    api.get_name = AsyncMock(return_value="Ambeo Soundbar Plus")
    api.get_serial = AsyncMock(return_value="SN123456")
    api.get_model = AsyncMock(return_value="AMBEO Soundbar Plus")
    api.get_version = AsyncMock(return_value="1.0.0")
    api.get_all_sources = AsyncMock(return_value=[])
    api.get_all_presets = AsyncMock(return_value=[])
    api.get_volume = AsyncMock(return_value=50)
    api.is_mute = AsyncMock(return_value=False)
    api.get_state = AsyncMock(return_value="online")
    api.get_current_source = AsyncMock(return_value=None)
    api.get_current_preset = AsyncMock(return_value=None)
    api.player_data = AsyncMock(return_value=None)
    api.has_capability = MagicMock(return_value=False)
    api.support_debounce_mode = MagicMock(return_value=False)
    api.get_volume_step = MagicMock(return_value=0.01)
    api.get_volume_max = MagicMock(return_value=100)
    api.has_subwoofer = AsyncMock(return_value=False)
    return api


@pytest.fixture
def mock_coordinator(mock_api):
    """Return a mocked coordinator."""
    coordinator = MagicMock()
    coordinator.data = {"volume": 50, "muted": False, "state": "online"}
    coordinator.has_capability = MagicMock(return_value=False)
    coordinator.support_debounce_mode = MagicMock(return_value=False)
    coordinator.get_volume_step = MagicMock(return_value=0.01)
    coordinator.get_volume_max = MagicMock(return_value=100)
    coordinator.async_config_entry_first_refresh = AsyncMock()
    return coordinator
