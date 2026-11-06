"""Tests for the Ambeo Soundbar image entity."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.const import EntityCategory
from homeassistant.exceptions import PlatformNotReady
from pyambeo import AmbeoConnectionError

from custom_components.ambeo_soundbar.coordinator import AmbeoCoordinator
from custom_components.ambeo_soundbar.image import ProductPicture, async_setup_entry

URL = "http://ambeo.local:80/assets/images/Soundbar_M_black.png"


def _make_coordinator(hass, url=URL):
    coordinator = MagicMock(spec=AmbeoCoordinator)
    coordinator.hass = hass
    coordinator.data = {}
    if isinstance(url, Exception):
        coordinator.fetch_image_url = AsyncMock(side_effect=url)
    else:
        coordinator.fetch_image_url = AsyncMock(return_value=url)
    return coordinator


def _make_device():
    device = MagicMock()
    device.serial = "SN123456"
    return device


def _make_entry(coordinator):
    config_entry = MagicMock()
    config_entry.runtime_data.coordinator = coordinator
    config_entry.runtime_data.device = _make_device()
    return config_entry


class TestProductPicture:
    """Tests for the ProductPicture image entity."""

    def test_attributes(self, hass):
        """Serve the device picture as a diagnostic image."""
        entity = ProductPicture(_make_coordinator(hass), _make_device(), URL)
        assert entity.image_url == URL
        assert entity.image_last_updated is not None
        assert entity.entity_category == EntityCategory.DIAGNOSTIC
        assert entity.unique_id == "SN123456_product_picture"


class TestImageSetupEntry:
    """Tests for image platform setup entry."""

    async def test_adds_picture(self, hass):
        """Add the picture with the URL read once from the soundbar."""
        coordinator = _make_coordinator(hass)
        added = []
        await async_setup_entry(hass, _make_entry(coordinator), added.extend)
        assert len(added) == 1
        assert added[0].image_url == URL
        coordinator.fetch_image_url.assert_awaited_once()

    async def test_no_picture(self, hass):
        """Add nothing when the soundbar has no picture."""
        added = []
        await async_setup_entry(
            hass, _make_entry(_make_coordinator(hass, None)), added.extend
        )
        assert not added

    async def test_soundbar_unreachable(self, hass):
        """Retry the platform setup later when the soundbar cannot be reached."""
        coordinator = _make_coordinator(hass, AmbeoConnectionError("timeout"))
        with pytest.raises(PlatformNotReady):
            await async_setup_entry(hass, _make_entry(coordinator), MagicMock())
