"""
Comprehensive Error Handling Tests

Tests for error scenarios, edge cases, and failure modes across all components
of the Tidal MCP server. Ensures robust error handling and graceful degradation.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import aiohttp
import json

from tidal_mcp.auth import TidalAuth, TidalAuthError
from tidal_mcp.service import TidalService
from tidal_mcp.server import (
    tidal_search, tidal_login, tidal_get_playlist, tidal_create_playlist,
    tidal_add_to_playlist, tidal_get_favorites, ensure_service
)
from tidal_mcp.models import Track, Album, Artist, Playlist
from tidal_mcp.utils import sanitize_query, validate_tidal_id


class TestAuthenticationErrors:
    """Test authentication error scenarios."""
    
    @pytest.mark.asyncio
    async def test_auth_network_failure(self, temp_session_file):
        """Test authentication with network failures."""
        with patch.object(TidalAuth, '_oauth2_flow', new_callable=AsyncMock) as mock_oauth:
            mock_oauth.side_effect = aiohttp.ClientError("Network unreachable")
            
            auth = TidalAuth()
            result = await auth.authenticate()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_auth_invalid_response(self, temp_session_file):
        """Test authentication with invalid API responses."""
        with patch.object(TidalAuth, '_exchange_code_for_tokens', new_callable=AsyncMock) as mock_exchange:
            # Simulate malformed response
            mock_exchange.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            
            auth = TidalAuth()
            result = await auth._oauth2_flow()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_auth_token_corruption(self, temp_session_file):
        """Test handling of corrupted tokens."""
        auth = TidalAuth()
        auth.session_file = temp_session_file
        
        # Write corrupted session file
        with open(temp_session_file, 'w') as f:
            f.write("invalid json content")
        
        # Should handle corruption gracefully
        auth._load_session()
        assert auth.access_token is None
        assert auth.refresh_token is None
    
    @pytest.mark.asyncio
    async def test_auth_expired_refresh_token(self, temp_session_file):
        """Test handling of expired refresh tokens."""
        auth = TidalAuth()
        auth.refresh_token = "expired_token"
        
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value='{"error": "invalid_grant"}')
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await auth.refresh_access_token()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_auth_rate_limiting(self, temp_session_file):
        """Test handling of rate limit responses."""
        auth = TidalAuth()
        auth.refresh_token = "valid_token"
        
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.text = AsyncMock(return_value='Rate limit exceeded')
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await auth.refresh_access_token()
            assert result is False
    
    def test_auth_file_permission_error(self, temp_session_file):
        """Test handling of file permission errors."""
        auth = TidalAuth()
        auth.session_file = temp_session_file
        auth.access_token = "test_token"
        
        # Mock permission error on file write
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            # Should not raise exception, just log error
            auth._save_session()
    
    @pytest.mark.asyncio
    async def test_auth_timeout_error(self, temp_session_file):
        """Test handling of timeout errors during authentication."""
        auth = TidalAuth()
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            mock_session.post.side_effect = asyncio.TimeoutError("Request timeout")
            
            result = await auth.refresh_access_token()
            assert result is False


class TestServiceLayerErrors:
    """Test service layer error scenarios."""
    
    @pytest.fixture
    def mock_auth_failed(self):
        """Create mock auth that fails."""
        auth = Mock(spec=TidalAuth)
        auth.ensure_valid_token = AsyncMock(return_value=False)
        auth.get_tidal_session.side_effect = TidalAuthError("Not authenticated")
        return auth
    
    @pytest.fixture
    def mock_auth_expired(self):
        """Create mock auth with expired token."""
        auth = Mock(spec=TidalAuth)
        auth.ensure_valid_token = AsyncMock(side_effect=TidalAuthError("Token expired"))
        return auth
    
    @pytest.mark.asyncio
    async def test_service_authentication_failure(self, mock_auth_failed):
        """Test service operations with authentication failures."""
        service = TidalService(auth=mock_auth_failed)
        
        # All operations should fail gracefully
        results = await service.search_tracks("test query")
        assert results == []
        
        playlist = await service.get_playlist("playlist123")
        assert playlist is None
        
        favorites = await service.get_user_favorites("tracks")
        assert favorites == []
    
    @pytest.mark.asyncio
    async def test_service_tidal_api_errors(self, mock_auth):
        """Test service with Tidal API errors."""
        mock_session = Mock()
        mock_session.search.side_effect = Exception("Tidal API error")
        mock_session.playlist.side_effect = Exception("Playlist not accessible")
        mock_session.user.favorites.tracks.side_effect = Exception("Favorites unavailable")
        
        mock_auth.get_tidal_session.return_value = mock_session
        service = TidalService(auth=mock_auth)
        
        # Should handle API errors gracefully
        tracks = await service.search_tracks("query")
        assert tracks == []
        
        playlist = await service.get_playlist("test")
        assert playlist is None
        
        favorites = await service.get_user_favorites("tracks")
        assert favorites == []
    
    @pytest.mark.asyncio
    async def test_service_malformed_api_response(self, mock_auth):
        """Test service with malformed API responses."""
        mock_session = Mock()
        
        # Mock malformed search response
        mock_session.search.return_value = {"invalid": "structure"}
        
        # Mock malformed track object
        malformed_track = Mock()
        malformed_track.id = None
        malformed_track.name = None
        mock_session.search.return_value = {"tracks": [malformed_track]}
        
        mock_auth.get_tidal_session.return_value = mock_session
        service = TidalService(auth=mock_auth)
        
        tracks = await service.search_tracks("query")
        # Should filter out malformed tracks
        assert tracks == []
    
    @pytest.mark.asyncio
    async def test_service_partial_failures(self, mock_auth):
        """Test service handling partial failures."""
        mock_session = Mock()
        
        # Mock mixed valid and invalid tracks
        valid_track = Mock()
        valid_track.id = 123
        valid_track.name = "Valid Track"
        valid_track.duration = 240
        valid_track.track_num = 1
        valid_track.volume_num = 1
        valid_track.explicit = False
        valid_track.audio_quality = "LOSSLESS"
        valid_track.artist = Mock(id=1, name="Artist")
        valid_track.artists = [valid_track.artist]
        valid_track.album = Mock(id=1, name="Album", artists=[valid_track.artist])
        
        invalid_track = Mock()
        invalid_track.id = None  # This will cause conversion to fail
        
        mock_session.search.return_value = {"tracks": [valid_track, invalid_track]}
        mock_auth.get_tidal_session.return_value = mock_session
        service = TidalService(auth=mock_auth)
        
        tracks = await service.search_tracks("query")
        # Should return only valid tracks
        assert len(tracks) == 1
        assert tracks[0].id == "123"
    
    @pytest.mark.asyncio
    async def test_service_conversion_errors(self, mock_auth):
        """Test service model conversion errors."""
        service = TidalService(auth=mock_auth)
        
        # Test track conversion with None input
        result = await service._convert_tidal_track(None)
        assert result is None
        
        # Test track conversion with invalid data
        invalid_track = Mock()
        invalid_track.id = None
        
        result = await service._convert_tidal_track(invalid_track)
        assert result is None


class TestServerToolErrors:
    """Test MCP server tool error scenarios."""
    
    @pytest.mark.asyncio
    async def test_server_ensure_service_failures(self):
        """Test ensure_service error scenarios."""
        # Reset global state
        import tidal_mcp.server as server_module
        server_module.auth_manager = None
        server_module.tidal_service = None
        
        with patch('tidal_mcp.server.TidalAuth') as MockAuth:
            # Mock auth creation failure
            MockAuth.side_effect = Exception("Auth creation failed")
            
            with pytest.raises(Exception, match="Auth creation failed"):
                await ensure_service()
    
    @pytest.mark.asyncio
    async def test_server_tool_authentication_errors(self):
        """Test server tools with authentication errors."""
        with patch('tidal_mcp.server.ensure_service') as mock_ensure:
            mock_ensure.side_effect = TidalAuthError("Authentication required")
            
            # Test various tools
            result = await tidal_search("query", "tracks")
            assert "error" in result
            assert "Authentication required" in result["error"]
            
            result = await tidal_get_playlist("playlist123")
            assert "error" in result
            
            result = await tidal_create_playlist("New Playlist")
            assert "error" in result
            
            result = await tidal_get_favorites("tracks")
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_server_tool_service_errors(self):
        """Test server tools with service layer errors."""
        mock_service = Mock()
        mock_service.search_tracks.side_effect = Exception("Search service error")
        mock_service.create_playlist.side_effect = Exception("Playlist creation error")
        mock_service.get_user_favorites.side_effect = Exception("Favorites error")
        
        with patch('tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await tidal_search("query", "tracks")
            assert "error" in result
            assert "Search failed" in result["error"]
            
            result = await tidal_create_playlist("Test")
            assert "error" in result
            assert "Failed to create playlist" in result["error"]
            
            result = await tidal_get_favorites("tracks")
            assert "error" in result
            assert "Failed to get favorites" in result["error"]
    
    @pytest.mark.asyncio
    async def test_server_parameter_validation_errors(self):
        """Test server tools with invalid parameters."""
        mock_service = Mock()
        mock_service.search_tracks = AsyncMock(return_value=[])
        
        with patch('tidal_mcp.server.ensure_service', return_value=mock_service):
            # Test with empty track list
            result = await tidal_add_to_playlist("playlist123", [])
            assert result["success"] is False
            assert "No track IDs provided" in result["error"]
            
            # Test with empty indices list
            result = await tidal_remove_from_playlist("playlist123", [])
            assert result["success"] is False
            assert "No track indices provided" in result["error"]


class TestModelValidationErrors:
    """Test model validation and edge cases."""
    
    def test_model_creation_with_none_values(self):
        """Test model creation with None values."""
        # Test Track with None required fields
        track = Track(id=None, title=None)
        assert track.id is None
        assert track.title is None
        
        # Test serialization doesn't crash
        track_dict = track.to_dict()
        assert track_dict["id"] is None
        assert track_dict["title"] is None
    
    def test_model_from_api_data_none_input(self):
        """Test model creation from None API data."""
        track = Track.from_api_data(None)
        assert track.id == ""
        assert track.title == ""
        
        album = Album.from_api_data(None)
        assert album.id == ""
        assert album.title == ""
        
        artist = Artist.from_api_data(None)
        assert artist.id == ""
        assert artist.name == ""
    
    def test_model_circular_reference_handling(self):
        """Test handling of circular references in models."""
        # Create artist
        artist = Artist(id="1", name="Test Artist")
        
        # Create album with artist
        album = Album(id="1", title="Test Album", artists=[artist])
        
        # Create track with both artist and album
        track = Track(id="1", title="Test Track", artists=[artist], album=album)
        
        # Test serialization doesn't cause infinite recursion
        track_dict = track.to_dict()
        assert track_dict["artists"][0]["name"] == "Test Artist"
        assert track_dict["album"]["artists"][0]["name"] == "Test Artist"
    
    def test_playlist_invalid_date_handling(self):
        """Test playlist with invalid date formats."""
        api_data = {
            "uuid": "test",
            "title": "Test Playlist",
            "created": "not-a-date",
            "lastUpdated": "also-not-a-date"
        }
        
        playlist = Playlist.from_api_data(api_data)
        assert playlist.created_at is None
        assert playlist.updated_at is None
        
        # Test serialization
        playlist_dict = playlist.to_dict()
        assert playlist_dict["created_at"] is None
        assert playlist_dict["updated_at"] is None


class TestUtilityErrors:
    """Test utility function error scenarios."""
    
    def test_sanitize_query_edge_cases(self):
        """Test query sanitization with edge cases."""
        # Test with None
        assert sanitize_query(None) == ""
        
        # Test with non-string input
        assert sanitize_query(123) == ""
        assert sanitize_query([]) == ""
        assert sanitize_query({}) == ""
    
    def test_validate_tidal_id_edge_cases(self):
        """Test ID validation with edge cases."""
        # Test with None
        assert validate_tidal_id(None) is False
        
        # Test with non-string input
        assert validate_tidal_id(123) is False
        assert validate_tidal_id([]) is False
        assert validate_tidal_id({}) is False
    
    def test_safe_get_error_scenarios(self):
        """Test safe_get with error scenarios."""
        from tidal_mcp.utils import safe_get
        
        # Test with None data
        assert safe_get(None, "key") is None
        
        # Test with non-dict data
        assert safe_get("string", "key") is None
        assert safe_get(123, "key") is None
        assert safe_get([], "key") is None
    
    def test_duration_formatting_errors(self):
        """Test duration formatting with invalid inputs."""
        from tidal_mcp.utils import format_duration, parse_duration
        
        # Test format_duration with invalid inputs
        assert format_duration(None) == "0:00"
        assert format_duration(-10) == "0:00"
        assert format_duration("invalid") == "0:00"
        
        # Test parse_duration with invalid inputs
        assert parse_duration(None) == 0
        assert parse_duration("") == 0
        assert parse_duration("invalid:format") == 0
        assert parse_duration("1:2:3:4:5") == 0  # Too many parts


class TestConcurrencyErrors:
    """Test error scenarios under concurrent load."""
    
    @pytest.mark.asyncio
    async def test_concurrent_authentication_failures(self):
        """Test concurrent operations with authentication failures."""
        # Create multiple tasks that will all fail authentication
        async def failing_operation():
            with patch('tidal_mcp.server.ensure_service') as mock_ensure:
                mock_ensure.side_effect = TidalAuthError("Auth failed")
                return await tidal_search("query", "tracks")
        
        # Run 10 concurrent failing operations
        tasks = [failing_operation() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should return error responses, not raise exceptions
        for result in results:
            assert isinstance(result, dict)
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_concurrent_service_errors(self):
        """Test concurrent service layer errors."""
        mock_service = Mock()
        mock_service.search_tracks.side_effect = Exception("Service error")
        
        async def failing_search():
            with patch('tidal_mcp.server.ensure_service', return_value=mock_service):
                return await tidal_search("query", "tracks")
        
        # Run concurrent failing searches
        tasks = [failing_search() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All should handle errors gracefully
        for result in results:
            assert "error" in result
            assert "Search failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_mixed_success_failure_scenarios(self):
        """Test mixed success and failure scenarios."""
        call_count = 0
        
        def alternating_behavior(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:
                raise Exception("Intermittent failure")
            return [Track(id="1", title="Success Track")]
        
        mock_service = Mock()
        mock_service.search_tracks = AsyncMock(side_effect=alternating_behavior)
        
        async def search_operation():
            with patch('tidal_mcp.server.ensure_service', return_value=mock_service):
                return await tidal_search("query", "tracks")
        
        # Run multiple operations
        tasks = [search_operation() for _ in range(6)]
        results = await asyncio.gather(*tasks)
        
        # Should have mix of successes and failures
        successes = sum(1 for r in results if "results" in r)
        failures = sum(1 for r in results if "error" in r)
        
        assert successes > 0
        assert failures > 0
        assert successes + failures == 6


class TestResourceExhaustionScenarios:
    """Test behavior under resource exhaustion."""
    
    @pytest.mark.asyncio
    async def test_memory_pressure_handling(self):
        """Test behavior under memory pressure."""
        # Create a scenario that could cause memory issues
        large_tracks = []
        
        try:
            # Create many large track objects
            for i in range(10000):
                artists = [Artist(id=str(j), name=f"Artist {j}") for j in range(10)]
                track = Track(
                    id=str(i),
                    title=f"Large Track {i}" * 10,  # Long title
                    artists=artists,
                    duration=300
                )
                large_tracks.append(track)
            
            # Test serialization under memory pressure
            serialized = [track.to_dict() for track in large_tracks[:100]]
            assert len(serialized) == 100
            
        finally:
            # Clean up
            del large_tracks
    
    @pytest.mark.asyncio
    async def test_file_descriptor_exhaustion(self, temp_session_file):
        """Test behavior with file descriptor issues."""
        auth = TidalAuth()
        auth.session_file = temp_session_file
        
        # Mock file operations to simulate descriptor exhaustion
        with patch('builtins.open', side_effect=OSError("Too many open files")):
            # Should handle file errors gracefully
            auth._load_session()
            assert auth.access_token is None
            
            auth.access_token = "test"
            auth._save_session()  # Should not crash


class TestDataIntegrityErrors:
    """Test data integrity and validation errors."""
    
    def test_search_results_data_consistency(self):
        """Test search results data consistency."""
        from tidal_mcp.models import SearchResults
        
        # Create search results with inconsistent data
        results = SearchResults()
        
        # Add tracks with None IDs (shouldn't happen but test robustness)
        bad_track = Track(id=None, title="Bad Track")
        results.tracks.append(bad_track)
        
        # Test serialization handles bad data
        results_dict = results.to_dict()
        assert len(results_dict["tracks"]) == 1
        assert results_dict["tracks"][0]["id"] is None
    
    def test_playlist_track_integrity(self):
        """Test playlist track list integrity."""
        # Create playlist with mixed valid/invalid tracks
        valid_track = Track(id="1", title="Valid")
        invalid_track = Track(id="", title="")  # Empty values
        
        playlist = Playlist(
            id="test",
            title="Mixed Playlist",
            tracks=[valid_track, invalid_track]
        )
        
        playlist_dict = playlist.to_dict()
        assert len(playlist_dict["tracks"]) == 2
        # Both tracks should be serialized, even with empty values
        assert playlist_dict["tracks"][0]["id"] == "1"
        assert playlist_dict["tracks"][1]["id"] == ""


if __name__ == "__main__":
    # Run error handling tests
    pytest.main([__file__, "-v"])