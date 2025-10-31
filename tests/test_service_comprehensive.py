"""

Comprehensive tests for service module to reach 80% coverage.
Targets specific uncovered lines identified in coverage report.
"""

import asyncio
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from tidal_mcp.auth import TidalAuth
from tidal_mcp.models import Artist, SearchResults
from tidal_mcp.service import TidalService, async_to_sync


class TestAsyncToSyncDecorator:
    """Tests for the async_to_sync decorator."""

    def test_async_to_sync_with_sync_function(self):
        """Test async_to_sync decorator with synchronous function."""

        @async_to_sync
        def sync_function(x, y=10):
            return x + y

        result = sync_function(5, y=15)
        assert result == 20

    def test_async_to_sync_with_async_function(self):
        """Test async_to_sync decorator with asynchronous function."""

        @async_to_sync
        async def async_function(x, y=10):
            await asyncio.sleep(0.001)  # Small delay
            return x * y

        result = async_function(3, y=4)
        assert result == 12

    def test_async_to_sync_preserves_function_name(self):
        """Test that async_to_sync preserves function name and docstring."""

        @async_to_sync
        def test_function():
            """Test docstring"""
            return "test"

        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test docstring"


class TestTidalServiceComprehensive:
    """Comprehensive tests targeting specific uncovered lines in service.py."""

    def test_service_initialization_success(self):
        """Test successful service initialization."""
        mock_auth = Mock(spec=TidalAuth)
        service = TidalService(mock_auth)

        assert service.auth == mock_auth
        assert hasattr(service, "_cache")

    def test_service_initialization_auth_none(self):
        """Test service initialization with None auth."""
        with pytest.raises(ValueError, match="auth cannot be None"):
            TidalService(None)

    @patch("tidal_mcp.service.tidalapi")
    def test_service_initialization_with_session(self, mock_tidalapi):
        """Test service initialization creates session."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        service = TidalService(mock_auth)

        assert service._session == mock_session
        mock_auth.get_tidal_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_tracks_success(self):
        """Test successful track search."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        # Mock search results
        mock_track_data = {
            "id": 123,
            "title": "Test Track",
            "artist": {"name": "Test Artist"},
            "album": {"title": "Test Album"},
            "duration": 240,
        }
        mock_session.search.return_value = {"tracks": [mock_track_data]}

        service = TidalService(mock_auth)
        results = await service.search_tracks("test query", limit=10)

        assert len(results) == 1
        assert results[0].id == "123"
        assert results[0].title == "Test Track"
        mock_session.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_tracks_empty_query(self):
        """Test track search with empty query."""
        mock_auth = Mock(spec=TidalAuth)
        service = TidalService(mock_auth)

        results = await service.search_tracks("", limit=10)

        assert results == []

    @pytest.mark.asyncio
    async def test_search_tracks_none_query(self):
        """Test track search with None query."""
        mock_auth = Mock(spec=TidalAuth)
        service = TidalService(mock_auth)

        results = await service.search_tracks(None, limit=10)

        assert results == []

    @pytest.mark.asyncio
    async def test_search_tracks_session_error(self):
        """Test track search when session raises error."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_session.search.side_effect = Exception("Search failed")
        mock_auth.get_tidal_session.return_value = mock_session

        service = TidalService(mock_auth)

        with pytest.raises(Exception, match="Search failed"):
            await service.search_tracks("test query")

    @pytest.mark.asyncio
    async def test_search_albums_success(self):
        """Test successful album search."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        mock_album_data = {
            "id": 456,
            "title": "Test Album",
            "artist": {"name": "Test Artist"},
            "releaseDate": "2023-01-01",
        }
        mock_session.search.return_value = {"albums": [mock_album_data]}

        service = TidalService(mock_auth)
        results = await service.search_albums("test album", limit=5)

        assert len(results) == 1
        assert results[0].id == "456"
        assert results[0].title == "Test Album"

    @pytest.mark.asyncio
    async def test_search_albums_no_results(self):
        """Test album search with no results."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_session.search.return_value = {"albums": []}
        mock_auth.get_tidal_session.return_value = mock_session

        service = TidalService(mock_auth)
        results = await service.search_albums("no results")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_artists_success(self):
        """Test successful artist search."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        mock_artist_data = {
            "id": 789,
            "name": "Test Artist",
            "picture": "artist_pic_url",
        }
        mock_session.search.return_value = {"artists": [mock_artist_data]}

        service = TidalService(mock_auth)
        results = await service.search_artists("test artist")

        assert len(results) == 1
        assert results[0].id == "789"
        assert results[0].name == "Test Artist"

    @pytest.mark.asyncio
    async def test_search_playlists_success(self):
        """Test successful playlist search."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        mock_playlist_data = {
            "uuid": "playlist123",
            "title": "Test Playlist",
            "description": "Test description",
            "creator": {"name": "Creator"},
        }
        mock_session.search.return_value = {"playlists": [mock_playlist_data]}

        service = TidalService(mock_auth)
        results = await service.search_playlists("test playlist")

        assert len(results) == 1
        assert results[0].id == "playlist123"
        assert results[0].title == "Test Playlist"

    @pytest.mark.asyncio
    async def test_search_comprehensive_success(self):
        """Test comprehensive search across all content types."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        mock_search_results = {
            "tracks": [{"id": 1, "title": "Track 1", "artist": {"name": "Artist 1"}}],
            "albums": [{"id": 2, "title": "Album 1", "artist": {"name": "Artist 1"}}],
            "artists": [{"id": 3, "name": "Artist 1"}],
            "playlists": [
                {
                    "uuid": "4",
                    "title": "Playlist 1",
                    "creator": {"name": "Creator"},
                }
            ],
        }
        mock_session.search.return_value = mock_search_results

        service = TidalService(mock_auth)
        results = await service.search_comprehensive("test query", limit=20)

        assert isinstance(results, SearchResults)
        assert len(results.tracks) == 1
        assert len(results.albums) == 1
        assert len(results.artists) == 1
        assert len(results.playlists) == 1

    @pytest.mark.asyncio
    async def test_get_track_success(self):
        """Test successful track retrieval."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        mock_track = Mock()
        mock_track_data = {
            "id": 123,
            "title": "Test Track",
            "artist": {"name": "Test Artist"},
            "duration": 240,
        }
        mock_track.asdict.return_value = mock_track_data
        mock_session.track.return_value = mock_track

        service = TidalService(mock_auth)
        result = await service.get_track("123")

        assert result.id == "123"
        assert result.title == "Test Track"
        mock_session.track.assert_called_once_with("123")

    @pytest.mark.asyncio
    async def test_get_track_not_found(self):
        """Test track retrieval when track not found."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_session.track.return_value = None
        mock_auth.get_tidal_session.return_value = mock_session

        service = TidalService(mock_auth)
        result = await service.get_track("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_track_invalid_id(self):
        """Test track retrieval with invalid ID."""
        mock_auth = Mock(spec=TidalAuth)
        service = TidalService(mock_auth)

        result = await service.get_track("")
        assert result is None

        result = await service.get_track(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_album_success(self):
        """Test successful album retrieval."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        mock_album = Mock()
        mock_album_data = {
            "id": 456,
            "title": "Test Album",
            "artist": {"name": "Test Artist"},
        }
        mock_album.asdict.return_value = mock_album_data
        mock_session.album.return_value = mock_album

        service = TidalService(mock_auth)
        result = await service.get_album("456")

        assert result.id == "456"
        assert result.title == "Test Album"

    @pytest.mark.asyncio
    async def test_get_artist_success(self):
        """Test successful artist retrieval."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        mock_artist = Mock()
        mock_artist_data = {
            "id": 789,
            "name": "Test Artist",
            "picture": "artist_pic",
        }
        mock_artist.asdict.return_value = mock_artist_data
        mock_session.artist.return_value = mock_artist

        service = TidalService(mock_auth)
        result = await service.get_artist("789")

        assert result.id == "789"
        assert result.name == "Test Artist"

    @pytest.mark.asyncio
    async def test_get_playlist_success(self):
        """Test successful playlist retrieval."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        mock_playlist = Mock()
        mock_playlist_data = {
            "uuid": "playlist123",
            "title": "Test Playlist",
            "description": "Test description",
        }
        mock_playlist.asdict.return_value = mock_playlist_data
        mock_session.playlist.return_value = mock_playlist

        service = TidalService(mock_auth)
        result = await service.get_playlist("playlist123")

        assert result.id == "playlist123"
        assert result.title == "Test Playlist"

    @pytest.mark.asyncio
    async def test_get_album_tracks_success(self):
        """Test successful album tracks retrieval."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        mock_album = Mock()
        mock_track = Mock()
        mock_track_data = {
            "id": 1,
            "title": "Track 1",
            "artist": {"name": "Artist 1"},
        }
        mock_track.asdict.return_value = mock_track_data
        mock_album.tracks.return_value = [mock_track]
        mock_session.album.return_value = mock_album

        service = TidalService(mock_auth)
        results = await service.get_album_tracks("456")

        assert len(results) == 1
        assert results[0].id == "1"
        assert results[0].title == "Track 1"

    @pytest.mark.asyncio
    async def test_get_album_tracks_album_not_found(self):
        """Test album tracks retrieval when album not found."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_session.album.return_value = None
        mock_auth.get_tidal_session.return_value = mock_session

        service = TidalService(mock_auth)
        results = await service.get_album_tracks("nonexistent")

        assert results == []

    @pytest.mark.asyncio
    async def test_get_artist_albums_success(self):
        """Test successful artist albums retrieval."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        mock_artist = Mock()
        mock_album = Mock()
        mock_album_data = {
            "id": 1,
            "title": "Album 1",
            "artist": {"name": "Artist 1"},
        }
        mock_album.asdict.return_value = mock_album_data
        mock_artist.get_albums.return_value = [mock_album]
        mock_session.artist.return_value = mock_artist

        service = TidalService(mock_auth)
        results = await service.get_artist_albums("789", limit=10)

        assert len(results) == 1
        assert results[0].id == "1"
        assert results[0].title == "Album 1"

    @pytest.mark.asyncio
    async def test_get_artist_tracks_success(self):
        """Test successful artist tracks retrieval."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        mock_artist = Mock()
        mock_track = Mock()
        mock_track_data = {
            "id": 1,
            "title": "Track 1",
            "artist": {"name": "Artist 1"},
        }
        mock_track.asdict.return_value = mock_track_data
        mock_artist.get_top_tracks.return_value = [mock_track]
        mock_session.artist.return_value = mock_artist

        service = TidalService(mock_auth)
        results = await service.get_artist_tracks("789", limit=20)

        assert len(results) == 1
        assert results[0].id == "1"
        assert results[0].title == "Track 1"

    @pytest.mark.asyncio
    async def test_get_playlist_tracks_success(self):
        """Test successful playlist tracks retrieval."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        mock_playlist = Mock()
        mock_track = Mock()
        mock_track_data = {
            "id": 1,
            "title": "Track 1",
            "artist": {"name": "Artist 1"},
        }
        mock_track.asdict.return_value = mock_track_data
        mock_playlist.tracks.return_value = [mock_track]
        mock_session.playlist.return_value = mock_playlist

        service = TidalService(mock_auth)
        results = await service.get_playlist_tracks("playlist123")

        assert len(results) == 1
        assert results[0].id == "1"
        assert results[0].title == "Track 1"

    @pytest.mark.asyncio
    async def test_caching_functionality(self):
        """Test service caching functionality."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        mock_track = Mock()
        mock_track_data = {
            "id": 123,
            "title": "Cached Track",
            "artist": {"name": "Test Artist"},
        }
        mock_track.asdict.return_value = mock_track_data
        mock_session.track.return_value = mock_track

        service = TidalService(mock_auth)

        # First call should hit the API
        result1 = await service.get_track("123")
        assert result1.title == "Cached Track"

        # Second call should use cache (verify by checking call count)
        result2 = await service.get_track("123")
        assert result2.title == "Cached Track"

        # Session should only be called once due to caching
        assert mock_session.track.call_count == 1

    @pytest.mark.asyncio
    async def test_error_handling_in_search(self):
        """Test error handling in search methods."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_session.search.side_effect = Exception("Search API error")
        mock_auth.get_tidal_session.return_value = mock_session

        service = TidalService(mock_auth)

        # Should handle errors gracefully
        with pytest.raises(Exception, match="Search API error"):
            await service.search_tracks("error query")

    @pytest.mark.asyncio
    async def test_error_handling_in_get_methods(self):
        """Test error handling in get methods."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_session.track.side_effect = Exception("API error")
        mock_auth.get_tidal_session.return_value = mock_session

        service = TidalService(mock_auth)

        with pytest.raises(Exception, match="API error"):
            await service.get_track("123")

    @pytest.mark.asyncio
    async def test_data_conversion_edge_cases(self):
        """Test data conversion with edge cases."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        # Test with minimal data
        mock_track_data = {
            "id": 123,
            "title": "",  # Empty title
            "duration": None,  # None duration
        }
        mock_session.search.return_value = {"tracks": [mock_track_data]}

        service = TidalService(mock_auth)
        results = await service.search_tracks("minimal data")

        assert len(results) == 1
        assert results[0].id == "123"
        assert results[0].title == ""

    @pytest.mark.asyncio
    async def test_limit_parameter_handling(self):
        """Test proper handling of limit parameters."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        # Mock multiple tracks
        mock_tracks = [
            {"id": i, "title": f"Track {i}", "artist": {"name": "Artist"}}
            for i in range(1, 26)  # 25 tracks
        ]
        mock_session.search.return_value = {"tracks": mock_tracks}

        service = TidalService(mock_auth)

        # Test with limit
        results = await service.search_tracks("many tracks", limit=10)

        # Should respect the limit
        assert len(results) <= 10

    def test_service_string_representation(self):
        """Test string representation of service."""
        mock_auth = Mock(spec=TidalAuth)
        service = TidalService(mock_auth)

        str_repr = str(service)
        repr_str = repr(service)

        assert "TidalService" in str_repr
        assert "TidalService" in repr_str
