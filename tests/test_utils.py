"""
Unit tests for utils.py - Input validation, sanitization, format conversion.

Tests cover:
- Input validation functions
- Sanitization utilities
- Format conversion accuracy
- Edge cases (empty/null inputs)
- URL building and parsing
- Text processing functions
- Data transformation utilities

All tests are fast, isolated, and focus on utility function correctness.
"""


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
        query = "test search query"
        result = sanitize_query(query)

        assert result == "test search query"

    def test_sanitize_query_with_extra_whitespace(self):
        """Test sanitization with extra whitespace."""
        query = "  test   search    query  "
        result = sanitize_query(query)

        assert result == "test search query"

    def test_sanitize_query_with_special_characters(self):
        """Test sanitization with potentially problematic characters."""
        query = "test<search>query{with}[brackets]\\backslash"
        result = sanitize_query(query)

        assert result == "testsearchquerywithbracketsbackslash"

    def test_sanitize_query_with_newlines_and_tabs(self):
        """Test sanitization with newlines and tabs."""
        query = "test\nsearch\tquery"
        result = sanitize_query(query)

        assert result == "test search query"

    def test_sanitize_query_empty_string(self):
        """Test sanitization with empty string."""
        result = sanitize_query("")

        assert result == ""

    def test_sanitize_query_none(self):
        """Test sanitization with None input."""
        result = sanitize_query(None)

        assert result == ""

    def test_sanitize_query_non_string(self):
        """Test sanitization with non-string input."""
        result = sanitize_query(123)

        assert result == ""

    def test_sanitize_query_only_whitespace(self):
        """Test sanitization with only whitespace."""
        query = "   \t\n   "
        result = sanitize_query(query)

        assert result == ""

    def test_sanitize_query_mixed_problematic_chars(self):
        """Test sanitization with mixed problematic characters."""
        query = "   test<>{}[]\\  query   "
        result = sanitize_query(query)

        assert result == "test query"


class TestDurationFormatting:
    """Test duration formatting functionality."""

    def test_format_duration_minutes_seconds(self):
        """Test duration formatting for minutes and seconds."""
        result = format_duration(245)  # 4:05

        assert result == "4:05"

    def test_format_duration_hours_minutes_seconds(self):
        """Test duration formatting for hours, minutes, and seconds."""
        result = format_duration(7265)  # 2:01:05

        assert result == "2:01:05"

    def test_format_duration_zero(self):
        """Test duration formatting for zero."""
        result = format_duration(0)

        assert result == "0:00"

    def test_format_duration_negative(self):
        """Test duration formatting for negative values."""
        result = format_duration(-100)

        assert result == "0:00"

    def test_format_duration_float(self):
        """Test duration formatting for float values."""
        result = format_duration(125.5)  # Should handle float

        assert result == "2:05"

    def test_format_duration_none(self):
        """Test duration formatting for None."""
        result = format_duration(None)

        assert result == "0:00"

    def test_format_duration_invalid_type(self):
        """Test duration formatting for invalid types."""
        result = format_duration("invalid")

        assert result == "0:00"

    def test_format_duration_exact_hour(self):
        """Test duration formatting for exact hour."""
        result = format_duration(3600)  # 1:00:00

        assert result == "1:00:00"

    def test_format_duration_large_value(self):
        """Test duration formatting for large values."""
        result = format_duration(359999)  # 99:59:59

        assert result == "99:59:59"


class TestDurationParsing:
    """Test duration parsing functionality."""

    def test_parse_duration_mm_ss(self):
        """Test parsing MM:SS format."""
        result = parse_duration("4:05")

        assert result == 245

    def test_parse_duration_hh_mm_ss(self):
        """Test parsing HH:MM:SS format."""
        result = parse_duration("2:01:05")

        assert result == 7265

    def test_parse_duration_single_digit_minutes(self):
        """Test parsing with single digit minutes."""
        result = parse_duration("1:30")

        assert result == 90

    def test_parse_duration_zero_minutes(self):
        """Test parsing with zero minutes."""
        result = parse_duration("0:45")

        assert result == 45

    def test_parse_duration_empty_string(self):
        """Test parsing empty string."""
        result = parse_duration("")

        assert result == 0

    def test_parse_duration_none(self):
        """Test parsing None."""
        result = parse_duration(None)

        assert result == 0

    def test_parse_duration_invalid_format(self):
        """Test parsing invalid format."""
        result = parse_duration("invalid")

        assert result == 0

    def test_parse_duration_too_many_parts(self):
        """Test parsing with too many time parts."""
        result = parse_duration("1:2:3:4")

        assert result == 0

    def test_parse_duration_negative_values(self):
        """Test parsing with negative values."""
        result = parse_duration("-1:30")

        assert result == 0

    def test_parse_duration_non_numeric(self):
        """Test parsing with non-numeric values."""
        result = parse_duration("a:b")

        assert result == 0


class TestFileSizeFormatting:
    """Test file size formatting functionality."""

    def test_format_file_size_bytes(self):
        """Test file size formatting for bytes."""
        result = format_file_size(512)

        assert result == "512 B"

    def test_format_file_size_kilobytes(self):
        """Test file size formatting for kilobytes."""
        result = format_file_size(2048)

        assert result == "2.0 KB"

    def test_format_file_size_megabytes(self):
        """Test file size formatting for megabytes."""
        result = format_file_size(5242880)  # 5 MB

        assert result == "5.0 MB"

    def test_format_file_size_gigabytes(self):
        """Test file size formatting for gigabytes."""
        result = format_file_size(3221225472)  # 3 GB

        assert result == "3.0 GB"

    def test_format_file_size_zero(self):
        """Test file size formatting for zero."""
        result = format_file_size(0)

        assert result == "0 B"

    def test_format_file_size_exact_boundary(self):
        """Test file size formatting at exact unit boundaries."""
        result = format_file_size(1024)

        assert result == "1.0 KB"

    def test_format_file_size_fractional(self):
        """Test file size formatting with fractional values."""
        result = format_file_size(1536)  # 1.5 KB

        assert result == "1.5 KB"

    def test_format_file_size_large_value(self):
        """Test file size formatting for very large values."""
        result = format_file_size(1099511627776)  # 1 TB

        assert result == "1.0 TB"


class TestSafeGet:
    """Test safe dictionary access functionality."""

    def test_safe_get_simple_key(self):
        """Test safe_get with simple key."""
        data = {"name": "test", "value": 42}

        assert safe_get(data, "name") == "test"
        assert safe_get(data, "value") == 42

    def test_safe_get_nested_key(self):
        """Test safe_get with dot notation for nested keys."""
        data = {
            "user": {
                "profile": {
                    "name": "John Doe",
                    "age": 30
                }
            }
        }

        assert safe_get(data, "user.profile.name") == "John Doe"
        assert safe_get(data, "user.profile.age") == 30

    def test_safe_get_missing_key(self):
        """Test safe_get with missing key."""
        data = {"name": "test"}

        assert safe_get(data, "missing") is None
        assert safe_get(data, "missing", "default") == "default"

    def test_safe_get_missing_nested_key(self):
        """Test safe_get with missing nested key."""
        data = {"user": {"name": "test"}}

        assert safe_get(data, "user.missing") is None
        assert safe_get(data, "user.missing.deep", "default") == "default"

    def test_safe_get_non_dict_input(self):
        """Test safe_get with non-dictionary input."""
        assert safe_get("not a dict", "key") is None
        assert safe_get(None, "key", "default") == "default"

    def test_safe_get_non_dict_intermediate(self):
        """Test safe_get when intermediate value is not a dict."""
        data = {"user": "not_a_dict"}

        assert safe_get(data, "user.name") is None

    def test_safe_get_empty_key(self):
        """Test safe_get with empty key."""
        data = {"": "empty_key_value"}

        assert safe_get(data, "") == "empty_key_value"

    def test_safe_get_complex_nested_structure(self):
        """Test safe_get with complex nested structure."""
        data = {
            "api": {
                "response": {
                    "data": {
                        "tracks": [
                            {"id": 1, "name": "Track 1"},
                            {"id": 2, "name": "Track 2"}
                        ]
                    }
                }
            }
        }

        assert safe_get(data, "api.response.data") is not None
        # Note: safe_get doesn't handle array indexing
        assert safe_get(data, "api.response.data.tracks.0") is None


class TestTextTruncation:
    """Test text truncation functionality."""

    def test_truncate_text_basic(self):
        """Test basic text truncation."""
        text = "This is a long text that should be truncated"
        result = truncate_text(text, 20)

        assert result == "This is a long te..."
        assert len(result) == 20

    def test_truncate_text_exact_length(self):
        """Test truncation when text is exactly max length."""
        text = "Exactly twenty chars"
        result = truncate_text(text, 20)

        assert result == "Exactly twenty chars"

    def test_truncate_text_shorter_than_max(self):
        """Test truncation when text is shorter than max length."""
        text = "Short text"
        result = truncate_text(text, 20)

        assert result == "Short text"

    def test_truncate_text_custom_suffix(self):
        """Test truncation with custom suffix."""
        text = "This is a long text that should be truncated"
        result = truncate_text(text, 20, " [more]")

        assert result == "This is a lon [more]"
        assert len(result) == 20

    def test_truncate_text_suffix_too_long(self):
        """Test truncation when suffix is too long."""
        text = "This is a long text"
        result = truncate_text(text, 10, "very_long_suffix")

        assert result == "This is a "
        assert len(result) == 10

    def test_truncate_text_none_input(self):
        """Test truncation with None input."""
        result = truncate_text(None, 10)

        assert result == ""

    def test_truncate_text_empty_string(self):
        """Test truncation with empty string."""
        result = truncate_text("", 10)

        assert result == ""

    def test_truncate_text_zero_max_length(self):
        """Test truncation with zero max length."""
        text = "Some text"
        result = truncate_text(text, 0)

        assert result == ""


class TestTidalIdValidation:
    """Test Tidal ID validation functionality."""

    def test_validate_tidal_id_valid_numeric(self):
        """Test validation with valid numeric Tidal ID."""
        assert validate_tidal_id("12345") is True
        assert validate_tidal_id("987654321") is True

    def test_validate_tidal_id_invalid_non_numeric(self):
        """Test validation with non-numeric ID."""
        assert validate_tidal_id("abc123") is False
        assert validate_tidal_id("12345abc") is False

    def test_validate_tidal_id_empty_string(self):
        """Test validation with empty string."""
        assert validate_tidal_id("") is False

    def test_validate_tidal_id_none(self):
        """Test validation with None."""
        assert validate_tidal_id(None) is False

    def test_validate_tidal_id_non_string(self):
        """Test validation with non-string input."""
        assert validate_tidal_id(12345) is False
        assert validate_tidal_id([]) is False

    def test_validate_tidal_id_with_spaces(self):
        """Test validation with spaces."""
        assert validate_tidal_id("123 456") is False
        assert validate_tidal_id(" 12345 ") is False

    def test_validate_tidal_id_zero(self):
        """Test validation with zero."""
        assert validate_tidal_id("0") is True

    def test_validate_tidal_id_leading_zeros(self):
        """Test validation with leading zeros."""
        assert validate_tidal_id("00012345") is True


class TestUrlIdExtraction:
    """Test URL ID extraction functionality."""

    def test_extract_tidal_id_from_track_url(self):
        """Test ID extraction from track URL."""
        url = "https://tidal.com/browse/track/123456"
        result = extract_tidal_id_from_url(url)

        assert result == "123456"

    def test_extract_tidal_id_from_album_url(self):
        """Test ID extraction from album URL."""
        url = "https://tidal.com/browse/album/789012"
        result = extract_tidal_id_from_url(url)

        assert result == "789012"

    def test_extract_tidal_id_from_artist_url(self):
        """Test ID extraction from artist URL."""
        url = "https://tidal.com/browse/artist/345678"
        result = extract_tidal_id_from_url(url)

        assert result == "345678"

    def test_extract_tidal_id_from_playlist_url(self):
        """Test ID extraction from playlist URL."""
        url = "https://tidal.com/browse/playlist/550e8400-e29b-41d4-a716-446655440000"
        result = extract_tidal_id_from_url(url)

        assert result == "550e8400-e29b-41d4-a716-446655440000"

    def test_extract_tidal_id_from_short_track_url(self):
        """Test ID extraction from short track URL."""
        url = "https://tidal.com/track/123456"
        result = extract_tidal_id_from_url(url)

        assert result == "123456"

    def test_extract_tidal_id_from_case_insensitive_url(self):
        """Test ID extraction with case insensitive matching."""
        url = "https://TIDAL.COM/BROWSE/TRACK/123456"
        result = extract_tidal_id_from_url(url)

        assert result == "123456"

    def test_extract_tidal_id_from_invalid_url(self):
        """Test ID extraction from invalid URL."""
        url = "https://spotify.com/track/123456"
        result = extract_tidal_id_from_url(url)

        assert result is None

    def test_extract_tidal_id_from_empty_url(self):
        """Test ID extraction from empty URL."""
        result = extract_tidal_id_from_url("")

        assert result is None

    def test_extract_tidal_id_from_none_url(self):
        """Test ID extraction from None URL."""
        result = extract_tidal_id_from_url(None)

        assert result is None

    def test_extract_tidal_id_from_malformed_url(self):
        """Test ID extraction from malformed URL."""
        url = "tidal.com/browse/track/"
        result = extract_tidal_id_from_url(url)

        assert result is None


class TestQualityNormalization:
    """Test quality string normalization functionality."""

    def test_normalize_quality_string_lossless(self):
        """Test normalization of lossless quality."""
        assert normalize_quality_string("lossless") == "LOSSLESS"
        assert normalize_quality_string("LOSSLESS") == "LOSSLESS"

    def test_normalize_quality_string_high(self):
        """Test normalization of high quality."""
        assert normalize_quality_string("high") == "HIGH"
        assert normalize_quality_string("HIGH") == "HIGH"

    def test_normalize_quality_string_low(self):
        """Test normalization of low quality."""
        assert normalize_quality_string("low") == "LOW"
        assert normalize_quality_string("LOW") == "LOW"

    def test_normalize_quality_string_master(self):
        """Test normalization of master/MQA quality."""
        assert normalize_quality_string("master") == "MASTER"
        assert normalize_quality_string("MASTER") == "MASTER"
        assert normalize_quality_string("mqa") == "MASTER"
        assert normalize_quality_string("MQA") == "MASTER"

    def test_normalize_quality_string_hi_res(self):
        """Test normalization of hi-res quality."""
        assert normalize_quality_string("hi_res") == "HI_RES"
        assert normalize_quality_string("HI_RES") == "HI_RES"

    def test_normalize_quality_string_unknown(self):
        """Test normalization of unknown quality."""
        assert normalize_quality_string("unknown_quality") == "UNKNOWN_QUALITY"
        assert normalize_quality_string("custom") == "CUSTOM"

    def test_normalize_quality_string_empty(self):
        """Test normalization of empty quality."""
        assert normalize_quality_string("") == "UNKNOWN"
        assert normalize_quality_string(None) == "UNKNOWN"


class TestSearchUrlBuilding:
    """Test search URL building functionality."""

    def test_build_search_url_basic(self):
        """Test basic search URL building."""
        url = build_search_url(
            "https://api.tidal.com/v1/search",
            "test query",
            ["tracks", "albums"],
            limit=20,
            offset=0,
            country_code="US"
        )

        assert "https://api.tidal.com/v1/search?" in url
        assert "query=test%20query" in url
        assert "limit=20" in url
        assert "offset=0" in url
        assert "types=TRACKS,ALBUMS" in url
        assert "countryCode=US" in url

    def test_build_search_url_with_existing_params(self):
        """Test search URL building with existing parameters."""
        url = build_search_url(
            "https://api.tidal.com/v1/search?existing=param",
            "test query",
            ["tracks"],
            limit=10
        )

        assert "existing=param" in url
        assert "query=test%20query" in url
        assert url.count("?") == 1

    def test_build_search_url_empty_query(self):
        """Test search URL building with empty query."""
        url = build_search_url(
            "https://api.tidal.com/v1/search",
            "",
            ["tracks"]
        )

        assert url == "https://api.tidal.com/v1/search"

    def test_build_search_url_empty_content_types(self):
        """Test search URL building with empty content types."""
        url = build_search_url(
            "https://api.tidal.com/v1/search",
            "test query",
            []
        )

        assert url == "https://api.tidal.com/v1/search"

    def test_build_search_url_special_characters_in_query(self):
        """Test search URL building with special characters in query."""
        url = build_search_url(
            "https://api.tidal.com/v1/search",
            "test & query + special",
            ["tracks"]
        )

        assert "query=test%20%26%20query%20%2B%20special" in url


class TestContentFiltering:
    """Test content filtering functionality."""

    def test_filter_explicit_content_allow_all(self):
        """Test content filtering when allowing explicit content."""
        items = [
            {"id": 1, "title": "Clean Song", "explicit": False},
            {"id": 2, "title": "Explicit Song", "explicit": True},
            {"id": 3, "title": "No Explicit Field"}
        ]

        result = filter_explicit_content(items, allow_explicit=True)

        assert len(result) == 3
        assert result == items

    def test_filter_explicit_content_block_explicit(self):
        """Test content filtering when blocking explicit content."""
        items = [
            {"id": 1, "title": "Clean Song", "explicit": False},
            {"id": 2, "title": "Explicit Song", "explicit": True},
            {"id": 3, "title": "No Explicit Field"}
        ]

        result = filter_explicit_content(items, allow_explicit=False)

        assert len(result) == 2
        assert all(not item.get("explicit", False) for item in result)

    def test_filter_explicit_content_empty_list(self):
        """Test content filtering with empty list."""
        result = filter_explicit_content([], allow_explicit=False)

        assert result == []

    def test_filter_explicit_content_all_explicit(self):
        """Test content filtering when all items are explicit."""
        items = [
            {"id": 1, "title": "Explicit Song 1", "explicit": True},
            {"id": 2, "title": "Explicit Song 2", "explicit": True}
        ]

        result = filter_explicit_content(items, allow_explicit=False)

        assert result == []


class TestArtistNameMerging:
    """Test artist name merging functionality."""

    def test_merge_artist_names_multiple(self):
        """Test merging multiple artist names."""
        artists = [
            {"name": "Artist One"},
            {"name": "Artist Two"},
            {"name": "Artist Three"}
        ]

        result = merge_artist_names(artists)

        assert result == "Artist One, Artist Two, Artist Three"

    def test_merge_artist_names_single(self):
        """Test merging single artist name."""
        artists = [{"name": "Solo Artist"}]

        result = merge_artist_names(artists)

        assert result == "Solo Artist"

    def test_merge_artist_names_empty_list(self):
        """Test merging empty artist list."""
        result = merge_artist_names([])

        assert result == "Unknown Artist"

    def test_merge_artist_names_with_empty_names(self):
        """Test merging artists with empty names."""
        artists = [
            {"name": "Valid Artist"},
            {"name": ""},
            {"name": "  "},
            {"name": "Another Artist"}
        ]

        result = merge_artist_names(artists)

        assert result == "Valid Artist, Another Artist"

    def test_merge_artist_names_missing_name_field(self):
        """Test merging artists with missing name field."""
        artists = [
            {"name": "Valid Artist"},
            {"id": 123},  # Missing name field
            {"name": "Another Artist"}
        ]

        result = merge_artist_names(artists)

        assert result == "Valid Artist, Another Artist"

    def test_merge_artist_names_all_invalid(self):
        """Test merging when all artist names are invalid."""
        artists = [
            {"name": ""},
            {"id": 123},
            {"name": "   "}
        ]

        result = merge_artist_names(artists)

        assert result == "Unknown Artist"


class TestPlaylistStats:
    """Test playlist statistics calculation functionality."""

    def test_calculate_playlist_stats_basic(self):
        """Test basic playlist statistics calculation."""
        tracks = [
            {
                "duration": 180,
                "explicit": False,
                "artists": [{"name": "Artist 1"}],
                "album": {"title": "Album 1"}
            },
            {
                "duration": 240,
                "explicit": True,
                "artists": [{"name": "Artist 2"}],
                "album": {"title": "Album 2"}
            },
            {
                "duration": 200,
                "explicit": False,
                "artists": [{"name": "Artist 1"}],
                "album": {"title": "Album 1"}
            }
        ]

        stats = calculate_playlist_stats(tracks)

        assert stats["total_tracks"] == 3
        assert stats["total_duration"] == 620
        assert stats["explicit_tracks"] == 1
        assert stats["unique_artists"] == 2
        assert stats["unique_albums"] == 2

    def test_calculate_playlist_stats_empty_list(self):
        """Test playlist statistics for empty track list."""
        stats = calculate_playlist_stats([])

        expected = {
            "total_tracks": 0,
            "total_duration": 0,
            "explicit_tracks": 0,
            "unique_artists": 0,
            "unique_albums": 0
        }

        assert stats == expected

    def test_calculate_playlist_stats_missing_fields(self):
        """Test playlist statistics with missing fields."""
        tracks = [
            {
                "artists": [{"name": "Artist 1"}]
                # Missing duration, explicit, album
            },
            {
                "duration": 180,
                "explicit": True
                # Missing artists, album
            }
        ]

        stats = calculate_playlist_stats(tracks)

        assert stats["total_tracks"] == 2
        assert stats["total_duration"] == 180
        assert stats["explicit_tracks"] == 1
        assert stats["unique_artists"] == 1
        assert stats["unique_albums"] == 0

    def test_calculate_playlist_stats_multiple_artists_per_track(self):
        """Test playlist statistics with multiple artists per track."""
        tracks = [
            {
                "duration": 180,
                "explicit": False,
                "artists": [
                    {"name": "Artist 1"},
                    {"name": "Artist 2"}
                ],
                "album": {"title": "Collaboration Album"}
            }
        ]

        stats = calculate_playlist_stats(tracks)

        assert stats["total_tracks"] == 1
        assert stats["unique_artists"] == 2
        assert stats["unique_albums"] == 1

    def test_calculate_playlist_stats_invalid_artist_data(self):
        """Test playlist statistics with invalid artist data."""
        tracks = [
            {
                "duration": 180,
                "explicit": False,
                "artists": "not_a_list",  # Invalid artists data
                "album": {"title": "Album 1"}
            },
            {
                "duration": 200,
                "explicit": False,
                "artists": [
                    {"id": 123},  # Missing name field
                    {"name": "Valid Artist"}
                ],
                "album": {"title": "Album 2"}
            }
        ]

        stats = calculate_playlist_stats(tracks)

        assert stats["total_tracks"] == 2
        assert stats["unique_artists"] == 1  # Only "Valid Artist"
        assert stats["unique_albums"] == 2

    def test_calculate_playlist_stats_invalid_album_data(self):
        """Test playlist statistics with invalid album data."""
        tracks = [
            {
                "duration": 180,
                "artists": [{"name": "Artist 1"}],
                "album": "not_a_dict"  # Invalid album data
            },
            {
                "duration": 200,
                "artists": [{"name": "Artist 2"}],
                "album": {"id": 123}  # Missing title field
            }
        ]

        stats = calculate_playlist_stats(tracks)

        assert stats["total_tracks"] == 2
        assert stats["unique_artists"] == 2
        assert stats["unique_albums"] == 0  # No valid album titles


class TestUtilsEdgeCases:
    """Test edge cases and error handling for utility functions."""

    def test_format_functions_with_extreme_values(self):
        """Test format functions with extreme values."""
        # Very large duration
        large_duration = 999999999
        result = format_duration(large_duration)
        assert isinstance(result, str)
        assert ":" in result

        # Very large file size
        large_size = 999999999999999
        result = format_file_size(large_size)
        assert isinstance(result, str)
        assert any(unit in result for unit in ["B", "KB", "MB", "GB", "TB"])

    def test_validation_functions_with_unicode(self):
        """Test validation functions with Unicode characters."""
        # Unicode in Tidal ID validation
        assert validate_tidal_id("12345一二三") is False

        # Unicode in URL extraction
        unicode_url = "https://tidal.com/browse/track/12345测试"
        result = extract_tidal_id_from_url(unicode_url)
        assert result == "12345"  # Should extract the numeric part

    def test_text_processing_with_unicode(self):
        """Test text processing functions with Unicode."""
        unicode_text = "This is a test with Unicode: 你好世界"

        # Sanitization should preserve Unicode
        sanitized = sanitize_query(unicode_text)
        assert "你好世界" in sanitized

        # Truncation should handle Unicode properly
        truncated = truncate_text(unicode_text, 20)
        assert len(truncated) <= 20

    def test_safe_get_with_numeric_keys(self):
        """Test safe_get with numeric keys."""
        data = {
            "0": "zero",
            1: "one",
            "nested": {
                "2": "two",
                3: "three"
            }
        }

        assert safe_get(data, "0") == "zero"
        assert safe_get(data, "nested.2") == "two"
        # Note: safe_get uses string keys, so numeric keys won't match
        assert safe_get(data, "1") is None

    def test_url_building_with_special_cases(self):
        """Test URL building with special cases."""
        # Empty base URL
        url = build_search_url("", "query", ["tracks"])
        # Empty base URL should still append parameters
        assert "query=query" in url

        # Base URL with fragment
        url = build_search_url("https://api.tidal.com#fragment", "query", ["tracks"])
        assert "#fragment" in url

        # Very long query
        long_query = "a" * 1000
        url = build_search_url("https://api.tidal.com", long_query, ["tracks"])
        assert len(url) > 1000

    def test_artist_merging_with_special_characters(self):
        """Test artist name merging with special characters."""
        artists = [
            {"name": "Artist & Band"},
            {"name": "Ñoño López"},
            {"name": "MC Früh"}
        ]

        result = merge_artist_names(artists)
        expected = "Artist & Band, Ñoño López, MC Früh"
        assert result == expected
