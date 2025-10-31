"""

Comprehensive tests for Tidal MCP Server

Tests FastMCP server functionality, tool implementations, authentication flow,
and error handling. Focuses on achieving high coverage for server operations.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tidal_mcp.auth import TidalAuthError
from src.tidal_mcp.models import Album, Artist, Playlist, SearchResults, Track
from src.tidal_mcp.server import (
    ensure_service,
    mcp,
    tidal_add_favorite,
    tidal_add_to_playlist,
    tidal_create_playlist,
    tidal_get_album,
    tidal_get_artist,
    tidal_get_favorites,
    tidal_get_playlist,
    tidal_get_recommendations,
    tidal_get_track,
    tidal_get_track_radio,
    tidal_get_user_playlists,
    tidal_login,
    tidal_remove_favorite,
    tidal_remove_from_playlist,
    tidal_search,
)


class TestServerInitialization:
    """Test server initialization and global state management."""

    def test_mcp_server_creation(self):
        """Test that FastMCP server is created with correct name."""
        assert mcp.name == "Tidal Music Integration"

    @patch.dict(
        os.environ,
        {"TIDAL_CLIENT_ID": "test_id", "TIDAL_CLIENT_SECRET": "test_secret"},
    )
    @patch("src.tidal_mcp.server.TidalAuth")
    @patch("src.tidal_mcp.server.TidalService")
    async def test_ensure_service_initialization(
        self, mock_service_class, mock_auth_class
    ):
        """Test ensure_service initializes auth and service correctly."""
        # Mock TidalAuth
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        # Mock TidalService
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Clear global state
        import src.tidal_mcp.server as server_module

        server_module.auth_manager = None
        server_module.tidal_service = None

        service = await ensure_service()

        # Verify initialization
        mock_auth_class.assert_called_once_with(
            client_id="test_id", client_secret="test_secret"
        )
        mock_service_class.assert_called_once_with(mock_auth)
        assert service == mock_service

    @patch("src.tidal_mcp.server.TidalAuth")
    async def test_ensure_service_not_authenticated_raises_error(self, mock_auth_class):
        """Test ensure_service raises error when not authenticated."""
        # Mock TidalAuth that's not authenticated
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = False
        mock_auth_class.return_value = mock_auth

        # Clear global state
        import src.tidal_mcp.server as server_module

        server_module.auth_manager = None
        server_module.tidal_service = None

        with pytest.raises(TidalAuthError, match="Not authenticated"):
            await ensure_service()

    @patch("src.tidal_mcp.server.TidalAuth")
    @patch("src.tidal_mcp.server.TidalService")
    async def test_ensure_service_reuses_existing_instances(
        self, mock_service_class, mock_auth_class
    ):
        """Test ensure_service reuses existing instances when available."""
        # Set up existing instances
        import src.tidal_mcp.server as server_module

        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_service = MagicMock()
        server_module.auth_manager = mock_auth
        server_module.tidal_service = mock_service

        service = await ensure_service()

        # Should not create new instances
        mock_auth_class.assert_not_called()
        mock_service_class.assert_not_called()
        assert service == mock_service


class TestLoginTool:
    """Test tidal_login tool functionality."""

    @patch("src.tidal_mcp.server.TidalAuth")
    @patch("src.tidal_mcp.server.TidalService")
    async def test_tidal_login_success(self, mock_service_class, mock_auth_class):
        """Test successful login."""
        # Mock successful authentication
        mock_auth = MagicMock()
        mock_auth.authenticate = AsyncMock(return_value=True)
        mock_auth.get_user_info.return_value = {
            "id": "123",
            "username": "testuser",
            "country_code": "US",
        }
        mock_auth_class.return_value = mock_auth

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Clear global state
        import src.tidal_mcp.server as server_module

        server_module.auth_manager = None
        server_module.tidal_service = None

        result = await tidal_login()

        assert result["success"] is True
        assert "Successfully authenticated" in result["message"]
        assert result["user"]["id"] == "123"

    @patch("src.tidal_mcp.server.TidalAuth")
    async def test_tidal_login_failure(self, mock_auth_class):
        """Test failed login."""
        # Mock failed authentication
        mock_auth = MagicMock()
        mock_auth.authenticate = AsyncMock(return_value=False)
        mock_auth_class.return_value = mock_auth

        # Clear global state
        import src.tidal_mcp.server as server_module

        server_module.auth_manager = None
        server_module.tidal_service = None

        result = await tidal_login()

        assert result["success"] is False
        assert "Authentication failed" in result["message"]
        assert result["user"] is None

    @patch("src.tidal_mcp.server.TidalAuth")
    async def test_tidal_login_exception(self, mock_auth_class):
        """Test login with exception."""
        # Mock authentication that raises exception
        mock_auth_class.side_effect = Exception("Connection error")

        # Clear global state
        import src.tidal_mcp.server as server_module

        server_module.auth_manager = None
        server_module.tidal_service = None

        result = await tidal_login()

        assert result["success"] is False
        assert "Authentication error" in result["message"]
        assert result["user"] is None


class TestSearchTool:
    """Test tidal_search tool functionality."""

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_search_tracks(self, mock_ensure_service):
        """Test searching for tracks."""
        # Mock service
        mock_service = MagicMock()
        mock_tracks = [
            Track(id="123", title="Test Track 1"),
            Track(id="124", title="Test Track 2"),
        ]
        mock_service.search_tracks = AsyncMock(return_value=mock_tracks)
        mock_ensure_service.return_value = mock_service

        result = await tidal_search("test query", "tracks", 10, 0)

        assert result["query"] == "test query"
        assert result["content_type"] == "tracks"
        assert len(result["results"]["tracks"]) == 2
        assert result["total_results"] == 2
        mock_service.search_tracks.assert_called_once_with("test query", 10, 0)

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_search_albums(self, mock_ensure_service):
        """Test searching for albums."""
        mock_service = MagicMock()
        mock_albums = [Album(id="456", title="Test Album")]
        mock_service.search_albums = AsyncMock(return_value=mock_albums)
        mock_ensure_service.return_value = mock_service

        result = await tidal_search("test query", "albums", 5, 10)

        assert result["content_type"] == "albums"
        assert len(result["results"]["albums"]) == 1
        mock_service.search_albums.assert_called_once_with("test query", 5, 10)

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_search_artists(self, mock_ensure_service):
        """Test searching for artists."""
        mock_service = MagicMock()
        mock_artists = [Artist(id="789", name="Test Artist")]
        mock_service.search_artists = AsyncMock(return_value=mock_artists)
        mock_ensure_service.return_value = mock_service

        result = await tidal_search("test query", "artists")

        assert result["content_type"] == "artists"
        assert len(result["results"]["artists"]) == 1
        mock_service.search_artists.assert_called_once_with("test query", 20, 0)

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_search_playlists(self, mock_ensure_service):
        """Test searching for playlists."""
        mock_service = MagicMock()
        mock_playlists = [Playlist(id="abc", title="Test Playlist")]
        mock_service.search_playlists = AsyncMock(return_value=mock_playlists)
        mock_ensure_service.return_value = mock_service

        result = await tidal_search("test query", "playlists")

        assert result["content_type"] == "playlists"
        assert len(result["results"]["playlists"]) == 1

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_search_all(self, mock_ensure_service):
        """Test searching all content types."""
        mock_service = MagicMock()
        mock_search_results = SearchResults(
            tracks=[Track(id="123", title="Test Track")],
            albums=[Album(id="456", title="Test Album")],
            artists=[Artist(id="789", name="Test Artist")],
            playlists=[Playlist(id="abc", title="Test Playlist")],
        )
        mock_service.search_all = AsyncMock(return_value=mock_search_results)
        mock_ensure_service.return_value = mock_service

        result = await tidal_search("test query", "all", 15)

        assert result["content_type"] == "all"
        assert result["total_results"] == 4
        mock_service.search_all.assert_called_once_with("test query", 15)

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_search_limit_clamping(self, mock_ensure_service):
        """Test search limit is clamped to valid range."""
        mock_service = MagicMock()
        mock_service.search_tracks = AsyncMock(return_value=[])
        mock_ensure_service.return_value = mock_service

        # Test limit too high
        await tidal_search("test", "tracks", 100, 0)
        mock_service.search_tracks.assert_called_with("test", 50, 0)

        # Test limit too low
        await tidal_search("test", "tracks", 0, 0)
        mock_service.search_tracks.assert_called_with("test", 1, 0)

        # Test negative offset
        await tidal_search("test", "tracks", 20, -10)
        mock_service.search_tracks.assert_called_with("test", 20, 0)

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_search_auth_error(self, mock_ensure_service):
        """Test search with authentication error."""
        mock_ensure_service.side_effect = TidalAuthError("Not authenticated")

        result = await tidal_search("test query", "tracks")

        assert "error" in result
        assert "Authentication required" in result["error"]

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_search_general_error(self, mock_ensure_service):
        """Test search with general error."""
        mock_ensure_service.side_effect = Exception("API error")

        result = await tidal_search("test query", "tracks")

        assert "error" in result
        assert "Search failed" in result["error"]


class TestPlaylistTools:
    """Test playlist-related tools."""

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_get_playlist_success(self, mock_ensure_service):
        """Test getting playlist successfully."""
        mock_service = MagicMock()
        mock_playlist = Playlist(id="abc-123", title="Test Playlist")
        mock_service.get_playlist = AsyncMock(return_value=mock_playlist)
        mock_ensure_service.return_value = mock_service

        result = await tidal_get_playlist("abc-123", True)

        assert result["success"] is True
        assert result["playlist"]["title"] == "Test Playlist"
        mock_service.get_playlist.assert_called_once_with("abc-123", True)

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_get_playlist_not_found(self, mock_ensure_service):
        """Test getting non-existent playlist."""
        mock_service = MagicMock()
        mock_service.get_playlist = AsyncMock(return_value=None)
        mock_ensure_service.return_value = mock_service

        result = await tidal_get_playlist("nonexistent")

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_create_playlist_success(self, mock_ensure_service):
        """Test creating playlist successfully."""
        mock_service = MagicMock()
        mock_playlist = Playlist(id="new-123", title="New Playlist")
        mock_service.create_playlist = AsyncMock(return_value=mock_playlist)
        mock_ensure_service.return_value = mock_service

        result = await tidal_create_playlist("New Playlist", "Description")

        assert result["success"] is True
        assert "Created playlist" in result["message"]
        assert result["playlist"]["title"] == "New Playlist"
        mock_service.create_playlist.assert_called_once_with(
            "New Playlist", "Description"
        )

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_create_playlist_failure(self, mock_ensure_service):
        """Test creating playlist failure."""
        mock_service = MagicMock()
        mock_service.create_playlist = AsyncMock(return_value=None)
        mock_ensure_service.return_value = mock_service

        result = await tidal_create_playlist("Failed Playlist")

        assert result["success"] is False
        assert "Failed to create" in result["error"]

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_add_to_playlist_success(self, mock_ensure_service):
        """Test adding tracks to playlist successfully."""
        mock_service = MagicMock()
        mock_service.add_tracks_to_playlist = AsyncMock(return_value=True)
        mock_ensure_service.return_value = mock_service

        track_ids = ["123", "124", "125"]
        result = await tidal_add_to_playlist("playlist-123", track_ids)

        assert result["success"] is True
        assert "Added 3 tracks" in result["message"]
        mock_service.add_tracks_to_playlist.assert_called_once_with(
            "playlist-123", track_ids
        )

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_add_to_playlist_no_tracks(self, mock_ensure_service):
        """Test adding empty track list to playlist."""
        mock_ensure_service.return_value = MagicMock()

        result = await tidal_add_to_playlist("playlist-123", [])

        assert result["success"] is False
        assert "No track IDs provided" in result["error"]

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_remove_from_playlist_success(self, mock_ensure_service):
        """Test removing tracks from playlist successfully."""
        mock_service = MagicMock()
        mock_service.remove_tracks_from_playlist = AsyncMock(return_value=True)
        mock_ensure_service.return_value = mock_service

        track_indices = [0, 2, 5]
        result = await tidal_remove_from_playlist("playlist-123", track_indices)

        assert result["success"] is True
        assert "Removed 3 tracks" in result["message"]
        mock_service.remove_tracks_from_playlist.assert_called_once_with(
            "playlist-123", track_indices
        )

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_remove_from_playlist_no_indices(self, mock_ensure_service):
        """Test removing with empty indices list."""
        mock_ensure_service.return_value = MagicMock()

        result = await tidal_remove_from_playlist("playlist-123", [])

        assert result["success"] is False
        assert "No track indices provided" in result["error"]

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_get_user_playlists(self, mock_ensure_service):
        """Test getting user playlists."""
        mock_service = MagicMock()
        mock_playlists = [
            Playlist(id="pl1", title="Playlist 1"),
            Playlist(id="pl2", title="Playlist 2"),
        ]
        mock_service.get_user_playlists = AsyncMock(return_value=mock_playlists)
        mock_ensure_service.return_value = mock_service

        result = await tidal_get_user_playlists(30, 10)

        assert len(result["playlists"]) == 2
        assert result["total_results"] == 2
        mock_service.get_user_playlists.assert_called_once_with(30, 10)


class TestFavoritesTools:
    """Test favorites-related tools."""

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_get_favorites_tracks(self, mock_ensure_service):
        """Test getting favorite tracks."""
        mock_service = MagicMock()
        mock_tracks = [Track(id="123", title="Favorite Track")]
        mock_service.get_user_favorites = AsyncMock(return_value=mock_tracks)
        mock_ensure_service.return_value = mock_service

        result = await tidal_get_favorites("tracks", 25, 5)

        assert result["content_type"] == "tracks"
        assert len(result["favorites"]) == 1
        assert result["total_results"] == 1
        mock_service.get_user_favorites.assert_called_once_with("tracks", 25, 5)

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_get_favorites_limit_clamping(self, mock_ensure_service):
        """Test favorites limit is clamped to valid range."""
        mock_service = MagicMock()
        mock_service.get_user_favorites = AsyncMock(return_value=[])
        mock_ensure_service.return_value = mock_service

        # Test limit too high
        await tidal_get_favorites("tracks", 200, 0)
        mock_service.get_user_favorites.assert_called_with("tracks", 100, 0)

        # Test limit too low
        await tidal_get_favorites("tracks", 0, 0)
        mock_service.get_user_favorites.assert_called_with("tracks", 1, 0)

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_add_favorite_success(self, mock_ensure_service):
        """Test adding item to favorites successfully."""
        mock_service = MagicMock()
        mock_service.add_to_favorites = AsyncMock(return_value=True)
        mock_ensure_service.return_value = mock_service

        result = await tidal_add_favorite("123", "track")

        assert result["success"] is True
        assert "Added track 123 to favorites" in result["message"]
        mock_service.add_to_favorites.assert_called_once_with("123", "track")

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_add_favorite_failure(self, mock_ensure_service):
        """Test adding item to favorites failure."""
        mock_service = MagicMock()
        mock_service.add_to_favorites = AsyncMock(return_value=False)
        mock_ensure_service.return_value = mock_service

        result = await tidal_add_favorite("123", "track")

        assert result["success"] is False
        assert "Failed to add" in result["error"]

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_remove_favorite_success(self, mock_ensure_service):
        """Test removing item from favorites successfully."""
        mock_service = MagicMock()
        mock_service.remove_from_favorites = AsyncMock(return_value=True)
        mock_ensure_service.return_value = mock_service

        result = await tidal_remove_favorite("123", "album")

        assert result["success"] is True
        assert "Removed album 123 from favorites" in result["message"]
        mock_service.remove_from_favorites.assert_called_once_with("123", "album")


class TestRecommendationTools:
    """Test recommendation-related tools."""

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_get_recommendations(self, mock_ensure_service):
        """Test getting recommendations."""
        mock_service = MagicMock()
        mock_tracks = [Track(id="123", title="Recommended Track")]
        mock_service.get_recommended_tracks = AsyncMock(return_value=mock_tracks)
        mock_ensure_service.return_value = mock_service

        result = await tidal_get_recommendations(30)

        assert len(result["recommendations"]) == 1
        assert result["total_results"] == 1
        mock_service.get_recommended_tracks.assert_called_once_with(30)

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_get_recommendations_limit_clamping(self, mock_ensure_service):
        """Test recommendations limit clamping."""
        mock_service = MagicMock()
        mock_service.get_recommended_tracks = AsyncMock(return_value=[])
        mock_ensure_service.return_value = mock_service

        # Test limit too high
        await tidal_get_recommendations(150)
        mock_service.get_recommended_tracks.assert_called_with(100)

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_get_track_radio(self, mock_ensure_service):
        """Test getting track radio."""
        mock_service = MagicMock()
        mock_tracks = [Track(id="124", title="Radio Track")]
        mock_service.get_track_radio = AsyncMock(return_value=mock_tracks)
        mock_ensure_service.return_value = mock_service

        result = await tidal_get_track_radio("123", 40)

        assert result["seed_track_id"] == "123"
        assert len(result["radio_tracks"]) == 1
        assert result["total_results"] == 1
        mock_service.get_track_radio.assert_called_once_with("123", 40)


class TestContentDetailTools:
    """Test content detail retrieval tools."""

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_get_track_success(self, mock_ensure_service):
        """Test getting track details successfully."""
        mock_service = MagicMock()
        mock_track = Track(id="123", title="Test Track")
        mock_service.get_track = AsyncMock(return_value=mock_track)
        mock_ensure_service.return_value = mock_service

        result = await tidal_get_track("123")

        assert result["success"] is True
        assert result["track"]["title"] == "Test Track"
        mock_service.get_track.assert_called_once_with("123")

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_get_track_not_found(self, mock_ensure_service):
        """Test getting non-existent track."""
        mock_service = MagicMock()
        mock_service.get_track = AsyncMock(return_value=None)
        mock_ensure_service.return_value = mock_service

        result = await tidal_get_track("nonexistent")

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_get_album_success(self, mock_ensure_service):
        """Test getting album details successfully."""
        mock_service = MagicMock()
        mock_album = Album(id="456", title="Test Album")
        mock_service.get_album = AsyncMock(return_value=mock_album)
        mock_ensure_service.return_value = mock_service

        result = await tidal_get_album("456", False)

        assert result["success"] is True
        assert result["album"]["title"] == "Test Album"
        mock_service.get_album.assert_called_once_with("456", False)

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_get_album_with_tracks(self, mock_ensure_service):
        """Test getting album with tracks."""
        mock_service = MagicMock()
        mock_album = Album(id="456", title="Test Album")
        mock_service.get_album = AsyncMock(return_value=mock_album)
        mock_ensure_service.return_value = mock_service

        _ = await tidal_get_album("456")  # Default include_tracks=True

        mock_service.get_album.assert_called_once_with("456", True)

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tidal_get_artist_success(self, mock_ensure_service):
        """Test getting artist details successfully."""
        mock_service = MagicMock()
        mock_artist = Artist(id="789", name="Test Artist")
        mock_service.get_artist = AsyncMock(return_value=mock_artist)
        mock_ensure_service.return_value = mock_service

        result = await tidal_get_artist("789")

        assert result["success"] is True
        assert result["artist"]["name"] == "Test Artist"
        mock_service.get_artist.assert_called_once_with("789")


class TestErrorHandling:
    """Test error handling across all tools."""

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tools_handle_auth_errors(self, mock_ensure_service):
        """Test that tools properly handle authentication errors."""
        mock_ensure_service.side_effect = TidalAuthError("Authentication required")

        tools_to_test = [
            (tidal_search, ("query", "tracks")),
            (tidal_get_playlist, ("playlist-id",)),
            (tidal_create_playlist, ("title",)),
            (tidal_add_to_playlist, ("playlist-id", ["track-id"])),
            (tidal_remove_from_playlist, ("playlist-id", [0])),
            (tidal_get_favorites, ("tracks",)),
            (tidal_add_favorite, ("item-id", "track")),
            (tidal_remove_favorite, ("item-id", "track")),
            (tidal_get_recommendations, ()),
            (tidal_get_track_radio, ("track-id",)),
            (tidal_get_user_playlists, ()),
            (tidal_get_track, ("track-id",)),
            (tidal_get_album, ("album-id",)),
            (tidal_get_artist, ("artist-id",)),
        ]

        for tool_func, args in tools_to_test:
            result = await tool_func(*args)
            assert "error" in result
            assert "Authentication required" in result["error"]

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_tools_handle_general_errors(self, mock_ensure_service):
        """Test that tools properly handle general exceptions."""
        mock_ensure_service.side_effect = Exception("General error")

        # Test a few representative tools
        result = await tidal_search("query", "tracks")
        assert "error" in result
        assert "Search failed" in result["error"]

        result = await tidal_get_playlist("playlist-id")
        assert "error" in result
        assert "Failed to get playlist" in result["error"]

        result = await tidal_create_playlist("title")
        assert "error" in result
        assert "Failed to create playlist" in result["error"]


class TestServerMain:
    """Test server main function and entry point."""

    @patch("src.tidal_mcp.server.mcp.run")
    @patch("src.tidal_mcp.server.logging.basicConfig")
    def test_main_function(self, mock_logging_config, mock_mcp_run):
        """Test main function sets up logging and runs server."""
        from src.tidal_mcp.server import main

        main()

        # Verify logging is configured
        mock_logging_config.assert_called_once()
        call_args = mock_logging_config.call_args[1]
        assert call_args["level"] == 10  # logging.INFO
        assert "%(asctime)s" in call_args["format"]

        # Verify server runs without banner
        mock_mcp_run.assert_called_once_with(show_banner=False)

    def test_server_name_is_set(self):
        """Test that server has the correct name."""
        assert hasattr(mcp, "name")
        assert mcp.name == "Tidal Music Integration"


class TestToolParameterValidation:
    """Test tool parameter validation and edge cases."""

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_search_with_edge_case_parameters(self, mock_ensure_service):
        """Test search tool with edge case parameters."""
        mock_service = MagicMock()
        mock_service.search_tracks = AsyncMock(return_value=[])
        mock_ensure_service.return_value = mock_service

        # Test with very large limit
        result = await tidal_search("query", "tracks", 1000, 0)
        # Should be clamped to 50
        mock_service.search_tracks.assert_called_with("query", 50, 0)

        # Test with negative limit
        result = await tidal_search("query", "tracks", -5, 0)
        # Should be clamped to 1
        mock_service.search_tracks.assert_called_with("query", 1, 0)

        # Test with negative offset
        _ = await tidal_search("query", "tracks", 20, -10)
        # Should be clamped to 0
        mock_service.search_tracks.assert_called_with("query", 20, 0)

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_favorites_with_edge_case_parameters(self, mock_ensure_service):
        """Test favorites tool with edge case parameters."""
        mock_service = MagicMock()
        mock_service.get_user_favorites = AsyncMock(return_value=[])
        mock_ensure_service.return_value = mock_service

        # Test with very large limit
        await tidal_get_favorites("tracks", 200, 0)
        # Should be clamped to 100
        mock_service.get_user_favorites.assert_called_with("tracks", 100, 0)

        # Test with zero limit
        await tidal_get_favorites("tracks", 0, 0)
        # Should be clamped to 1
        mock_service.get_user_favorites.assert_called_with("tracks", 1, 0)

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_recommendations_with_edge_case_parameters(self, mock_ensure_service):
        """Test recommendations tool with edge case parameters."""
        mock_service = MagicMock()
        mock_service.get_recommended_tracks = AsyncMock(return_value=[])
        mock_service.get_track_radio = AsyncMock(return_value=[])
        mock_ensure_service.return_value = mock_service

        # Test recommendations with large limit
        await tidal_get_recommendations(150)
        mock_service.get_recommended_tracks.assert_called_with(100)

        # Test track radio with large limit
        await tidal_get_track_radio("123", 150)
        mock_service.get_track_radio.assert_called_with("123", 100)

        # Test with zero limit
        await tidal_get_recommendations(0)
        mock_service.get_recommended_tracks.assert_called_with(1)

    @patch("src.tidal_mcp.server.ensure_service")
    async def test_user_playlists_with_edge_case_parameters(self, mock_ensure_service):
        """Test user playlists tool with edge case parameters."""
        mock_service = MagicMock()
        mock_service.get_user_playlists = AsyncMock(return_value=[])
        mock_ensure_service.return_value = mock_service

        # Test with large limit
        await tidal_get_user_playlists(150, 0)
        mock_service.get_user_playlists.assert_called_with(100, 0)

        # Test with negative offset
        await tidal_get_user_playlists(50, -10)
        mock_service.get_user_playlists.assert_called_with(50, 0)
