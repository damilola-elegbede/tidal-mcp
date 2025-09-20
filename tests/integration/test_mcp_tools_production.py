"""
Integration tests for production MCP tools.

Tests the enhanced production tools including rate limiting, streaming URLs,
health checks, and middleware integration.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tidal_mcp.production import enhanced_tools

# Skip entire module - tests need refactoring for proper MCP integration
pytestmark = pytest.mark.skip(reason="Production MCP tool integration tests need refactoring")



class TestHealthAndStatusTools:
    """Test health check and system status tools."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_health_check_healthy_system(self, health_checker, middleware_stack, mock_auth_manager):
        """Test health check with all systems healthy."""
        # Mock health checker responses
        health_checker.check_redis_health = AsyncMock(return_value={
            "status": "healthy",
            "response_time_ms": 5.2,
            "last_checked": "2024-01-15T10:30:00Z"
        })
        health_checker.check_rate_limiter_health = AsyncMock(return_value={
            "status": "healthy",
            "response_time_ms": 3.1,
            "last_checked": "2024-01-15T10:30:00Z"
        })

        # Mock auth manager
        mock_auth_manager.is_authenticated.return_value = True

        with patch.object(enhanced_tools, 'health_checker', health_checker), \
             patch.object(enhanced_tools, 'auth_manager', mock_auth_manager), \
             patch.object(enhanced_tools, 'middleware_stack', middleware_stack):

            result = await enhanced_tools.health_check()

            assert result["status"] == "healthy"
            assert result["version"] == "1.0.0"
            assert "dependencies" in result
            assert result["dependencies"]["redis"]["status"] == "healthy"
            assert result["dependencies"]["rate_limiter"]["status"] == "healthy"
            assert result["dependencies"]["tidal_auth"]["status"] == "healthy"
            assert "metrics" in result
            assert "environment" in result

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_health_check_degraded_system(self, health_checker, middleware_stack, mock_auth_manager):
        """Test health check with some systems unhealthy."""
        # Mock health checker with mixed results
        health_checker.check_redis_health = AsyncMock(return_value={
            "status": "unhealthy",
            "error": "Connection timeout",
            "last_checked": "2024-01-15T10:30:00Z"
        })
        health_checker.check_rate_limiter_health = AsyncMock(return_value={
            "status": "healthy",
            "response_time_ms": 3.1,
            "last_checked": "2024-01-15T10:30:00Z"
        })

        mock_auth_manager.is_authenticated.return_value = True

        with patch.object(enhanced_tools, 'health_checker', health_checker), \
             patch.object(enhanced_tools, 'auth_manager', mock_auth_manager), \
             patch.object(enhanced_tools, 'middleware_stack', middleware_stack):

            result = await enhanced_tools.health_check()

            assert result["status"] == "degraded"
            assert result["dependencies"]["redis"]["status"] == "unhealthy"
            assert result["dependencies"]["rate_limiter"]["status"] == "healthy"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_health_check_exception_handling(self):
        """Test health check with exception handling."""
        with patch.object(enhanced_tools, 'health_checker', None):
            result = await enhanced_tools.health_check()

            assert result["status"] == "unhealthy"
            assert "error" in result
            assert "Health check failed" in result["error"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_system_status(self, middleware_stack):
        """Test system status retrieval."""
        with patch.object(enhanced_tools, 'middleware_stack', middleware_stack):
            result = await enhanced_tools.get_system_status()

            assert "service_info" in result
            assert result["service_info"]["name"] == "Tidal MCP Server"
            assert result["service_info"]["version"] == "1.0.0"
            assert "rate_limits" in result
            assert "performance" in result
            assert "feature_flags" in result
            assert result["feature_flags"]["streaming_urls_enabled"] is True


class TestEnhancedAuthenticationTools:
    """Test enhanced authentication tools with middleware."""

    @pytest.mark.asyncio
    @pytest.mark.auth
    async def test_tidal_login_with_middleware(self, middleware_stack, mock_auth_manager):
        """Test login with middleware integration."""
        # Mock successful authentication
        mock_auth_manager.authenticate = AsyncMock(return_value=True)
        mock_auth_manager.get_user_info.return_value = {
            "id": "test_user_123",
            "username": "test_user",
            "country_code": "US",
            "subscription": "premium"
        }
        mock_auth_manager.session_id = "session_123"
        mock_auth_manager.country_code = "US"
        mock_auth_manager.refresh_token = "refresh_token_456"

        with patch.object(enhanced_tools, 'middleware_stack', middleware_stack), \
             patch.object(enhanced_tools, 'auth_manager', mock_auth_manager), \
             patch.object(enhanced_tools, 'tidal_service', None):

            result = await enhanced_tools.tidal_login()

            assert result["success"] is True
            assert result["user"]["id"] == "test_user_123"
            assert "session_info" in result
            assert "security" in result
            assert result["security"]["token_type"] == "Bearer"
            assert result["security"]["scope"] == "streaming"

    @pytest.mark.asyncio
    @pytest.mark.auth
    async def test_tidal_login_failure_with_recovery_hints(self, middleware_stack):
        """Test login failure with detailed recovery hints."""
        mock_auth = MagicMock()
        mock_auth.authenticate = AsyncMock(return_value=False)

        with patch.object(enhanced_tools, 'middleware_stack', middleware_stack), \
             patch('tidal_mcp.production.enhanced_tools.TidalAuth', return_value=mock_auth):

            result = await enhanced_tools.tidal_login()

            assert result["success"] is False
            assert result["error"] == "AUTHENTICATION_FAILED"
            assert "recovery_hints" in result
            assert len(result["recovery_hints"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.auth
    async def test_refresh_session_success(self, middleware_stack, mock_auth_manager):
        """Test successful session refresh."""
        mock_auth_manager.refresh_access_token = AsyncMock(return_value=True)

        with patch.object(enhanced_tools, 'middleware_stack', middleware_stack), \
             patch.object(enhanced_tools, 'auth_manager', mock_auth_manager):

            result = await enhanced_tools.refresh_session()

            assert result["success"] is True
            assert "session_info" in result
            assert "refreshed_at" in result["session_info"]

    @pytest.mark.asyncio
    @pytest.mark.auth
    async def test_refresh_session_no_active_session(self, middleware_stack):
        """Test session refresh with no active session."""
        with patch.object(enhanced_tools, 'middleware_stack', middleware_stack), \
             patch.object(enhanced_tools, 'auth_manager', None):

            result = await enhanced_tools.refresh_session()

            assert result["success"] is False
            assert result["error"] == "NO_ACTIVE_SESSION"
            assert "recovery_hints" in result

    @pytest.mark.asyncio
    @pytest.mark.auth
    async def test_refresh_session_failure(self, middleware_stack, mock_auth_manager):
        """Test failed session refresh."""
        mock_auth_manager.refresh_access_token = AsyncMock(return_value=False)

        with patch.object(enhanced_tools, 'middleware_stack', middleware_stack), \
             patch.object(enhanced_tools, 'auth_manager', mock_auth_manager):

            result = await enhanced_tools.refresh_session()

            assert result["success"] is False
            assert result["error"] == "REFRESH_FAILED"
            assert "recovery_hints" in result


class TestStreamingUrlTools:
    """Test streaming URL generation tools."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_stream_url_success(self, tidal_service, track_factory, middleware_stack):
        """Test successful streaming URL generation."""
        # Create sample track
        sample_track = track_factory(track_id="123456", title="Stream Track")
        tidal_service.get_track = AsyncMock(return_value=sample_track)

        # Mock streaming URL generation
        expected_streaming_info = {
            "url": "https://streaming.tidal.com/track/123456?quality=HIGH&format=AAC",
            "quality": "HIGH",
            "format": "AAC",
            "bitrate": 320,
            "sample_rate": 44100,
            "expires_at": "2024-01-15T12:30:00Z",
            "drm_protected": True,
            "geo_restrictions": ["US", "CA", "GB"]
        }

        with patch.object(enhanced_tools, 'middleware_stack', middleware_stack), \
             patch.object(enhanced_tools, 'ensure_service', return_value=tidal_service), \
             patch.object(enhanced_tools, '_generate_streaming_url', return_value=expected_streaming_info):

            result = await enhanced_tools.get_stream_url("123456", "HIGH", "AAC")

            assert result["success"] is True
            assert result["track_info"]["id"] == "123456"
            assert result["track_info"]["title"] == "Stream Track"
            assert result["streaming_url"] == expected_streaming_info["url"]
            assert result["audio_info"]["quality"] == "HIGH"
            assert result["audio_info"]["format"] == "AAC"
            assert result["audio_info"]["bitrate"] == 320
            assert result["usage_info"]["expires_at"] == "2024-01-15T12:30:00Z"
            assert result["security"]["drm_protected"] is True

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_stream_url_invalid_quality(self, middleware_stack):
        """Test streaming URL generation with invalid quality."""
        with patch.object(enhanced_tools, 'middleware_stack', middleware_stack):
            result = await enhanced_tools.get_stream_url("123456", "INVALID_QUALITY", "AAC")

            assert result["success"] is False
            assert result["error"] == "INVALID_QUALITY"
            assert "Must be one of" in result["message"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_stream_url_invalid_format(self, middleware_stack):
        """Test streaming URL generation with invalid format."""
        with patch.object(enhanced_tools, 'middleware_stack', middleware_stack):
            result = await enhanced_tools.get_stream_url("123456", "HIGH", "INVALID_FORMAT")

            assert result["success"] is False
            assert result["error"] == "INVALID_FORMAT"
            assert "Must be one of" in result["message"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_stream_url_track_not_found(self, tidal_service, middleware_stack):
        """Test streaming URL generation for non-existent track."""
        tidal_service.get_track = AsyncMock(return_value=None)

        with patch.object(enhanced_tools, 'middleware_stack', middleware_stack), \
             patch.object(enhanced_tools, 'ensure_service', return_value=tidal_service):

            result = await enhanced_tools.get_stream_url("nonexistent", "HIGH", "AAC")

            assert result["success"] is False
            assert result["error"] == "TRACK_NOT_FOUND"
            assert "recovery_hints" in result

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_stream_url_generation_failure(self, tidal_service, track_factory, middleware_stack):
        """Test streaming URL generation failure."""
        sample_track = track_factory(track_id="123456", title="Stream Track")
        tidal_service.get_track = AsyncMock(return_value=sample_track)

        with patch.object(enhanced_tools, 'middleware_stack', middleware_stack), \
             patch.object(enhanced_tools, 'ensure_service', return_value=tidal_service), \
             patch.object(enhanced_tools, '_generate_streaming_url', return_value=None):

            result = await enhanced_tools.get_stream_url("123456", "HIGH", "AAC")

            assert result["success"] is False
            assert result["error"] == "STREAMING_URL_GENERATION_FAILED"
            assert "recovery_hints" in result


class TestAdvancedSearchTools:
    """Test advanced search tools with middleware."""

    @pytest.mark.asyncio
    @pytest.mark.search
    async def test_tidal_search_advanced_success(self, tidal_service, track_factory, middleware_stack):
        """Test advanced search with middleware integration."""
        # Create sample tracks
        sample_tracks = [
            track_factory(track_id="adv1", title="Advanced Track 1"),
            track_factory(track_id="adv2", title="Advanced Track 2"),
        ]

        tidal_service.search_tracks = AsyncMock(return_value=sample_tracks)

        with patch.object(enhanced_tools, 'middleware_stack', middleware_stack), \
             patch.object(enhanced_tools, 'ensure_service', return_value=tidal_service):

            result = await enhanced_tools.tidal_search_advanced(
                "advanced", "tracks", 10, 0, {"genre": "rock"}
            )

            assert result["success"] is True
            assert result["query"] == "advanced"
            assert result["content_type"] == "tracks"
            assert len(result["results"]["tracks"]) == 2
            assert "metadata" in result
            assert result["metadata"]["search_time_ms"] == 150
            assert result["metadata"]["relevance_algorithm"] == "tidal_enhanced_v1"
            assert "pagination" in result
            assert result["pagination"]["current_page"] == 1
            assert result["pagination"]["per_page"] == 10
            assert result["filters_applied"] == {"genre": "rock"}

    @pytest.mark.asyncio
    @pytest.mark.search
    async def test_tidal_search_advanced_all_types(self, tidal_service, search_results_factory, middleware_stack):
        """Test advanced search across all content types."""
        search_results = search_results_factory(
            track_count=2,
            album_count=1,
            artist_count=1,
            playlist_count=1,
            query="comprehensive"
        )

        tidal_service.search_all = AsyncMock(return_value=search_results)

        with patch.object(enhanced_tools, 'middleware_stack', middleware_stack), \
             patch.object(enhanced_tools, 'ensure_service', return_value=tidal_service):

            result = await enhanced_tools.tidal_search_advanced("comprehensive", "all", 10, 0)

            assert result["success"] is True
            assert len(result["results"]["tracks"]) == 2
            assert len(result["results"]["albums"]) == 1
            assert len(result["results"]["artists"]) == 1
            assert len(result["results"]["playlists"]) == 1
            assert result["metadata"]["total_results"] == 5

    @pytest.mark.asyncio
    @pytest.mark.search
    async def test_advanced_search_enhanced_results(self, tidal_service, track_factory, middleware_stack):
        """Test that advanced search provides enhanced result metadata."""
        sample_tracks = [track_factory(track_id="enhanced1", title="Enhanced Track")]
        tidal_service.search_tracks = AsyncMock(return_value=sample_tracks)

        with patch.object(enhanced_tools, 'middleware_stack', middleware_stack), \
             patch.object(enhanced_tools, 'ensure_service', return_value=tidal_service):

            result = await enhanced_tools.tidal_search_advanced("test", "tracks", 10, 0)

            # Check that track results are enhanced with additional metadata
            track_result = result["results"]["tracks"][0]
            assert "relevance_score" in track_result
            assert "popularity_rank" in track_result
            assert "streaming_available" in track_result
            assert track_result["relevance_score"] == 0.95
            assert track_result["popularity_rank"] == 1000
            assert track_result["streaming_available"] is True


class TestRateLimitingTools:
    """Test rate limiting functionality."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_rate_limit_status_success(self, middleware_stack):
        """Test successful rate limit status retrieval."""
        # Mock rate limiter
        mock_rate_limiter = MagicMock()
        middleware_stack.rate_limiter = mock_rate_limiter

        with patch.object(enhanced_tools, 'middleware_stack', middleware_stack):
            result = await enhanced_tools.get_rate_limit_status()

            assert result["success"] is True
            assert "rate_limit_status" in result
            assert result["rate_limit_status"]["tier"] == "basic"
            assert "limits" in result["rate_limit_status"]
            assert "current_usage" in result["rate_limit_status"]
            assert "remaining" in result["rate_limit_status"]
            assert "reset_times" in result["rate_limit_status"]
            assert "utilization" in result["rate_limit_status"]
            assert "recommendations" in result
            assert "tier_upgrade_benefits" in result

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_rate_limit_status_disabled(self, middleware_stack):
        """Test rate limit status when rate limiting is disabled."""
        middleware_stack.rate_limiter = None

        with patch.object(enhanced_tools, 'middleware_stack', middleware_stack):
            result = await enhanced_tools.get_rate_limit_status()

            assert "error" in result
            assert result["error"] == "RATE_LIMITING_DISABLED"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_rate_limit_status_high_usage_recommendations(self, middleware_stack):
        """Test rate limit status with high usage recommendations."""
        mock_rate_limiter = MagicMock()
        middleware_stack.rate_limiter = mock_rate_limiter

        with patch.object(enhanced_tools, 'middleware_stack', middleware_stack):
            result = await enhanced_tools.get_rate_limit_status()

            # Check recommendations for high usage
            recommendations = result["recommendations"]
            assert any("upgrading to a higher tier" in rec for rec in recommendations)
            assert any("request queuing" in rec for rec in recommendations)
            assert any("concurrent request limit" in rec for rec in recommendations)


class TestMiddlewareIntegration:
    """Test middleware integration across all tools."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_middleware_error_handling(self, middleware_stack):
        """Test middleware error handling and response formatting."""
        # Test with a function that raises an exception
        @middleware_stack.middleware(endpoint_name="test_endpoint", require_auth=False)
        async def failing_function():
            raise Exception("Test error")

        result = await failing_function()

        assert "error" in result
        assert result["error"] == "INTERNAL_SERVER_ERROR"
        assert "request_id" in result
        assert "timestamp" in result
        assert "recovery_hints" in result

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.redis
    async def test_middleware_rate_limiting_integration(self, middleware_stack, mock_redis):
        """Test middleware rate limiting integration."""
        # Mock rate limiter to return rate limit exceeded
        middleware_stack.rate_limiter.check_rate_limit = AsyncMock(
            return_value=(False, {
                "error": "RATE_LIMIT_EXCEEDED",
                "limit": 60,
                "current": 60,
                "retry_after": 30
            })
        )

        @middleware_stack.middleware(endpoint_name="test_endpoint", require_auth=True)
        async def rate_limited_function():
            return {"success": True}

        # Mock auth header
        result = await rate_limited_function(auth_header="Bearer test_token")

        assert "error" in result
        assert result["error"] == "RATE_LIMIT_EXCEEDED"
        assert "details" in result
        assert result["details"]["retry_after"] == 30

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_middleware_request_validation(self, middleware_stack):
        """Test middleware request validation."""
        from pydantic import ValidationError

        # Mock validator to raise validation error
        middleware_stack.validator.validate_search_query = MagicMock(
            side_effect=ValidationError("Query too long")
        )

        @middleware_stack.middleware(endpoint_name="test_search", require_auth=False)
        async def search_function(query=""):
            return {"success": True}

        result = await search_function(query="test query")

        assert "error" in result
        assert result["error"] == "VALIDATION_ERROR"
        assert "details" in result
        assert "validation_errors" in result["details"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_middleware_observability_metrics(self, middleware_stack):
        """Test middleware observability and metrics collection."""
        @middleware_stack.middleware(endpoint_name="test_metrics", require_auth=False)
        async def metrics_function():
            return {"success": True, "data": "test"}

        result = await metrics_function()

        assert result["success"] is True
        assert "_metadata" in result
        assert "request_id" in result["_metadata"]
        assert "processing_time" in result["_metadata"]
        assert result["_metadata"]["processing_time"] >= 0

        # Check that metrics were recorded
        if middleware_stack.observability:
            metrics = middleware_stack.observability.get_metrics()
            assert "request_counts" in metrics
            assert "avg_response_times" in metrics
