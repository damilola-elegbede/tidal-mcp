"""
Simple tests for service module to boost coverage.
Focus on basic functionality without complex mocking.
"""

from unittest.mock import Mock, patch

import pytest

from tidal_mcp.auth import TidalAuth
from tidal_mcp.service import TidalService, async_to_sync


class TestAsyncToSyncSimple:
    """Simple tests for async_to_sync decorator."""

    def test_async_to_sync_basic(self):
        """Test async_to_sync with basic function."""

        @async_to_sync
        def simple_func(x):
            return x * 2

        result = simple_func(5)
        assert result == 10

    def test_async_to_sync_preserves_attributes(self):
        """Test that decorator preserves function attributes."""

        @async_to_sync
        def test_func():
            """Test docstring"""
            return "test"

        assert test_func.__name__ == "test_func"
        assert test_func.__doc__ == "Test docstring"


class TestTidalServiceSimple:
    """Simple tests for TidalService class."""

    def test_service_init_with_auth(self):
        """Test service initialization with auth."""
        mock_auth = Mock(spec=TidalAuth)
        service = TidalService(mock_auth)

        assert service.auth == mock_auth
        assert hasattr(service, "_cache")

    def test_service_init_none_auth_raises_error(self):
        """Test service initialization with None auth raises error."""
        with pytest.raises(ValueError, match="auth cannot be None"):
            TidalService(None)

    @patch("tidal_mcp.service.tidalapi")
    def test_service_has_session_property(self, mock_tidalapi):
        """Test that service initializes session property."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        service = TidalService(mock_auth)

        # Access the session property
        session = service._session
        assert session == mock_session

    @pytest.mark.asyncio
    async def test_search_tracks_empty_query(self):
        """Test search_tracks with empty query."""
        mock_auth = Mock(spec=TidalAuth)
        service = TidalService(mock_auth)

        result = await service.search_tracks("")
        assert result == []

        result = await service.search_tracks(None)
        assert result == []

    @pytest.mark.asyncio
    async def test_search_albums_empty_query(self):
        """Test search_albums with empty query."""
        mock_auth = Mock(spec=TidalAuth)
        service = TidalService(mock_auth)

        result = await service.search_albums("")
        assert result == []

    @pytest.mark.asyncio
    async def test_search_artists_empty_query(self):
        """Test search_artists with empty query."""
        mock_auth = Mock(spec=TidalAuth)
        service = TidalService(mock_auth)

        result = await service.search_artists("")
        assert result == []

    @pytest.mark.asyncio
    async def test_search_playlists_empty_query(self):
        """Test search_playlists with empty query."""
        mock_auth = Mock(spec=TidalAuth)
        service = TidalService(mock_auth)

        result = await service.search_playlists("")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_track_invalid_id(self):
        """Test get_track with invalid ID."""
        mock_auth = Mock(spec=TidalAuth)
        service = TidalService(mock_auth)

        result = await service.get_track("")
        assert result is None

        result = await service.get_track(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_album_invalid_id(self):
        """Test get_album with invalid ID."""
        mock_auth = Mock(spec=TidalAuth)
        service = TidalService(mock_auth)

        result = await service.get_album("")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_artist_invalid_id(self):
        """Test get_artist with invalid ID."""
        mock_auth = Mock(spec=TidalAuth)
        service = TidalService(mock_auth)

        result = await service.get_artist("")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_playlist_invalid_id(self):
        """Test get_playlist with invalid ID."""
        mock_auth = Mock(spec=TidalAuth)
        service = TidalService(mock_auth)

        result = await service.get_playlist("")
        assert result is None

    @pytest.mark.asyncio
    @patch("tidal_mcp.service.tidalapi")
    async def test_search_tracks_with_valid_query(self, mock_tidalapi):
        """Test search_tracks with valid query."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        # Mock search results
        mock_session.search.return_value = {
            "tracks": [
                {
                    "id": 123,
                    "title": "Test Track",
                    "artist": {"name": "Test Artist"},
                    "duration": 240,
                }
            ]
        }

        service = TidalService(mock_auth)
        results = await service.search_tracks("test query")

        assert len(results) == 1
        assert results[0].id == "123"
        assert results[0].title == "Test Track"

    @pytest.mark.asyncio
    @patch("tidal_mcp.service.tidalapi")
    async def test_search_tracks_no_results(self, mock_tidalapi):
        """Test search_tracks with no results."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        mock_session.search.return_value = {"tracks": []}

        service = TidalService(mock_auth)
        results = await service.search_tracks("no results")

        assert results == []

    @pytest.mark.asyncio
    @patch("tidal_mcp.service.tidalapi")
    async def test_search_albums_with_results(self, mock_tidalapi):
        """Test search_albums with results."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        mock_session.search.return_value = {
            "albums": [
                {"id": 456, "title": "Test Album", "artist": {"name": "Test Artist"}}
            ]
        }

        service = TidalService(mock_auth)
        results = await service.search_albums("test album")

        assert len(results) == 1
        assert results[0].id == "456"
        assert results[0].title == "Test Album"

    @pytest.mark.asyncio
    @patch("tidal_mcp.service.tidalapi")
    async def test_search_artists_with_results(self, mock_tidalapi):
        """Test search_artists with results."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        mock_session.search.return_value = {
            "artists": [{"id": 789, "name": "Test Artist"}]
        }

        service = TidalService(mock_auth)
        results = await service.search_artists("test artist")

        assert len(results) == 1
        assert results[0].id == "789"
        assert results[0].name == "Test Artist"

    @pytest.mark.asyncio
    @patch("tidal_mcp.service.tidalapi")
    async def test_search_playlists_with_results(self, mock_tidalapi):
        """Test search_playlists with results."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        mock_session.search.return_value = {
            "playlists": [{"uuid": "playlist123", "title": "Test Playlist"}]
        }

        service = TidalService(mock_auth)
        results = await service.search_playlists("test playlist")

        assert len(results) == 1
        assert results[0].id == "playlist123"
        assert results[0].title == "Test Playlist"

    @pytest.mark.asyncio
    @patch("tidal_mcp.service.tidalapi")
    async def test_get_track_with_valid_id(self, mock_tidalapi):
        """Test get_track with valid ID."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        mock_track = Mock()
        mock_track.asdict.return_value = {
            "id": 123,
            "title": "Test Track",
            "artist": {"name": "Test Artist"},
        }
        mock_session.track.return_value = mock_track

        service = TidalService(mock_auth)
        result = await service.get_track("123")

        assert result.id == "123"
        assert result.title == "Test Track"

    @pytest.mark.asyncio
    @patch("tidal_mcp.service.tidalapi")
    async def test_get_track_not_found(self, mock_tidalapi):
        """Test get_track when track not found."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        mock_session.track.return_value = None

        service = TidalService(mock_auth)
        result = await service.get_track("nonexistent")

        assert result is None

    def test_service_string_representation(self):
        """Test service string representation."""
        mock_auth = Mock(spec=TidalAuth)
        service = TidalService(mock_auth)

        str_repr = str(service)
        repr_str = repr(service)

        assert "TidalService" in str_repr
        assert "TidalService" in repr_str

    @pytest.mark.asyncio
    @patch("tidal_mcp.service.tidalapi")
    async def test_search_comprehensive_basic(self, mock_tidalapi):
        """Test search_comprehensive with basic functionality."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        mock_session.search.return_value = {
            "tracks": [{"id": 1, "title": "Track 1"}],
            "albums": [{"id": 2, "title": "Album 1"}],
            "artists": [{"id": 3, "name": "Artist 1"}],
            "playlists": [{"uuid": "4", "title": "Playlist 1"}],
        }

        service = TidalService(mock_auth)
        results = await service.search_comprehensive("test query")

        assert len(results.tracks) == 1
        assert len(results.albums) == 1
        assert len(results.artists) == 1
        assert len(results.playlists) == 1

    @pytest.mark.asyncio
    @patch("tidal_mcp.service.tidalapi")
    async def test_get_album_tracks_basic(self, mock_tidalapi):
        """Test get_album_tracks basic functionality."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        mock_album = Mock()
        mock_track = Mock()
        mock_track.asdict.return_value = {"id": 1, "title": "Track 1"}
        mock_album.tracks.return_value = [mock_track]
        mock_session.album.return_value = mock_album

        service = TidalService(mock_auth)
        results = await service.get_album_tracks("123")

        assert len(results) == 1
        assert results[0].id == "1"

    @pytest.mark.asyncio
    @patch("tidal_mcp.service.tidalapi")
    async def test_get_album_tracks_album_not_found(self, mock_tidalapi):
        """Test get_album_tracks when album not found."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        mock_session.album.return_value = None

        service = TidalService(mock_auth)
        results = await service.get_album_tracks("nonexistent")

        assert results == []

    @pytest.mark.asyncio
    @patch("tidal_mcp.service.tidalapi")
    async def test_get_artist_albums_basic(self, mock_tidalapi):
        """Test get_artist_albums basic functionality."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        mock_artist = Mock()
        mock_album = Mock()
        mock_album.asdict.return_value = {"id": 1, "title": "Album 1"}
        mock_artist.get_albums.return_value = [mock_album]
        mock_session.artist.return_value = mock_artist

        service = TidalService(mock_auth)
        results = await service.get_artist_albums("123")

        assert len(results) == 1
        assert results[0].id == "1"

    @pytest.mark.asyncio
    @patch("tidal_mcp.service.tidalapi")
    async def test_get_artist_tracks_basic(self, mock_tidalapi):
        """Test get_artist_tracks basic functionality."""
        mock_auth = Mock(spec=TidalAuth)
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        mock_artist = Mock()
        mock_track = Mock()
        mock_track.asdict.return_value = {"id": 1, "title": "Track 1"}
        mock_artist.get_top_tracks.return_value = [mock_track]
        mock_session.artist.return_value = mock_artist

        service = TidalService(mock_auth)
        results = await service.get_artist_tracks("123")

        assert len(results) == 1
        assert results[0].id == "1"
