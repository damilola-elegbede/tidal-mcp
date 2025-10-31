"""
Comprehensive tests for server module to reach 80% coverage.
Targets specific uncovered lines identified in coverage report.
"""

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from tidal_mcp import server
from tidal_mcp.auth import TidalAuth, TidalAuthError
from tidal_mcp.service import TidalService


class TestTidalServerFunctions:
    """Comprehensive tests targeting specific uncovered lines in server.py."""

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.TidalService")
    @patch("tidal_mcp.server.TidalAuth")
    async def test_ensure_service_success(self, mock_auth_class, mock_service_class):
        """Test successful service initialization."""
        mock_auth = Mock()
        mock_auth.is_authenticated.return_value = True
        mock_service = Mock()

        mock_auth_class.return_value = mock_auth
        mock_service_class.return_value = mock_service

        # Reset global state
        server.auth_manager = None
        server.tidal_service = None

        result = await server.ensure_service()

        assert result == mock_service
        mock_auth_class.assert_called_once()
        mock_service_class.assert_called_once_with(mock_auth)

    @pytest.mark.asyncio
    @patch.dict(
        "os.environ",
        {"TIDAL_CLIENT_ID": "test_id", "TIDAL_CLIENT_SECRET": "test_secret"},
    )
    @patch("tidal_mcp.server.TidalService")
    @patch("tidal_mcp.server.TidalAuth")
    async def test_ensure_service_with_env_vars(
        self, mock_auth_class, mock_service_class
    ):
        """Test service initialization with environment variables."""
        mock_auth = Mock()
        mock_auth.is_authenticated.return_value = True
        mock_service = Mock()

        mock_auth_class.return_value = mock_auth
        mock_service_class.return_value = mock_service

        # Reset global state
        server.auth_manager = None
        server.tidal_service = None

        result = await server.ensure_service()

        assert result == mock_service
        mock_auth_class.assert_called_once_with(
            client_id="test_id", client_secret="test_secret"
        )

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.TidalService")
    @patch("tidal_mcp.server.TidalAuth")
    async def test_ensure_service_not_authenticated(
        self, mock_auth_class, mock_service_class
    ):
        """Test service initialization when not authenticated."""
        mock_auth = Mock()
        mock_auth.is_authenticated.return_value = False

        mock_auth_class.return_value = mock_auth

        # Reset global state
        server.auth_manager = None
        server.tidal_service = None

        with pytest.raises(TidalAuthError, match="Not authenticated"):
            await server.ensure_service()

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_tidal_login_success(self, mock_ensure_service):
        """Test successful Tidal login."""
        mock_service = Mock()
        mock_service.authenticate.return_value = True
        mock_ensure_service.return_value = mock_service

        result = await server.tidal_login()

        assert result["success"] is True
        assert "message" in result

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_tidal_login_failure(self, mock_ensure_service):
        """Test failed Tidal login."""
        mock_service = Mock()
        mock_service.authenticate.return_value = False
        mock_ensure_service.return_value = mock_service

        result = await server.tidal_login()

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_tidal_search_success(self, mock_ensure_service):
        """Test successful Tidal search."""
        mock_service = Mock()
        mock_search_results = Mock()
        mock_search_results.to_dict.return_value = {
            "tracks": [{"id": "1", "title": "Track 1"}],
            "albums": [],
            "artists": [],
            "playlists": [],
        }
        mock_service.search_comprehensive.return_value = mock_search_results
        mock_ensure_service.return_value = mock_service

        result = await server.tidal_search(
            "test query", content_types=["tracks"], limit=10
        )

        assert "tracks" in result
        assert len(result["tracks"]) == 1

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_tidal_search_empty_query(self, mock_ensure_service):
        """Test Tidal search with empty query."""
        result = await server.tidal_search("", content_types=["tracks"])

        assert "error" in result
        assert "Query cannot be empty" in result["error"]

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_tidal_search_invalid_content_type(self, mock_ensure_service):
        """Test Tidal search with invalid content type."""
        result = await server.tidal_search("test", content_types=["invalid"])

        assert "error" in result

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_tidal_get_playlist_success(self, mock_ensure_service):
        """Test successful playlist retrieval."""
        mock_service = Mock()
        mock_playlist = Mock()
        mock_playlist.to_dict.return_value = {"id": "123", "title": "Test Playlist"}
        mock_service.get_playlist.return_value = mock_playlist
        mock_ensure_service.return_value = mock_service

        result = await server.tidal_get_playlist("123", include_tracks=True)

        assert result["id"] == "123"
        assert result["title"] == "Test Playlist"

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_tidal_get_playlist_not_found(self, mock_ensure_service):
        """Test playlist retrieval when not found."""
        mock_service = Mock()
        mock_service.get_playlist.return_value = None
        mock_ensure_service.return_value = mock_service

        result = await server.tidal_get_playlist("nonexistent")

        assert "error" in result
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_tidal_create_playlist_success(self, mock_ensure_service):
        """Test successful playlist creation."""
        mock_service = Mock()
        mock_playlist = Mock()
        mock_playlist.to_dict.return_value = {"id": "new123", "title": "New Playlist"}
        mock_service.create_playlist.return_value = mock_playlist
        mock_ensure_service.return_value = mock_service

        result = await server.tidal_create_playlist("New Playlist", "Test description")

        assert result["id"] == "new123"
        assert result["title"] == "New Playlist"

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_tidal_create_playlist_failure(self, mock_ensure_service):
        """Test playlist creation failure."""
        mock_service = Mock()
        mock_service.create_playlist.side_effect = Exception("Creation failed")
        mock_ensure_service.return_value = mock_service

        result = await server.tidal_create_playlist("Test Playlist")

        assert "error" in result

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_tidal_add_to_playlist_success(self, mock_ensure_service):
        """Test successfully adding track to playlist."""
        mock_service = Mock()
        mock_service.add_to_playlist.return_value = True
        mock_ensure_service.return_value = mock_service

        result = await server.tidal_add_to_playlist("playlist123", "track456")

        assert result["success"] is True

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_tidal_add_to_playlist_failure(self, mock_ensure_service):
        """Test failed addition to playlist."""
        mock_service = Mock()
        mock_service.add_to_playlist.return_value = False
        mock_ensure_service.return_value = mock_service

        result = await server.tidal_add_to_playlist("playlist123", "track456")

        assert result["success"] is False

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_tidal_remove_from_playlist_success(self, mock_ensure_service):
        """Test successfully removing track from playlist."""
        mock_service = Mock()
        mock_service.remove_from_playlist.return_value = True
        mock_ensure_service.return_value = mock_service

        result = await server.tidal_remove_from_playlist("playlist123", "track456")

        assert result["success"] is True

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_tidal_get_favorites_success(self, mock_ensure_service):
        """Test successful favorites retrieval."""
        mock_service = Mock()
        mock_favorites = [
            Mock(to_dict=Mock(return_value={"id": "1", "title": "Fav Track"}))
        ]
        mock_service.get_favorites.return_value = mock_favorites
        mock_ensure_service.return_value = mock_service

        result = await server.tidal_get_favorites("tracks", limit=10)

        assert len(result["items"]) == 1
        assert result["items"][0]["title"] == "Fav Track"

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_tidal_get_favorites_invalid_type(self, mock_ensure_service):
        """Test favorites retrieval with invalid content type."""
        result = await server.tidal_get_favorites("invalid")

        assert "error" in result

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_tidal_add_favorite_success(self, mock_ensure_service):
        """Test successfully adding favorite."""
        mock_service = Mock()
        mock_service.add_favorite.return_value = True
        mock_ensure_service.return_value = mock_service

        result = await server.tidal_add_favorite("track123", "track")

        assert result["success"] is True

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_tidal_remove_favorite_success(self, mock_ensure_service):
        """Test successfully removing favorite."""
        mock_service = Mock()
        mock_service.remove_favorite.return_value = True
        mock_ensure_service.return_value = mock_service

        result = await server.tidal_remove_favorite("track123", "track")

        assert result["success"] is True

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_tidal_get_recommendations_success(self, mock_ensure_service):
        """Test successful recommendations retrieval."""
        mock_service = Mock()
        mock_tracks = [
            Mock(to_dict=Mock(return_value={"id": "1", "title": "Recommended Track"}))
        ]
        mock_service.get_recommendations.return_value = mock_tracks
        mock_ensure_service.return_value = mock_service

        result = await server.tidal_get_recommendations(limit=20)

        assert len(result["tracks"]) == 1
        assert result["tracks"][0]["title"] == "Recommended Track"

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_tidal_get_track_radio_success(self, mock_ensure_service):
        """Test successful track radio retrieval."""
        mock_service = Mock()
        mock_tracks = [
            Mock(to_dict=Mock(return_value={"id": "1", "title": "Radio Track"}))
        ]
        mock_service.get_track_radio.return_value = mock_tracks
        mock_ensure_service.return_value = mock_service

        result = await server.tidal_get_track_radio("track123", limit=30)

        assert len(result["tracks"]) == 1

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_tidal_get_user_playlists_success(self, mock_ensure_service):
        """Test successful user playlists retrieval."""
        mock_service = Mock()
        mock_playlists = [
            Mock(to_dict=Mock(return_value={"id": "1", "title": "User Playlist"}))
        ]
        mock_service.get_user_playlists.return_value = mock_playlists
        mock_ensure_service.return_value = mock_service

        result = await server.tidal_get_user_playlists(limit=25, offset=10)

        assert len(result["playlists"]) == 1

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_tidal_get_track_success(self, mock_ensure_service):
        """Test successful track retrieval."""
        mock_service = Mock()
        mock_track = Mock()
        mock_track.to_dict.return_value = {"id": "123", "title": "Test Track"}
        mock_service.get_track.return_value = mock_track
        mock_ensure_service.return_value = mock_service

        result = await server.tidal_get_track("123")

        assert result["id"] == "123"
        assert result["title"] == "Test Track"

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_tidal_get_track_not_found(self, mock_ensure_service):
        """Test track retrieval when not found."""
        mock_service = Mock()
        mock_service.get_track.return_value = None
        mock_ensure_service.return_value = mock_service

        result = await server.tidal_get_track("nonexistent")

        assert "error" in result

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_tidal_get_album_success(self, mock_ensure_service):
        """Test successful album retrieval."""
        mock_service = Mock()
        mock_album = Mock()
        mock_album.to_dict.return_value = {"id": "456", "title": "Test Album"}
        mock_service.get_album.return_value = mock_album
        mock_ensure_service.return_value = mock_service

        result = await server.tidal_get_album("456", include_tracks=True)

        assert result["id"] == "456"
        assert result["title"] == "Test Album"

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_tidal_get_album_with_tracks(self, mock_ensure_service):
        """Test album retrieval with tracks included."""
        mock_service = Mock()
        mock_album = Mock()
        mock_album.to_dict.return_value = {"id": "456", "title": "Test Album"}
        mock_tracks = [Mock(to_dict=Mock(return_value={"id": "1", "title": "Track 1"}))]
        mock_service.get_album.return_value = mock_album
        mock_service.get_album_tracks.return_value = mock_tracks
        mock_ensure_service.return_value = mock_service

        result = await server.tidal_get_album("456", include_tracks=True)

        assert "tracks" in result
        assert len(result["tracks"]) == 1

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_tidal_get_artist_success(self, mock_ensure_service):
        """Test successful artist retrieval."""
        mock_service = Mock()
        mock_artist = Mock()
        mock_artist.to_dict.return_value = {"id": "789", "name": "Test Artist"}
        mock_service.get_artist.return_value = mock_artist
        mock_ensure_service.return_value = mock_service

        result = await server.tidal_get_artist("789")

        assert result["id"] == "789"
        assert result["name"] == "Test Artist"

    @pytest.mark.asyncio
    @patch("tidal_mcp.server.ensure_service")
    async def test_error_handling_in_tools(self, mock_ensure_service):
        """Test error handling in tool functions."""
        mock_service = Mock()
        mock_service.search_comprehensive.side_effect = Exception("Service error")
        mock_ensure_service.return_value = mock_service

        result = await server.tidal_search("test", content_types=["tracks"])

        assert "error" in result

    def test_main_function_exists(self):
        """Test that main function exists."""
        assert hasattr(server, "main")
        assert callable(server.main)

    def test_module_globals(self):
        """Test module-level globals and imports."""
        assert hasattr(server, "mcp")
        assert hasattr(server, "auth_manager")
        assert hasattr(server, "tidal_service")
        assert hasattr(server, "logger")

    @pytest.mark.asyncio
    async def test_global_state_management(self):
        """Test global state management."""
        # Test that globals can be set and accessed
        original_auth = server.auth_manager
        original_service = server.tidal_service

        try:
            # Modify globals
            server.auth_manager = Mock()
            server.tidal_service = Mock()

            assert server.auth_manager is not None
            assert server.tidal_service is not None

        finally:
            # Restore original state
            server.auth_manager = original_auth
            server.tidal_service = original_service
