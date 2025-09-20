"""
Global test configuration and fixtures for Tidal MCP tests.

This module provides shared fixtures, mock objects, and test utilities
for comprehensive testing of the Tidal MCP server implementation.
"""

import asyncio
import re
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import aioresponses
import pytest
from faker import Faker

from src.tidal_mcp.auth import TidalAuth
from src.tidal_mcp.models import Album, Artist, Playlist, Track
from src.tidal_mcp.service import TidalService

# Initialize faker for generating test data
fake = Faker()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def performance_monitor():
    """Monitor test execution times and fail if suite exceeds 30 seconds."""
    import time
    start_time = time.time()
    yield
    total_time = time.time() - start_time
    if total_time > 30:
        pytest.fail(f"Test suite took {total_time:.2f}s, exceeding 30s limit")


@pytest.fixture(autouse=True)
async def clean_global_state():
    """Ensure clean global state between tests."""
    # Reset global variables in both server modules
    import src.tidal_mcp.server as server_module
    try:
        import src.tidal_mcp.production.enhanced_tools as enhanced_module
        enhanced_available = True
    except ImportError:
        enhanced_available = False

    # Store original state
    original_auth = server_module.auth_manager
    original_service = server_module.tidal_service

    if enhanced_available:
        original_enhanced_auth = enhanced_module.auth_manager
        original_enhanced_service = enhanced_module.tidal_service

    # Reset for test
    server_module.auth_manager = None
    server_module.tidal_service = None

    if enhanced_available:
        enhanced_module.auth_manager = None
        enhanced_module.tidal_service = None

    yield

    # Restore original state
    server_module.auth_manager = original_auth
    server_module.tidal_service = original_service

    if enhanced_available:
        enhanced_module.auth_manager = original_enhanced_auth
        enhanced_module.tidal_service = original_enhanced_service


# Authentication Fixtures
@pytest.fixture
def mock_auth():
    """Mock authenticated TidalAuth instance."""
    auth = Mock(spec=TidalAuth)
    auth.is_authenticated.return_value = True
    auth.get_user_info.return_value = {
        "id": "test_user_123",
        "username": "testuser",
        "country_code": "US",
        "subscription": {"type": "PREMIUM"},
    }
    auth.access_token = "mock_access_token"
    auth.refresh_token = "mock_refresh_token"
    auth.country_code = "US"
    auth.session_id = "mock_session_id"
    auth.token_expires_at = datetime.now(timezone.utc)
    auth.refresh_access_token = AsyncMock(return_value=True)
    return auth


@pytest.fixture
def mock_unauthenticated_auth():
    """Mock unauthenticated TidalAuth instance."""
    auth = Mock(spec=TidalAuth)
    auth.is_authenticated.return_value = False
    auth.access_token = None
    auth.refresh_token = None
    return auth


# Service Fixtures
@pytest.fixture
def mock_service(mock_auth):
    """Mock TidalService with authenticated auth manager."""
    service = Mock(spec=TidalService)
    service.auth_manager = mock_auth
    return service


# Test Data Fixtures
@pytest.fixture
def sample_track():
    """Sample track data for testing."""
    return Track(
        id="123456789",
        title="Test Track",
        artist_names=["Test Artist", "Featured Artist"],
        album_title="Test Album",
        duration=180,
        track_number=1,
        quality="HIGH",
        explicit=False,
    )


@pytest.fixture
def sample_tracks():
    """List of sample tracks for testing."""
    return [
        Track(
            id=f"track_{i}",
            title=f"Test Track {i}",
            artist_names=[f"Artist {i}"],
            album_title=f"Album {i}",
            duration=180 + i * 10,
            track_number=i,
            quality="HIGH",
            explicit=False,
        )
        for i in range(1, 6)
    ]


@pytest.fixture
def sample_album():
    """Sample album data for testing."""
    return Album(
        id="album_123",
        title="Test Album",
        artist_names=["Test Artist"],
        release_date=datetime(2023, 1, 1).date(),
        number_of_tracks=12,
        duration=2400,
    )


@pytest.fixture
def sample_artist():
    """Sample artist data for testing."""
    return Artist(
        id="artist_123",
        name="Test Artist",
        picture_url="https://example.com/artist.jpg",
    )


@pytest.fixture
def sample_playlist(sample_tracks):
    """Sample playlist data for testing."""
    return Playlist(
        id="playlist_123",
        title="Test Playlist",
        description="A test playlist",
        number_of_tracks=len(sample_tracks),
        duration=sum(track.duration for track in sample_tracks),
        creator="Test User",
        tracks=sample_tracks,
    )


# HTTP Mocking Fixtures
@pytest.fixture
def mock_tidal_api_responses():
    """Fixture providing aioresponses for mocking HTTP calls."""
    with aioresponses.aioresponses() as m:
        yield m


@pytest.fixture
def tidal_response_data():
    """Standard Tidal API response data for testing."""
    return {
        "search_response": {
            "tracks": [
                {
                    "id": "123456789",
                    "title": "Test Track",
                    "artist": {"name": "Test Artist"},
                    "album": {"title": "Test Album"},
                    "duration": 180,
                    "trackNumber": 1,
                    "quality": "HIGH",
                }
            ],
            "albums": [
                {
                    "id": "album_123",
                    "title": "Test Album",
                    "artist": {"name": "Test Artist"},
                    "releaseDate": "2023-01-01",
                    "numberOfTracks": 12,
                    "duration": 2400,
                }
            ],
            "artists": [
                {
                    "id": "artist_123",
                    "name": "Test Artist",
                    "picture": "https://example.com/artist.jpg",
                }
            ],
            "playlists": [
                {
                    "id": "playlist_123",
                    "title": "Test Playlist",
                    "description": "A test playlist",
                    "numberOfTracks": 5,
                    "duration": 900,
                    "creator": {"name": "Test User"},
                }
            ],
        },
        "auth_response": {
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "expires_in": 3600,
            "user": {
                "id": "test_user_123",
                "username": "testuser",
                "countryCode": "US",
                "subscription": {"type": "PREMIUM"},
            },
        },
        "track_response": {
            "id": "123456789",
            "title": "Test Track",
            "artist": {"name": "Test Artist"},
            "album": {"title": "Test Album"},
            "duration": 180,
            "trackNumber": 1,
            "quality": "HIGH",
            "explicit": False,
        },
        "playlist_response": {
            "id": "playlist_123",
            "title": "Test Playlist",
            "description": "A test playlist",
            "numberOfTracks": 5,
            "duration": 900,
            "creator": {"name": "Test User"},
            "tracks": [
                {
                    "id": f"track_{i}",
                    "title": f"Track {i}",
                    "artist": {"name": f"Artist {i}"},
                    "duration": 180,
                }
                for i in range(1, 6)
            ],
        },
    }


def setup_tidal_api_mocks(aioresponses_mock, response_data):
    """Setup comprehensive Tidal API mocks."""
    # Search endpoints
    aioresponses_mock.get(
        re.compile(r"https://api\.tidalhifi\.com/v1/search.*"),
        payload=response_data["search_response"],
    )

    # Authentication endpoints
    aioresponses_mock.post(
        "https://auth.tidal.com/v1/oauth2/token",
        payload=response_data["auth_response"],
    )

    # Track details
    aioresponses_mock.get(
        re.compile(r"https://api\.tidalhifi\.com/v1/tracks/\d+"),
        payload=response_data["track_response"],
    )

    # Album details
    aioresponses_mock.get(
        re.compile(r"https://api\.tidalhifi\.com/v1/albums/\d+"),
        payload={
            "id": "album_123",
            "title": "Test Album",
            "artist": {"name": "Test Artist"},
            "releaseDate": "2023-01-01",
            "numberOfTracks": 12,
            "duration": 2400,
        },
    )

    # Artist details
    aioresponses_mock.get(
        re.compile(r"https://api\.tidalhifi\.com/v1/artists/\d+"),
        payload={
            "id": "artist_123",
            "name": "Test Artist",
            "picture": "https://example.com/artist.jpg",
        },
    )

    # Playlist details
    aioresponses_mock.get(
        re.compile(r"https://api\.tidalhifi\.com/v1/playlists/[\w-]+"),
        payload=response_data["playlist_response"],
    )

    # User favorites endpoints
    aioresponses_mock.get(
        re.compile(r"https://api\.tidalhifi\.com/v1/users/\w+/favorites.*"),
        payload={"items": []},
    )

    # Playlist creation
    aioresponses_mock.post(
        re.compile(r"https://api\.tidalhifi\.com/v1/users/\w+/playlists"),
        payload={"id": "new_playlist_123", "title": "New Playlist"},
    )

    # Playlist modification endpoints
    aioresponses_mock.post(
        re.compile(r"https://api\.tidalhifi\.com/v1/playlists/[\w-]+/tracks"),
        payload={"status": "OK"},
    )

    aioresponses_mock.delete(
        re.compile(r"https://api\.tidalhifi\.com/v1/playlists/[\w-]+/tracks/\d+"),
        payload={"status": "OK"},
    )


# Redis and Production Tool Fixtures
@pytest.fixture
async def mock_redis():
    """Mock Redis client for rate limiting tests."""
    redis_mock = AsyncMock()
    redis_mock.get.return_value = "0"  # No rate limit hit
    redis_mock.incr.return_value = 1
    redis_mock.expire.return_value = True
    redis_mock.ping.return_value = True
    redis_mock.delete.return_value = True
    return redis_mock


@pytest.fixture
async def mock_middleware_stack(mock_redis):
    """Mock middleware stack for production tool tests."""
    try:
        from src.tidal_mcp.production.middleware import MiddlewareStack
    except ImportError:
        # Return a basic mock if middleware is not available
        middleware = Mock()
        middleware.rate_limiter = Mock()
        middleware.rate_limiter.is_allowed = AsyncMock(return_value=True)
        middleware.observability = Mock()
        middleware.observability.get_metrics.return_value = {}
        middleware.middleware = lambda **kwargs: lambda func: func
        return middleware

    middleware = Mock(spec=MiddlewareStack)
    middleware.rate_limiter = Mock()
    middleware.rate_limiter.is_allowed = AsyncMock(return_value=True)
    middleware.observability = Mock()
    middleware.observability.get_metrics.return_value = {
        "request_counts": {"total": 100, "success": 95, "error": 5},
        "avg_response_times": {"search": 150, "auth": 200, "playlist": 120},
    }
    # Mock the middleware decorator
    middleware.middleware = lambda **kwargs: lambda func: func
    return middleware


# Utility Fixtures
@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    file_path = tmp_path / "test_file.json"
    return file_path


@pytest.fixture
def mock_environment_vars(monkeypatch):
    """Mock environment variables for testing."""
    test_env_vars = {
        "TIDAL_CLIENT_ID": "test_client_id",
        "TIDAL_CLIENT_SECRET": "test_client_secret",
        "REDIS_URL": "redis://localhost:6379",
        "ENVIRONMENT": "test",
        "INSTANCE_ID": "test_instance",
    }
    for key, value in test_env_vars.items():
        monkeypatch.setenv(key, value)
    return test_env_vars


# Test Data Generators
@pytest.fixture
def generate_test_data():
    """Generate various test data objects."""
    def _generate(data_type: str, count: int = 1, **kwargs):
        """Generate test data of specified type."""
        if data_type == "tracks":
            return [
                Track(
                    id=f"track_{i}",
                    title=fake.sentence(nb_words=3),
                    artist_names=[fake.name() for _ in range(fake.random_int(min=1, max=3))],
                    album_title=fake.sentence(nb_words=2),
                    duration=fake.random_int(min=120, max=300),
                    track_number=i,
                    quality=fake.random_element(elements=("HIGH", "LOSSLESS", "LOW")),
                    explicit=fake.boolean(),
                    **kwargs,
                )
                for i in range(1, count + 1)
            ]
        elif data_type == "albums":
            return [
                Album(
                    id=f"album_{i}",
                    title=fake.sentence(nb_words=2),
                    artist_names=[fake.name()],
                    release_date=fake.date_object(),
                    number_of_tracks=fake.random_int(min=8, max=20),
                    duration=fake.random_int(min=2000, max=4000),
                    **kwargs,
                )
                for i in range(1, count + 1)
            ]
        elif data_type == "artists":
            return [
                Artist(
                    id=f"artist_{i}",
                    name=fake.name(),
                    picture_url=fake.image_url(),
                    **kwargs,
                )
                for i in range(1, count + 1)
            ]
        elif data_type == "playlists":
            return [
                Playlist(
                    id=f"playlist_{i}",
                    title=fake.sentence(nb_words=2),
                    description=fake.text(max_nb_chars=200),
                    number_of_tracks=fake.random_int(min=10, max=100),
                    duration=fake.random_int(min=2000, max=6000),
                    creator=fake.name(),
                    tracks=[],  # Empty for now, can be populated as needed
                    **kwargs,
                )
                for i in range(1, count + 1)
            ]
        else:
            raise ValueError(f"Unknown data type: {data_type}")

    return _generate


# Custom pytest markers for better test organization
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as authentication related"
    )
    config.addinivalue_line(
        "markers", "redis: mark test as requiring Redis"
    )
    config.addinivalue_line(
        "markers", "network: mark test as making network calls"
    )
    config.addinivalue_line(
        "markers", "mcp: mark test as MCP tool related"
    )


# Timeout configuration for individual tests
@pytest.fixture(autouse=True)
def test_timeout():
    """Ensure individual tests don't run too long."""
    import signal

    def timeout_handler(signum, frame):
        pytest.fail("Test exceeded 5 second timeout")

    # Set up timeout for individual tests
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(5)  # 5 second timeout per test

    yield

    # Clean up
    signal.alarm(0)
