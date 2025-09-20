"""
Test helpers and utilities for integration testing.

Provides helper functions, mock data generators, and test utilities
for comprehensive integration testing of the Tidal MCP server.
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

from tidal_mcp.models import Album, Artist, Playlist, SearchResults, Track


class TidalMockDataGenerator:
    """Generate realistic mock data for Tidal API responses."""

    # Sample data pools
    ARTISTS = [
        "Taylor Swift", "The Beatles", "Drake", "Billie Eilish", "Ed Sheeran",
        "Ariana Grande", "Post Malone", "Dua Lipa", "The Weeknd", "Bruno Mars",
        "Adele", "Kanye West", "Beyoncé", "Justin Bieber", "Rihanna",
        "Coldplay", "Imagine Dragons", "Maroon 5", "OneRepublic", "Eminem"
    ]

    GENRES = [
        "Pop", "Rock", "Hip Hop", "R&B", "Electronic", "Country", "Jazz",
        "Classical", "Alternative", "Indie", "Folk", "Reggae", "Blues",
        "Metal", "Punk", "Funk", "Soul", "Gospel", "Latin", "World"
    ]

    ADJECTIVES = [
        "Beautiful", "Amazing", "Incredible", "Fantastic", "Wonderful",
        "Perfect", "Epic", "Magical", "Divine", "Brilliant", "Stunning",
        "Spectacular", "Magnificent", "Extraordinary", "Phenomenal"
    ]

    NOUNS = [
        "Love", "Dreams", "Night", "Day", "Heart", "Soul", "Life", "Time",
        "World", "Sky", "Ocean", "Fire", "Light", "Shadow", "Moon", "Star",
        "Hope", "Joy", "Peace", "Freedom", "Journey", "Adventure", "Story"
    ]

    @classmethod
    def generate_track_id(cls) -> str:
        """Generate a realistic track ID."""
        return str(random.randint(100000000, 999999999))

    @classmethod
    def generate_album_id(cls) -> str:
        """Generate a realistic album ID."""
        return str(random.randint(100000000, 999999999))

    @classmethod
    def generate_artist_id(cls) -> str:
        """Generate a realistic artist ID."""
        return str(random.randint(10000000, 99999999))

    @classmethod
    def generate_playlist_id(cls) -> str:
        """Generate a realistic playlist UUID."""
        return str(uuid.uuid4())

    @classmethod
    def generate_track_title(cls, prefix: str = "") -> str:
        """Generate a realistic track title."""
        if prefix:
            return f"{prefix} {random.choice(cls.ADJECTIVES)} {random.choice(cls.NOUNS)}"
        return f"{random.choice(cls.ADJECTIVES)} {random.choice(cls.NOUNS)}"

    @classmethod
    def generate_album_title(cls, prefix: str = "") -> str:
        """Generate a realistic album title."""
        templates = [
            f"{random.choice(cls.ADJECTIVES)} {random.choice(cls.NOUNS)}",
            f"The {random.choice(cls.NOUNS)} of {random.choice(cls.NOUNS)}",
            f"{random.choice(cls.NOUNS)} & {random.choice(cls.NOUNS)}",
            f"{random.choice(cls.ADJECTIVES)} {random.choice(cls.ADJECTIVES)}"
        ]
        title = random.choice(templates)
        return f"{prefix} {title}" if prefix else title

    @classmethod
    def generate_artist_name(cls, prefix: str = "") -> str:
        """Generate a realistic artist name."""
        if prefix:
            return f"{prefix} {random.choice(cls.ARTISTS)}"
        return random.choice(cls.ARTISTS)

    @classmethod
    def generate_duration(cls, min_seconds: int = 120, max_seconds: int = 360) -> int:
        """Generate a realistic track duration in seconds."""
        return random.randint(min_seconds, max_seconds)

    @classmethod
    def generate_release_date(cls) -> str:
        """Generate a realistic release date."""
        start_date = datetime(2000, 1, 1)
        end_date = datetime.now()
        time_between = end_date - start_date
        days_between = time_between.days
        random_days = random.randrange(days_between)
        random_date = start_date + timedelta(days=random_days)
        return random_date.strftime("%Y-%m-%d")

    @classmethod
    def generate_popularity(cls) -> int:
        """Generate a realistic popularity score."""
        return random.randint(1, 100)

    @classmethod
    def generate_image_url(cls, content_type: str = "album") -> str:
        """Generate a realistic image URL."""
        image_id = random.randint(1000, 9999)
        return f"https://resources.tidal.com/images/{image_id}/{image_id}.jpg"


class MockTidalObjects:
    """Create mock Tidal API objects with realistic data."""

    @staticmethod
    def create_mock_track(
        track_id: Optional[str] = None,
        title: Optional[str] = None,
        artist_name: Optional[str] = None,
        album_title: Optional[str] = None,
        **kwargs
    ) -> MagicMock:
        """Create a mock Tidal track object."""
        mock_track = MagicMock()

        # Basic track properties
        mock_track.id = track_id or TidalMockDataGenerator.generate_track_id()
        mock_track.name = title or TidalMockDataGenerator.generate_track_title()
        mock_track.duration = TidalMockDataGenerator.generate_duration()
        mock_track.track_num = kwargs.get("track_number", random.randint(1, 20))
        mock_track.volume_num = kwargs.get("disc_number", 1)
        mock_track.explicit = kwargs.get("explicit", random.choice([True, False]))
        mock_track.audio_quality = kwargs.get("quality", "HIGH")

        # Mock artist
        artist_mock = MagicMock()
        artist_mock.id = TidalMockDataGenerator.generate_artist_id()
        artist_mock.name = artist_name or TidalMockDataGenerator.generate_artist_name()
        artist_mock.picture = TidalMockDataGenerator.generate_image_url("artist")
        artist_mock.popularity = TidalMockDataGenerator.generate_popularity()

        mock_track.artist = artist_mock
        mock_track.artists = [artist_mock]

        # Mock album
        album_mock = MagicMock()
        album_mock.id = TidalMockDataGenerator.generate_album_id()
        album_mock.name = album_title or TidalMockDataGenerator.generate_album_title()
        album_mock.release_date = TidalMockDataGenerator.generate_release_date()
        album_mock.duration = TidalMockDataGenerator.generate_duration(2400, 4800)  # Album duration
        album_mock.num_tracks = random.randint(8, 16)
        album_mock.image = TidalMockDataGenerator.generate_image_url("album")
        album_mock.explicit = kwargs.get("explicit", False)
        album_mock.artist = artist_mock
        album_mock.artists = [artist_mock]

        mock_track.album = album_mock

        # Mock radio method
        mock_track.get_track_radio = MagicMock(return_value=[])

        return mock_track

    @staticmethod
    def create_mock_album(
        album_id: Optional[str] = None,
        title: Optional[str] = None,
        artist_name: Optional[str] = None,
        **kwargs
    ) -> MagicMock:
        """Create a mock Tidal album object."""
        mock_album = MagicMock()

        # Basic album properties
        mock_album.id = album_id or TidalMockDataGenerator.generate_album_id()
        mock_album.name = title or TidalMockDataGenerator.generate_album_title()
        mock_album.release_date = TidalMockDataGenerator.generate_release_date()
        mock_album.duration = TidalMockDataGenerator.generate_duration(2400, 4800)
        mock_album.num_tracks = kwargs.get("num_tracks", random.randint(8, 16))
        mock_album.image = TidalMockDataGenerator.generate_image_url("album")
        mock_album.explicit = kwargs.get("explicit", False)

        # Mock artist
        artist_mock = MagicMock()
        artist_mock.id = TidalMockDataGenerator.generate_artist_id()
        artist_mock.name = artist_name or TidalMockDataGenerator.generate_artist_name()
        artist_mock.picture = TidalMockDataGenerator.generate_image_url("artist")
        artist_mock.popularity = TidalMockDataGenerator.generate_popularity()

        mock_album.artist = artist_mock
        mock_album.artists = [artist_mock]

        # Mock tracks method
        mock_album.tracks = MagicMock(return_value=[])

        return mock_album

    @staticmethod
    def create_mock_artist(
        artist_id: Optional[str] = None,
        name: Optional[str] = None,
        **kwargs
    ) -> MagicMock:
        """Create a mock Tidal artist object."""
        mock_artist = MagicMock()

        # Basic artist properties
        mock_artist.id = artist_id or TidalMockDataGenerator.generate_artist_id()
        mock_artist.name = name or TidalMockDataGenerator.generate_artist_name()
        mock_artist.picture = TidalMockDataGenerator.generate_image_url("artist")
        mock_artist.popularity = TidalMockDataGenerator.generate_popularity()

        # Mock methods
        mock_artist.get_albums = MagicMock(return_value=[])
        mock_artist.get_top_tracks = MagicMock(return_value=[])
        mock_artist.get_radio = MagicMock(return_value=[])

        return mock_artist

    @staticmethod
    def create_mock_playlist(
        playlist_id: Optional[str] = None,
        title: Optional[str] = None,
        **kwargs
    ) -> MagicMock:
        """Create a mock Tidal playlist object."""
        mock_playlist = MagicMock()

        # Basic playlist properties
        mock_playlist.uuid = playlist_id or TidalMockDataGenerator.generate_playlist_id()
        mock_playlist.name = title or f"Playlist {random.randint(1, 1000)}"
        mock_playlist.description = kwargs.get("description", "A test playlist")
        mock_playlist.creator = kwargs.get("creator", {"name": "Test User"})
        mock_playlist.num_tracks = kwargs.get("num_tracks", random.randint(10, 50))
        mock_playlist.duration = kwargs.get("duration", random.randint(1800, 7200))
        mock_playlist.created = kwargs.get("created", "2023-01-01T00:00:00Z")
        mock_playlist.last_updated = kwargs.get("last_updated", "2023-01-15T12:00:00Z")
        mock_playlist.image = TidalMockDataGenerator.generate_image_url("playlist")
        mock_playlist.public = kwargs.get("public", True)

        # Mock methods
        mock_playlist.tracks = MagicMock(return_value=[])
        mock_playlist.add = MagicMock(return_value=True)
        mock_playlist.remove_by_index = MagicMock(return_value=True)
        mock_playlist.delete = MagicMock(return_value=True)

        return mock_playlist


class TestDataFactories:
    """Factories for creating consistent test data."""

    @staticmethod
    def create_search_scenario(
        query: str,
        track_count: int = 3,
        album_count: int = 2,
        artist_count: int = 2,
        playlist_count: int = 1
    ) -> Dict[str, Any]:
        """Create a complete search scenario with mock data."""
        scenario = {
            "query": query,
            "tracks": [],
            "albums": [],
            "artists": [],
            "playlists": []
        }

        # Generate tracks
        for i in range(track_count):
            track = MockTidalObjects.create_mock_track(
                title=f"{query} Track {i+1}",
                artist_name=f"{query} Artist {i+1}"
            )
            scenario["tracks"].append(track)

        # Generate albums
        for i in range(album_count):
            album = MockTidalObjects.create_mock_album(
                title=f"{query} Album {i+1}",
                artist_name=f"{query} Artist {i+1}"
            )
            scenario["albums"].append(album)

        # Generate artists
        for i in range(artist_count):
            artist = MockTidalObjects.create_mock_artist(
                name=f"{query} Artist {i+1}"
            )
            scenario["artists"].append(artist)

        # Generate playlists
        for i in range(playlist_count):
            playlist = MockTidalObjects.create_mock_playlist(
                title=f"{query} Playlist {i+1}"
            )
            scenario["playlists"].append(playlist)

        return scenario

    @staticmethod
    def create_user_library_scenario(
        track_count: int = 5,
        album_count: int = 3,
        artist_count: int = 4,
        playlist_count: int = 6
    ) -> Dict[str, Any]:
        """Create a user library scenario with favorites and playlists."""
        scenario = {
            "favorite_tracks": [],
            "favorite_albums": [],
            "favorite_artists": [],
            "favorite_playlists": [],
            "user_playlists": []
        }

        # Generate favorite tracks
        for i in range(track_count):
            track = MockTidalObjects.create_mock_track(
                title=f"Favorite Track {i+1}"
            )
            scenario["favorite_tracks"].append(track)

        # Generate favorite albums
        for i in range(album_count):
            album = MockTidalObjects.create_mock_album(
                title=f"Favorite Album {i+1}"
            )
            scenario["favorite_albums"].append(album)

        # Generate favorite artists
        for i in range(artist_count):
            artist = MockTidalObjects.create_mock_artist(
                name=f"Favorite Artist {i+1}"
            )
            scenario["favorite_artists"].append(artist)

        # Generate user playlists
        for i in range(playlist_count):
            playlist = MockTidalObjects.create_mock_playlist(
                title=f"My Playlist {i+1}",
                num_tracks=random.randint(5, 25)
            )
            scenario["user_playlists"].append(playlist)
            if i < 2:  # First 2 playlists are also favorites
                scenario["favorite_playlists"].append(playlist)

        return scenario

    @staticmethod
    def create_recommendation_scenario(
        recommended_count: int = 10,
        radio_count: int = 15
    ) -> Dict[str, Any]:
        """Create a recommendation scenario with various recommendation types."""
        scenario = {
            "recommended_tracks": [],
            "track_radio": [],
            "artist_radio": []
        }

        # Generate recommended tracks
        for i in range(recommended_count):
            track = MockTidalObjects.create_mock_track(
                title=f"Recommended Track {i+1}"
            )
            scenario["recommended_tracks"].append(track)

        # Generate track radio
        for i in range(radio_count):
            track = MockTidalObjects.create_mock_track(
                title=f"Radio Track {i+1}"
            )
            scenario["track_radio"].append(track)

        # Generate artist radio
        for i in range(radio_count):
            track = MockTidalObjects.create_mock_track(
                title=f"Artist Radio Track {i+1}"
            )
            scenario["artist_radio"].append(track)

        return scenario


class ResponseValidators:
    """Validators for ensuring response format compliance."""

    @staticmethod
    def validate_search_response(response: Dict[str, Any]) -> bool:
        """Validate search response format."""
        required_fields = ["query", "content_type", "results", "total_results"]
        return all(field in response for field in required_fields)

    @staticmethod
    def validate_track_response(response: Dict[str, Any]) -> bool:
        """Validate track response format."""
        if "success" not in response:
            return False

        if response["success"]:
            return "track" in response and "id" in response["track"]
        else:
            return "error" in response

    @staticmethod
    def validate_playlist_response(response: Dict[str, Any]) -> bool:
        """Validate playlist response format."""
        if "success" not in response:
            return False

        if response["success"]:
            return "playlist" in response and "id" in response["playlist"]
        else:
            return "error" in response

    @staticmethod
    def validate_favorites_response(response: Dict[str, Any]) -> bool:
        """Validate favorites response format."""
        required_fields = ["content_type", "favorites", "total_results"]
        return all(field in response for field in required_fields)

    @staticmethod
    def validate_boolean_operation_response(response: Dict[str, Any]) -> bool:
        """Validate boolean operation response format."""
        if "success" not in response:
            return False

        if response["success"]:
            return "message" in response
        else:
            return "error" in response

    @staticmethod
    def validate_enhanced_response(response: Dict[str, Any]) -> bool:
        """Validate enhanced tool response format."""
        if "success" not in response:
            return False

        # Enhanced responses should have metadata
        return "_metadata" in response or "metadata" in response


class TestAssertion:
    """Custom assertions for test validation."""

    @staticmethod
    def assert_valid_track_data(track_data: Dict[str, Any]):
        """Assert that track data is valid and complete."""
        required_fields = ["id", "title", "artists"]
        for field in required_fields:
            assert field in track_data, f"Track missing required field: {field}"

        assert isinstance(track_data["artists"], list), "Track artists must be a list"
        assert len(track_data["artists"]) > 0, "Track must have at least one artist"

        for artist in track_data["artists"]:
            assert "id" in artist, "Artist missing ID"
            assert "name" in artist, "Artist missing name"

    @staticmethod
    def assert_valid_album_data(album_data: Dict[str, Any]):
        """Assert that album data is valid and complete."""
        required_fields = ["id", "title", "artists"]
        for field in required_fields:
            assert field in album_data, f"Album missing required field: {field}"

        assert isinstance(album_data["artists"], list), "Album artists must be a list"
        assert len(album_data["artists"]) > 0, "Album must have at least one artist"

    @staticmethod
    def assert_valid_artist_data(artist_data: Dict[str, Any]):
        """Assert that artist data is valid and complete."""
        required_fields = ["id", "name"]
        for field in required_fields:
            assert field in artist_data, f"Artist missing required field: {field}"

    @staticmethod
    def assert_valid_playlist_data(playlist_data: Dict[str, Any]):
        """Assert that playlist data is valid and complete."""
        required_fields = ["id", "title"]
        for field in required_fields:
            assert field in playlist_data, f"Playlist missing required field: {field}"

        assert isinstance(playlist_data.get("tracks", []), list), "Playlist tracks must be a list"

    @staticmethod
    def assert_response_time_acceptable(start_time: float, end_time: float, max_seconds: float = 5.0):
        """Assert that response time is within acceptable limits."""
        response_time = end_time - start_time
        assert response_time <= max_seconds, f"Response time {response_time:.2f}s exceeds limit {max_seconds}s"

    @staticmethod
    def assert_pagination_valid(response: Dict[str, Any], expected_limit: int, expected_offset: int):
        """Assert that pagination information is valid."""
        if "pagination" in response:
            pagination = response["pagination"]
            assert pagination["per_page"] == expected_limit
            current_page = (expected_offset // expected_limit) + 1
            assert pagination["current_page"] == current_page


# Integration test utilities
def create_test_suite_data() -> Dict[str, Any]:
    """Create a comprehensive test suite data set."""
    return {
        "search_scenarios": [
            TestDataFactories.create_search_scenario("rock", 5, 3, 3, 2),
            TestDataFactories.create_search_scenario("pop", 4, 2, 2, 1),
            TestDataFactories.create_search_scenario("jazz", 3, 2, 2, 1),
        ],
        "user_library": TestDataFactories.create_user_library_scenario(8, 5, 6, 10),
        "recommendations": TestDataFactories.create_recommendation_scenario(15, 20),
    }


def simulate_api_latency(min_ms: int = 50, max_ms: int = 200):
    """Simulate realistic API latency for testing."""
    import asyncio
    import random

    delay = random.randint(min_ms, max_ms) / 1000.0
    return asyncio.sleep(delay)