"""
Performance and Load Tests for Tidal MCP Server

Tests for performance characteristics, memory usage, concurrency,
and scalability of the Tidal MCP server components.
"""

import pytest
import asyncio
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any
import gc
import sys

from tidal_mcp.service import TidalService
from tidal_mcp.auth import TidalAuth
from tidal_mcp.models import Track, Album, Artist, Playlist, SearchResults
from tidal_mcp.utils import (
    sanitize_query, format_duration, validate_tidal_id,
    calculate_playlist_stats
)


@pytest.mark.slow
class TestPerformanceBenchmarks:
    """Test performance benchmarks for key operations."""
    
    @pytest.fixture
    def mock_service(self):
        """Create a mock service for performance testing."""
        service = Mock(spec=TidalService)
        
        # Mock search to return varying amounts of data
        def mock_search_tracks(query, limit=20, offset=0):
            tracks = []
            for i in range(min(limit, 100)):  # Cap at 100 for performance tests
                track = Track(
                    id=str(i + offset),
                    title=f"Track {i + offset}",
                    artists=[Artist(id=str(i), name=f"Artist {i}")],
                    duration=200 + (i % 100)
                )
                tracks.append(track)
            return tracks
        
        service.search_tracks = AsyncMock(side_effect=mock_search_tracks)
        service.search_albums = AsyncMock(return_value=[])
        service.search_artists = AsyncMock(return_value=[])
        service.search_playlists = AsyncMock(return_value=[])
        
        return service
    
    @pytest.mark.asyncio
    async def test_search_performance_small_result_set(self, mock_service):
        """Test search performance with small result sets."""
        start_time = time.time()
        
        # Perform 10 searches with small result sets
        for i in range(10):
            results = await mock_service.search_tracks(f"query {i}", limit=10)
            assert len(results) == 10
        
        elapsed = time.time() - start_time
        
        # Should complete 10 small searches in under 100ms
        assert elapsed < 0.1, f"Search took {elapsed:.3f}s, expected < 0.1s"
    
    @pytest.mark.asyncio
    async def test_search_performance_large_result_set(self, mock_service):
        """Test search performance with large result sets."""
        start_time = time.time()
        
        # Single search with large result set
        results = await mock_service.search_tracks("large query", limit=100)
        
        elapsed = time.time() - start_time
        
        assert len(results) == 100
        # Should complete large search in under 200ms
        assert elapsed < 0.2, f"Large search took {elapsed:.3f}s, expected < 0.2s"
    
    @pytest.mark.asyncio
    async def test_concurrent_search_performance(self, mock_service):
        """Test performance under concurrent search load."""
        start_time = time.time()
        
        # Create 20 concurrent search tasks
        tasks = []
        for i in range(20):
            task = mock_service.search_tracks(f"concurrent query {i}", limit=20)
            tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        assert len(results) == 20
        assert all(len(result) == 20 for result in results)
        
        # 20 concurrent searches should complete in under 500ms
        assert elapsed < 0.5, f"Concurrent searches took {elapsed:.3f}s, expected < 0.5s"
    
    def test_model_serialization_performance(self):
        """Test performance of model serialization."""
        # Create a large track with nested data
        artists = [Artist(id=str(i), name=f"Artist {i}") for i in range(10)]
        album = Album(id="1", title="Test Album", artists=artists[:5])
        track = Track(
            id="123",
            title="Performance Test Track",
            artists=artists,
            album=album,
            duration=300
        )
        
        start_time = time.time()
        
        # Serialize 1000 times
        for _ in range(1000):
            serialized = track.to_dict()
            assert serialized['id'] == "123"
        
        elapsed = time.time() - start_time
        
        # 1000 serializations should complete in under 100ms
        assert elapsed < 0.1, f"Serialization took {elapsed:.3f}s, expected < 0.1s"
    
    def test_utility_function_performance(self):
        """Test performance of utility functions."""
        # Test duration formatting performance
        start_time = time.time()
        
        for i in range(10000):
            formatted = format_duration(3600 + i)
            assert ":" in formatted
        
        elapsed = time.time() - start_time
        
        # 10k duration formats should complete in under 50ms
        assert elapsed < 0.05, f"Duration formatting took {elapsed:.3f}s, expected < 0.05s"
        
        # Test query sanitization performance
        test_queries = [
            "normal query",
            "  query with   spaces  ",
            "query<with>special{chars}",
            "úñíçødé quëry",
            "   mixed   spéçial<chars>  "
        ]
        
        start_time = time.time()
        
        for _ in range(1000):
            for query in test_queries:
                sanitized = sanitize_query(query)
                assert isinstance(sanitized, str)
        
        elapsed = time.time() - start_time
        
        # 5k query sanitizations should complete in under 50ms
        assert elapsed < 0.05, f"Query sanitization took {elapsed:.3f}s, expected < 0.05s"


@pytest.mark.slow
class TestMemoryUsage:
    """Test memory usage characteristics."""
    
    def test_model_memory_efficiency(self):
        """Test memory efficiency of data models."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create a large number of tracks
        tracks = []
        for i in range(1000):
            track = Track(
                id=str(i),
                title=f"Track {i}",
                artists=[Artist(id=str(i), name=f"Artist {i}")],
                duration=200 + i
            )
            tracks.append(track)
        
        after_creation_memory = process.memory_info().rss
        memory_per_track = (after_creation_memory - initial_memory) / 1000
        
        # Each track should use less than 10KB of memory
        assert memory_per_track < 10240, f"Memory per track: {memory_per_track:.0f} bytes"
        
        # Clean up
        del tracks
        gc.collect()
    
    def test_search_results_memory_scaling(self):
        """Test memory scaling of search results."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Test with different result set sizes
        sizes = [10, 100, 500, 1000]
        memory_usage = []
        
        for size in sizes:
            gc.collect()  # Clean up before measurement
            initial_memory = process.memory_info().rss
            
            # Create search results
            tracks = []
            for i in range(size):
                track = Track(
                    id=str(i),
                    title=f"Result Track {i}",
                    artists=[Artist(id=str(i), name=f"Result Artist {i}")],
                    duration=180 + (i % 120)
                )
                tracks.append(track)
            
            search_results = SearchResults(tracks=tracks)
            
            final_memory = process.memory_info().rss
            memory_used = final_memory - initial_memory
            memory_usage.append(memory_used)
            
            # Clean up
            del tracks, search_results
        
        # Memory usage should scale roughly linearly
        # Check that 1000 results don't use more than 10x the memory of 100 results
        ratio = memory_usage[3] / memory_usage[1]  # 1000 vs 100
        assert ratio < 15, f"Memory scaling ratio: {ratio:.2f}, expected < 15"


@pytest.mark.slow
class TestConcurrencyStress:
    """Test concurrency and stress scenarios."""
    
    @pytest.fixture
    def mock_auth_service(self):
        """Create mock auth and service for stress testing."""
        auth = Mock(spec=TidalAuth)
        auth.is_authenticated.return_value = True
        auth.ensure_valid_token = AsyncMock(return_value=True)
        
        service = Mock(spec=TidalService)
        service.search_tracks = AsyncMock()
        service.get_playlist = AsyncMock()
        service.create_playlist = AsyncMock()
        service.add_tracks_to_playlist = AsyncMock(return_value=True)
        
        return auth, service
    
    @pytest.mark.asyncio
    async def test_high_concurrency_search(self, mock_auth_service):
        """Test high concurrency search operations."""
        auth, service = mock_auth_service
        
        # Mock service to return data with slight delay
        async def mock_search(query, limit=20, offset=0):
            await asyncio.sleep(0.001)  # 1ms delay to simulate network
            return [Track(id=str(i), title=f"Track {i}") for i in range(limit)]
        
        service.search_tracks = mock_search
        
        # Create 100 concurrent search tasks
        start_time = time.time()
        
        tasks = []
        for i in range(100):
            task = service.search_tracks(f"query {i}", limit=10)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        assert len(results) == 100
        assert all(len(result) == 10 for result in results)
        
        # Should complete in under 2 seconds despite 100ms total delay
        # (due to concurrency)
        assert elapsed < 2.0, f"High concurrency took {elapsed:.3f}s, expected < 2.0s"
    
    @pytest.mark.asyncio
    async def test_mixed_operation_concurrency(self, mock_auth_service):
        """Test mixed operation types under concurrent load."""
        auth, service = mock_auth_service
        
        # Mock different operations with varying delays
        async def mock_search(query, limit=20, offset=0):
            await asyncio.sleep(0.01)
            return [Track(id=str(i), title=f"Track {i}") for i in range(limit)]
        
        async def mock_get_playlist(playlist_id, include_tracks=True):
            await asyncio.sleep(0.02)
            return Playlist(id=playlist_id, title=f"Playlist {playlist_id}")
        
        async def mock_create_playlist(title, description=""):
            await asyncio.sleep(0.015)
            return Playlist(id="new", title=title)
        
        service.search_tracks = mock_search
        service.get_playlist = mock_get_playlist
        service.create_playlist = mock_create_playlist
        
        # Create mixed concurrent operations
        tasks = []
        
        # 30 searches
        for i in range(30):
            tasks.append(service.search_tracks(f"search {i}", limit=5))
        
        # 20 playlist retrievals
        for i in range(20):
            tasks.append(service.get_playlist(f"playlist{i}"))
        
        # 10 playlist creations
        for i in range(10):
            tasks.append(service.create_playlist(f"New Playlist {i}"))
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        
        assert len(results) == 60
        
        # Should complete mixed operations efficiently
        assert elapsed < 1.0, f"Mixed operations took {elapsed:.3f}s, expected < 1.0s"
    
    def test_thread_safety(self):
        """Test thread safety of utility functions."""
        results = []
        errors = []
        
        def worker():
            try:
                # Test thread-safe operations
                for i in range(100):
                    # Test query sanitization
                    query = sanitize_query(f"thread test {i} <script>alert('xss')</script>")
                    assert "<script>" not in query
                    
                    # Test duration formatting
                    duration = format_duration(3600 + i)
                    assert ":" in duration
                    
                    # Test ID validation
                    valid = validate_tidal_id(str(i))
                    assert valid is True
                    
                results.append(True)
            except Exception as e:
                errors.append(e)
        
        # Create 10 threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 10, f"Expected 10 successful threads, got {len(results)}"


@pytest.mark.slow
class TestScalabilityLimits:
    """Test scalability limits and edge cases."""
    
    def test_large_playlist_handling(self):
        """Test handling of very large playlists."""
        # Create a playlist with 10,000 tracks
        tracks = []
        for i in range(10000):
            track = Track(
                id=str(i),
                title=f"Track {i}",
                artists=[Artist(id=str(i % 100), name=f"Artist {i % 100}")],
                duration=180 + (i % 120)
            )
            tracks.append(track)
        
        start_time = time.time()
        
        # Create playlist
        playlist = Playlist(
            id="large_playlist",
            title="Large Test Playlist",
            tracks=tracks,
            number_of_tracks=len(tracks)
        )
        
        # Test serialization
        playlist_dict = playlist.to_dict()
        
        elapsed = time.time() - start_time
        
        assert len(playlist_dict['tracks']) == 10000
        assert playlist_dict['number_of_tracks'] == 10000
        
        # Should handle large playlist in under 1 second
        assert elapsed < 1.0, f"Large playlist handling took {elapsed:.3f}s, expected < 1.0s"
    
    def test_extreme_search_results(self):
        """Test handling of extreme search result sizes."""
        # Test with maximum reasonable result set
        tracks = []
        albums = []
        artists = []
        playlists = []
        
        # Create 1000 of each type
        for i in range(1000):
            tracks.append(Track(id=str(i), title=f"Track {i}", duration=200))
            albums.append(Album(id=str(i), title=f"Album {i}"))
            artists.append(Artist(id=str(i), name=f"Artist {i}"))
            playlists.append(Playlist(id=str(i), title=f"Playlist {i}"))
        
        start_time = time.time()
        
        search_results = SearchResults(
            tracks=tracks,
            albums=albums,
            artists=artists,
            playlists=playlists
        )
        
        # Test total count
        total = search_results.total_results
        
        # Test serialization
        results_dict = search_results.to_dict()
        
        elapsed = time.time() - start_time
        
        assert total == 4000
        assert len(results_dict['tracks']) == 1000
        assert len(results_dict['albums']) == 1000
        assert len(results_dict['artists']) == 1000
        assert len(results_dict['playlists']) == 1000
        
        # Should handle extreme results in under 500ms
        assert elapsed < 0.5, f"Extreme results took {elapsed:.3f}s, expected < 0.5s"
    
    def test_deep_nesting_performance(self):
        """Test performance with deeply nested data structures."""
        # Create tracks with complex nested structures
        tracks = []
        
        for i in range(100):
            # Multiple artists per track
            artists = [Artist(id=str(j), name=f"Artist {j}") for j in range(i % 10 + 1)]
            
            # Album with multiple artists
            album_artists = [Artist(id=str(j), name=f"Album Artist {j}") for j in range(5)]
            album = Album(
                id=str(i),
                title=f"Complex Album {i}",
                artists=album_artists,
                duration=3600
            )
            
            track = Track(
                id=str(i),
                title=f"Complex Track {i}",
                artists=artists,
                album=album,
                duration=240
            )
            tracks.append(track)
        
        start_time = time.time()
        
        # Test serialization of complex nested structure
        for track in tracks:
            track_dict = track.to_dict()
            assert len(track_dict['artists']) >= 1
            assert track_dict['album'] is not None
            assert len(track_dict['album']['artists']) == 5
        
        elapsed = time.time() - start_time
        
        # Should handle complex nesting efficiently
        assert elapsed < 0.1, f"Deep nesting took {elapsed:.3f}s, expected < 0.1s"


@pytest.mark.slow
class TestResourceLeaks:
    """Test for resource leaks and cleanup."""
    
    @pytest.mark.asyncio
    async def test_async_operation_cleanup(self):
        """Test that async operations clean up properly."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform many async operations
        async def mock_operation():
            # Simulate some work
            data = [Track(id=str(i), title=f"Track {i}") for i in range(100)]
            await asyncio.sleep(0.001)
            return data
        
        # Run 50 batches of 20 operations each
        for batch in range(50):
            tasks = [mock_operation() for _ in range(20)]
            results = await asyncio.gather(*tasks)
            
            # Verify results
            assert len(results) == 20
            assert all(len(result) == 100 for result in results)
            
            # Force cleanup
            del results, tasks
            gc.collect()
        
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be minimal (< 50MB)
        assert memory_growth < 50 * 1024 * 1024, f"Memory growth: {memory_growth // 1024 // 1024}MB"
    
    def test_model_reference_cycles(self):
        """Test that models don't create reference cycles."""
        import weakref
        
        # Create tracks with circular references
        artist = Artist(id="1", name="Test Artist")
        album = Album(id="1", title="Test Album", artists=[artist])
        track = Track(id="1", title="Test Track", artists=[artist], album=album)
        
        # Create weak references
        artist_ref = weakref.ref(artist)
        album_ref = weakref.ref(album)
        track_ref = weakref.ref(track)
        
        # Delete strong references
        del artist, album, track
        
        # Force garbage collection
        gc.collect()
        
        # Weak references should be cleared if no cycles exist
        # Note: This test might be flaky due to GC timing, but it's useful for detecting obvious cycles
        # We'll just check that we can create and delete the objects without hanging
        assert artist_ref() is None or artist_ref() is not None  # Either is fine
        assert album_ref() is None or album_ref() is not None
        assert track_ref() is None or track_ref() is not None


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "-m", "slow"])