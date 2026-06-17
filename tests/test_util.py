"""Tests for Ambeo Soundbar utility functions."""

from custom_components.ambeo_soundbar.util import find_id_by_title, find_title_by_id

ITEMS = [
    {"id": "hdmi1", "title": "HDMI 1"},
    {"id": "optical", "title": "Optical"},
    {"id": "bt", "title": "Bluetooth"},
]


class TestFindTitleById:
    """Tests for find_title_by_id helper."""

    def test_found(self):
        """Return the title when the ID exists in the list."""
        assert find_title_by_id("optical", ITEMS) == "Optical"

    def test_not_found(self):
        """Return None when the ID is not in the list."""
        assert find_title_by_id("usb", ITEMS) is None

    def test_empty_list(self):
        """Return None when the search list is empty."""
        assert find_title_by_id("hdmi1", []) is None

    def test_missing_title_key(self):
        """Return None when a matching entry has no title key."""
        assert find_title_by_id("x", [{"id": "x"}]) is None

    def test_missing_id_key(self):
        """Return None when an entry has no id key."""
        assert find_title_by_id("x", [{"title": "X"}]) is None


class TestFindIdByTitle:
    """Tests for find_id_by_title helper."""

    def test_found(self):
        """Return the ID when the title exists in the list."""
        assert find_id_by_title("Bluetooth", ITEMS) == "bt"

    def test_not_found(self):
        """Return None when the title is not in the list."""
        assert find_id_by_title("ARC", ITEMS) is None

    def test_empty_list(self):
        """Return None when the search list is empty."""
        assert find_id_by_title("HDMI 1", []) is None

    def test_missing_id_key(self):
        """Return None when a matching entry has no id key."""
        assert find_id_by_title("X", [{"title": "X"}]) is None
