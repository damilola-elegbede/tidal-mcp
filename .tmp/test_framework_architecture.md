# Comprehensive Test Framework Architecture for Tidal MCP

## Project Analysis

**Current Status:**
- **Total MCP Tools:** 22 (15 in server.py + 7 in production/enhanced_tools.py)
- **Core Modules:** auth.py, service.py, server.py, models.py, utils.py, production/
- **Dependencies:** aiohttp, tidalapi, fastmcp, asyncio-throttle, cryptography, python-dotenv
- **Target Coverage:** 85% with 80% minimum unit test coverage
- **Performance Target:** < 30 seconds full test suite execution

## 1. Framework Architecture Design

### 1.1 Testing Stack Configuration

```toml
# pyproject.toml additions for testing dependencies
[project.optional-dependencies]
test = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "aioresponses>=0.7.4",
    "pytest-mock>=3.11.0",
    "faker>=19.0.0",
    "freezegun>=1.2.0",
    "pytest-xdist>=3.3.0",  # For parallel execution
    "pytest-timeout>=2.1.0",  # For timeout control
    "pytest-benchmark>=4.0.0",  # For performance testing
    "httpx>=0.24.0",  # For async HTTP testing
    "respx>=0.20.0",  # HTTP mocking for httpx
]
```

### 1.2 Pytest Configuration (pytest.ini)

```ini
[tool:pytest]
minversion = 7.0
addopts =
    --strict-markers
    --strict-config
    --asyncio-mode=auto
    --cov=src/tidal_mcp
    --cov-report=html:htmlcov
    --cov-report=xml:coverage.xml
    --cov-report=term-missing
    --cov-fail-under=80
    --cov-exclude=src/tidal_mcp/__main__.py
    --cov-exclude=src/tidal_mcp/production/middleware.py
    -v
    --tb=short
    --timeout=300
    --durations=10
    -x
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Tests that take more than 1 second
    auth: Authentication related tests
    redis: Tests requiring Redis
    network: Tests making network calls
    mcp: MCP tool tests
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
    error::UserWarning
```

### 1.3 Coverage Configuration

```toml
# pyproject.toml coverage configuration
[tool.coverage.run]
source = ["src/tidal_mcp"]
omit = [
    "src/tidal_mcp/__main__.py",
    "src/tidal_mcp/production/middleware.py",  # Complex external dependency
    "tests/*",
    "examples/*",
    ".venv/*",
    "*/__pycache__/*",
]
branch = true
concurrency = ["thread", "multiprocessing"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod",
    "except ImportError:",
    "except ModuleNotFoundError:",
]
show_missing = true
skip_covered = false
precision = 2
```

## 2. Test Directory Structure

```
tests/
├── __init__.py
├── conftest.py                 # Global fixtures and configuration
├── unit/                       # Unit tests (80%+ coverage target)
│   ├── __init__.py
│   ├── test_auth.py           # TidalAuth class tests
│   ├── test_service.py        # TidalService class tests
│   ├── test_models.py         # Data models tests
│   ├── test_utils.py          # Utility functions tests
│   └── production/
│       ├── __init__.py
│       └── test_enhanced_tools.py
├── integration/                # Integration tests for MCP tools
│   ├── __init__.py
│   ├── test_mcp_tools_basic.py       # Basic MCP tools (auth, search, etc.)
│   ├── test_mcp_tools_playlists.py   # Playlist management tools
│   ├── test_mcp_tools_favorites.py   # Favorites management tools
│   ├── test_mcp_tools_recommendations.py # Recommendation tools
│   ├── test_mcp_tools_metadata.py    # Track/album/artist detail tools
│   └── production/
│       ├── __init__.py
│       ├── test_enhanced_auth.py     # Enhanced auth tools
│       ├── test_streaming_urls.py    # Streaming URL generation
│       ├── test_advanced_search.py   # Advanced search features
│       └── test_system_monitoring.py # Health check and monitoring
├── e2e/                        # End-to-end tests
│   ├── __init__.py
│   ├── test_complete_workflows.py    # Complete user workflows
│   ├── test_authentication_flow.py  # Full auth workflow
│   └── test_playlist_management.py  # Complete playlist operations
├── fixtures/                   # Test data and fixtures
│   ├── __init__.py
│   ├── tidal_responses/        # Mock Tidal API responses
│   │   ├── search_responses.json
│   │   ├── track_responses.json
│   │   ├── playlist_responses.json
│   │   └── auth_responses.json
│   ├── test_data.py           # Test data factories
│   └── factories.py           # Data model factories
└── utils/                      # Test utilities
    ├── __init__.py
    ├── mock_helpers.py         # Mock creation helpers
    ├── async_helpers.py        # Async test utilities
    └── assertion_helpers.py    # Custom assertions
```

## 3. Core Testing Patterns

### 3.1 Async Testing Pattern

```python
# tests/conftest.py - Core async fixtures
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
import aioresponses
from src.tidal_mcp.auth import TidalAuth
from src.tidal_mcp.service import TidalService

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def mock_auth():
    """Mock authenticated TidalAuth instance."""
    auth = Mock(spec=TidalAuth)
    auth.is_authenticated.return_value = True
    auth.get_user_info.return_value = {
        "id": "test_user_123",
        "username": "testuser",
        "country_code": "US"
    }
    auth.access_token = "mock_access_token"
    auth.country_code = "US"
    auth.session_id = "mock_session_id"
    return auth

@pytest.fixture
async def mock_service(mock_auth):
    """Mock TidalService with authenticated auth manager."""
    service = Mock(spec=TidalService)
    service.auth_manager = mock_auth
    return service

@pytest.fixture
def mock_tidal_api_responses():
    """Fixture providing aioresponses for mocking HTTP calls."""
    with aioresponses.aioresponses() as m:
        yield m
```

### 3.2 Test Data Factories

```python
# tests/fixtures/factories.py
import factory
from datetime import datetime, timezone
from src.tidal_mcp.models import Track, Album, Artist, Playlist

class TrackFactory(factory.Factory):
    class Meta:
        model = Track

    id = factory.Sequence(lambda n: f"track_{n}")
    title = factory.Faker("sentence", nb_words=3)
    artist_names = factory.List([factory.Faker("name") for _ in range(2)])
    album_title = factory.Faker("sentence", nb_words=2)
    duration = factory.Faker("random_int", min=120, max=300)
    track_number = factory.Faker("random_int", min=1, max=15)
    quality = "HIGH"
    explicit = False

class AlbumFactory(factory.Factory):
    class Meta:
        model = Album

    id = factory.Sequence(lambda n: f"album_{n}")
    title = factory.Faker("sentence", nb_words=2)
    artist_names = factory.List([factory.Faker("name")])
    release_date = factory.Faker("date_object")
    number_of_tracks = factory.Faker("random_int", min=8, max=20)
    duration = factory.Faker("random_int", min=2000, max=4000)

class PlaylistFactory(factory.Factory):
    class Meta:
        model = Playlist

    id = factory.Sequence(lambda n: f"playlist_{n}")
    title = factory.Faker("sentence", nb_words=2)
    description = factory.Faker("text", max_nb_chars=200)
    number_of_tracks = factory.Faker("random_int", min=10, max=100)
    duration = factory.Faker("random_int", min=2000, max=6000)
    creator = factory.Faker("name")
    tracks = factory.SubFactory(TrackFactory)
```

### 3.3 MCP Tool Testing Pattern

```python
# tests/utils/mcp_test_helpers.py
import pytest
from unittest.mock import AsyncMock, patch

class MCPToolTester:
    """Helper class for testing MCP tools with consistent patterns."""

    def __init__(self, tool_function):
        self.tool_function = tool_function

    async def test_authentication_required(self):
        """Test that tool requires authentication."""
        with patch('src.tidal_mcp.server.ensure_service') as mock_ensure:
            mock_ensure.side_effect = TidalAuthError("Not authenticated")

            result = await self.tool_function(test_param="value")

            assert "error" in result
            assert "Authentication required" in result["error"]

    async def test_with_valid_auth(self, mock_service, **kwargs):
        """Test tool with valid authentication."""
        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await self.tool_function(**kwargs)
            return result

    async def test_error_handling(self, mock_service, exception_type, **kwargs):
        """Test error handling for various exception types."""
        mock_service.side_effect = exception_type("Test error")

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await self.tool_function(**kwargs)

        assert "error" in result
        return result
```

## 4. Performance Testing Strategy

### 4.1 Execution Time Optimization

```python
# tests/conftest.py - Performance fixtures
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
def fast_test_execution():
    """Ensure individual tests complete quickly."""
    import asyncio
    # Reduce default timeouts for faster failure detection
    original_timeout = asyncio._get_running_loop()._default_timeout if hasattr(asyncio, '_get_running_loop') else None
    yield
    # Reset timeout if needed

# Parallel execution configuration
# pytest-xdist configuration for parallel test execution
# Add to pytest.ini:
# addopts = -n auto  # Use all available CPUs
```

### 4.2 Test Isolation Strategy

```python
# tests/conftest.py - Isolation fixtures
@pytest.fixture(autouse=True)
async def clean_global_state():
    """Ensure clean global state between tests."""
    # Reset global variables
    import src.tidal_mcp.server as server_module
    import src.tidal_mcp.production.enhanced_tools as enhanced_module

    # Store original state
    original_auth = server_module.auth_manager
    original_service = server_module.tidal_service
    original_enhanced_auth = enhanced_module.auth_manager
    original_enhanced_service = enhanced_module.tidal_service

    # Reset for test
    server_module.auth_manager = None
    server_module.tidal_service = None
    enhanced_module.auth_manager = None
    enhanced_module.tidal_service = None

    yield

    # Restore original state
    server_module.auth_manager = original_auth
    server_module.tidal_service = original_service
    enhanced_module.auth_manager = original_enhanced_auth
    enhanced_module.tidal_service = original_enhanced_service
```

## 5. Mocking Strategy

### 5.1 Tidal API Mocking with aioresponses

```python
# tests/fixtures/tidal_responses.py
MOCK_SEARCH_RESPONSE = {
    "tracks": [
        {
            "id": "123456789",
            "title": "Test Track",
            "artist": {"name": "Test Artist"},
            "album": {"title": "Test Album"},
            "duration": 180,
            "trackNumber": 1,
            "quality": "HIGH"
        }
    ],
    "albums": [],
    "artists": [],
    "playlists": []
}

MOCK_AUTH_RESPONSE = {
    "access_token": "mock_access_token",
    "refresh_token": "mock_refresh_token",
    "expires_in": 3600,
    "user": {
        "id": "test_user_123",
        "username": "testuser",
        "countryCode": "US"
    }
}

# tests/utils/mock_helpers.py
def setup_tidal_api_mocks(aioresponses_mock):
    """Setup comprehensive Tidal API mocks."""
    # Search endpoints
    aioresponses_mock.get(
        "https://api.tidalhifi.com/v1/search",
        payload=MOCK_SEARCH_RESPONSE
    )

    # Authentication endpoints
    aioresponses_mock.post(
        "https://auth.tidal.com/v1/oauth2/token",
        payload=MOCK_AUTH_RESPONSE
    )

    # Track details
    aioresponses_mock.get(
        re.compile(r"https://api\.tidalhifi\.com/v1/tracks/\d+"),
        payload={"id": "123", "title": "Test Track"}
    )
```

### 5.2 Redis Mocking for Production Tools

```python
# tests/fixtures/redis_mocks.py
from unittest.mock import AsyncMock, Mock

@pytest.fixture
async def mock_redis():
    """Mock Redis client for rate limiting tests."""
    redis_mock = AsyncMock()
    redis_mock.get.return_value = "0"  # No rate limit hit
    redis_mock.incr.return_value = 1
    redis_mock.expire.return_value = True
    redis_mock.ping.return_value = True
    return redis_mock

@pytest.fixture
async def mock_middleware_stack(mock_redis):
    """Mock middleware stack for production tool tests."""
    from src.tidal_mcp.production.middleware import MiddlewareStack

    middleware = Mock(spec=MiddlewareStack)
    middleware.rate_limiter = Mock()
    middleware.rate_limiter.is_allowed = AsyncMock(return_value=True)
    middleware.observability = Mock()
    middleware.observability.get_metrics.return_value = {}

    return middleware
```

## 6. Integration Test Patterns

### 6.1 MCP Tool Integration Tests

```python
# tests/integration/test_mcp_tools_basic.py
import pytest
from unittest.mock import patch, AsyncMock
from src.tidal_mcp.server import tidal_login, tidal_search, tidal_get_track

class TestMCPToolsIntegration:
    """Integration tests for basic MCP tools."""

    @pytest.mark.integration
    @pytest.mark.auth
    async def test_login_flow(self, mock_tidal_api_responses):
        """Test complete login flow with mocked API."""
        setup_tidal_api_mocks(mock_tidal_api_responses)

        result = await tidal_login()

        assert result["success"] is True
        assert "user" in result
        assert result["user"]["id"] == "test_user_123"

    @pytest.mark.integration
    @pytest.mark.mcp
    async def test_search_integration(self, mock_auth, mock_service, mock_tidal_api_responses):
        """Test search tool with complete service integration."""
        # Setup mock service responses
        mock_service.search_all = AsyncMock()
        mock_service.search_all.return_value = Mock(
            to_dict=lambda: MOCK_SEARCH_RESPONSE,
            total_results=1
        )

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await tidal_search("test query", "all", 20, 0)

        assert "error" not in result
        assert result["query"] == "test query"
        assert result["content_type"] == "all"
        assert "results" in result

    @pytest.mark.integration
    @pytest.mark.parametrize("content_type,expected_method", [
        ("tracks", "search_tracks"),
        ("albums", "search_albums"),
        ("artists", "search_artists"),
        ("playlists", "search_playlists"),
        ("all", "search_all")
    ])
    async def test_search_content_types(self, mock_service, content_type, expected_method):
        """Test search with different content types."""
        mock_method = AsyncMock()
        setattr(mock_service, expected_method, mock_method)

        if content_type == "all":
            mock_method.return_value = Mock(
                to_dict=lambda: {"tracks": [], "albums": [], "artists": [], "playlists": []},
                total_results=0
            )
        else:
            mock_method.return_value = []

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await tidal_search("test", content_type)

        mock_method.assert_called_once()
        assert "error" not in result
```

### 6.2 Production Tools Integration Tests

```python
# tests/integration/production/test_enhanced_auth.py
import pytest
from unittest.mock import patch, AsyncMock
from src.tidal_mcp.production.enhanced_tools import tidal_login, refresh_session

class TestEnhancedAuthIntegration:
    """Integration tests for enhanced authentication tools."""

    @pytest.mark.integration
    @pytest.mark.auth
    async def test_enhanced_login_with_middleware(self, mock_middleware_stack, mock_redis):
        """Test enhanced login with middleware integration."""
        with patch('src.tidal_mcp.production.enhanced_tools.middleware_stack', mock_middleware_stack):
            # Mock the middleware decorator
            mock_middleware_stack.middleware = lambda **kwargs: lambda func: func

            result = await tidal_login()

            assert "success" in result
            if result["success"]:
                assert "session_info" in result
                assert "security" in result

    @pytest.mark.integration
    @pytest.mark.auth
    async def test_session_refresh_integration(self, mock_auth, mock_middleware_stack):
        """Test session refresh with complete integration."""
        mock_auth.refresh_access_token = AsyncMock(return_value=True)
        mock_auth.token_expires_at = None

        with patch('src.tidal_mcp.production.enhanced_tools.auth_manager', mock_auth):
            with patch('src.tidal_mcp.production.enhanced_tools.middleware_stack', mock_middleware_stack):
                mock_middleware_stack.middleware = lambda **kwargs: lambda func: func

                result = await refresh_session()

        assert result["success"] is True
        assert "session_info" in result
        mock_auth.refresh_access_token.assert_called_once()
```

## 7. End-to-End Test Patterns

### 7.1 Complete Workflow Tests

```python
# tests/e2e/test_complete_workflows.py
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteWorkflows:
    """End-to-end tests for complete user workflows."""

    async def test_discover_music_workflow(self, mock_tidal_api_responses):
        """Test complete music discovery workflow."""
        setup_tidal_api_mocks(mock_tidal_api_responses)

        # 1. Authenticate
        from src.tidal_mcp.server import tidal_login
        login_result = await tidal_login()
        assert login_result["success"] is True

        # 2. Search for music
        from src.tidal_mcp.server import tidal_search
        search_result = await tidal_search("jazz piano", "tracks", 5)
        assert "results" in search_result

        # 3. Get track details
        if search_result.get("results", {}).get("tracks"):
            track_id = search_result["results"]["tracks"][0]["id"]
            from src.tidal_mcp.server import tidal_get_track
            track_result = await tidal_get_track(track_id)
            assert track_result["success"] is True

        # 4. Add to favorites
        from src.tidal_mcp.server import tidal_add_favorite
        favorite_result = await tidal_add_favorite(track_id, "track")
        assert favorite_result["success"] is True

    async def test_playlist_management_workflow(self, mock_tidal_api_responses):
        """Test complete playlist management workflow."""
        setup_tidal_api_mocks(mock_tidal_api_responses)

        # 1. Authenticate
        from src.tidal_mcp.server import tidal_login
        await tidal_login()

        # 2. Create playlist
        from src.tidal_mcp.server import tidal_create_playlist
        playlist_result = await tidal_create_playlist("Test Playlist", "E2E Test")
        assert playlist_result["success"] is True
        playlist_id = playlist_result["playlist"]["id"]

        # 3. Search for tracks
        from src.tidal_mcp.server import tidal_search
        search_result = await tidal_search("test music", "tracks", 3)
        track_ids = [t["id"] for t in search_result.get("results", {}).get("tracks", [])]

        # 4. Add tracks to playlist
        if track_ids:
            from src.tidal_mcp.server import tidal_add_to_playlist
            add_result = await tidal_add_to_playlist(playlist_id, track_ids)
            assert add_result["success"] is True

        # 5. Get playlist details
        from src.tidal_mcp.server import tidal_get_playlist
        playlist_details = await tidal_get_playlist(playlist_id, True)
        assert playlist_details["success"] is True
        assert len(playlist_details["playlist"]["tracks"]) == len(track_ids)
```

## 8. Test Execution Strategy

### 8.1 Test Categories and Execution

```bash
# Fast unit tests (< 10 seconds)
pytest tests/unit/ -m "not slow" --maxfail=5

# Integration tests (< 15 seconds)
pytest tests/integration/ -m "not slow" --maxfail=3

# Full test suite with coverage (< 30 seconds)
pytest tests/ --cov=src/tidal_mcp --cov-report=html --maxfail=10

# Parallel execution for speed
pytest tests/ -n auto --dist=loadfile

# Performance-focused execution
pytest tests/ --benchmark-only --benchmark-sort=mean
```

### 8.2 CI/CD Integration Commands

```yaml
# .github/workflows/test.yml excerpt
- name: Run Unit Tests
  run: |
    pytest tests/unit/ \
      --cov=src/tidal_mcp \
      --cov-report=xml \
      --cov-fail-under=80 \
      --timeout=300 \
      --maxfail=5

- name: Run Integration Tests
  run: |
    pytest tests/integration/ \
      --timeout=600 \
      --maxfail=3

- name: Validate Performance
  run: |
    timeout 30s pytest tests/ || (echo "Test suite exceeded 30 second limit" && exit 1)
```

## 9. Quality Gates and Coverage

### 9.1 Coverage Targets by Module

- **Unit Tests:** 85% minimum coverage
- **auth.py:** 95% (critical authentication logic)
- **service.py:** 90% (core business logic)
- **server.py:** 85% (MCP tools)
- **models.py:** 95% (data structures)
- **utils.py:** 90% (utility functions)
- **production/enhanced_tools.py:** 80% (complex production features)

### 9.2 Quality Metrics

- **Test Execution Time:** < 30 seconds for full suite
- **Individual Test Timeout:** 5 seconds max
- **Memory Usage:** < 500MB during test execution
- **Test Reliability:** 99.9% pass rate (no flaky tests)
- **Branch Coverage:** 80% minimum

## 10. Implementation Checklist

### Phase 1: Foundation (Days 1-2)
- [ ] Install test dependencies in pyproject.toml
- [ ] Create pytest.ini with coverage configuration
- [ ] Setup test directory structure
- [ ] Create base fixtures in conftest.py
- [ ] Implement mock helpers and test utilities

### Phase 2: Unit Tests (Days 3-4)
- [ ] Write comprehensive auth.py unit tests
- [ ] Write service.py unit tests with mocking
- [ ] Write models.py unit tests
- [ ] Write utils.py unit tests
- [ ] Achieve 80%+ unit test coverage

### Phase 3: Integration Tests (Days 5-6)
- [ ] Test all 15 basic MCP tools
- [ ] Test all 7 enhanced production tools
- [ ] Test authentication flows
- [ ] Test error handling patterns
- [ ] Validate middleware integration

### Phase 4: E2E and Performance (Day 7)
- [ ] Implement complete workflow tests
- [ ] Performance optimization for < 30s execution
- [ ] Parallel test execution setup
- [ ] CI/CD integration testing
- [ ] Final coverage validation (85% target)

This architecture provides a comprehensive, production-ready testing framework that meets all specification requirements while ensuring high code quality, fast execution, and reliable test coverage for the Tidal MCP project.