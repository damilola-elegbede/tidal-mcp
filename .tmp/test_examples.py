"""
Example test implementations showing testing patterns for Tidal MCP.

These examples demonstrate the testing patterns and fixtures for unit,
integration, and end-to-end tests following the framework architecture.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

import src.tidal_mcp.server as server
from src.tidal_mcp.auth import TidalAuth, TidalAuthError
from src.tidal_mcp.service import TidalService

from .conftest_template import setup_tidal_api_mocks

# =============================================================================
# UNIT TEST EXAMPLES
# =============================================================================

class TestTidalAuthUnit:
    """Example unit tests for TidalAuth class."""

    @pytest.mark.unit
    @pytest.mark.auth
    def test_init_with_custom_credentials(self):
        """Test TidalAuth initialization with custom credentials."""
        client_id = "test_client_id"
        client_secret = "test_client_secret"

        auth = TidalAuth(client_id=client_id, client_secret=client_secret)

        assert auth.client_id == client_id
        assert auth.client_secret == client_secret

    @pytest.mark.unit
    @pytest.mark.auth
    def test_is_authenticated_when_not_authenticated(self):
        """Test is_authenticated returns False when not authenticated."""
        auth = TidalAuth()
        auth.access_token = None

        result = auth.is_authenticated()

        assert result is False

    @pytest.mark.unit
    @pytest.mark.auth
    def test_is_authenticated_when_authenticated(self):
        """Test is_authenticated returns True when authenticated."""
        auth = TidalAuth()
        auth.access_token = "valid_token"

        result = auth.is_authenticated()

        assert result is True

    @pytest.mark.unit
    @pytest.mark.auth
    async def test_authenticate_success(self, mock_tidal_api_responses, tidal_response_data):
        """Test successful authentication flow."""
        setup_tidal_api_mocks(mock_tidal_api_responses, tidal_response_data)

        auth = TidalAuth()

        # Mock the browser opening and callback handling
        with patch.object(auth, '_open_auth_url') as mock_open:
            with patch.object(auth, '_start_callback_server') as mock_server:
                mock_server.return_value = "auth_code_123"

                result = await auth.authenticate()

        assert result is True
        assert auth.access_token is not None
        mock_open.assert_called_once()
        mock_server.assert_called_once()


class TestTidalServiceUnit:
    """Example unit tests for TidalService class."""

    @pytest.mark.unit
    def test_init_with_auth_manager(self, mock_auth):
        """Test TidalService initialization with auth manager."""
        service = TidalService(mock_auth)

        assert service.auth_manager == mock_auth

    @pytest.mark.unit
    async def test_search_tracks_with_mocked_api(self, mock_auth, mock_tidal_api_responses, tidal_response_data):
        """Test search_tracks with mocked API responses."""
        setup_tidal_api_mocks(mock_tidal_api_responses, tidal_response_data)

        service = TidalService(mock_auth)

        result = await service.search_tracks("test query", limit=10, offset=0)

        assert len(result) == 1  # Based on mock response
        assert result[0].title == "Test Track"
        assert result[0].id == "123456789"

    @pytest.mark.unit
    async def test_search_tracks_authentication_error(self, mock_unauthenticated_auth):
        """Test search_tracks raises error when not authenticated."""
        service = TidalService(mock_unauthenticated_auth)

        with pytest.raises(TidalAuthError):
            await service.search_tracks("test query")


# =============================================================================
# INTEGRATION TEST EXAMPLES
# =============================================================================

class TestMCPToolsIntegration:
    """Example integration tests for MCP tools."""

    @pytest.mark.integration
    @pytest.mark.mcp
    async def test_tidal_login_integration(self, mock_tidal_api_responses, tidal_response_data):
        """Test tidal_login tool with complete integration."""
        setup_tidal_api_mocks(mock_tidal_api_responses, tidal_response_data)

        # Mock the browser interaction
        with patch('src.tidal_mcp.auth.TidalAuth._open_auth_url'):
            with patch('src.tidal_mcp.auth.TidalAuth._start_callback_server', return_value="auth_code"):
                result = await server.tidal_login()

        assert result["success"] is True
        assert "user" in result
        assert result["user"]["id"] == "test_user_123"

    @pytest.mark.integration
    @pytest.mark.mcp
    async def test_tidal_search_integration(self, mock_auth, mock_service, mock_tidal_api_responses, tidal_response_data):
        """Test tidal_search tool with service integration."""
        # Setup mock service responses
        mock_service.search_all = AsyncMock()
        mock_service.search_all.return_value = Mock(
            to_dict=lambda: tidal_response_data["search_response"],
            total_results=4  # tracks + albums + artists + playlists
        )

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_search("test query", "all", 20, 0)

        assert "error" not in result
        assert result["query"] == "test query"
        assert result["content_type"] == "all"
        assert "results" in result
        assert "tracks" in result["results"]
        assert len(result["results"]["tracks"]) == 1

    @pytest.mark.integration
    @pytest.mark.mcp
    @pytest.mark.parametrize("content_type,expected_method", [
        ("tracks", "search_tracks"),
        ("albums", "search_albums"),
        ("artists", "search_artists"),
        ("playlists", "search_playlists"),
    ])
    async def test_search_content_types_integration(self, mock_service, content_type, expected_method, sample_tracks):
        """Test search with different content types calls correct service methods."""
        # Setup appropriate mock return based on content type
        mock_method = AsyncMock()
        setattr(mock_service, expected_method, mock_method)

        if content_type == "tracks":
            mock_method.return_value = sample_tracks
        else:
            mock_method.return_value = []

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_search("test", content_type)

        mock_method.assert_called_once_with("test", 20, 0)
        assert "error" not in result

    @pytest.mark.integration
    @pytest.mark.mcp
    async def test_playlist_creation_integration(self, mock_service, sample_playlist):
        """Test playlist creation tool integration."""
        mock_service.create_playlist = AsyncMock(return_value=sample_playlist)

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_create_playlist("Test Playlist", "Test Description")

        assert result["success"] is True
        assert result["playlist"]["id"] == sample_playlist.id
        assert result["playlist"]["title"] == "Test Playlist"
        mock_service.create_playlist.assert_called_once_with("Test Playlist", "Test Description")

    @pytest.mark.integration
    @pytest.mark.mcp
    async def test_add_tracks_to_playlist_integration(self, mock_service):
        """Test adding tracks to playlist integration."""
        mock_service.add_tracks_to_playlist = AsyncMock(return_value=True)
        track_ids = ["track_1", "track_2", "track_3"]

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_add_to_playlist("playlist_123", track_ids)

        assert result["success"] is True
        assert "Added 3 tracks" in result["message"]
        mock_service.add_tracks_to_playlist.assert_called_once_with("playlist_123", track_ids)

    @pytest.mark.integration
    @pytest.mark.mcp
    async def test_authentication_required_for_all_tools(self):
        """Test that all MCP tools require authentication."""
        # List of tools that require authentication (excluding tidal_login)
        authenticated_tools = [
            (server.tidal_search, {"query": "test"}),
            (server.tidal_get_track, {"track_id": "123"}),
            (server.tidal_get_album, {"album_id": "123"}),
            (server.tidal_get_artist, {"artist_id": "123"}),
            (server.tidal_get_playlist, {"playlist_id": "123"}),
            (server.tidal_create_playlist, {"title": "Test"}),
            (server.tidal_add_to_playlist, {"playlist_id": "123", "track_ids": ["1"]}),
            (server.tidal_remove_from_playlist, {"playlist_id": "123", "track_indices": [0]}),
            (server.tidal_get_favorites, {}),
            (server.tidal_add_favorite, {"item_id": "123", "content_type": "track"}),
            (server.tidal_remove_favorite, {"item_id": "123", "content_type": "track"}),
            (server.tidal_get_recommendations, {}),
            (server.tidal_get_track_radio, {"track_id": "123"}),
            (server.tidal_get_user_playlists, {}),
        ]

        for tool_func, kwargs in authenticated_tools:
            with patch('src.tidal_mcp.server.ensure_service') as mock_ensure:
                mock_ensure.side_effect = TidalAuthError("Not authenticated")

                result = await tool_func(**kwargs)

                assert "error" in result
                assert "Authentication required" in result["error"]


# =============================================================================
# PRODUCTION TOOLS INTEGRATION TESTS
# =============================================================================

@pytest.mark.integration
class TestProductionToolsIntegration:
    """Example integration tests for production tools."""

    @pytest.mark.redis
    async def test_health_check_integration(self, mock_redis, mock_middleware_stack):
        """Test health check tool with Redis and middleware integration."""
        try:
            from src.tidal_mcp.production.enhanced_tools import health_check
        except ImportError:
            pytest.skip("Production tools not available")

        with patch('src.tidal_mcp.production.enhanced_tools.health_checker') as mock_health:
            mock_health.check_redis_health.return_value = {"status": "healthy"}
            mock_health.check_rate_limiter_health.return_value = {"status": "healthy"}

            result = await health_check()

        assert result["status"] in ["healthy", "degraded", "unhealthy"]
        assert "dependencies" in result
        assert "metrics" in result

    @pytest.mark.redis
    async def test_get_rate_limit_status_integration(self, mock_middleware_stack):
        """Test rate limit status tool integration."""
        try:
            from src.tidal_mcp.production.enhanced_tools import get_rate_limit_status
        except ImportError:
            pytest.skip("Production tools not available")

        with patch('src.tidal_mcp.production.enhanced_tools.middleware_stack', mock_middleware_stack):
            result = await get_rate_limit_status()

        assert result["success"] is True
        assert "rate_limit_status" in result
        assert "recommendations" in result

    @pytest.mark.integration
    async def test_enhanced_search_integration(self, mock_service, mock_middleware_stack, sample_tracks):
        """Test enhanced search with middleware integration."""
        try:
            from src.tidal_mcp.production.enhanced_tools import tidal_search_advanced
        except ImportError:
            pytest.skip("Production tools not available")

        mock_service.search_tracks = AsyncMock(return_value=sample_tracks)

        with patch('src.tidal_mcp.production.enhanced_tools.ensure_service', return_value=mock_service):
            with patch('src.tidal_mcp.production.enhanced_tools.middleware_stack', mock_middleware_stack):
                result = await tidal_search_advanced("test query", "tracks", 5, 0)

        assert result["success"] is True
        assert "results" in result
        assert "metadata" in result
        assert "pagination" in result


# =============================================================================
# END-TO-END TEST EXAMPLES
# =============================================================================

@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteWorkflows:
    """Example end-to-end tests for complete user workflows."""

    async def test_music_discovery_workflow(self, mock_tidal_api_responses, tidal_response_data):
        """Test complete music discovery workflow."""
        setup_tidal_api_mocks(mock_tidal_api_responses, tidal_response_data)

        # 1. Authenticate
        with patch('src.tidal_mcp.auth.TidalAuth._open_auth_url'):
            with patch('src.tidal_mcp.auth.TidalAuth._start_callback_server', return_value="auth_code"):
                login_result = await server.tidal_login()

        assert login_result["success"] is True

        # 2. Search for music
        search_result = await server.tidal_search("jazz piano", "tracks", 5)
        assert "results" in search_result

        # 3. Get track details
        if search_result.get("results", {}).get("tracks"):
            track_id = search_result["results"]["tracks"][0]["id"]
            track_result = await server.tidal_get_track(track_id)
            assert track_result["success"] is True

            # 4. Add to favorites
            favorite_result = await server.tidal_add_favorite(track_id, "track")
            assert favorite_result["success"] is True

    async def test_playlist_management_workflow(self, mock_tidal_api_responses, tidal_response_data):
        """Test complete playlist management workflow."""
        setup_tidal_api_mocks(mock_tidal_api_responses, tidal_response_data)

        # 1. Authenticate
        with patch('src.tidal_mcp.auth.TidalAuth._open_auth_url'):
            with patch('src.tidal_mcp.auth.TidalAuth._start_callback_server', return_value="auth_code"):
                await server.tidal_login()

        # 2. Create playlist
        playlist_result = await server.tidal_create_playlist("E2E Test Playlist", "Created by E2E test")
        assert playlist_result["success"] is True
        playlist_id = playlist_result["playlist"]["id"]

        # 3. Search for tracks
        search_result = await server.tidal_search("test music", "tracks", 3)
        track_ids = [t["id"] for t in search_result.get("results", {}).get("tracks", [])]

        # 4. Add tracks to playlist
        if track_ids:
            add_result = await server.tidal_add_to_playlist(playlist_id, track_ids)
            assert add_result["success"] is True

        # 5. Get playlist details
        playlist_details = await server.tidal_get_playlist(playlist_id, True)
        assert playlist_details["success"] is True

        # 6. Remove first track
        if playlist_details["playlist"]["tracks"]:
            remove_result = await server.tidal_remove_from_playlist(playlist_id, [0])
            assert remove_result["success"] is True

    async def test_recommendations_workflow(self, mock_tidal_api_responses, tidal_response_data):
        """Test recommendations and radio workflow."""
        setup_tidal_api_mocks(mock_tidal_api_responses, tidal_response_data)

        # 1. Authenticate
        with patch('src.tidal_mcp.auth.TidalAuth._open_auth_url'):
            with patch('src.tidal_mcp.auth.TidalAuth._start_callback_server', return_value="auth_code"):
                await server.tidal_login()

        # 2. Get recommendations
        recs_result = await server.tidal_get_recommendations(10)
        assert "recommendations" in recs_result

        # 3. Get track radio based on first recommendation
        if recs_result.get("recommendations"):
            track_id = recs_result["recommendations"][0]["id"]
            radio_result = await server.tidal_get_track_radio(track_id, 15)
            assert "radio_tracks" in radio_result
            assert radio_result["seed_track_id"] == track_id


# =============================================================================
# PERFORMANCE TEST EXAMPLES
# =============================================================================

@pytest.mark.benchmark
class TestPerformance:
    """Example performance tests."""

    @pytest.mark.unit
    def test_auth_initialization_performance(self, benchmark):
        """Benchmark TidalAuth initialization."""
        def init_auth():
            return TidalAuth(client_id="test", client_secret="test")

        result = benchmark(init_auth)
        assert result is not None

    @pytest.mark.integration
    async def test_search_response_time(self, mock_service, sample_tracks):
        """Test search response time is acceptable."""
        import time

        mock_service.search_tracks = AsyncMock(return_value=sample_tracks)

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            start_time = time.time()
            result = await server.tidal_search("test", "tracks", 20)
            execution_time = time.time() - start_time

        assert execution_time < 1.0  # Should complete in under 1 second
        assert "error" not in result

    @pytest.mark.integration
    async def test_parallel_search_performance(self, mock_service, sample_tracks):
        """Test parallel searches complete efficiently."""
        import asyncio
        import time

        mock_service.search_tracks = AsyncMock(return_value=sample_tracks)

        async def single_search(query):
            with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
                return await server.tidal_search(query, "tracks", 10)

        # Run 5 searches in parallel
        queries = [f"test query {i}" for i in range(5)]

        start_time = time.time()
        results = await asyncio.gather(*[single_search(q) for q in queries])
        execution_time = time.time() - start_time

        assert execution_time < 2.0  # All 5 searches should complete in under 2 seconds
        assert len(results) == 5
        assert all("error" not in result for result in results)


# =============================================================================
# ERROR HANDLING TEST EXAMPLES
# =============================================================================

class TestErrorHandling:
    """Example error handling tests."""

    @pytest.mark.unit
    async def test_search_with_invalid_content_type(self, mock_service):
        """Test search handles invalid content type gracefully."""
        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_search("test", "invalid_type", 20)

        # Should default to "all" search for invalid content types
        assert "error" not in result
        assert result["content_type"] == "all"

    @pytest.mark.integration
    async def test_service_timeout_handling(self, mock_service):
        """Test handling of service timeouts."""
        import asyncio

        mock_service.search_tracks = AsyncMock(side_effect=asyncio.TimeoutError("Request timeout"))

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_search("test", "tracks")

        assert "error" in result
        assert "timeout" in result["error"].lower() or "failed" in result["error"].lower()

    @pytest.mark.integration
    async def test_network_error_handling(self, mock_service):
        """Test handling of network errors."""
        import aiohttp

        mock_service.search_tracks = AsyncMock(side_effect=aiohttp.ClientError("Network error"))

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_search("test", "tracks")

        assert "error" in result
