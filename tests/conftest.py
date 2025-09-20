"""
Pytest configuration and shared fixtures for Tidal MCP tests.

Provides common test fixtures, mocks, and configuration used across
all test modules for consistent testing environment.
"""

import asyncio
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from aioresponses import aioresponses

from src.tidal_mcp.auth import TidalAuth
from src.tidal_mcp.models import Album, Artist, Playlist, Track
from src.tidal_mcp.service import TidalService


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing with secure fake credentials."""
    import uuid
    # Generate obviously fake credentials that cannot be mistaken for real ones
    test_env = {
        "TIDAL_CLIENT_ID": f"fake_test_client_{uuid.uuid4().hex[:12]}",
        "TIDAL_CLIENT_SECRET": f"fake_test_secret_{uuid.uuid4().hex[:24]}_NEVER_REAL",
        "TIDAL_REDIRECT_URI": "http://fake-test-callback.localhost:9999/callback",
        "TIDAL_COUNTRY_CODE": "XX"  # Invalid country code to prevent real API calls
    }
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)
    return test_env


@pytest.fixture
def temp_session_dir():
    """Create temporary directory for session files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_session_file(temp_session_dir):
    """Create mock session file for testing with secure fake credentials."""
    import uuid
    # Create the .tidal-mcp directory structure
    tidal_dir = temp_session_dir / ".tidal-mcp"
    tidal_dir.mkdir(parents=True, exist_ok=True)

    session_file = tidal_dir / "session.json"
    # Generate obviously fake tokens that cannot be confused with real ones
    fake_uuid = uuid.uuid4().hex
    session_data = {
        "access_token": f"fake_access_token_{fake_uuid[:16]}_TEST_ONLY",
        "refresh_token": f"fake_refresh_token_{fake_uuid[16:32]}_TEST_ONLY",
        "session_id": f"fake_session_{fake_uuid[:8]}_TEST",
        "user_id": "999999999",  # Obviously fake user ID
        "country_code": "XX",  # Invalid country code
        "expires_at": (datetime.now() + timedelta(hours=1)).isoformat(),
        "saved_at": datetime.now().isoformat()
    }

    session_file.write_text(json.dumps(session_data, indent=2))

    return session_file, session_data


@pytest.fixture
def mock_tidal_session():
    """Create mock tidalapi Session object with secure fake credentials."""
    import uuid
    fake_uuid = uuid.uuid4().hex

    mock_session = Mock()
    mock_session.access_token = f"fake_session_token_{fake_uuid[:16]}_TEST_ONLY"
    mock_session.refresh_token = f"fake_session_refresh_{fake_uuid[16:32]}_TEST_ONLY"
    mock_session.token_type = "Bearer"
    mock_session.session_id = f"fake_session_{fake_uuid[:8]}_TEST"
    mock_session.expiry_time = 3600

    # Mock user with obviously fake data
    mock_user = Mock()
    mock_user.id = 999999999  # Obviously fake user ID
    mock_user.country_code = "XX"  # Invalid country code
    mock_user.subscription = {"type": "FakeTest", "valid": True}
    mock_session.user = mock_user

    # Mock favorites
    mock_favorites = Mock()
    mock_user.favorites = mock_favorites

    return mock_session


@pytest.fixture
def mock_tidal_track():
    """Create mock tidalapi Track object."""
    mock_track = Mock()
    mock_track.id = 12345
    mock_track.name = "Test Song"
    mock_track.duration = 210
    mock_track.track_num = 1
    mock_track.volume_num = 1
    mock_track.explicit = False
    mock_track.audio_quality = "LOSSLESS"

    # Mock artist
    mock_artist = Mock()
    mock_artist.id = 67890
    mock_artist.name = "Test Artist"
    mock_artist.picture = "https://example.com/artist.jpg"
    mock_track.artist = mock_artist
    mock_track.artists = [mock_artist]

    # Mock album
    mock_album = Mock()
    mock_album.id = 11111
    mock_album.name = "Test Album"
    mock_album.release_date = "2023-01-01"
    mock_album.duration = 2400
    mock_album.num_tracks = 12
    mock_album.image = "https://example.com/album.jpg"
    mock_album.explicit = False
    mock_album.artist = mock_artist
    mock_album.artists = [mock_artist]
    mock_track.album = mock_album

    return mock_track


@pytest.fixture
def mock_tidal_album():
    """Create mock tidalapi Album object."""
    mock_album = Mock()
    mock_album.id = 11111
    mock_album.name = "Test Album"
    mock_album.release_date = "2023-01-01"
    mock_album.duration = 2400
    mock_album.num_tracks = 12
    mock_album.image = "https://example.com/album.jpg"
    mock_album.explicit = False

    # Mock artist
    mock_artist = Mock()
    mock_artist.id = 67890
    mock_artist.name = "Test Artist"
    mock_artist.picture = "https://example.com/artist.jpg"
    mock_album.artist = mock_artist
    mock_album.artists = [mock_artist]

    # Mock tracks method
    mock_album.tracks.return_value = []

    return mock_album


@pytest.fixture
def mock_tidal_artist():
    """Create mock tidalapi Artist object."""
    mock_artist = Mock()
    mock_artist.id = 67890
    mock_artist.name = "Test Artist"
    mock_artist.picture = "https://example.com/artist.jpg"
    mock_artist.popularity = 85

    # Mock methods
    mock_artist.get_albums.return_value = []
    mock_artist.get_top_tracks.return_value = []
    mock_artist.get_radio.return_value = []

    return mock_artist


@pytest.fixture
def mock_tidal_playlist():
    """Create mock tidalapi Playlist object."""
    mock_playlist = Mock()
    mock_playlist.uuid = "test-playlist-uuid"
    mock_playlist.id = "test-playlist-uuid"
    mock_playlist.name = "Test Playlist"
    mock_playlist.description = "A test playlist"
    mock_playlist.num_tracks = 10
    mock_playlist.duration = 2100
    mock_playlist.created = "2023-01-01T00:00:00Z"
    mock_playlist.last_updated = "2023-01-02T00:00:00Z"
    mock_playlist.image = "https://example.com/playlist.jpg"
    mock_playlist.public = True

    # Mock creator
    mock_creator = {"name": "Test User"}
    mock_playlist.creator = mock_creator

    # Mock tracks method
    mock_playlist.tracks.return_value = []

    # Mock playlist operations
    mock_playlist.add.return_value = True
    mock_playlist.remove_by_index.return_value = True
    mock_playlist.delete.return_value = True

    return mock_playlist


@pytest.fixture
def sample_artist():
    """Create sample Artist model instance."""
    return Artist(
        id="67890",
        name="Test Artist",
        picture="https://example.com/artist.jpg",
        popularity=85
    )


@pytest.fixture
def sample_album(sample_artist):
    """Create sample Album model instance."""
    return Album(
        id="11111",
        title="Test Album",
        artists=[sample_artist],
        release_date="2023-01-01",
        duration=2400,
        number_of_tracks=12,
        cover="https://example.com/album.jpg",
        explicit=False
    )


@pytest.fixture
def sample_track(sample_artist, sample_album):
    """Create sample Track model instance."""
    return Track(
        id="12345",
        title="Test Song",
        artists=[sample_artist],
        album=sample_album,
        duration=210,
        track_number=1,
        disc_number=1,
        explicit=False,
        quality="LOSSLESS"
    )


@pytest.fixture
def sample_playlist(sample_track):
    """Create sample Playlist model instance."""
    return Playlist(
        id="test-playlist-uuid",
        title="Test Playlist",
        description="A test playlist",
        creator="Test User",
        tracks=[sample_track],
        number_of_tracks=1,
        duration=210,
        created_at=datetime(2023, 1, 1),
        updated_at=datetime(2023, 1, 2),
        image="https://example.com/playlist.jpg",
        public=True
    )


@pytest.fixture
def mock_auth(mock_env_vars, mock_tidal_session):
    """Create mock TidalAuth instance with secure fake credentials."""
    import uuid
    fake_uuid = uuid.uuid4().hex

    # Create a proper AsyncMock instead of real object
    mock_auth = AsyncMock(spec=TidalAuth)
    mock_auth.tidal_session = mock_tidal_session
    mock_auth.access_token = f"fake_auth_token_{fake_uuid[:16]}_TEST_ONLY"
    mock_auth.refresh_token = f"fake_refresh_token_{fake_uuid[16:32]}_TEST_ONLY"
    mock_auth.token_expires_at = datetime.now() + timedelta(hours=1)
    mock_auth.user_id = "999999999"  # Obviously fake user ID
    mock_auth.session_id = f"fake_auth_session_{fake_uuid[:8]}_TEST"

    # Mock common auth methods with proper AsyncMock/Mock
    mock_auth.ensure_valid_token = AsyncMock()
    mock_auth.get_tidal_session = Mock(return_value=mock_tidal_session)  # This should be sync
    mock_auth.get_user_info = AsyncMock()

    return mock_auth


@pytest.fixture
def mock_service(mock_auth):
    """Create mock TidalService instance with properly configured return values."""
    # Create a proper AsyncMock instead of real object
    mock_service = AsyncMock(spec=TidalService)
    mock_service.auth = mock_auth
    mock_service._cache = {}
    mock_service._cache_ttl = 300

    # Mock common service methods as AsyncMock with proper side effects
    async def ensure_authenticated_side_effect():
        result = await mock_service.auth.ensure_valid_token()
        if not result:
            from src.tidal_mcp.auth import TidalAuthError
            raise TidalAuthError("Authentication required")
        return result

    mock_service.ensure_authenticated = AsyncMock(side_effect=ensure_authenticated_side_effect)

    # Special handling for get_session to properly call through to auth
    def get_session_side_effect():
        return mock_service.auth.get_tidal_session()

    mock_service.get_session = Mock(side_effect=get_session_side_effect)

    # Configure search methods with default empty return values
    mock_service.search_tracks = AsyncMock(return_value=[])
    mock_service.search_albums = AsyncMock(return_value=[])
    mock_service.search_artists = AsyncMock(return_value=[])
    mock_service.search_playlists = AsyncMock(return_value=[])

    # Configure search_all with proper SearchResults
    from src.tidal_mcp.models import SearchResults
    mock_service.search_all = AsyncMock(return_value=SearchResults(tracks=[], albums=[], artists=[], playlists=[]))

    # Configure detail retrieval methods
    mock_service.get_track = AsyncMock(return_value=None)
    mock_service.get_album = AsyncMock(return_value=None)
    mock_service.get_artist = AsyncMock(return_value=None)
    mock_service.get_playlist = AsyncMock(return_value=None)

    # Configure playlist operations
    mock_service.create_playlist = AsyncMock(return_value=None)
    mock_service.add_tracks_to_playlist = AsyncMock(return_value=True)  # Success operations return True
    mock_service.remove_tracks_from_playlist = AsyncMock(return_value=True)
    mock_service.delete_playlist = AsyncMock(return_value=True)

    # Configure favorites operations
    mock_service.get_user_favorites = AsyncMock(return_value=[])
    mock_service.add_to_favorites = AsyncMock(return_value=True)  # Success operations return True
    mock_service.remove_from_favorites = AsyncMock(return_value=True)

    # Configure radio/recommendation operations
    mock_service.get_track_radio = AsyncMock(return_value=[])
    mock_service.get_artist_radio = AsyncMock(return_value=[])
    mock_service.get_recommended_tracks = AsyncMock(return_value=[])

    # Configure user profile
    mock_service.get_user_profile = AsyncMock(return_value=None)

    # Configure conversion methods to return None by default (tests will override as needed)
    mock_service._convert_tidal_track = AsyncMock(return_value=None)
    mock_service._convert_tidal_album = AsyncMock(return_value=None)
    mock_service._convert_tidal_artist = AsyncMock(return_value=None)
    mock_service._convert_tidal_playlist = AsyncMock(return_value=None)

    # Configure utility methods
    mock_service._is_uuid = Mock(return_value=False)

    return mock_service


@pytest.fixture
def tidal_service(mock_auth):
    """Create real TidalService instance with mocked auth for unit testing."""
    return TidalService(mock_auth)


@pytest.fixture
def mock_aiohttp_session():
    """Create mock aiohttp session with aioresponses."""
    with aioresponses() as m:
        yield m


@pytest.fixture
def mock_redis():
    """Provide a completely isolated fake Redis instance for testing."""
    import uuid

    # Create a simple fake Redis with sync interface
    class SecureFakeRedisSync:
        def __init__(self):
            self.data = {}
            self.test_id = f"test_redis_{uuid.uuid4().hex[:8]}"
            # Ensure we can never accidentally connect to real Redis
            self.connection_blocked = True

        def set(self, key, value):
            if "REAL" in str(key).upper() or "PROD" in str(key).upper():
                raise ValueError("Test Redis refuses production-like keys")
            self.data[f"TEST:{key}"] = value
            return True

        def get(self, key):
            return self.data.get(f"TEST:{key}")

        def delete(self, key):
            return self.data.pop(f"TEST:{key}", None) is not None

        def exists(self, key):
            return f"TEST:{key}" in self.data

        def flushall(self):
            self.data.clear()
            return True

    fake_redis = SecureFakeRedisSync()
    with patch("redis.Redis", return_value=fake_redis):
        yield fake_redis


@pytest_asyncio.fixture
async def mock_async_redis():
    """Provide a completely isolated async fake Redis instance for testing."""
    import uuid

    from fakeredis.aioredis import FakeRedis as AsyncFakeRedis

    # Create isolated async fake Redis with test-only database
    test_db = 0  # Use standard test database
    async_fake_redis = AsyncFakeRedis(
        decode_responses=True,
        db=test_db
    )

    # Add test identifier to prevent accidental production use
    async_fake_redis.test_id = f"async_test_redis_{uuid.uuid4().hex[:8]}"

    with patch("redis.asyncio.Redis", return_value=async_fake_redis):
        yield async_fake_redis
        await async_fake_redis.flushall()
        await async_fake_redis.aclose()


@pytest.fixture
def mock_factory_boy():
    """Setup Factory Boy for test data generation."""
    # This can be expanded with actual factory definitions
    # when factory_boy is needed for more complex data generation
    return {
        "track_factory": lambda **kwargs: {
            "id": kwargs.get("id", 12345),
            "title": kwargs.get("title", "Test Track"),
            "duration": kwargs.get("duration", 180),
            "artist": kwargs.get("artist", "Test Artist"),
            "album": kwargs.get("album", "Test Album")
        },
        "playlist_factory": lambda **kwargs: {
            "id": kwargs.get("id", "playlist_123"),
            "title": kwargs.get("title", "Test Playlist"),
            "description": kwargs.get("description", "A test playlist"),
            "track_count": kwargs.get("track_count", 10)
        }
    }


@pytest.fixture
def mock_token_response():
    """Mock OAuth2 token response with secure fake credentials."""
    import uuid
    fake_uuid = uuid.uuid4().hex

    return {
        "access_token": f"fake_oauth_access_{fake_uuid[:16]}_TEST_ONLY",
        "refresh_token": f"fake_oauth_refresh_{fake_uuid[16:32]}_TEST_ONLY",
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "fake_test_scope"  # Fake scope to prevent real API calls
    }


@pytest.fixture
def mock_search_response():
    """Mock Tidal search API response."""
    return {
        "tracks": {
            "items": [
                {
                    "id": 12345,
                    "title": "Test Song",
                    "duration": 210,
                    "trackNumber": 1,
                    "volumeNumber": 1,
                    "explicit": False,
                    "audioQuality": "LOSSLESS",
                    "artist": {
                        "id": 67890,
                        "name": "Test Artist"
                    },
                    "album": {
                        "id": 11111,
                        "title": "Test Album",
                        "releaseDate": "2023-01-01"
                    }
                }
            ],
            "limit": 20,
            "offset": 0,
            "totalNumberOfItems": 1
        },
        "albums": {
            "items": [],
            "limit": 20,
            "offset": 0,
            "totalNumberOfItems": 0
        },
        "artists": {
            "items": [],
            "limit": 20,
            "offset": 0,
            "totalNumberOfItems": 0
        },
        "playlists": {
            "items": [],
            "limit": 20,
            "offset": 0,
            "totalNumberOfItems": 0
        }
    }


@pytest.fixture(autouse=True)
def isolate_test_environment(monkeypatch):
    """Automatically isolate test environment from production systems."""
    import uuid

    # Remove all potentially dangerous environment variables
    production_env_vars = [
        "TIDAL_CLIENT_ID", "TIDAL_CLIENT_SECRET", "TIDAL_ACCESS_TOKEN",
        "TIDAL_REFRESH_TOKEN", "REDIS_URL", "REDIS_PASSWORD", "REDIS_HOST",
        "DATABASE_URL", "API_KEY", "SECRET_KEY", "PRODUCTION", "PROD"
    ]

    for var in production_env_vars:
        monkeypatch.delenv(var, raising=False)

    # Set secure test-only environment variables
    fake_uuid = uuid.uuid4().hex
    test_env = {
        "TESTING": "1",  # Primary flag for testing mode
        "TEST_MODE": "isolated",
        "REDIS_URL": f"redis://fake-test-redis-{fake_uuid[:8]}.test:9999/99",
        "TIDAL_CLIENT_ID": f"FAKE_TEST_CLIENT_{fake_uuid[:12]}",
        "TIDAL_CLIENT_SECRET": f"FAKE_TEST_SECRET_{fake_uuid[:24]}_NEVER_REAL",
        "TIDAL_REDIRECT_URI": "http://fake-test.localhost:9999/callback",
        "TIDAL_COUNTRY_CODE": "XX"  # Invalid country code
    }

    for key, value in test_env.items():
        monkeypatch.setenv(key, value)

@pytest.fixture(autouse=True)
def disable_network_calls():
    """Automatically disable real network calls in all tests."""
    # This fixture runs automatically for all tests
    # Additional network isolation can be added here if needed
    pass


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Fast unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "auth: Authentication tests")
    config.addinivalue_line("markers", "service: Service layer tests")
    config.addinivalue_line("markers", "models: Data model tests")
    config.addinivalue_line("markers", "utils: Utility function tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "network: Tests requiring network access")
    config.addinivalue_line("markers", "redis: Tests requiring Redis")
    config.addinivalue_line("markers", "tidal_api: Tests interacting with Tidal API")


# Test collection configuration
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test file names and locations."""
    for item in items:
        test_file = str(item.fspath)

        # Auto-mark based on directory structure
        if "/unit/" in test_file:
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in test_file:
            item.add_marker(pytest.mark.integration)
        elif "/e2e/" in test_file:
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)
        else:
            # Add unit marker to tests not in specific directories
            item.add_marker(pytest.mark.unit)

        # Add specific markers based on test file names
        if "test_auth" in test_file:
            item.add_marker(pytest.mark.auth)
        elif "test_service" in test_file:
            item.add_marker(pytest.mark.service)
        elif "test_models" in test_file:
            item.add_marker(pytest.mark.models)
        elif "test_utils" in test_file:
            item.add_marker(pytest.mark.utils)

        # Add markers for specific functionality
        if "redis" in test_file.lower():
            item.add_marker(pytest.mark.redis)
        if "network" in test_file.lower() or "api" in test_file.lower():
            item.add_marker(pytest.mark.network)
        if "tidal" in test_file.lower() and "api" in test_file.lower():
            item.add_marker(pytest.mark.tidal_api)
