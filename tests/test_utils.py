"""
Comprehensive tests for Tidal MCP Utility Functions

Tests utility functions for data processing, formatting, validation, and helper operations.
Focuses on achieving high coverage for all utility functions and edge cases.
"""

import pytest

from src.tidal_mcp.utils import (
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


class TestQuerySanitization:
    """Test query sanitization functionality."""

    def test_sanitize_query_basic(self):
        """Test basic query sanitization."""
        result = sanitize_query("test query")
        assert result == "test query"

    def test_sanitize_query_with_extra_whitespace(self):
        """Test sanitizing query with extra whitespace."""
        result = sanitize_query("  test   query  with   spaces  ")
        assert result == "test query with spaces"

    def test_sanitize_query_with_problematic_characters(self):
        """Test sanitizing query with problematic characters."""
        result = sanitize_query("test<query>with{bad}[chars]\\")
        assert result == "testquerywithbadchars"

    def test_sanitize_query_empty_string(self):
        """Test sanitizing empty string."""
        result = sanitize_query("")
        assert result == ""

    def test_sanitize_query_none_input(self):
        """Test sanitizing None input."""
        result = sanitize_query(None)
        assert result == ""

    def test_sanitize_query_non_string_input(self):
        """Test sanitizing non-string input."""
        result = sanitize_query(123)
        assert result == ""

        result = sanitize_query(["list", "input"])
        assert result == ""

    def test_sanitize_query_only_whitespace(self):
        """Test sanitizing query with only whitespace."""
        result = sanitize_query("   \t\n  ")
        assert result == ""

    def test_sanitize_query_with_newlines_and_tabs(self):
        """Test sanitizing query with newlines and tabs."""
        result = sanitize_query("test\nquery\twith\nspecial\tspaces")
        assert result == "test query with special spaces"


class TestDurationFormatting:
    """Test duration formatting and parsing functionality."""

    def test_format_duration_seconds_only(self):
        """Test formatting duration with seconds only."""
        assert format_duration(45) == "0:45"
        assert format_duration(9) == "0:09"

    def test_format_duration_minutes_seconds(self):
        """Test formatting duration with minutes and seconds."""
        assert format_duration(125) == "2:05"
        assert format_duration(240) == "4:00"
        assert format_duration(3599) == "59:59"

    def test_format_duration_hours_minutes_seconds(self):
        """Test formatting duration with hours, minutes, and seconds."""
        assert format_duration(3600) == "1:00:00"
        assert format_duration(3665) == "1:01:05"
        assert format_duration(7265) == "2:01:05"

    def test_format_duration_zero(self):
        """Test formatting zero duration."""
        assert format_duration(0) == "0:00"

    def test_format_duration_negative(self):
        """Test formatting negative duration."""
        assert format_duration(-10) == "0:00"

    def test_format_duration_none(self):
        """Test formatting None duration."""
        assert format_duration(None) == "0:00"

    def test_format_duration_invalid_types(self):
        """Test formatting invalid duration types."""
        assert format_duration("string") == "0:00"
        assert format_duration([1, 2, 3]) == "0:00"
        assert format_duration({"key": "value"}) == "0:00"

    def test_format_duration_float(self):
        """Test formatting float duration."""
        # The function converts floats to int using floor division
        assert format_duration(125.7) == "2:05"  # 125 seconds
        assert format_duration(3665.9) == "1:01:05"  # 3665 seconds

    def test_parse_duration_minutes_seconds(self):
        """Test parsing MM:SS format."""
        assert parse_duration("3:45") == 225
        assert parse_duration("0:30") == 30
        assert parse_duration("59:59") == 3599

    def test_parse_duration_hours_minutes_seconds(self):
        """Test parsing HH:MM:SS format."""
        assert parse_duration("1:30:45") == 5445
        assert parse_duration("2:00:00") == 7200
        assert parse_duration("0:05:30") == 330

    def test_parse_duration_empty_string(self):
        """Test parsing empty string."""
        assert parse_duration("") == 0
        assert parse_duration(None) == 0

    def test_parse_duration_invalid_format(self):
        """Test parsing invalid duration formats."""
        assert parse_duration("invalid") == 0
        assert parse_duration("1:2:3:4") == 0
        assert parse_duration("1") == 0
        assert parse_duration("a:b") == 0

    def test_parse_duration_negative_values(self):
        """Test parsing duration with negative values."""
        assert parse_duration("-1:30") == 0
        assert parse_duration("1:-30") == 0
        assert parse_duration("-1:-30:-45") == 0

    def test_parse_duration_zero_values(self):
        """Test parsing duration with zero values."""
        assert parse_duration("0:00") == 0
        assert parse_duration("0:00:00") == 0


class TestFileSizeFormatting:
    """Test file size formatting functionality."""

    def test_format_file_size_bytes(self):
        """Test formatting file size in bytes."""
        assert format_file_size(0) == "0 B"
        assert format_file_size(512) == "512 B"
        assert format_file_size(1023) == "1023 B"

    def test_format_file_size_kilobytes(self):
        """Test formatting file size in kilobytes."""
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1536) == "1.5 KB"
        assert format_file_size(2048) == "2.0 KB"

    def test_format_file_size_megabytes(self):
        """Test formatting file size in megabytes."""
        assert format_file_size(1048576) == "1.0 MB"
        assert format_file_size(1572864) == "1.5 MB"
        assert format_file_size(5242880) == "5.0 MB"

    def test_format_file_size_gigabytes(self):
        """Test formatting file size in gigabytes."""
        assert format_file_size(1073741824) == "1.0 GB"
        assert format_file_size(2147483648) == "2.0 GB"

    def test_format_file_size_terabytes(self):
        """Test formatting file size in terabytes."""
        assert format_file_size(1099511627776) == "1.0 TB"

    def test_format_file_size_large_values(self):
        """Test formatting very large file sizes."""
        # Should cap at TB
        very_large = 1024 * 1024 * 1024 * 1024 * 1024  # Beyond TB
        result = format_file_size(very_large)
        assert "TB" in result

    def test_format_file_size_decimal_precision(self):
        """Test file size formatting decimal precision."""
        # Should show one decimal place for non-bytes
        assert format_file_size(1536) == "1.5 KB"  # Exactly 1.5
        assert format_file_size(1587) == "1.5 KB"  # Rounds to 1.5


class TestSafeGet:
    """Test safe dictionary access functionality."""

    def test_safe_get_simple_key(self):
        """Test safe get with simple key."""
        data = {"name": "test", "value": 42}
        assert safe_get(data, "name") == "test"
        assert safe_get(data, "value") == 42

    def test_safe_get_missing_key(self):
        """Test safe get with missing key."""
        data = {"name": "test"}
        assert safe_get(data, "missing") is None
        assert safe_get(data, "missing", "default") == "default"

    def test_safe_get_dot_notation(self):
        """Test safe get with dot notation."""
        data = {"user": {"profile": {"name": "John Doe", "age": 30}}}
        assert safe_get(data, "user.profile.name") == "John Doe"
        assert safe_get(data, "user.profile.age") == 30

    def test_safe_get_dot_notation_missing(self):
        """Test safe get with dot notation and missing keys."""
        data = {"user": {"profile": {"name": "John"}}}
        assert safe_get(data, "user.profile.age") is None
        assert safe_get(data, "user.missing.name") is None
        assert safe_get(data, "missing.user.name") is None

    def test_safe_get_non_dict_input(self):
        """Test safe get with non-dictionary input."""
        assert safe_get("string", "key") is None
        assert safe_get(123, "key") is None
        assert safe_get(None, "key") is None
        assert safe_get([], "key") is None

    def test_safe_get_non_dict_intermediate(self):
        """Test safe get when intermediate value is not dict."""
        data = {"user": "not_a_dict"}
        assert safe_get(data, "user.profile.name") is None

    def test_safe_get_empty_key(self):
        """Test safe get with empty key."""
        data = {"": "empty_key_value"}
        assert safe_get(data, "") == "empty_key_value"

    def test_safe_get_custom_default(self):
        """Test safe get with custom default values."""
        data = {"existing": "value"}
        assert safe_get(data, "missing", "custom_default") == "custom_default"
        assert safe_get(data, "missing", 0) == 0
        assert safe_get(data, "missing", []) == []


class TestTextTruncation:
    """Test text truncation functionality."""

    def test_truncate_text_within_limit(self):
        """Test truncating text within limit."""
        text = "Short text"
        result = truncate_text(text, 20)
        assert result == "Short text"

    def test_truncate_text_exceeds_limit(self):
        """Test truncating text that exceeds limit."""
        text = "This is a very long text that exceeds the limit"
        result = truncate_text(text, 20)
        assert result == "This is a very lo..."
        assert len(result) == 20

    def test_truncate_text_exact_limit(self):
        """Test truncating text at exact limit."""
        text = "Exactly twenty chars"  # 20 characters
        result = truncate_text(text, 20)
        assert result == "Exactly twenty chars"

    def test_truncate_text_custom_suffix(self):
        """Test truncating text with custom suffix."""
        text = "Long text that needs truncation"
        result = truncate_text(text, 15, " [more]")
        assert result == "Long tex [more]"
        assert len(result) == 15

    def test_truncate_text_none_input(self):
        """Test truncating None input."""
        result = truncate_text(None, 10)
        assert result == ""

    def test_truncate_text_empty_string(self):
        """Test truncating empty string."""
        result = truncate_text("", 10)
        assert result == ""

    def test_truncate_text_suffix_longer_than_limit(self):
        """Test truncating when suffix is longer than limit."""
        text = "Some text"
        result = truncate_text(text, 5, "very_long_suffix")
        assert result == "Some "  # Should just truncate without suffix

    def test_truncate_text_zero_limit(self):
        """Test truncating with zero limit."""
        text = "Some text"
        result = truncate_text(text, 0)
        assert result == ""


class TestTidalIdValidation:
    """Test Tidal ID validation functionality."""

    def test_validate_tidal_id_valid(self):
        """Test validating valid Tidal IDs."""
        assert validate_tidal_id("123456789") is True
        assert validate_tidal_id("1") is True
        assert validate_tidal_id("999999999999") is True

    def test_validate_tidal_id_invalid(self):
        """Test validating invalid Tidal IDs."""
        assert validate_tidal_id("abc123") is False
        assert validate_tidal_id("123abc") is False
        assert validate_tidal_id("12.34") is False
        assert validate_tidal_id("12-34") is False

    def test_validate_tidal_id_empty(self):
        """Test validating empty Tidal ID."""
        assert validate_tidal_id("") is False
        assert validate_tidal_id(None) is False

    def test_validate_tidal_id_non_string(self):
        """Test validating non-string Tidal ID."""
        assert validate_tidal_id(123) is False
        assert validate_tidal_id(["123"]) is False
        assert validate_tidal_id({"id": "123"}) is False

    def test_validate_tidal_id_with_whitespace(self):
        """Test validating Tidal ID with whitespace."""
        assert validate_tidal_id(" 123 ") is False
        assert validate_tidal_id("12 34") is False


class TestTidalUrlExtraction:
    """Test Tidal URL ID extraction functionality."""

    def test_extract_tidal_id_track_urls(self):
        """Test extracting ID from track URLs."""
        urls = [
            "https://tidal.com/browse/track/123456",
            "https://listen.tidal.com/track/123456",
            "http://tidal.com/track/123456",
        ]
        for url in urls:
            assert extract_tidal_id_from_url(url) == "123456"

    def test_extract_tidal_id_album_urls(self):
        """Test extracting ID from album URLs."""
        urls = [
            "https://tidal.com/browse/album/789012",
            "https://listen.tidal.com/album/789012",
        ]
        for url in urls:
            assert extract_tidal_id_from_url(url) == "789012"

    def test_extract_tidal_id_artist_urls(self):
        """Test extracting ID from artist URLs."""
        urls = [
            "https://tidal.com/browse/artist/345678",
            "https://listen.tidal.com/artist/345678",
        ]
        for url in urls:
            assert extract_tidal_id_from_url(url) == "345678"

    def test_extract_tidal_id_playlist_urls(self):
        """Test extracting ID from playlist URLs."""
        playlist_id = "abc123def-456-789-012-345678901234"
        urls = [
            f"https://tidal.com/browse/playlist/{playlist_id}",
            f"https://listen.tidal.com/playlist/{playlist_id}",
        ]
        for url in urls:
            assert extract_tidal_id_from_url(url) == playlist_id

    def test_extract_tidal_id_case_insensitive(self):
        """Test URL extraction is case insensitive."""
        url = "HTTPS://TIDAL.COM/BROWSE/TRACK/123456"
        assert extract_tidal_id_from_url(url) == "123456"

    def test_extract_tidal_id_invalid_urls(self):
        """Test extracting ID from invalid URLs."""
        invalid_urls = [
            "https://spotify.com/track/123456",
            "https://tidal.com/browse/invalid/123456",
            "not_a_url",
            "",
            None,
        ]
        for url in invalid_urls:
            assert extract_tidal_id_from_url(url) is None

    def test_extract_tidal_id_with_query_params(self):
        """Test extracting ID from URLs with query parameters."""
        url = "https://tidal.com/browse/track/123456?utm_source=test"
        assert extract_tidal_id_from_url(url) == "123456"

    def test_extract_tidal_id_with_fragments(self):
        """Test extracting ID from URLs with fragments."""
        url = "https://tidal.com/browse/track/123456#section"
        assert extract_tidal_id_from_url(url) == "123456"


class TestQualityNormalization:
    """Test audio quality string normalization."""

    def test_normalize_quality_standard_values(self):
        """Test normalizing standard quality values."""
        assert normalize_quality_string("LOW") == "LOW"
        assert normalize_quality_string("HIGH") == "HIGH"
        assert normalize_quality_string("LOSSLESS") == "LOSSLESS"
        assert normalize_quality_string("HI_RES") == "HI_RES"
        assert normalize_quality_string("MASTER") == "MASTER"

    def test_normalize_quality_case_insensitive(self):
        """Test quality normalization is case insensitive."""
        assert normalize_quality_string("low") == "LOW"
        assert normalize_quality_string("High") == "HIGH"
        assert normalize_quality_string("lossless") == "LOSSLESS"

    def test_normalize_quality_mqa_mapping(self):
        """Test MQA quality mapping to MASTER."""
        assert normalize_quality_string("MQA") == "MASTER"
        assert normalize_quality_string("mqa") == "MASTER"

    def test_normalize_quality_unknown_values(self):
        """Test normalizing unknown quality values."""
        assert normalize_quality_string("UNKNOWN_QUALITY") == "UNKNOWN_QUALITY"
        assert normalize_quality_string("CUSTOM") == "CUSTOM"

    def test_normalize_quality_empty_input(self):
        """Test normalizing empty quality input."""
        assert normalize_quality_string("") == "UNKNOWN"
        assert normalize_quality_string(None) == "UNKNOWN"

    def test_normalize_quality_whitespace(self):
        """Test normalizing quality with whitespace."""
        assert (
            normalize_quality_string(" LOW ") == " LOW "
        )  # Returns original for unknown patterns


class TestSearchUrlBuilder:
    """Test search URL building functionality."""

    def test_build_search_url_basic(self):
        """Test building basic search URL."""
        url = build_search_url(
            "https://api.tidal.com/search",
            "test query",
            ["tracks"],
            limit=20,
            offset=0,
            country_code="US",
        )
        assert "query=test%20query" in url
        assert "limit=20" in url
        assert "offset=0" in url
        assert "types=TRACKS" in url
        assert "countryCode=US" in url

    def test_build_search_url_multiple_types(self):
        """Test building search URL with multiple content types."""
        url = build_search_url(
            "https://api.tidal.com/search",
            "test",
            ["tracks", "albums", "artists"],
            limit=10,
        )
        assert (
            "types=TRACKS%2CALBUMS%2CARTISTS" in url
            or "types=TRACKS,ALBUMS,ARTISTS" in url
        )

    def test_build_search_url_with_existing_params(self):
        """Test building search URL with existing parameters."""
        base_url = "https://api.tidal.com/search?api_key=123"
        url = build_search_url(base_url, "test", ["tracks"])
        assert "api_key=123" in url
        assert "query=test" in url
        assert "&" in url  # Should add params with &

    def test_build_search_url_empty_query(self):
        """Test building search URL with empty query."""
        url = build_search_url("https://api.tidal.com/search", "", ["tracks"])
        assert url == "https://api.tidal.com/search"

    def test_build_search_url_empty_types(self):
        """Test building search URL with empty content types."""
        url = build_search_url("https://api.tidal.com/search", "test", [])
        assert url == "https://api.tidal.com/search"

    def test_build_search_url_special_characters(self):
        """Test building search URL with special characters in query."""
        url = build_search_url(
            "https://api.tidal.com/search", "test & query with spaces", ["tracks"]
        )
        assert (
            "test%20%26%20query%20with%20spaces" in url
            or "test%20&%20query%20with%20spaces" in url
        )


class TestExplicitContentFilter:
    """Test explicit content filtering functionality."""

    def test_filter_explicit_content_allow_all(self):
        """Test filtering with explicit content allowed."""
        items = [
            {"title": "Clean Song", "explicit": False},
            {"title": "Explicit Song", "explicit": True},
            {"title": "Unknown", "explicit": None},
        ]
        result = filter_explicit_content(items, allow_explicit=True)
        assert len(result) == 3

    def test_filter_explicit_content_block_explicit(self):
        """Test filtering with explicit content blocked."""
        items = [
            {"title": "Clean Song", "explicit": False},
            {"title": "Explicit Song", "explicit": True},
            {"title": "No explicit field"},
        ]
        result = filter_explicit_content(items, allow_explicit=False)
        assert len(result) == 2
        assert all(not item.get("explicit", False) for item in result)

    def test_filter_explicit_content_empty_list(self):
        """Test filtering empty list."""
        result = filter_explicit_content([], allow_explicit=False)
        assert result == []

    def test_filter_explicit_content_missing_explicit_field(self):
        """Test filtering items without explicit field."""
        items = [{"title": "Song 1"}, {"title": "Song 2"}]
        result = filter_explicit_content(items, allow_explicit=False)
        assert len(result) == 2  # Should include items without explicit field


class TestArtistNameMerging:
    """Test artist name merging functionality."""

    def test_merge_artist_names_single_artist(self):
        """Test merging single artist name."""
        artists = [{"name": "Artist Name"}]
        result = merge_artist_names(artists)
        assert result == "Artist Name"

    def test_merge_artist_names_multiple_artists(self):
        """Test merging multiple artist names."""
        artists = [
            {"name": "Artist One"},
            {"name": "Artist Two"},
            {"name": "Artist Three"},
        ]
        result = merge_artist_names(artists)
        assert result == "Artist One, Artist Two, Artist Three"

    def test_merge_artist_names_empty_list(self):
        """Test merging empty artist list."""
        result = merge_artist_names([])
        assert result == "Unknown Artist"

    def test_merge_artist_names_missing_name_field(self):
        """Test merging artists with missing name fields."""
        artists = [
            {"name": "Valid Artist"},
            {"id": "123"},  # No name field
            {"name": ""},  # Empty name
            {"name": "   "},  # Whitespace only
        ]
        result = merge_artist_names(artists)
        assert result == "Valid Artist"

    def test_merge_artist_names_all_invalid(self):
        """Test merging artists with all invalid names."""
        artists = [{"id": "123"}, {"name": ""}, {"name": "   "}]
        result = merge_artist_names(artists)
        assert result == "Unknown Artist"

    def test_merge_artist_names_none_input(self):
        """Test merging None input."""
        result = merge_artist_names(None)
        assert result == "Unknown Artist"


class TestPlaylistStatsCalculation:
    """Test playlist statistics calculation functionality."""

    def test_calculate_playlist_stats_basic(self):
        """Test calculating basic playlist statistics."""
        tracks = [
            {
                "duration": 240,
                "explicit": False,
                "artists": [{"name": "Artist 1"}],
                "album": {"title": "Album 1"},
            },
            {
                "duration": 180,
                "explicit": True,
                "artists": [{"name": "Artist 2"}],
                "album": {"title": "Album 2"},
            },
        ]

        stats = calculate_playlist_stats(tracks)

        assert stats["total_tracks"] == 2
        assert stats["total_duration"] == 420
        assert stats["explicit_tracks"] == 1
        assert stats["unique_artists"] == 2
        assert stats["unique_albums"] == 2

    def test_calculate_playlist_stats_duplicate_artists_albums(self):
        """Test calculating stats with duplicate artists and albums."""
        tracks = [
            {
                "duration": 200,
                "explicit": False,
                "artists": [{"name": "Same Artist"}],
                "album": {"title": "Same Album"},
            },
            {
                "duration": 250,
                "explicit": False,
                "artists": [{"name": "Same Artist"}],
                "album": {"title": "Same Album"},
            },
            {
                "duration": 180,
                "explicit": True,
                "artists": [{"name": "Different Artist"}],
                "album": {"title": "Different Album"},
            },
        ]

        stats = calculate_playlist_stats(tracks)

        assert stats["total_tracks"] == 3
        assert stats["total_duration"] == 630
        assert stats["explicit_tracks"] == 1
        assert stats["unique_artists"] == 2  # Should deduplicate
        assert stats["unique_albums"] == 2  # Should deduplicate

    def test_calculate_playlist_stats_multiple_artists_per_track(self):
        """Test calculating stats with multiple artists per track."""
        tracks = [
            {
                "duration": 300,
                "explicit": False,
                "artists": [{"name": "Artist 1"}, {"name": "Artist 2"}],
                "album": {"title": "Collaboration Album"},
            }
        ]

        stats = calculate_playlist_stats(tracks)

        assert stats["total_tracks"] == 1
        assert stats["unique_artists"] == 2

    def test_calculate_playlist_stats_missing_fields(self):
        """Test calculating stats with missing fields."""
        tracks = [
            {
                "explicit": True
                # Missing duration, artists, album
            },
            {
                "duration": 200,
                "artists": "not_a_list",  # Invalid format
                "album": "not_a_dict",  # Invalid format
            },
        ]

        stats = calculate_playlist_stats(tracks)

        assert stats["total_tracks"] == 2
        assert stats["total_duration"] == 200  # Only one valid duration
        assert stats["explicit_tracks"] == 1
        assert stats["unique_artists"] == 0  # No valid artists
        assert stats["unique_albums"] == 0  # No valid albums

    def test_calculate_playlist_stats_empty_list(self):
        """Test calculating stats for empty track list."""
        stats = calculate_playlist_stats([])

        assert stats["total_tracks"] == 0
        assert stats["total_duration"] == 0
        assert stats["explicit_tracks"] == 0
        assert stats["unique_artists"] == 0
        assert stats["unique_albums"] == 0

    def test_calculate_playlist_stats_none_input(self):
        """Test calculating stats for None input."""
        stats = calculate_playlist_stats(None)

        assert stats["total_tracks"] == 0
        assert stats["total_duration"] == 0
        assert stats["explicit_tracks"] == 0
        assert stats["unique_artists"] == 0
        assert stats["unique_albums"] == 0

    def test_calculate_playlist_stats_invalid_artists_format(self):
        """Test calculating stats with invalid artists format."""
        tracks = [
            {
                "duration": 240,
                "explicit": False,
                "artists": [
                    "not_a_dict",  # Invalid artist format
                    {"id": "123"},  # Missing name
                    {"name": "Valid Artist"},
                ],
                "album": {"title": "Test Album"},
            }
        ]

        stats = calculate_playlist_stats(tracks)

        assert stats["unique_artists"] == 1  # Only valid artist counted

    def test_calculate_playlist_stats_invalid_album_format(self):
        """Test calculating stats with invalid album format."""
        tracks = [
            {
                "duration": 240,
                "explicit": False,
                "artists": [{"name": "Artist"}],
                "album": {"id": "123"},  # Missing title
            },
            {
                "duration": 180,
                "explicit": False,
                "artists": [{"name": "Artist"}],
                "album": "not_a_dict",  # Invalid format
            },
        ]

        stats = calculate_playlist_stats(tracks)

        assert stats["unique_albums"] == 0  # No valid albums
