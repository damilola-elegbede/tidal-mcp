"""
Comprehensive tests for utils module to maximize coverage.
"""

import pytest

from tidal_mcp.utils import (
    build_search_url,
    calculate_playlist_stats,
    extract_tidal_id_from_url,
    filter_explicit_content,
    format_duration,
    format_file_size,
    merge_artist_names,
    normalize_quality_string,
    parse_duration,
    safe_get,
    sanitize_query,
    truncate_text,
    validate_tidal_id,
)


class TestUtilsComprehensive:
    """Comprehensive tests for utils module."""

    def test_parse_duration_valid_formats(self):
        """Test parse_duration with valid formats."""
        assert parse_duration("3:45") == 225
        assert parse_duration("1:23:45") == 5025
        assert parse_duration("0:30") == 30
        assert parse_duration("1:00:00") == 3600

    def test_parse_duration_invalid_formats(self):
        """Test parse_duration with invalid formats."""
        assert parse_duration("") == 0
        assert parse_duration("invalid") == 0
        assert parse_duration("1:2:3:4") == 0
        assert parse_duration("1") == 0
        assert parse_duration("abc:def") == 0
        assert parse_duration("-1:30") == 0  # Negative values
        assert parse_duration("1:-30") == 0

    def test_parse_duration_edge_cases(self):
        """Test parse_duration with edge cases."""
        assert parse_duration(None) == 0
        assert parse_duration("10:00") == 600

    def test_safe_get_simple_keys(self):
        """Test safe_get with simple keys."""
        data = {"key1": "value1", "key2": 42}
        assert safe_get(data, "key1") == "value1"
        assert safe_get(data, "key2") == 42
        assert safe_get(data, "missing") is None
        assert safe_get(data, "missing", "default") == "default"

    def test_safe_get_dot_notation(self):
        """Test safe_get with dot notation."""
        data = {"level1": {"level2": {"value": "nested_value"}}}
        assert safe_get(data, "level1.level2.value") == "nested_value"
        assert safe_get(data, "level1.level2.missing") is None
        assert safe_get(data, "level1.missing.value") is None

    def test_safe_get_invalid_input(self):
        """Test safe_get with invalid input."""
        assert safe_get(None, "key") is None
        assert safe_get("not_dict", "key") is None
        assert safe_get([], "key") is None

    def test_truncate_text_normal_cases(self):
        """Test truncate_text with normal cases."""
        assert truncate_text("short") == "short"
        assert truncate_text("a" * 150, 100) == "a" * 97 + "..."
        assert truncate_text("test", 100) == "test"

    def test_truncate_text_edge_cases(self):
        """Test truncate_text with edge cases."""
        assert truncate_text(None) == ""
        assert truncate_text("") == ""
        assert truncate_text("test", 2, "...") == "te"  # Suffix too long
        assert truncate_text("test", 10, "") == "test"  # No suffix

    def test_truncate_text_custom_suffix(self):
        """Test truncate_text with custom suffix."""
        text = "a" * 50
        result = truncate_text(text, 10, "[...]")
        assert len(result) == 10
        assert result.endswith("[...]")

    def test_normalize_quality_string_known_values(self):
        """Test normalize_quality_string with known values."""
        assert normalize_quality_string("LOW") == "LOW"
        assert normalize_quality_string("high") == "HIGH"
        assert normalize_quality_string("LoSsLeSs") == "LOSSLESS"
        assert normalize_quality_string("HI_RES") == "HI_RES"
        assert normalize_quality_string("master") == "MASTER"
        assert normalize_quality_string("MQA") == "MASTER"

    def test_normalize_quality_string_unknown_values(self):
        """Test normalize_quality_string with unknown values."""
        assert normalize_quality_string("UNKNOWN_QUALITY") == "UNKNOWN_QUALITY"
        assert normalize_quality_string("custom") == "CUSTOM"

    def test_normalize_quality_string_edge_cases(self):
        """Test normalize_quality_string with edge cases."""
        assert normalize_quality_string("") == "UNKNOWN"
        assert normalize_quality_string(None) == "UNKNOWN"

    def test_build_search_url_basic(self):
        """Test build_search_url with basic parameters."""
        url = build_search_url(
            "https://api.tidal.com/search", "test query", ["tracks", "albums"]
        )
        assert "query=test%20query" in url
        assert "types=TRACKS,ALBUMS" in url
        assert "limit=20" in url

    def test_build_search_url_custom_params(self):
        """Test build_search_url with custom parameters."""
        url = build_search_url(
            "https://api.tidal.com/search",
            "artist search",
            ["artists"],
            limit=50,
            offset=100,
            country_code="UK",
        )
        assert "limit=50" in url
        assert "offset=100" in url
        assert "countryCode=UK" in url

    def test_build_search_url_edge_cases(self):
        """Test build_search_url with edge cases."""
        # Empty query
        url = build_search_url("https://api.tidal.com", "", ["tracks"])
        assert url == "https://api.tidal.com"

        # Empty content types
        url = build_search_url("https://api.tidal.com", "query", [])
        assert url == "https://api.tidal.com"

    def test_build_search_url_with_existing_params(self):
        """Test build_search_url with base URL that has parameters."""
        url = build_search_url(
            "https://api.tidal.com/search?existing=param", "test", ["tracks"]
        )
        assert "existing=param" in url
        assert "query=test" in url

    def test_filter_explicit_content_allow_all(self):
        """Test filter_explicit_content when allowing explicit content."""
        items = [
            {"title": "Clean Song", "explicit": False},
            {"title": "Explicit Song", "explicit": True},
            {"title": "No Explicit Field"},
        ]
        result = filter_explicit_content(items, allow_explicit=True)
        assert len(result) == 3

    def test_filter_explicit_content_filter_explicit(self):
        """Test filter_explicit_content when filtering explicit content."""
        items = [
            {"title": "Clean Song", "explicit": False},
            {"title": "Explicit Song", "explicit": True},
            {"title": "No Explicit Field"},
        ]
        result = filter_explicit_content(items, allow_explicit=False)
        assert len(result) == 2
        assert all(not item.get("explicit", False) for item in result)

    def test_merge_artist_names_normal_cases(self):
        """Test merge_artist_names with normal cases."""
        artists = [{"name": "Artist 1"}, {"name": "Artist 2"}, {"name": "Artist 3"}]
        result = merge_artist_names(artists)
        assert result == "Artist 1, Artist 2, Artist 3"

    def test_merge_artist_names_edge_cases(self):
        """Test merge_artist_names with edge cases."""
        assert merge_artist_names([]) == "Unknown Artist"
        assert merge_artist_names([{"name": ""}]) == "Unknown Artist"
        assert merge_artist_names([{"name": "  "}]) == "Unknown Artist"
        assert merge_artist_names([{"no_name": "value"}]) == "Unknown Artist"

    def test_merge_artist_names_mixed_valid_invalid(self):
        """Test merge_artist_names with mix of valid and invalid names."""
        artists = [
            {"name": "Valid Artist"},
            {"name": ""},
            {"name": "Another Artist"},
            {"no_name": "value"},
        ]
        result = merge_artist_names(artists)
        assert result == "Valid Artist, Another Artist"

    def test_calculate_playlist_stats_empty(self):
        """Test calculate_playlist_stats with empty playlist."""
        result = calculate_playlist_stats([])
        assert result["total_tracks"] == 0
        assert result["total_duration"] == 0
        assert result["explicit_tracks"] == 0
        assert result["unique_artists"] == 0
        assert result["unique_albums"] == 0

    def test_calculate_playlist_stats_with_tracks(self):
        """Test calculate_playlist_stats with tracks."""
        tracks = [
            {
                "duration": 180,
                "explicit": False,
                "artists": [{"name": "Artist 1"}, {"name": "Artist 2"}],
                "album": {"title": "Album 1"},
            },
            {
                "duration": 200,
                "explicit": True,
                "artists": [{"name": "Artist 1"}],
                "album": {"title": "Album 2"},
            },
            {
                "duration": 150,
                "explicit": False,
                "artists": [{"name": "Artist 3"}],
                "album": {"title": "Album 1"},  # Duplicate album
            },
        ]

        result = calculate_playlist_stats(tracks)
        assert result["total_tracks"] == 3
        assert result["total_duration"] == 530
        assert result["explicit_tracks"] == 1
        assert result["unique_artists"] == 3
        assert result["unique_albums"] == 2

    def test_calculate_playlist_stats_malformed_data(self):
        """Test calculate_playlist_stats with malformed data."""
        tracks = [
            {
                "duration": 180,
                # Missing explicit field
                "artists": "not_a_list",  # Invalid artists format
                "album": "not_a_dict",  # Invalid album format
            },
            {
                # Missing duration
                "explicit": True,
                "artists": [{"no_name": "value"}],  # Artist without name
                "album": {"no_title": "value"},  # Album without title
            },
        ]

        result = calculate_playlist_stats(tracks)
        assert result["total_tracks"] == 2
        assert result["total_duration"] == 180  # Only first track has duration
        assert result["explicit_tracks"] == 1
        assert result["unique_artists"] == 0  # No valid artist names
        assert result["unique_albums"] == 0  # No valid album titles

    def test_url_extraction_edge_cases(self):
        """Test URL extraction with more edge cases."""
        # Test various Tidal URL formats
        urls_and_expected = [
            ("https://tidal.com/browse/track/123456", "123456"),
            ("https://tidal.com/track/789012", "789012"),
            ("https://tidal.com/browse/album/345678", "345678"),
            ("https://tidal.com/album/901234", "901234"),
            ("https://tidal.com/browse/artist/567890", "567890"),
            ("https://tidal.com/artist/123890", "123890"),
            ("https://tidal.com/browse/playlist/abc-def-123", "abc-def-123"),
            # Note: Non-browse playlist URLs may not be supported by current regex
            ("https://tidal.com/playlist/xyz-456-789", None),
            ("https://example.com/track/123", None),  # Non-Tidal URL
            ("not-a-url", None),
            ("", None),
        ]

        for url, expected in urls_and_expected:
            result = extract_tidal_id_from_url(url)
            assert result == expected, f"Failed for URL: {url}"

    def test_url_extraction_case_insensitive(self):
        """Test URL extraction is case insensitive."""
        url = "HTTPS://TIDAL.COM/TRACK/123456"
        result = extract_tidal_id_from_url(url)
        assert result == "123456"
