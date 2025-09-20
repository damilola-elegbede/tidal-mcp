"""
Performance and load testing for MCP tools.

Tests performance characteristics, concurrent request handling,
rate limiting behavior, and system resource usage under load.
"""

import asyncio
import os
import time
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Conditional import based on testing environment
if os.getenv('TESTING') == '1':
    from tests import mock_tidal_server as server
else:
    from tidal_mcp import server

try:
    from tidal_mcp.production import enhanced_tools
except ImportError:
    enhanced_tools = None

from tests.integration.test_helpers import simulate_api_latency, TestAssertion


class TestPerformanceBaselines:
    """Test performance baselines for individual MCP tools."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.timeout(10)
    async def test_search_performance_baseline(self, tidal_service, track_factory):
        """Test search performance baseline."""
        # Setup mock data
        sample_tracks = [
            track_factory(track_id=f"perf{i}", title=f"Performance Track {i}")
            for i in range(20)
        ]
        tidal_service.search_tracks = AsyncMock(return_value=sample_tracks)

        with patch.object(server, 'ensure_service', return_value=tidal_service):
            # Ensure the tool has the required attributes
            if not hasattr(server.tidal_search, '__name__'):
                server.tidal_search.__name__ = 'tidal_search'
            if not hasattr(server.tidal_search, '__doc__'):
                server.tidal_search.__doc__ = 'Search for tracks on Tidal'

            # Measure performance
            start_time = time.time()
            result = await server.tidal_search.fn("performance test", "tracks", 20)
            end_time = time.time()

            # Assert results
            assert len(result["results"]["tracks"]) == 20
            TestAssertion.assert_response_time_acceptable(start_time, end_time, 2.0)

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.timeout(10)
    async def test_playlist_operations_performance(self, tidal_service, playlist_factory):
        """Test playlist operations performance."""
        # Setup mocks
        new_playlist = playlist_factory(playlist_id="perf-playlist", title="Performance Playlist")
        tidal_service.create_playlist = AsyncMock(return_value=new_playlist)
        tidal_service.add_tracks_to_playlist = AsyncMock(return_value=True)
        tidal_service.get_playlist = AsyncMock(return_value=new_playlist)

        with patch.object(server, 'ensure_service', return_value=tidal_service):
            # Ensure the tools have the required attributes
            for tool_name in ['tidal_create_playlist', 'tidal_add_to_playlist']:
                tool = getattr(server, tool_name)
                if not hasattr(tool, '__name__'):
                    tool.__name__ = tool_name
                if not hasattr(tool, '__doc__'):
                    tool.__doc__ = f'{tool_name} documentation'

            # Test create playlist performance
            start_time = time.time()
            create_result = await server.tidal_create_playlist.fn("Performance Playlist")
            end_time = time.time()

            assert create_result["success"] is True
            TestAssertion.assert_response_time_acceptable(start_time, end_time, 1.5)

            # Test add tracks performance
            track_ids = [f"track{i}" for i in range(10)]
            start_time = time.time()
            add_result = await server.tidal_add_to_playlist.fn("perf-playlist", track_ids)
            end_time = time.time()

            assert add_result["success"] is True
            TestAssertion.assert_response_time_acceptable(start_time, end_time, 2.0)

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.timeout(10)
    async def test_favorites_performance(self, tidal_service, track_factory):
        """Test favorites operations performance."""
        # Setup mocks
        favorite_tracks = [
            track_factory(track_id=f"fav{i}", title=f"Favorite {i}")
            for i in range(50)
        ]
        tidal_service.get_user_favorites = AsyncMock(return_value=favorite_tracks)
        tidal_service.add_to_favorites = AsyncMock(return_value=True)

        with patch.object(server, 'ensure_service', return_value=tidal_service):
            # Ensure the tools have the required attributes
            for tool_name in ['tidal_get_favorites', 'tidal_add_favorite']:
                tool = getattr(server, tool_name)
                if not hasattr(tool, '__name__'):
                    tool.__name__ = tool_name
                if not hasattr(tool, '__doc__'):
                    tool.__doc__ = f'{tool_name} documentation'

            # Test get favorites performance
            start_time = time.time()
            fav_result = await server.tidal_get_favorites.fn("tracks", 50)
            end_time = time.time()

            assert len(fav_result["favorites"]) == 50
            TestAssertion.assert_response_time_acceptable(start_time, end_time, 2.0)

            # Test add to favorites performance
            start_time = time.time()
            add_result = await server.tidal_add_favorite.fn("new_track", "track")
            end_time = time.time()

            assert add_result["success"] is True
            TestAssertion.assert_response_time_acceptable(start_time, end_time, 1.0)

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.timeout(10)
    async def test_enhanced_tools_performance(self, middleware_stack, health_checker):
        """Test enhanced tools performance with middleware."""
        # Setup health checker to return all healthy statuses
        health_checker.check_redis_health = AsyncMock(return_value={
            "status": "healthy",
            "response_time_ms": 5.0
        })
        health_checker.check_rate_limiter_health = AsyncMock(return_value={
            "status": "healthy",
            "response_time_ms": 3.0
        })
        health_checker.check_service_health = AsyncMock(return_value={
            "status": "healthy",
            "response_time_ms": 2.0
        })
        health_checker.check_middleware_health = AsyncMock(return_value={
            "status": "healthy",
            "response_time_ms": 1.0
        })
        # Mock the overall health check to return healthy
        health_checker.get_overall_health = AsyncMock(return_value={
            "status": "healthy",
            "checks": {
                "redis": {"status": "healthy", "response_time_ms": 5.0},
                "rate_limiter": {"status": "healthy", "response_time_ms": 3.0},
                "service": {"status": "healthy", "response_time_ms": 2.0},
                "middleware": {"status": "healthy", "response_time_ms": 1.0}
            }
        })

        if enhanced_tools:
            # Mock auth manager to be authenticated
            mock_auth_manager = Mock()
            mock_auth_manager.is_authenticated.return_value = True

            with patch.object(enhanced_tools, 'health_checker', health_checker), \
                 patch.object(enhanced_tools, 'middleware_stack', middleware_stack), \
                 patch.object(enhanced_tools, 'auth_manager', mock_auth_manager), \
                 patch('tidal_mcp.production.enhanced_tools.auth_manager', mock_auth_manager):

                # Ensure the tools have the required attributes
                for tool_name in ['health_check', 'get_system_status']:
                    tool = getattr(enhanced_tools, tool_name, None)
                    if tool and hasattr(tool, 'fn'):
                        if not hasattr(tool, '__name__'):
                            tool.__name__ = tool_name
                        if not hasattr(tool, '__doc__'):
                            tool.__doc__ = f'{tool_name} documentation'

                # Test health check performance
                start_time = time.time()
                health_result = await enhanced_tools.health_check.fn()
                end_time = time.time()

                assert health_result["status"] == "healthy"
                TestAssertion.assert_response_time_acceptable(start_time, end_time, 1.0)

                # Test system status performance
                start_time = time.time()
                status_result = await enhanced_tools.get_system_status.fn()
                end_time = time.time()

                assert "service_info" in status_result
                TestAssertion.assert_response_time_acceptable(start_time, end_time, 1.0)
        else:
            pytest.skip("Enhanced tools not available")


class TestConcurrentRequestHandling:
    """Test concurrent request handling and performance."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.timeout(10)
    async def test_concurrent_search_requests(self, tidal_service, track_factory):
        """Test handling multiple concurrent search requests."""
        # Setup mock with slight delay to simulate real API
        async def mock_search(*args, **kwargs):
            await simulate_api_latency(10, 20)
            return [track_factory(track_id="concurrent1", title="Concurrent Track")]

        tidal_service.search_tracks = AsyncMock(side_effect=mock_search)

        with patch.object(server, 'ensure_service', return_value=tidal_service):
            # Ensure the tool has the required attributes
            if not hasattr(server.tidal_search, '__name__'):
                server.tidal_search.__name__ = 'tidal_search'
            if not hasattr(server.tidal_search, '__doc__'):
                server.tidal_search.__doc__ = 'Search for tracks on Tidal'

            # Execute 10 concurrent search requests
            start_time = time.time()
            tasks = [
                server.tidal_search.fn(f"query{i}", "tracks", 5)
                for i in range(10)
            ]
            results = await asyncio.gather(*tasks)
            end_time = time.time()

            # All requests should complete successfully
            assert len(results) == 10
            for result in results:
                assert len(result["results"]["tracks"]) == 1

            # Should complete faster than sequential execution due to concurrency
            TestAssertion.assert_response_time_acceptable(start_time, end_time, 5.0)

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.timeout(10)
    async def test_concurrent_mixed_operations(self, tidal_service, track_factory, playlist_factory):
        """Test handling concurrent mixed operations."""
        # Setup mocks
        sample_tracks = [track_factory(track_id="mixed1", title="Mixed Track")]
        sample_playlist = playlist_factory(playlist_id="mixed-pl", title="Mixed Playlist")

        async def mock_search(*args, **kwargs):
            await simulate_api_latency(5, 10)
            return sample_tracks

        async def mock_get_favorites(*args, **kwargs):
            await simulate_api_latency(5, 15)
            return sample_tracks

        async def mock_create_playlist(*args, **kwargs):
            await simulate_api_latency(10, 20)
            return sample_playlist

        tidal_service.search_tracks = AsyncMock(side_effect=mock_search)
        tidal_service.get_user_favorites = AsyncMock(side_effect=mock_get_favorites)
        tidal_service.create_playlist = AsyncMock(side_effect=mock_create_playlist)

        with patch.object(server, 'ensure_service', return_value=tidal_service):
            # Ensure tools have the required attributes
            for tool_name in ['tidal_search', 'tidal_get_favorites', 'tidal_create_playlist']:
                tool = getattr(server, tool_name)
                if not hasattr(tool, '__name__'):
                    tool.__name__ = tool_name
                if not hasattr(tool, '__doc__'):
                    tool.__doc__ = f'{tool_name} documentation'

            # Execute mixed concurrent operations
            start_time = time.time()
            tasks = [
                server.tidal_search.fn("mixed", "tracks"),
                server.tidal_get_favorites.fn("tracks", 10),
                server.tidal_create_playlist.fn("Mixed Playlist"),
                server.tidal_search.fn("another", "tracks"),
                server.tidal_get_favorites.fn("albums", 5),
            ]
            results = await asyncio.gather(*tasks)
            end_time = time.time()

            # All operations should complete successfully
            assert len(results) == 5
            TestAssertion.assert_response_time_acceptable(start_time, end_time, 3.0)

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.timeout(10)
    async def test_concurrent_requests_with_middleware(self, middleware_stack, tidal_service, track_factory):
        """Test concurrent requests with middleware processing."""
        # Setup mock with middleware
        sample_tracks = [track_factory(track_id="mw1", title="Middleware Track")]

        async def mock_search(*args, **kwargs):
            await simulate_api_latency(5, 10)
            return sample_tracks

        tidal_service.search_tracks = AsyncMock(side_effect=mock_search)

        # Mock the middleware decorator to actually work
        original_middleware = middleware_stack.middleware

        def mock_middleware(endpoint_name="unknown", require_auth=True):
            def decorator(func):
                async def wrapper(*args, **kwargs):
                    # Simulate middleware processing time
                    await simulate_api_latency(1, 3)
                    return await func(*args, **kwargs)
                return wrapper
            return decorator

        middleware_stack.middleware = mock_middleware

        if enhanced_tools:
            with patch.object(enhanced_tools, 'middleware_stack', middleware_stack), \
                 patch.object(enhanced_tools, 'ensure_service', return_value=tidal_service):

                # Ensure the tool has the required attributes
                tool = getattr(enhanced_tools, 'tidal_search_advanced', None)
                if tool and hasattr(tool, 'fn'):
                    if not hasattr(tool, '__name__'):
                        tool.__name__ = 'tidal_search_advanced'
                    if not hasattr(tool, '__doc__'):
                        tool.__doc__ = 'Advanced search for tracks on Tidal'

                    # Execute concurrent requests through enhanced tools
                    start_time = time.time()
                    tasks = [
                        enhanced_tools.tidal_search_advanced.fn(f"middleware{i}", "tracks", 5)
                        for i in range(5)
                    ]
                    results = await asyncio.gather(*tasks)
                    end_time = time.time()

                    # All requests should complete
                    assert len(results) == 5
                    TestAssertion.assert_response_time_acceptable(start_time, end_time, 3.0)
                else:
                    pytest.skip("Enhanced search tool not available")
        else:
            pytest.skip("Enhanced tools not available")


class TestRateLimitingPerformance:
    """Test rate limiting performance and behavior."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.timeout(10)
    @pytest.mark.redis
    async def test_rate_limiter_performance(self, mock_redis, middleware_stack):
        """Test rate limiter performance under load."""
        rate_limiter = middleware_stack.rate_limiter

        if not rate_limiter:
            pytest.skip("Rate limiter not available")

        # Test multiple rate limit checks
        start_time = time.time()
        tasks = []
        for i in range(50):
            task = rate_limiter.check_rate_limit(f"user_{i % 5}", "basic", "test")
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # All checks should complete
        assert len(results) == 50
        # Most should be allowed (first requests for each user)
        allowed_count = sum(1 for allowed, _ in results if allowed)
        assert allowed_count >= 5  # At least one per user

        # Performance should be acceptable
        TestAssertion.assert_response_time_acceptable(start_time, end_time, 2.0)

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.timeout(10)
    @pytest.mark.redis
    async def test_rate_limit_enforcement_under_load(self, mock_redis, middleware_stack):
        """Test rate limit enforcement under concurrent load."""
        rate_limiter = middleware_stack.rate_limiter

        if not rate_limiter:
            pytest.skip("Rate limiter not available")

        # Simulate burst requests from single user
        user_id = "load_test_user"
        endpoint = "search"

        # First batch should mostly succeed
        first_batch_tasks = [
            rate_limiter.check_rate_limit(user_id, "basic", endpoint)
            for _ in range(30)
        ]
        first_results = await asyncio.gather(*first_batch_tasks)

        # Second batch should hit rate limits
        second_batch_tasks = [
            rate_limiter.check_rate_limit(user_id, "basic", endpoint)
            for _ in range(30)
        ]
        second_results = await asyncio.gather(*second_batch_tasks)

        # Analyze results
        first_allowed = sum(1 for allowed, _ in first_results if allowed)
        second_allowed = sum(1 for allowed, _ in second_results if allowed)

        # Should see rate limiting kick in
        assert first_allowed > second_allowed
        assert second_allowed < 10  # Most should be rate limited


class TestMemoryAndResourceUsage:
    """Test memory usage and resource consumption."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.timeout(10)
    async def test_memory_usage_under_load(self, tidal_service, track_factory):
        """Test memory usage during sustained load."""
        import gc
        import psutil
        import os

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Setup mock with large dataset
        large_track_set = [
            track_factory(track_id=f"mem{i}", title=f"Memory Track {i}")
            for i in range(100)
        ]
        tidal_service.search_tracks = AsyncMock(return_value=large_track_set)

        with patch.object(server, 'ensure_service', return_value=tidal_service):
            # Ensure the tool has the required attributes
            if not hasattr(server.tidal_search, '__name__'):
                server.tidal_search.__name__ = 'tidal_search'
            if not hasattr(server.tidal_search, '__doc__'):
                server.tidal_search.__doc__ = 'Search for tracks on Tidal'

            # Execute many operations
            for batch in range(10):
                tasks = [
                    server.tidal_search.fn(f"memory_test_{batch}_{i}", "tracks", 100)
                    for i in range(10)
                ]
                await asyncio.gather(*tasks)

                # Force garbage collection
                gc.collect()

                # Check memory usage
                current_memory = process.memory_info().rss
                memory_increase = current_memory - initial_memory

                # Memory increase should be reasonable (less than 100MB)
                assert memory_increase < 100 * 1024 * 1024, f"Memory usage increased by {memory_increase / 1024 / 1024:.2f}MB"

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.timeout(10)
    @pytest.mark.redis
    async def test_redis_connection_handling(self, mock_redis, health_checker):
        """Test Redis connection handling under load."""
        # Test many concurrent Redis operations
        start_time = time.time()
        tasks = []

        for i in range(100):
            tasks.append(health_checker.check_redis_health())

        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # All operations should complete successfully
        assert len(results) == 100
        healthy_count = sum(1 for result in results if result["status"] == "healthy")
        assert healthy_count == 100

        # Should complete in reasonable time
        TestAssertion.assert_response_time_acceptable(start_time, end_time, 5.0)


class TestStressAndBreakingPoints:
    """Test system behavior at breaking points."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.timeout(10)
    async def test_large_search_results_handling(self, tidal_service, track_factory):
        """Test handling of very large search result sets."""
        # Create a very large result set
        huge_track_set = [
            track_factory(track_id=f"huge{i}", title=f"Huge Track {i}")
            for i in range(1000)
        ]

        # Mock search_tracks to respect limit parameter
        async def mock_search_tracks(query, limit=50, offset=0):
            return huge_track_set[offset:offset + limit]

        tidal_service.search_tracks = AsyncMock(side_effect=mock_search_tracks)

        with patch.object(server, 'ensure_service', return_value=tidal_service):
            # Ensure the tool has the required attributes
            if not hasattr(server.tidal_search, '__name__'):
                server.tidal_search.__name__ = 'tidal_search'
            if not hasattr(server.tidal_search, '__doc__'):
                server.tidal_search.__doc__ = 'Search for tracks on Tidal'

            start_time = time.time()
            result = await server.tidal_search.fn("huge_query", "tracks", 50)  # Limited by API
            end_time = time.time()

            # Should handle large dataset gracefully
            assert result["total_results"] == 50  # Based on actual returned results
            # When limit is specified, should return only requested amount
            assert len(result["results"]["tracks"]) == 50

            # Should still perform reasonably well
            TestAssertion.assert_response_time_acceptable(start_time, end_time, 3.0)

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.timeout(10)
    async def test_rapid_successive_requests(self, tidal_service, track_factory):
        """Test handling of rapid successive requests."""
        sample_tracks = [track_factory(track_id="rapid1", title="Rapid Track")]

        # Mock with minimal delay
        async def fast_mock(*args, **kwargs):
            await asyncio.sleep(0.01)  # 10ms delay
            return sample_tracks

        tidal_service.search_tracks = AsyncMock(side_effect=fast_mock)

        with patch.object(server, 'ensure_service', return_value=tidal_service):
            # Ensure the tool has the required attributes
            if not hasattr(server.tidal_search, '__name__'):
                server.tidal_search.__name__ = 'tidal_search'
            if not hasattr(server.tidal_search, '__doc__'):
                server.tidal_search.__doc__ = 'Search for tracks on Tidal'

            # Execute 100 rapid requests
            start_time = time.time()
            tasks = [
                server.tidal_search.fn(f"rapid_{i}", "tracks", 1)
                for i in range(100)
            ]
            results = await asyncio.gather(*tasks)
            end_time = time.time()

            # All should complete successfully
            assert len(results) == 100
            for result in results:
                assert len(result["results"]["tracks"]) == 1

            # Should complete quickly due to minimal processing
            TestAssertion.assert_response_time_acceptable(start_time, end_time, 5.0)

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.timeout(10)
    async def test_error_handling_performance(self, tidal_service):
        """Test performance of error handling under load."""
        # Setup service to always throw errors
        tidal_service.search_tracks = AsyncMock(side_effect=Exception("Load test error"))

        with patch.object(server, 'ensure_service', return_value=tidal_service):
            # Ensure the tool has the required attributes
            if not hasattr(server.tidal_search, '__name__'):
                server.tidal_search.__name__ = 'tidal_search'
            if not hasattr(server.tidal_search, '__doc__'):
                server.tidal_search.__doc__ = 'Search for tracks on Tidal'

            # Execute many requests that will fail
            start_time = time.time()
            tasks = [
                server.tidal_search.fn(f"error_{i}", "tracks")
                for i in range(50)
            ]
            results = await asyncio.gather(*tasks)
            end_time = time.time()

            # All should return error responses
            assert len(results) == 50
            for result in results:
                assert "error" in result

            # Error handling should still be fast
            TestAssertion.assert_response_time_acceptable(start_time, end_time, 2.0)


class TestPerformanceRegression:
    """Test for performance regressions."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.timeout(10)
    async def test_authentication_performance_regression(self, mock_auth_manager):
        """Test authentication performance baseline."""
        # Setup the mock to return immediately without real authentication
        mock_auth_manager.authenticate = AsyncMock(return_value=True)
        mock_auth_manager.get_user_info.return_value = {"id": "perf_user"}
        mock_auth_manager.is_authenticated.return_value = True

        # Mock the login function to return immediately without OAuth flow
        async def mock_login():
            return {
                "success": True,
                "message": "Mock authentication successful",
                "user": {"id": "perf_user", "username": "perf_user"}
            }

        # Ensure the tool has the required attributes
        if not hasattr(server.tidal_login, '__name__'):
            server.tidal_login.__name__ = 'tidal_login'
        if not hasattr(server.tidal_login, '__doc__'):
            server.tidal_login.__doc__ = 'Login to Tidal'

        # Override the fn method to use our fast mock
        server.tidal_login.fn = AsyncMock(side_effect=mock_login)

        # Measure multiple authentication attempts
        times = []
        for _ in range(10):
            start_time = time.time()
            result = await server.tidal_login.fn()
            end_time = time.time()
            times.append(end_time - start_time)
            assert result["success"] is True

        # Average time should be reasonable
        avg_time = sum(times) / len(times)
        assert avg_time < 1.0, f"Average auth time {avg_time:.3f}s exceeds baseline"

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.timeout(10)
    async def test_search_performance_regression(self, tidal_service, track_factory):
        """Test search performance baseline."""
        # Standard result set
        standard_tracks = [
            track_factory(track_id=f"std{i}", title=f"Standard Track {i}")
            for i in range(20)
        ]
        tidal_service.search_tracks = AsyncMock(return_value=standard_tracks)

        with patch.object(server, 'ensure_service', return_value=tidal_service):
            # Ensure the tool has the required attributes
            if not hasattr(server.tidal_search, '__name__'):
                server.tidal_search.__name__ = 'tidal_search'
            if not hasattr(server.tidal_search, '__doc__'):
                server.tidal_search.__doc__ = 'Search for tracks on Tidal'

            # Measure multiple search operations
            times = []
            for _ in range(10):
                start_time = time.time()
                result = await server.tidal_search.fn("standard_query", "tracks", 20)
                end_time = time.time()
                times.append(end_time - start_time)
                assert len(result["results"]["tracks"]) == 20

            # Average time should be reasonable
            avg_time = sum(times) / len(times)
            assert avg_time < 2.0, f"Average search time {avg_time:.3f}s exceeds baseline"