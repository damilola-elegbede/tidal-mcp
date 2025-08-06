"""
Tests for Tidal Utility Functions

Comprehensive unit tests for utility functions including string sanitization,
duration formatting, validation, URL parsing, and data processing helpers.
"""

import pytest

from tidal_mcp.utils import (
    sanitize_query,
    format_duration,
    parse_duration,
    format_file_size,
    safe_get,
    truncate_text,
    validate_tidal_id,
    extract_tidal_id_from_url,
    normalize_quality_string,
    build_search_url,
    filter_explicit_content,
    merge_artist_names,
    calculate_playlist_stats,
)


class TestSanitizeQuery:
    """Test query sanitization function."""

    def test_sanitize_query_normal(self):
        """Test normal query sanitization."""
        assert sanitize_query("hello world") == "hello world"
        assert sanitize_query("The Beatles") == "The Beatles"
        assert sanitize_query("song-name") == "song-name"

    def test_sanitize_query_extra_whitespace(self):
        """Test query with extra whitespace."""
        assert sanitize_query("  hello   world  ") == "hello world"
        assert sanitize_query("\t\n  test  \r\n") == "test"
        assert sanitize_query("multiple    spaces") == "multiple spaces"

    def test_sanitize_query_special_characters(self):
        """Test query with special characters."""
        assert sanitize_query("song<script>") == "songscript"
        assert sanitize_query("track{with}brackets") == "trackwithbrackets"
        assert sanitize_query("album[name]") == "albumname"
        assert sanitize_query("artist\\name") == "artistname"

    def test_sanitize_query_edge_cases(self):
        """Test edge cases for query sanitization."""
        assert sanitize_query("") == ""
        assert sanitize_query(None) == ""
        assert sanitize_query("   ") == ""
        assert (
            sanitize_query("!@#$%^&*()") == "!@#$%^&*()"
        )  # These should be preserved

    def test_sanitize_query_unicode(self):
        """Test query with unicode characters."""
        assert sanitize_query("café música") == "café música"
        assert sanitize_query("ñiño español") == "ñiño español"
        assert sanitize_query("中文音乐") == "中文音乐"


class TestFormatDuration:
    """Test duration formatting function."""

    def test_format_duration_seconds_only(self):
        """Test duration formatting for seconds only."""
        assert format_duration(45) == "0:45"
        assert format_duration(9) == "0:09"
        assert format_duration(59) == "0:59"

    def test_format_duration_minutes_seconds(self):
        """Test duration formatting for minutes and seconds."""
        assert format_duration(65) == "1:05"
        assert format_duration(125) == "2:05"
        assert format_duration(245) == "4:05"
        assert format_duration(3599) == "59:59"

    def test_format_duration_hours(self):
        """Test duration formatting with hours."""
        assert format_duration(3600) == "1:00:00"
        assert format_duration(3665) == "1:01:05"
        assert format_duration(7322) == "2:02:02"
        assert format_duration(86400) == "24:00:00"

    def test_format_duration_edge_cases(self):
        """Test edge cases for duration formatting."""
        assert format_duration(0) == "0:00"
        assert format_duration(None) == "0:00"
        assert format_duration(-10) == "0:00"


class TestParseDuration:
    """Test duration parsing function."""

    def test_parse_duration_minutes_seconds(self):
        """Test parsing MM:SS format."""
        assert parse_duration("3:45") == 225
        assert parse_duration("0:30") == 30
        assert parse_duration("12:05") == 725
        assert parse_duration("59:59") == 3599

    def test_parse_duration_hours_minutes_seconds(self):
        """Test parsing HH:MM:SS format."""
        assert parse_duration("1:23:45") == 5025
        assert parse_duration("0:03:45") == 225
        assert parse_duration("2:00:00") == 7200
        assert parse_duration("24:59:59") == 89999

    def test_parse_duration_edge_cases(self):
        """Test edge cases for duration parsing."""
        assert parse_duration("") == 0
        assert parse_duration(None) == 0
        assert parse_duration("invalid") == 0
        assert parse_duration("1:2:3:4") == 0  # Too many parts
        assert parse_duration("1") == 0  # Too few parts

    def test_parse_duration_invalid_values(self):
        """Test parsing with invalid values."""
        assert parse_duration("abc:def") == 0
        assert parse_duration("1:abc") == 0
        assert parse_duration("1:-5") == 0


class TestFormatFileSize:
    """Test file size formatting function."""

    def test_format_file_size_bytes(self):
        """Test file size formatting in bytes."""
        assert format_file_size(0) == "0 B"
        assert format_file_size(512) == "512 B"
        assert format_file_size(1023) == "1023 B"

    def test_format_file_size_kilobytes(self):
        """Test file size formatting in kilobytes."""
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1536) == "1.5 KB"
        assert format_file_size(2048) == "2.0 KB"
        assert format_file_size(1048575) == "1024.0 KB"

    def test_format_file_size_megabytes(self):
        """Test file size formatting in megabytes."""
        assert format_file_size(1048576) == "1.0 MB"
        assert format_file_size(1572864) == "1.5 MB"
        assert format_file_size(10485760) == "10.0 MB"

    def test_format_file_size_gigabytes(self):
        """Test file size formatting in gigabytes."""
        assert format_file_size(1073741824) == "1.0 GB"
        assert format_file_size(2147483648) == "2.0 GB"

    def test_format_file_size_terabytes(self):
        """Test file size formatting in terabytes."""
        assert format_file_size(1099511627776) == "1.0 TB"


class TestSafeGet:
    """Test safe dictionary access function."""

    def test_safe_get_simple_key(self):
        """Test safe get with simple key."""
        data = {"name": "test", "value": 42}

        assert safe_get(data, "name") == "test"
        assert safe_get(data, "value") == 42
        assert safe_get(data, "missing") is None
        assert safe_get(data, "missing", "default") == "default"

    def test_safe_get_dot_notation(self):
        """Test safe get with dot notation."""
        data = {
            "user": {
                "profile": {"name": "John", "age": 30},
                "settings": {"theme": "dark"},
            }
        }

        assert safe_get(data, "user.profile.name") == "John"
        assert safe_get(data, "user.profile.age") == 30
        assert safe_get(data, "user.settings.theme") == "dark"
        assert safe_get(data, "user.profile.missing") is None
        assert safe_get(data, "user.missing.key") is None
        assert safe_get(data, "missing.user.name") is None

    def test_safe_get_edge_cases(self):
        """Test safe get edge cases."""
        # Non-dict input
        assert safe_get("not a dict", "key") is None
        assert safe_get(None, "key") is None
        assert safe_get([], "key") is None

        # Empty key
        data = {"test": "value"}
        assert safe_get(data, "") is None

        # None values in path
        data = {"user": None}
        assert safe_get(data, "user.name") is None


class TestTruncateText:
    """Test text truncation function."""

    def test_truncate_text_normal(self):
        """Test normal text truncation."""
        text = "This is a long text that needs to be truncated"

        assert truncate_text(text, 20) == "This is a long te..."
        assert truncate_text(text, 10) == "This is..."
        assert truncate_text(text, 50) == text  # No truncation needed

    def test_truncate_text_custom_suffix(self):
        """Test text truncation with custom suffix."""
        text = "Long text here"

        assert truncate_text(text, 10, " [more]") == "Lon [more]"
        assert truncate_text(text, 8, ">>") == "Long t>>"

    def test_truncate_text_edge_cases(self):
        """Test text truncation edge cases."""
        # Empty or None text
        assert truncate_text("", 10) == ""
        assert truncate_text(None, 10) == ""

        # Suffix longer than max_length
        assert truncate_text("test", 5, "very long suffix") == "test"

        # Exact length
        assert truncate_text("12345", 5) == "12345"


class TestValidateTidalId:
    """Test Tidal ID validation function."""

    def test_validate_tidal_id_valid(self):
        """Test valid Tidal IDs."""
        assert validate_tidal_id("123456") is True
        assert validate_tidal_id("1") is True
        assert validate_tidal_id("999999999") is True
        assert validate_tidal_id("0") is True

    def test_validate_tidal_id_invalid(self):
        """Test invalid Tidal IDs."""
        assert validate_tidal_id("") is False
        assert validate_tidal_id(None) is False
        assert validate_tidal_id("abc123") is False
        assert validate_tidal_id("123-456") is False
        assert validate_tidal_id("123.456") is False
        assert validate_tidal_id("123 456") is False


class TestExtractTidalIdFromUrl:
    """Test Tidal ID extraction from URLs."""

    def test_extract_track_ids(self):
        """Test extracting track IDs from URLs."""
        urls = [
            "https://tidal.com/browse/track/123456",
            "https://tidal.com/track/789012",
            "http://tidal.com/browse/track/345678",
        ]

        assert extract_tidal_id_from_url(urls[0]) == "123456"
        assert extract_tidal_id_from_url(urls[1]) == "789012"
        assert extract_tidal_id_from_url(urls[2]) == "345678"

    def test_extract_album_ids(self):
        """Test extracting album IDs from URLs."""
        urls = [
            "https://tidal.com/browse/album/456789",
            "https://tidal.com/album/123890",
        ]

        assert extract_tidal_id_from_url(urls[0]) == "456789"
        assert extract_tidal_id_from_url(urls[1]) == "123890"

    def test_extract_artist_ids(self):
        """Test extracting artist IDs from URLs."""
        urls = [
            "https://tidal.com/browse/artist/789123",
            "https://tidal.com/artist/456987",
        ]

        assert extract_tidal_id_from_url(urls[0]) == "789123"
        assert extract_tidal_id_from_url(urls[1]) == "456987"

    def test_extract_playlist_ids(self):
        """Test extracting playlist IDs from URLs."""
        playlist_uuid1 = "550e8400-e29b-41d4-a716-446655440000"
        playlist_uuid2 = "123e4567-e89b-12d3-a456-426614174000"
        urls = [
            f"https://tidal.com/browse/playlist/{playlist_uuid1}",
            f"https://tidal.com/playlist/{playlist_uuid2}",
        ]

        assert extract_tidal_id_from_url(urls[0]) == playlist_uuid1
        assert extract_tidal_id_from_url(urls[1]) == playlist_uuid2

    def test_extract_id_invalid_urls(self):
        """Test ID extraction from invalid URLs."""
        invalid_urls = [
            "",
            None,
            "https://spotify.com/track/123",
            "https://tidal.com/something/else",
            "not a url",
            "https://tidal.com/browse/",
        ]

        for url in invalid_urls:
            assert extract_tidal_id_from_url(url) is None


class TestNormalizeQualityString:
    """Test audio quality normalization function."""

    def test_normalize_quality_standard(self):
        """Test normalizing standard quality strings."""
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
        """Test MQA to MASTER mapping."""
        assert normalize_quality_string("MQA") == "MASTER"
        assert normalize_quality_string("mqa") == "MASTER"

    def test_normalize_quality_unknown(self):
        """Test unknown quality strings."""
        assert normalize_quality_string("") == "UNKNOWN"
        assert normalize_quality_string(None) == "UNKNOWN"
        assert normalize_quality_string("CUSTOM") == "CUSTOM"
        assert normalize_quality_string("WEIRD_QUALITY") == "WEIRD_QUALITY"


class TestBuildSearchUrl:
    """Test search URL building function."""

    def test_build_search_url_basic(self):
        """Test basic search URL building."""
        url = build_search_url(
            "https://api.tidal.com/v1/search",
            "test query",
            ["tracks"],
            limit=20,
            offset=0,
            country_code="US",
        )

        assert "https://api.tidal.com/v1/search?" in url
        assert "query=test%20query" in url
        assert "limit=20" in url
        assert "offset=0" in url
        assert "types=TRACKS" in url
        assert "countryCode=US" in url

    def test_build_search_url_multiple_types(self):
        """Test search URL with multiple content types."""
        url = build_search_url(
            "https://api.tidal.com/v1/search",
            "artist name",
            ["tracks", "albums", "artists"],
            limit=50,
            offset=10,
        )

        assert "types=TRACKS,ALBUMS,ARTISTS" in url
        assert "limit=50" in url
        assert "offset=10" in url

    def test_build_search_url_special_characters(self):
        """Test search URL with special characters in query."""
        url = build_search_url(
            "https://api.tidal.com/v1/search", "artist & song", ["tracks"]
        )

        assert "query=artist%20%26%20song" in url

    def test_build_search_url_edge_cases(self):
        """Test search URL building edge cases."""
        # Empty query
        url = build_search_url("https://api.com", "", ["tracks"])
        assert url == "https://api.com"

        # Empty content types
        url = build_search_url("https://api.com", "query", [])
        assert url == "https://api.com"

        # URL with existing query params
        url = build_search_url(
            "https://api.com?existing=param", "query", ["tracks"]
        )
        assert "existing=param&query=" in url


class TestFilterExplicitContent:
    """Test explicit content filtering function."""

    def test_filter_explicit_allow_all(self):
        """Test filtering when allowing explicit content."""
        items = [
            {"title": "Clean Song", "explicit": False},
            {"title": "Explicit Song", "explicit": True},
            {"title": "No Explicit Field"},
        ]

        result = filter_explicit_content(items, allow_explicit=True)
        assert len(result) == 3
        assert result == items

    def test_filter_explicit_block_explicit(self):
        """Test filtering when blocking explicit content."""
        items = [
            {"title": "Clean Song", "explicit": False},
            {"title": "Explicit Song", "explicit": True},
            {"title": "No Explicit Field"},
            {"title": "Another Clean", "explicit": False},
        ]

        result = filter_explicit_content(items, allow_explicit=False)
        assert len(result) == 3
        assert all(not item.get("explicit", False) for item in result)

    def test_filter_explicit_empty_list(self):
        """Test filtering empty list."""
        result = filter_explicit_content([], allow_explicit=False)
        assert result == []


class TestMergeArtistNames:
    """Test artist name merging function."""

    def test_merge_artist_names_single(self):
        """Test merging single artist name."""
        artists = [{"name": "Solo Artist"}]
        assert merge_artist_names(artists) == "Solo Artist"

    def test_merge_artist_names_multiple(self):
        """Test merging multiple artist names."""
        artists = [
            {"name": "First Artist"},
            {"name": "Second Artist"},
            {"name": "Third Artist"},
        ]

        assert (
            merge_artist_names(artists)
            == "First Artist, Second Artist, Third Artist"
        )

    def test_merge_artist_names_with_empty_names(self):
        """Test merging artists with empty names."""
        artists = [
            {"name": "Valid Artist"},
            {"name": ""},
            {"name": "   "},  # Whitespace only
            {"name": "Another Valid"},
        ]

        result = merge_artist_names(artists)
        assert result == "Valid Artist, Another Valid"

    def test_merge_artist_names_edge_cases(self):
        """Test artist name merging edge cases."""
        # Empty list
        assert merge_artist_names([]) == "Unknown Artist"

        # No valid names
        artists = [{"name": ""}, {"name": "   "}, {}]
        assert merge_artist_names(artists) == "Unknown Artist"

        # Missing name field
        artists = [{"id": 1}, {"title": "Not name"}]
        assert merge_artist_names(artists) == "Unknown Artist"


class TestCalculatePlaylistStats:
    """Test playlist statistics calculation function."""

    def test_calculate_playlist_stats_basic(self):
        """Test basic playlist statistics calculation."""
        tracks = [
            {
                "duration": 200,
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
            {
                "duration": 220,
                "explicit": False,
                "artists": [{"name": "Artist 1"}],  # Same artist
                "album": {"title": "Album 1"},  # Same album
            },
        ]

        stats = calculate_playlist_stats(tracks)

        assert stats["total_tracks"] == 3
        assert stats["total_duration"] == 600  # 200 + 180 + 220
        assert stats["explicit_tracks"] == 1
        assert stats["unique_artists"] == 2  # Artist 1, Artist 2
        assert stats["unique_albums"] == 2  # Album 1, Album 2

    def test_calculate_playlist_stats_multiple_artists_per_track(self):
        """Test stats with multiple artists per track."""
        tracks = [
            {
                "duration": 200,
                "explicit": False,
                "artists": [
                    {"name": "Main Artist"},
                    {"name": "Featured Artist"},
                ],
                "album": {"title": "Collab Album"},
            }
        ]

        stats = calculate_playlist_stats(tracks)

        assert stats["total_tracks"] == 1
        assert stats["unique_artists"] == 2
        assert stats["unique_albums"] == 1

    def test_calculate_playlist_stats_missing_fields(self):
        """Test stats calculation with missing fields."""
        tracks = [
            {"duration": 150},  # No explicit, artists, or album
            {
                "explicit": True,
                "artists": "not a list",  # Invalid format
                "album": "not a dict",  # Invalid format
            },
            {
                "duration": 0,  # Zero duration
                "artists": [{"not_name": "Invalid"}],  # Missing name field
                "album": {"not_title": "Invalid"},  # Missing title field
            },
        ]

        stats = calculate_playlist_stats(tracks)

        assert stats["total_tracks"] == 3
        assert (
            stats["total_duration"] == 150
        )  # Only first track has valid duration
        assert stats["explicit_tracks"] == 1  # Only second track is explicit
        assert stats["unique_artists"] == 0  # No valid artist names
        assert stats["unique_albums"] == 0  # No valid album titles

    def test_calculate_playlist_stats_empty(self):
        """Test stats calculation for empty playlist."""
        stats = calculate_playlist_stats([])

        assert stats["total_tracks"] == 0
        assert stats["total_duration"] == 0
        assert stats["explicit_tracks"] == 0
        assert stats["unique_artists"] == 0
        assert stats["unique_albums"] == 0


class TestUtilsIntegration:
    """Test integration between utility functions."""

    def test_duration_round_trip(self):
        """Test duration formatting and parsing round trip."""
        original_seconds = 3665  # 1:01:05
        formatted = format_duration(original_seconds)
        parsed = parse_duration(formatted)

        assert parsed == original_seconds

    def test_query_and_url_building(self):
        """Test query sanitization with URL building."""
        raw_query = "  artist & song  "
        sanitized = sanitize_query(raw_query)
        url = build_search_url("https://api.com", sanitized, ["tracks"])

        assert "artist%20%26%20song" in url

    def test_safe_get_with_complex_data(self):
        """Test safe_get with complex nested data."""
        complex_data = {
            "playlist": {
                "tracks": [
                    {"artist": {"name": "Test Artist"}, "duration": 245}
                ],
                "stats": calculate_playlist_stats(
                    [{"duration": 200, "artists": [{"name": "Artist"}]}]
                ),
            }
        }

        # Test nested dict access

        tracks = safe_get(complex_data, "playlist.tracks")
        assert len(tracks) == 1

        stats = safe_get(complex_data, "playlist.stats")
        assert stats["total_tracks"] == 1


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
