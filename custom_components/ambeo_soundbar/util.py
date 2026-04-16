"""Utility functions for Ambeo Soundbar integration."""

from typing import Any


def find_title_by_id(id: Any, search_list: list[dict]) -> str | None:
    """Find title by ID from a list."""
    for source in search_list:
        if source.get("id") == id:
            return source.get("title")
    return None


def find_id_by_title(title: str, search_list: list[dict]) -> Any:
    """Find ID by title from a list."""
    for source in search_list:
        if source.get("title") == title:
            return source.get("id")
    return None
