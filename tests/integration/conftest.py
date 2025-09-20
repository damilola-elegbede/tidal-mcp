"""
Integration test configuration and fixtures.

Provides comprehensive test fixtures, mock data factories, and helper functions
for integration testing of the Tidal MCP server.
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import fakeredis.aioredis
import pytest
from freezegun import freeze_time

from tidal_mcp.auth import TidalAuth
from tidal_mcp.models import Album, Artist, Playlist, SearchResults, Track
from tidal_mcp.production.middleware import HealthChecker, MiddlewareStack
from tidal_mcp.service import TidalService

# Test Configuration - Using obviously fake IDs to prevent production access
_test_uuid = uuid.uuid4().hex
TEST_USER_ID = f"fake_test_user_{_test_uuid[:8]}"
TEST_SESSION_ID = f"fake_test_session_{_test_uuid[8:16]}"
TEST_TOKEN = f"fake_test_token_{_test_uuid[16:24]}_TEST_ONLY"


@pytest.fixture
async def mock_redis():
    """Mock Redis client for testing."""
    redis_mock = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield redis_mock
    await redis_mock.flushall()
    await redis_mock.aclose()


@pytest.fixture
def mock_auth_manager():
    """Mock Tidal authentication manager."""
    auth_mock = MagicMock(spec=TidalAuth)
    auth_mock.is_authenticated.return_value = True
    auth_mock.get_user_info.return_value = {
        "id": TEST_USER_ID,
        "username": "test_user",
        "country_code": "US",
        "subscription": "premium"
    }
    auth_mock.session_id = TEST_SESSION_ID
    auth_mock.access_token = TEST_TOKEN
    auth_mock.country_code = "US"
    auth_mock.token_expires_at = datetime.utcnow() + timedelta(hours=1)
    auth_mock.refresh_token = "test_refresh_token"

    # Mock async methods
    auth_mock.authenticate = AsyncMock(return_value=True)
    auth_mock.refresh_access_token = AsyncMock(return_value=True)
    auth_mock.ensure_valid_token = AsyncMock(return_value=True)
    auth_mock.validate_token = AsyncMock(return_value=True)
    auth_mock.get_user_id_from_token = AsyncMock(return_value=TEST_USER_ID)

    return auth_mock


@pytest.fixture
async def middleware_stack(mock_redis, mock_auth_manager):
    """Production middleware stack for testing."""
    return MiddlewareStack(
        redis_client=mock_redis,
        auth_manager=mock_auth_manager,
        enable_rate_limiting=True,
        enable_validation=True,
        enable_observability=True,
    )


@pytest.fixture
async def health_checker(mock_redis):
    """Health checker instance for testing."""
    return HealthChecker(mock_redis)


@pytest.fixture
def mock_tidal_session():
    """Mock Tidal API session."""
    session_mock = MagicMock()

    # Mock user object
    user_mock = MagicMock()
    favorites_mock = MagicMock()

    # Setup favorites mock
    favorites_mock.tracks.return_value = []
    favorites_mock.albums.return_value = []
    favorites_mock.artists.return_value = []
    favorites_mock.playlists.return_value = []
    favorites_mock.add_track = MagicMock(return_value=True)
    favorites_mock.add_album = MagicMock(return_value=True)
    favorites_mock.add_artist = MagicMock(return_value=True)
    favorites_mock.add_playlist = MagicMock(return_value=True)
    favorites_mock.remove_track = MagicMock(return_value=True)
    favorites_mock.remove_album = MagicMock(return_value=True)
    favorites_mock.remove_artist = MagicMock(return_value=True)
    favorites_mock.remove_playlist = MagicMock(return_value=True)

    user_mock.favorites = favorites_mock
    user_mock.playlists.return_value = []
    user_mock.create_playlist = MagicMock()

    session_mock.user = user_mock
    session_mock.search = MagicMock(return_value={})
    session_mock.track = MagicMock()
    session_mock.album = MagicMock()
    session_mock.artist = MagicMock()
    session_mock.playlist = MagicMock()
    session_mock.featured = MagicMock()

    return session_mock


@pytest.fixture
async def tidal_service(mock_auth_manager, mock_tidal_session):
    """Mock Tidal service with pre-configured session."""
    service = TidalService(mock_auth_manager)

    # Mock the get_session method to return our mock session
    with patch.object(service, 'get_session', return_value=mock_tidal_session):
        yield service


@pytest.fixture
def sample_track_data():
    """Sample track data for testing."""
    return {
        "id": 123456789,
        "name": "Test Track",
        "duration": 180,
        "track_num": 1,
        "volume_num": 1,
        "explicit": False,
        "audio_quality": "HIGH",
        "artist": {
            "id": 987654321,
            "name": "Test Artist",
            "picture": "https://example.com/artist.jpg",
            "popularity": 85
        },
        "album": {
            "id": 456789123,
            "name": "Test Album",
            "release_date": "2023-01-15",
            "duration": 3600,
            "num_tracks": 12,
            "image": "https://example.com/album.jpg",
            "explicit": False,
            "artist": {
                "id": 987654321,
                "name": "Test Artist",
                "picture": "https://example.com/artist.jpg",
                "popularity": 85
            }
        }
    }


@pytest.fixture
def sample_album_data():
    """Sample album data for testing."""
    return {
        "id": 456789123,
        "name": "Test Album",
        "release_date": "2023-01-15",
        "duration": 3600,
        "num_tracks": 12,
        "image": "https://example.com/album.jpg",
        "explicit": False,
        "artist": {
            "id": 987654321,
            "name": "Test Artist",
            "picture": "https://example.com/artist.jpg",
            "popularity": 85
        }
    }


@pytest.fixture
def sample_artist_data():
    """Sample artist data for testing."""
    return {
        "id": 987654321,
        "name": "Test Artist",
        "picture": "https://example.com/artist.jpg",
        "popularity": 85
    }


@pytest.fixture
def sample_playlist_data():
    """Sample playlist data for testing."""
    return {
        "uuid": "test-playlist-uuid-123",
        "name": "Test Playlist",
        "description": "A test playlist",
        "creator": {"name": "Test User"},
        "num_tracks": 5,
        "duration": 900,
        "created": "2023-01-01T00:00:00Z",
        "last_updated": "2023-01-15T12:00:00Z",
        "image": "https://example.com/playlist.jpg",
        "public": True
    }


@pytest.fixture
def mock_track_objects(sample_track_data):
    """Mock track objects for service layer testing."""
    def create_mock_track(track_data=None):
        if track_data is None:
            track_data = sample_track_data

        mock_track = MagicMock()
        mock_track.id = track_data["id"]
        mock_track.name = track_data["name"]
        mock_track.duration = track_data["duration"]
        mock_track.track_num = track_data.get("track_num")
        mock_track.volume_num = track_data.get("volume_num")
        mock_track.explicit = track_data.get("explicit", False)
        mock_track.audio_quality = track_data.get("audio_quality")

        # Mock artist
        if "artist" in track_data:
            artist_mock = MagicMock()
            artist_mock.id = track_data["artist"]["id"]
            artist_mock.name = track_data["artist"]["name"]
            artist_mock.picture = track_data["artist"].get("picture")
            artist_mock.popularity = track_data["artist"].get("popularity")
            mock_track.artist = artist_mock
            mock_track.artists = [artist_mock]

        # Mock album
        if "album" in track_data:
            album_mock = MagicMock()
            album_mock.id = track_data["album"]["id"]
            album_mock.name = track_data["album"]["name"]
            album_mock.release_date = track_data["album"].get("release_date")
            album_mock.duration = track_data["album"].get("duration")
            album_mock.num_tracks = track_data["album"].get("num_tracks")
            album_mock.image = track_data["album"].get("image")
            album_mock.explicit = track_data["album"].get("explicit", False)

            if "artist" in track_data["album"]:
                album_artist_mock = MagicMock()
                album_artist_mock.id = track_data["album"]["artist"]["id"]
                album_artist_mock.name = track_data["album"]["artist"]["name"]
                album_artist_mock.picture = track_data["album"]["artist"].get("picture")
                album_artist_mock.popularity = track_data["album"]["artist"].get("popularity")
                album_mock.artist = album_artist_mock
                album_mock.artists = [album_artist_mock]

            mock_track.album = album_mock

        # Mock radio method
        mock_track.get_track_radio = MagicMock(return_value=[])

        return mock_track

    return create_mock_track


@pytest.fixture
def mock_album_objects(sample_album_data):
    """Mock album objects for service layer testing."""
    def create_mock_album(album_data=None):
        if album_data is None:
            album_data = sample_album_data

        mock_album = MagicMock()
        mock_album.id = album_data["id"]
        mock_album.name = album_data["name"]
        mock_album.release_date = album_data.get("release_date")
        mock_album.duration = album_data.get("duration")
        mock_album.num_tracks = album_data.get("num_tracks")
        mock_album.image = album_data.get("image")
        mock_album.explicit = album_data.get("explicit", False)

        # Mock artist
        if "artist" in album_data:
            artist_mock = MagicMock()
            artist_mock.id = album_data["artist"]["id"]
            artist_mock.name = album_data["artist"]["name"]
            artist_mock.picture = album_data["artist"].get("picture")
            artist_mock.popularity = album_data["artist"].get("popularity")
            mock_album.artist = artist_mock
            mock_album.artists = [artist_mock]

        # Mock tracks method
        mock_album.tracks = MagicMock(return_value=[])

        return mock_album

    return create_mock_album


@pytest.fixture
def mock_artist_objects(sample_artist_data):
    """Mock artist objects for service layer testing."""
    def create_mock_artist(artist_data=None):
        if artist_data is None:
            artist_data = sample_artist_data

        mock_artist = MagicMock()
        mock_artist.id = artist_data["id"]
        mock_artist.name = artist_data["name"]
        mock_artist.picture = artist_data.get("picture")
        mock_artist.popularity = artist_data.get("popularity")

        # Mock methods
        mock_artist.get_albums = MagicMock(return_value=[])
        mock_artist.get_top_tracks = MagicMock(return_value=[])
        mock_artist.get_radio = MagicMock(return_value=[])

        return mock_artist

    return create_mock_artist


@pytest.fixture
def mock_playlist_objects(sample_playlist_data):
    """Mock playlist objects for service layer testing."""
    def create_mock_playlist(playlist_data=None):
        if playlist_data is None:
            playlist_data = sample_playlist_data

        mock_playlist = MagicMock()
        mock_playlist.uuid = playlist_data["uuid"]
        mock_playlist.name = playlist_data["name"]
        mock_playlist.description = playlist_data.get("description")
        mock_playlist.creator = playlist_data.get("creator", {})
        mock_playlist.num_tracks = playlist_data.get("num_tracks", 0)
        mock_playlist.duration = playlist_data.get("duration")
        mock_playlist.created = playlist_data.get("created")
        mock_playlist.last_updated = playlist_data.get("last_updated")
        mock_playlist.image = playlist_data.get("image")
        mock_playlist.public = playlist_data.get("public", True)

        # Mock methods
        mock_playlist.tracks = MagicMock(return_value=[])
        mock_playlist.add = MagicMock(return_value=True)
        mock_playlist.remove_by_index = MagicMock(return_value=True)
        mock_playlist.delete = MagicMock(return_value=True)

        return mock_playlist

    return create_mock_playlist


@pytest.fixture
def track_factory():
    """Factory for creating Track model instances."""
    def create_track(
        track_id: str = "123456789",
        title: str = "Test Track",
        artist_name: str = "Test Artist",
        album_title: str = "Test Album",
        duration: int = 180,
        **kwargs
    ) -> Track:
        artist = Artist(
            id=kwargs.get("artist_id", "987654321"),
            name=artist_name,
            picture=kwargs.get("artist_picture"),
            popularity=kwargs.get("artist_popularity", 85)
        )

        album = Album(
            id=kwargs.get("album_id", "456789123"),
            title=album_title,
            artists=[artist],
            release_date=kwargs.get("release_date", "2023-01-15"),
            duration=kwargs.get("album_duration", 3600),
            number_of_tracks=kwargs.get("num_tracks", 12),
            cover=kwargs.get("album_cover"),
            explicit=kwargs.get("explicit", False)
        )

        return Track(
            id=track_id,
            title=title,
            artists=[artist],
            album=album,
            duration=duration,
            track_number=kwargs.get("track_number", 1),
            disc_number=kwargs.get("disc_number", 1),
            explicit=kwargs.get("explicit", False),
            quality=kwargs.get("quality", "HIGH")
        )

    return create_track


@pytest.fixture
def album_factory():
    """Factory for creating Album model instances."""
    def create_album(
        album_id: str = "456789123",
        title: str = "Test Album",
        artist_name: str = "Test Artist",
        **kwargs
    ) -> Album:
        artist = Artist(
            id=kwargs.get("artist_id", "987654321"),
            name=artist_name,
            picture=kwargs.get("artist_picture"),
            popularity=kwargs.get("artist_popularity", 85)
        )

        return Album(
            id=album_id,
            title=title,
            artists=[artist],
            release_date=kwargs.get("release_date", "2023-01-15"),
            duration=kwargs.get("duration", 3600),
            number_of_tracks=kwargs.get("number_of_tracks", 12),
            cover=kwargs.get("cover"),
            explicit=kwargs.get("explicit", False)
        )

    return create_album


@pytest.fixture
def artist_factory():
    """Factory for creating Artist model instances."""
    def create_artist(
        artist_id: str = "987654321",
        name: str = "Test Artist",
        **kwargs
    ) -> Artist:
        return Artist(
            id=artist_id,
            name=name,
            picture=kwargs.get("picture"),
            popularity=kwargs.get("popularity", 85)
        )

    return create_artist


@pytest.fixture
def playlist_factory(track_factory):
    """Factory for creating Playlist model instances."""
    def create_playlist(
        playlist_id: str = "test-playlist-uuid",
        title: str = "Test Playlist",
        track_count: int = 0,
        **kwargs
    ) -> Playlist:
        tracks = []
        if track_count > 0:
            tracks = [
                track_factory(
                    track_id=str(1000 + i),
                    title=f"Track {i+1}",
                    artist_name=f"Artist {i+1}",
                    album_title=f"Album {i+1}"
                )
                for i in range(track_count)
            ]

        return Playlist(
            id=playlist_id,
            title=title,
            description=kwargs.get("description", "Test playlist description"),
            creator=kwargs.get("creator", "Test User"),
            tracks=tracks,
            number_of_tracks=len(tracks),
            duration=kwargs.get("duration", len(tracks) * 180),
            created_at=kwargs.get("created_at"),
            updated_at=kwargs.get("updated_at"),
            image=kwargs.get("image"),
            public=kwargs.get("public", True)
        )

    return create_playlist


@pytest.fixture
def search_results_factory(track_factory, album_factory, artist_factory, playlist_factory):
    """Factory for creating SearchResults instances."""
    def create_search_results(
        track_count: int = 3,
        album_count: int = 2,
        artist_count: int = 2,
        playlist_count: int = 1,
        query: str = "test",
        **kwargs
    ) -> SearchResults:
        tracks = [
            track_factory(
                track_id=str(2000 + i),
                title=f"{query} Track {i+1}",
                artist_name=f"{query} Artist {i+1}"
            )
            for i in range(track_count)
        ]

        albums = [
            album_factory(
                album_id=str(3000 + i),
                title=f"{query} Album {i+1}",
                artist_name=f"{query} Artist {i+1}"
            )
            for i in range(album_count)
        ]

        artists = [
            artist_factory(
                artist_id=str(4000 + i),
                name=f"{query} Artist {i+1}"
            )
            for i in range(artist_count)
        ]

        playlists = [
            playlist_factory(
                playlist_id=f"{query}-playlist-{i}",
                title=f"{query} Playlist {i+1}"
            )
            for i in range(playlist_count)
        ]

        return SearchResults(
            tracks=tracks,
            albums=albums,
            artists=artists,
            playlists=playlists
        )

    return create_search_results


@pytest.fixture
def mock_successful_response():
    """Mock successful API response format."""
    def create_response(data: Any, success: bool = True, **metadata) -> dict[str, Any]:
        response = {
            "success": success,
            "data": data,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        if metadata:
            response["metadata"] = metadata

        return response

    return create_response


@pytest.fixture
def mock_error_response():
    """Mock error response format."""
    def create_error(
        error_code: str,
        message: str,
        details: dict[str, Any] | None = None,
        request_id: str | None = None
    ) -> dict[str, Any]:
        response = {
            "error": error_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id or str(uuid.uuid4())
        }

        if details:
            response["details"] = details

        return response

    return create_error


@pytest.fixture
async def mock_mcp_server():
    """Mock FastMCP server instance for integration testing."""
    def create_function_tool_mock(name: str, description: str = None):
        """Create a mock that looks like a FunctionTool"""
        mock_tool = MagicMock()
        mock_tool.name = name
        mock_tool.description = description or f"Mock {name} tool for testing"
        mock_tool.__name__ = name
        mock_tool.__doc__ = description or f"Mock {name} tool for testing"
        mock_tool.fn = AsyncMock(return_value={"success": True, "message": f"Mock {name} called"})
        return mock_tool

    # Create a mock server that doesn't start actual HTTP services
    server_mock = MagicMock()
    server_mock.name = "Test Tidal MCP Server"
    server_mock._tools = {
        'tidal_login': create_function_tool_mock('tidal_login', 'Authenticate with Tidal using OAuth2 flow'),
        'tidal_search': create_function_tool_mock('tidal_search', 'Search for tracks, albums, artists, or playlists'),
        'tidal_get_playlist': create_function_tool_mock('tidal_get_playlist', 'Get a specific playlist by ID'),
        'tidal_create_playlist': create_function_tool_mock('tidal_create_playlist', 'Create a new playlist'),
        'tidal_add_to_playlist': create_function_tool_mock('tidal_add_to_playlist', 'Add tracks to a playlist'),
        'tidal_remove_from_playlist': create_function_tool_mock('tidal_remove_from_playlist', 'Remove tracks from a playlist'),
        'tidal_get_favorites': create_function_tool_mock('tidal_get_favorites', 'Get user favorites'),
        'tidal_add_favorite': create_function_tool_mock('tidal_add_favorite', 'Add item to favorites'),
        'tidal_remove_favorite': create_function_tool_mock('tidal_remove_favorite', 'Remove item from favorites'),
        'tidal_get_recommendations': create_function_tool_mock('tidal_get_recommendations', 'Get recommendations'),
        'tidal_get_track_radio': create_function_tool_mock('tidal_get_track_radio', 'Get track radio'),
        'tidal_get_user_playlists': create_function_tool_mock('tidal_get_user_playlists', 'Get user playlists'),
        'tidal_get_track': create_function_tool_mock('tidal_get_track', 'Get track details'),
        'tidal_get_album': create_function_tool_mock('tidal_get_album', 'Get album details'),
        'tidal_get_artist': create_function_tool_mock('tidal_get_artist', 'Get artist details')
    }

    # Enhanced production tools
    server_mock._tools.update({
        'health_check': create_function_tool_mock('health_check', 'Check system health status'),
        'get_system_status': create_function_tool_mock('get_system_status', 'Get detailed system status'),
        'refresh_session': create_function_tool_mock('refresh_session', 'Refresh authentication session'),
        'get_stream_url': create_function_tool_mock('get_stream_url', 'Get streaming URL for a track'),
        'tidal_search_advanced': create_function_tool_mock('tidal_search_advanced', 'Advanced search with enhanced features'),
        'get_rate_limit_status': create_function_tool_mock('get_rate_limit_status', 'Check rate limit status')
    })

    yield server_mock


# Test utilities and helpers
class MockTidalResponse:
    """Helper class for creating consistent mock Tidal API responses."""

    @staticmethod
    def create_search_response(
        tracks: list[Any] = None,
        albums: list[Any] = None,
        artists: list[Any] = None,
        playlists: list[Any] = None
    ) -> dict[str, list[Any]]:
        return {
            "tracks": tracks or [],
            "albums": albums or [],
            "artists": artists or [],
            "playlists": playlists or []
        }

    @staticmethod
    def create_pagination_info(
        limit: int = 20,
        offset: int = 0,
        total: int = 100
    ) -> dict[str, Any]:
        return {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": offset + limit < total
        }


# Environment setup helpers
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    test_env = {
        "TIDAL_CLIENT_ID": f"fake_integration_client_{_test_uuid[:12]}",
        "TIDAL_CLIENT_SECRET": f"fake_integration_secret_{_test_uuid[:16]}_NEVER_REAL",
        "REDIS_URL": f"redis://fake-test-redis-{_test_uuid[:8]}.test:9999/99",  # Isolated test database
        "ENVIRONMENT": "test"
    }

    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    yield

    # Restore original environment
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


# Time-based testing helpers
@pytest.fixture
def fixed_time():
    """Provide a fixed reference time for consistent testing.

    Note: This fixture provides a reference time but does not freeze system time
    to avoid interference with pytest's timing measurements.
    """
    # Return a fixed datetime for tests that need consistent time references
    reference_time = datetime(2024, 1, 15, 10, 30, 0)
    yield reference_time


@pytest.fixture
def frozen_time():
    """Freeze time for tests that specifically need time control.

    Use this fixture only when you need to control time flow during the test.
    Most tests should use 'fixed_time' for consistent reference times.
    """
    with freeze_time("2024-01-15T10:30:00Z") as frozen:
        yield frozen


# Integration test markers
pytestmark = pytest.mark.integration
