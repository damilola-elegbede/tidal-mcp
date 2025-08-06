"""
Tidal MCP Utility Functions

Helper functions and utilities for the Tidal MCP server.
Provides common functionality for data processing, formatting, and validation.
"""

import logging
import re
from typing import Any
from urllib.parse import quote

logger = logging.getLogger(__name__)


def sanitize_query(query: str) -> str:
    """
    Sanitize and normalize search query string.

    Args:
        query: Raw search query

    Returns:
        Sanitized query string safe for API use
    """
    if not query or not isinstance(query, str):
        return ""

    # Remove extra whitespace and normalize
    sanitized = re.sub(r"\s+", " ", query.strip())

    # Remove potentially problematic characters for API
    sanitized = re.sub(r"[<>{}[\]\\]", "", sanitized)

    return sanitized


def format_duration(seconds: int | None) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string (e.g., "3:45", "1:23:45")
    """
    if not seconds or seconds <= 0:
        return "0:00"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def parse_duration(duration_str: str) -> int:
    """
    Parse duration string to seconds.

    Args:
        duration_str: Duration string (e.g., "3:45", "1:23:45")

    Returns:
        Duration in seconds
    """
    if not duration_str:
        return 0

    try:
        parts = duration_str.split(":")
        if len(parts) == 2:  # MM:SS
            minutes, seconds = map(int, parts)
            # Validate non-negative values
            if minutes < 0 or seconds < 0:
                return 0
            return minutes * 60 + seconds
        elif len(parts) == 3:  # HH:MM:SS
            hours, minutes, seconds = map(int, parts)
            # Validate non-negative values
            if hours < 0 or minutes < 0 or seconds < 0:
                return 0
            return hours * 3600 + minutes * 60 + seconds
        else:
            return 0
    except (ValueError, TypeError):
        return 0


def format_file_size(bytes_size: int) -> str:
    """
    Format file size in bytes to human-readable string.

    Args:
        bytes_size: Size in bytes

    Returns:
        Formatted size string (e.g., "3.2 MB", "1.5 GB")
    """
    if bytes_size == 0:
        return "0 B"

    size_units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(bytes_size)

    while size >= 1024 and unit_index < len(size_units) - 1:
        size /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} {size_units[unit_index]}"
    else:
        return f"{size:.1f} {size_units[unit_index]}"


def safe_get(data: dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely get value from dictionary with dot notation support.

    Args:
        data: Dictionary to search
        key: Key to retrieve (supports dot notation like "artist.name")
        default: Default value if key not found

    Returns:
        Value from dictionary or default
    """
    if not isinstance(data, dict):
        return default

    keys = key.split(".")
    current = data

    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return default

    return current


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length with suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length of resul
        suffix: Suffix to add if truncated

    Returns:
        Truncated text with suffix if needed
    """
    if text is None:
        return ""

    if not text or len(text) <= max_length:
        return text

    if len(suffix) >= max_length:
        return text[:max_length]

    return text[: max_length - len(suffix)] + suffix


def validate_tidal_id(tidal_id: str) -> bool:
    """
    Validate Tidal ID format.

    Args:
        tidal_id: Tidal ID to validate

    Returns:
        True if valid Tidal ID forma
    """
    if not tidal_id or not isinstance(tidal_id, str):
        return False

    # Tidal IDs are typically numeric strings
    return tidal_id.isdigit() and len(tidal_id) > 0


def extract_tidal_id_from_url(url: str) -> str | None:
    """
    Extract Tidal ID from Tidal URL.

    Args:
        url: Tidal URL (e.g., "https://tidal.com/browse/track/123456")

    Returns:
        Extracted Tidal ID or None if not found
    """
    if not url:
        return None

    # Pattern to match Tidal URLs with IDs
    patterns = [
        r"tidal\.com/browse/track/(\d+)",
        r"tidal\.com/browse/album/(\d+)",
        r"tidal\.com/browse/artist/(\d+)",
        r"tidal\.com/browse/playlist/([a-f0-9-]+)",
        r"tidal\.com/track/(\d+)",
        r"tidal\.com/album/(\d+)",
        r"tidal\.com/artist/(\d+)",
        r"tidal\.com/playlist/([a-f0-9-]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def normalize_quality_string(quality: str) -> str:
    """
    Normalize audio quality string to standard format.

    Args:
        quality: Raw quality string from API

    Returns:
        Normalized quality string
    """
    if not quality:
        return "UNKNOWN"

    quality_upper = quality.upper()

    quality_map = {
        "LOW": "LOW",
        "HIGH": "HIGH",
        "LOSSLESS": "LOSSLESS",
        "HI_RES": "HI_RES",
        "MASTER": "MASTER",
        "MQA": "MASTER",
    }

    return quality_map.get(quality_upper, quality_upper)


def build_search_url(
    base_url: str,
    query: str,
    content_types: list[str],
    limit: int = 20,
    offset: int = 0,
    country_code: str = "US",
) -> str:
    """
    Build search API URL with parameters.

    Args:
        base_url: Base API URL
        query: Search query
        content_types: List of content types to search
        limit: Result limi
        offset: Result offse
        country_code: Country code for results

    Returns:
        Complete search URL with parameters
    """
    if not query or not content_types:
        return base_url

    params = {
        "query": quote(query),
        "limit": str(limit),
        "offset": str(offset),
        "types": ",".join(content_types).upper(),
        "countryCode": country_code,
    }

    param_string = "&".join(f"{key}={value}" for key, value in params.items())
    separator = "&" if "?" in base_url else "?"

    return f"{base_url}{separator}{param_string}"


def filter_explicit_content(
    items: list[dict[str, Any]], allow_explicit: bool = True
) -> list[dict[str, Any]]:
    """
    Filter explicit content from results.

    Args:
        items: List of content items
        allow_explicit: Whether to include explicit conten

    Returns:
        Filtered list of items
    """
    if allow_explicit:
        return items

    return [item for item in items if not item.get("explicit", False)]


def merge_artist_names(artists: list[dict[str, Any]]) -> str:
    """
    Merge multiple artist names into a single string.

    Args:
        artists: List of artist dictionaries

    Returns:
        Comma-separated artist names
    """
    if not artists:
        return "Unknown Artist"

    names = []
    for artist in artists:
        name = artist.get("name", "").strip()
        if name:
            names.append(name)

    return ", ".join(names) if names else "Unknown Artist"


def calculate_playlist_stats(tracks: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Calculate statistics for a playlist.

    Args:
        tracks: List of track dictionaries

    Returns:
        Dictionary with playlist statistics
    """
    if not tracks:
        return {
            "total_tracks": 0,
            "total_duration": 0,
            "explicit_tracks": 0,
            "unique_artists": 0,
            "unique_albums": 0,
        }

    total_duration = sum(track.get("duration", 0) for track in tracks)
    explicit_tracks = sum(1 for track in tracks if track.get("explicit", False))

    artists = set()
    albums = set()

    for track in tracks:
        # Collect unique artists
        track_artists = track.get("artists", [])
        if isinstance(track_artists, list):
            for artist in track_artists:
                if isinstance(artist, dict) and "name" in artist:
                    artists.add(artist["name"])

        # Collect unique albums
        album = track.get("album")
        if isinstance(album, dict) and "title" in album:
            albums.add(album["title"])

    return {
        "total_tracks": len(tracks),
        "total_duration": total_duration,
        "explicit_tracks": explicit_tracks,
        "unique_artists": len(artists),
        "unique_albums": len(albums),
    }
