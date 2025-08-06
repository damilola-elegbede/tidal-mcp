"""
Pytest configuration and shared fixtures for Tidal MCP tests.

Provides common test fixtures and configuration for authentication,
service layer, and integration testing.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock
import tidalapi


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_session_file():
    """Create a temporary session file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    yield temp_path
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def mock_tidal_session():
    """Create a comprehensive mock tidalapi session."""
    session = Mock(spec=tidalapi.Session)

    # Mock user with realistic data
    user = Mock()
    user.id = 12345
    user.country_code = "US"
    user.username = "testuser"
    user.subscription = {"type": "HiFi", "valid": True}

    # Mock favorites
    favorites = Mock()
    favorites.tracks = Mock(return_value=[])
    favorites.albums = Mock(return_value=[])
    favorites.artists = Mock(return_value=[])
    favorites.playlists = Mock(return_value=[])
    favorites.add_track = Mock(return_value=True)
    favorites.add_album = Mock(return_value=True)
    favorites.add_artist = Mock(return_value=True)
    favorites.add_playlist = Mock(return_value=True)
    favorites.remove_track = Mock(return_value=True)
    favorites.remove_album = Mock(return_value=True)
    favorites.remove_artist = Mock(return_value=True)
    favorites.remove_playlist = Mock(return_value=True)
    user.favorites = favorites

    # Mock user playlists
    user.playlists = Mock(return_value=[])
    user.create_playlist = Mock()

    session.user = user
    session.load_oauth_session.return_value = True

    # Mock API methods
    session.search = Mock(
        return_value={
            "tracks": [],
            "albums": [],
            "artists": [],
            "playlists": [],
        }
    )
    session.track = Mock()
    session.album = Mock()
    session.artist = Mock()
    session.playlist = Mock()
    session.featured = Mock()

    return session


def create_sample_tidal_track(
    track_id=123456, name="Test Track", artist_name="Test Artist"
):
    """Create a sample tidalapi track for testing."""
    track = Mock()
    track.id = track_id
    track.name = name
    track.duration = 240
    track.track_num = 1
    track.volume_num = 1
    track.explicit = False
    track.audio_quality = "LOSSLESS"

    # Mock artist
    artist = Mock()
    artist.id = 789
    artist.name = artist_name
    artist.picture = "artist_pic_url"
    artist.popularity = 85
    track.artist = artist
    track.artists = [artist]

    # Mock album
    album = Mock()
    album.id = 456
    album.name = "Test Album"
    album.release_date = "2023-01-01"
    album.duration = 3600
    album.num_tracks = 12
    album.image = "album_cover_url"
    album.explicit = False
    album.artist = artist
    album.artists = [artist]
    track.album = album

    return track


def create_sample_tidal_playlist(playlist_id="playlist-uuid-123", name="Test Playlist"):
    """Create a sample tidalapi playlist for testing."""
    playlist = Mock()
    playlist.uuid = playlist_id
    playlist.id = playlist_id
    playlist.name = name
    playlist.description = f"Description for {name}"
    playlist.num_tracks = 10
    playlist.duration = 2400
    playlist.image = "playlist_image_url"
    playlist.public = True
    playlist.created = "2023-01-01T00:00:00Z"
    playlist.last_updated = "2023-01-02T00:00:00Z"
    playlist.creator = {"name": "Test User"}

    # Mock methods
    playlist.tracks = Mock(return_value=[])
    playlist.add = Mock(return_value=True)
    playlist.remove_by_index = Mock(return_value=True)
    playlist.delete = Mock(return_value=True)

    return playlist


@pytest.fixture
def mock_fastmcp_server():
    """Create a mock FastMCP server instance."""
    from fastmcp import FastMCP
    from unittest.mock import Mock

    server = Mock(spec=FastMCP)
    server.tools = {}
    server.run = Mock()
    return server


@pytest.fixture
def sample_search_results():
    """Create sample search results for testing."""
    from tidal_mcp.models import SearchResults, Track, Album, Artist, Playlist

    tracks = [
        Track(id="1", title="Search Track 1", artists=[], duration=200),
        Track(id="2", title="Search Track 2", artists=[], duration=180),
    ]

    albums = [
        Album(id="1", title="Search Album 1", artists=[]),
        Album(id="2", title="Search Album 2", artists=[]),
    ]

    artists = [
        Artist(id="1", name="Search Artist 1"),
        Artist(id="2", name="Search Artist 2"),
    ]

    playlists = [
        Playlist(id="1", title="Search Playlist 1"),
        Playlist(id="2", title="Search Playlist 2"),
    ]

    return SearchResults(
        tracks=tracks, albums=albums, artists=artists, playlists=playlists
    )


@pytest.fixture
def performance_test_data():
    """Create data for performance testing."""
    from tidal_mcp.models import Track, Artist, Album

    # Create large dataset for performance tests
    tracks = []
    for i in range(1000):
        artist = Artist(id=str(i), name=f"Perf Artist {i}")
        album = Album(id=str(i), title=f"Perf Album {i}", artists=[artist])
        track = Track(
            id=str(i),
            title=f"Perf Track {i}",
            artists=[artist],
            album=album,
            duration=180 + (i % 120),
        )
        tracks.append(track)

    return tracks


@pytest.fixture
def mock_aiohttp_response():
    """Create a mock aiohttp response for testing."""
    from unittest.mock import AsyncMock

    response = AsyncMock()
    response.status = 200
    response.json = AsyncMock(
        return_value={
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "expires_in": 3600,
        }
    )
    response.text = AsyncMock(return_value="Success")

    return response


@pytest.fixture
def error_scenarios():
    """Create common error scenarios for testing."""
    return {
        "network_error": Exception("Network connection failed"),
        "timeout_error": asyncio.TimeoutError("Request timeout"),
        "auth_error": Exception("Authentication failed"),
        "api_error": Exception("API returned error status"),
        "parse_error": ValueError("Failed to parse response"),
        "permission_error": PermissionError("Access denied"),
    }


# Export utility functions for use in tests
__all__ = [
    "temp_session_file",
    "mock_tidal_session",
    "create_sample_tidal_track",
    "create_sample_tidal_playlist",
    "mock_fastmcp_server",
    "sample_search_results",
    "performance_test_data",
    "mock_aiohttp_response",
    "error_scenarios",
]
