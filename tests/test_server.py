"""
Comprehensive tests for server.py MCP tools.

Tests all MCP tool implementations in server.py to achieve 40%+ coverage.
Focuses on tool registration, parameter validation, error handling, and response structure.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

# Always import the real server module for testing
from src.tidal_mcp import server
from src.tidal_mcp.auth import TidalAuthError
from src.tidal_mcp.models import SearchResults


class TestMCPToolRegistration:
    """Test that all MCP tools are properly registered."""

    def test_mcp_tools_registered(self):
        """Test that all expected tools are registered with FastMCP."""
        # Expected tools based on server.py analysis
        expected_tools = [
            "tidal_login",
            "tidal_search",
            "tidal_get_playlist",
            "tidal_create_playlist",
            "tidal_add_to_playlist",
            "tidal_remove_from_playlist",
            "tidal_get_favorites",
            "tidal_add_favorite",
            "tidal_remove_favorite",
            "tidal_get_recommendations",
            "tidal_get_track_radio",
            "tidal_get_user_playlists",
            "tidal_get_track",
            "tidal_get_album",
            "tidal_get_artist"
        ]

        # Check that tools exist as function objects
        for tool_name in expected_tools:
            tool = getattr(server, tool_name, None)
            assert tool is not None, f"Tool {tool_name} not found"
            # In testing mode, tools are mock objects created by @mcp.tool() decorator
            # Just verify they exist and are callable
            assert callable(tool), f"Tool {tool_name} is not callable"

    def test_mcp_server_name(self):
        """Test MCP server has correct name."""
        # In testing mode, mcp is a Mock object, so check if it has name attribute set
        if hasattr(server.mcp, 'name'):
            assert server.mcp.name == "Tidal Music Integration"
        else:
            # If it's a real FastMCP instance (shouldn't happen in testing)
            assert hasattr(server.mcp, 'name')

    def test_tool_count(self):
        """Test that we have the expected number of tools."""
        # Count tools decorated with @mcp.tool()
        tool_count = 0
        expected_tools = [
            "tidal_login", "tidal_search", "tidal_get_playlist", "tidal_create_playlist",
            "tidal_add_to_playlist", "tidal_remove_from_playlist", "tidal_get_favorites",
            "tidal_add_favorite", "tidal_remove_favorite", "tidal_get_recommendations",
            "tidal_get_track_radio", "tidal_get_user_playlists", "tidal_get_track",
            "tidal_get_album", "tidal_get_artist"
        ]

        for tool_name in expected_tools:
            if hasattr(server, tool_name):
                tool_count += 1

        assert tool_count == 15, f"Expected 15 tools, found {tool_count}"


class TestEnsureService:
    """Test the ensure_service helper function."""

    @pytest.mark.asyncio
    async def test_ensure_service_creates_instances(self, mock_env_vars):
        """Test ensure_service creates auth and service instances."""
        # Reset global instances
        server.auth_manager = None
        server.tidal_service = None

        with patch('src.tidal_mcp.server.TidalAuth') as mock_auth_class, \
             patch('src.tidal_mcp.server.TidalService') as mock_service_class:

            mock_auth = Mock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_class.return_value = mock_auth

            mock_service = Mock()
            mock_service_class.return_value = mock_service

            result = await server.ensure_service()

            assert result == mock_service
            assert server.auth_manager == mock_auth
            assert server.tidal_service == mock_service

    @pytest.mark.asyncio
    async def test_ensure_service_reuses_instances(self, mock_env_vars):
        """Test ensure_service reuses existing instances."""
        mock_auth = Mock()
        mock_auth.is_authenticated.return_value = True
        mock_service = Mock()

        server.auth_manager = mock_auth
        server.tidal_service = mock_service

        result = await server.ensure_service()

        assert result == mock_service

    @pytest.mark.asyncio
    async def test_ensure_service_not_authenticated(self, mock_env_vars):
        """Test ensure_service raises error when not authenticated."""
        server.auth_manager = None
        server.tidal_service = None

        with patch('src.tidal_mcp.server.TidalAuth') as mock_auth_class:
            mock_auth = Mock()
            mock_auth.is_authenticated.return_value = False
            mock_auth_class.return_value = mock_auth

            with pytest.raises(TidalAuthError, match="Not authenticated"):
                await server.ensure_service()


class TestTidalLogin:
    """Test tidal_login MCP tool."""

    @pytest.mark.asyncio
    async def test_tidal_login_success(self):
        """Test successful Tidal login."""
        with patch('src.tidal_mcp.server.TidalAuth') as mock_auth_class:
            mock_auth = Mock()
            mock_auth.authenticate = AsyncMock(return_value=True)
            mock_auth.get_user_info = Mock(return_value={
                "id": "12345",
                "username": "testuser",
                "country_code": "US"
            })
            mock_auth_class.return_value = mock_auth

            with patch('src.tidal_mcp.server.TidalService') as mock_service_class:
                mock_service = Mock()
                mock_service_class.return_value = mock_service

                # Call the function directly
                result = await server.tidal_login()

                assert result["success"] is True
                assert "Successfully authenticated" in result["message"]
                assert result["user"]["id"] == "12345"
                assert result["user"]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_tidal_login_failure(self):
        """Test failed Tidal login."""
        with patch('src.tidal_mcp.server.TidalAuth') as mock_auth_class:
            mock_auth = AsyncMock()
            mock_auth.authenticate.return_value = False
            mock_auth_class.return_value = mock_auth

            result = await server.tidal_login()

            assert result["success"] is False
            assert "Authentication failed" in result["message"]
            assert result["user"] is None

    @pytest.mark.asyncio
    async def test_tidal_login_exception(self):
        """Test Tidal login with exception."""
        with patch('src.tidal_mcp.server.TidalAuth') as mock_auth_class:
            mock_auth_class.side_effect = Exception("Auth error")

            result = await server.tidal_login()

            assert result["success"] is False
            assert "Authentication error" in result["message"]
            assert "Auth error" in result["message"]


class TestTidalSearch:
    """Test tidal_search MCP tool."""

    @pytest.mark.asyncio
    async def test_search_tracks_success(self, sample_track, mock_service):
        """Test successful track search."""
        mock_service.search_tracks.return_value = [sample_track]

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_search("test query", "tracks", 10, 0)

            assert result["query"] == "test query"
            assert result["content_type"] == "tracks"
            assert len(result["results"]["tracks"]) == 1
            assert result["results"]["tracks"][0]["id"] == "12345"
            assert result["total_results"] == 1

    @pytest.mark.asyncio
    async def test_search_albums_success(self, sample_album, mock_service):
        """Test successful album search."""
        mock_service.search_albums.return_value = [sample_album]

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_search("test album", "albums", 5, 10)

            assert result["query"] == "test album"
            assert result["content_type"] == "albums"
            assert len(result["results"]["albums"]) == 1
            assert result["results"]["albums"][0]["id"] == "11111"
            assert result["total_results"] == 1

    @pytest.mark.asyncio
    async def test_search_artists_success(self, sample_artist, mock_service):
        """Test successful artist search."""
        mock_service.search_artists.return_value = [sample_artist]

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_search("test artist", "artists", 15, 5)

            assert result["query"] == "test artist"
            assert result["content_type"] == "artists"
            assert len(result["results"]["artists"]) == 1
            assert result["results"]["artists"][0]["id"] == "67890"
            assert result["total_results"] == 1

    @pytest.mark.asyncio
    async def test_search_playlists_success(self, sample_playlist, mock_service):
        """Test successful playlist search."""
        mock_service.search_playlists.return_value = [sample_playlist]

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_search("test playlist", "playlists", 20, 0)

            assert result["query"] == "test playlist"
            assert result["content_type"] == "playlists"
            assert len(result["results"]["playlists"]) == 1
            assert result["results"]["playlists"][0]["id"] == "test-playlist-uuid"
            assert result["total_results"] == 1

    @pytest.mark.asyncio
    async def test_search_all_success(self, mock_service):
        """Test successful search all content types."""
        mock_search_results = SearchResults(
            tracks=[],
            albums=[],
            artists=[],
            playlists=[]
        )
        mock_service.search_all.return_value = mock_search_results

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_search("test all", "all", 25, 0)

            assert result["query"] == "test all"
            assert result["content_type"] == "all"
            assert "results" in result
            assert result["total_results"] == 0

    @pytest.mark.asyncio
    async def test_search_parameter_clamping(self, mock_service):
        """Test search parameter validation and clamping."""
        mock_service.search_tracks.return_value = []

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            # Test limit clamping (max 50)
            await server.tidal_search("test", "tracks", 100, 0)

            # Verify service was called with clamped limit
            mock_service.search_tracks.assert_called_with("test", 50, 0)

            # Test negative offset clamping
            await server.tidal_search("test", "tracks", 10, -5)
            mock_service.search_tracks.assert_called_with("test", 10, 0)

            # Test minimum limit clamping
            await server.tidal_search("test", "tracks", 0, 0)
            mock_service.search_tracks.assert_called_with("test", 1, 0)

    @pytest.mark.asyncio
    async def test_search_auth_error(self):
        """Test search with authentication error."""
        with patch('src.tidal_mcp.server.ensure_service', side_effect=TidalAuthError("Not authenticated")):
            result = await server.tidal_search("test", "tracks", 10, 0)

            assert "error" in result
            assert "Authentication required" in result["error"]

    @pytest.mark.asyncio
    async def test_search_general_error(self):
        """Test search with general error."""
        with patch('src.tidal_mcp.server.ensure_service', side_effect=Exception("API Error")):
            result = await server.tidal_search("test", "tracks", 10, 0)

            assert "error" in result
            assert "Search failed" in result["error"]


class TestPlaylistManagement:
    """Test playlist management MCP tools."""

    @pytest.mark.asyncio
    async def test_get_playlist_success(self, sample_playlist, mock_service):
        """Test successful playlist retrieval."""
        mock_service.get_playlist.return_value = sample_playlist

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_get_playlist("playlist_123", True)

            assert result["success"] is True
            assert result["playlist"]["id"] == "test-playlist-uuid"
            assert result["playlist"]["title"] == "Test Playlist"

    @pytest.mark.asyncio
    async def test_get_playlist_not_found(self, mock_service):
        """Test playlist not found."""
        mock_service.get_playlist.return_value = None

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_get_playlist("nonexistent", True)

            assert result["success"] is False
            assert "Playlist not found" in result["error"]

    @pytest.mark.asyncio
    async def test_create_playlist_success(self, sample_playlist, mock_service):
        """Test successful playlist creation."""
        mock_service.create_playlist.return_value = sample_playlist

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_create_playlist("New Playlist", "Description")

            assert result["success"] is True
            assert "Created playlist" in result["message"]
            assert result["playlist"]["title"] == "Test Playlist"

    @pytest.mark.asyncio
    async def test_create_playlist_failure(self, mock_service):
        """Test playlist creation failure."""
        mock_service.create_playlist.return_value = None

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_create_playlist("Failed Playlist", "")

            assert result["success"] is False
            assert "Failed to create playlist" in result["error"]

    @pytest.mark.asyncio
    async def test_add_to_playlist_success(self, mock_service):
        """Test successful track addition to playlist."""
        mock_service.add_tracks_to_playlist.return_value = True
        track_ids = ["track1", "track2", "track3"]

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_add_to_playlist("playlist_123", track_ids)

            assert result["success"] is True
            assert "Added 3 tracks" in result["message"]

    @pytest.mark.asyncio
    async def test_add_to_playlist_empty_list(self, mock_service):
        """Test adding empty track list to playlist."""
        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_add_to_playlist("playlist_123", [])

            assert result["success"] is False
            assert "No track IDs provided" in result["error"]

    @pytest.mark.asyncio
    async def test_add_to_playlist_failure(self, mock_service):
        """Test failed track addition to playlist."""
        mock_service.add_tracks_to_playlist.return_value = False

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_add_to_playlist("playlist_123", ["track1"])

            assert result["success"] is False
            assert "Failed to add tracks" in result["error"]

    @pytest.mark.asyncio
    async def test_remove_from_playlist_success(self, mock_service):
        """Test successful track removal from playlist."""
        mock_service.remove_tracks_from_playlist.return_value = True
        track_indices = [0, 2, 4]

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_remove_from_playlist("playlist_123", track_indices)

            assert result["success"] is True
            assert "Removed 3 tracks" in result["message"]

    @pytest.mark.asyncio
    async def test_remove_from_playlist_empty_list(self, mock_service):
        """Test removing with empty indices list."""
        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_remove_from_playlist("playlist_123", [])

            assert result["success"] is False
            assert "No track indices provided" in result["error"]

    @pytest.mark.asyncio
    async def test_remove_from_playlist_failure(self, mock_service):
        """Test failed track removal from playlist."""
        mock_service.remove_tracks_from_playlist.return_value = False

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_remove_from_playlist("playlist_123", [1])

            assert result["success"] is False
            assert "Failed to remove tracks" in result["error"]

    @pytest.mark.asyncio
    async def test_get_user_playlists_success(self, sample_playlist, mock_service):
        """Test successful user playlists retrieval."""
        mock_service.get_user_playlists.return_value = [sample_playlist]

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_get_user_playlists(25, 5)

            assert len(result["playlists"]) == 1
            assert result["playlists"][0]["id"] == "test-playlist-uuid"
            assert result["total_results"] == 1

    @pytest.mark.asyncio
    async def test_get_user_playlists_parameter_clamping(self, mock_service):
        """Test user playlists parameter validation."""
        mock_service.get_user_playlists.return_value = []

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            # Test limit clamping (max 100)
            await server.tidal_get_user_playlists(150, 0)
            mock_service.get_user_playlists.assert_called_with(100, 0)

            # Test negative offset clamping
            await server.tidal_get_user_playlists(50, -10)
            mock_service.get_user_playlists.assert_called_with(50, 0)


class TestFavoritesManagement:
    """Test favorites management MCP tools."""

    @pytest.mark.asyncio
    async def test_get_favorites_tracks(self, sample_track, mock_service):
        """Test getting favorite tracks."""
        mock_service.get_user_favorites.return_value = [sample_track]

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_get_favorites("tracks", 30, 0)

            assert result["content_type"] == "tracks"
            assert len(result["favorites"]) == 1
            assert result["favorites"][0]["id"] == "12345"
            assert result["total_results"] == 1

    @pytest.mark.asyncio
    async def test_get_favorites_parameter_clamping(self, mock_service):
        """Test favorites parameter validation."""
        mock_service.get_user_favorites.return_value = []

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            # Test limit clamping (max 100)
            await server.tidal_get_favorites("tracks", 200, 0)
            mock_service.get_user_favorites.assert_called_with("tracks", 100, 0)

            # Test minimum limit clamping
            await server.tidal_get_favorites("albums", 0, 5)
            mock_service.get_user_favorites.assert_called_with("albums", 1, 5)

    @pytest.mark.asyncio
    async def test_get_favorites_non_dict_items(self, mock_service):
        """Test favorites with items that don't have to_dict method."""
        mock_item = {"id": "test", "name": "Test Item"}
        mock_service.get_user_favorites.return_value = [mock_item]

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_get_favorites("artists", 10, 0)

            assert len(result["favorites"]) == 1
            assert result["favorites"][0] == mock_item

    @pytest.mark.asyncio
    async def test_add_favorite_success(self, mock_service):
        """Test successful addition to favorites."""
        mock_service.add_to_favorites.return_value = True

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_add_favorite("track_123", "track")

            assert result["success"] is True
            assert "Added track track_123 to favorites" in result["message"]

    @pytest.mark.asyncio
    async def test_add_favorite_failure(self, mock_service):
        """Test failed addition to favorites."""
        mock_service.add_to_favorites.return_value = False

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_add_favorite("album_456", "album")

            assert result["success"] is False
            assert "Failed to add album album_456 to favorites" in result["error"]

    @pytest.mark.asyncio
    async def test_remove_favorite_success(self, mock_service):
        """Test successful removal from favorites."""
        mock_service.remove_from_favorites.return_value = True

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_remove_favorite("artist_789", "artist")

            assert result["success"] is True
            assert "Removed artist artist_789 from favorites" in result["message"]

    @pytest.mark.asyncio
    async def test_remove_favorite_failure(self, mock_service):
        """Test failed removal from favorites."""
        mock_service.remove_from_favorites.return_value = False

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_remove_favorite("playlist_000", "playlist")

            assert result["success"] is False
            assert "Failed to remove playlist playlist_000 from favorites" in result["error"]


class TestRecommendationsAndRadio:
    """Test recommendation and radio MCP tools."""

    @pytest.mark.asyncio
    async def test_get_recommendations_success(self, sample_track, mock_service):
        """Test successful recommendations retrieval."""
        mock_service.get_recommended_tracks.return_value = [sample_track]

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_get_recommendations(30)

            assert len(result["recommendations"]) == 1
            assert result["recommendations"][0]["id"] == "12345"
            assert result["total_results"] == 1

    @pytest.mark.asyncio
    async def test_get_recommendations_parameter_clamping(self, mock_service):
        """Test recommendations parameter validation."""
        mock_service.get_recommended_tracks.return_value = []

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            # Test limit clamping (max 100)
            await server.tidal_get_recommendations(150)
            mock_service.get_recommended_tracks.assert_called_with(100)

            # Test minimum limit clamping
            await server.tidal_get_recommendations(0)
            mock_service.get_recommended_tracks.assert_called_with(1)

    @pytest.mark.asyncio
    async def test_get_track_radio_success(self, sample_track, mock_service):
        """Test successful track radio retrieval."""
        mock_service.get_track_radio.return_value = [sample_track]

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_get_track_radio("seed_track_123", 40)

            assert result["seed_track_id"] == "seed_track_123"
            assert len(result["radio_tracks"]) == 1
            assert result["radio_tracks"][0]["id"] == "12345"
            assert result["total_results"] == 1

    @pytest.mark.asyncio
    async def test_get_track_radio_parameter_clamping(self, mock_service):
        """Test track radio parameter validation."""
        mock_service.get_track_radio.return_value = []

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            # Test limit clamping (max 100)
            await server.tidal_get_track_radio("track_123", 200)
            mock_service.get_track_radio.assert_called_with("track_123", 100)

            # Test minimum limit clamping
            await server.tidal_get_track_radio("track_456", -5)
            mock_service.get_track_radio.assert_called_with("track_456", 1)


class TestDetailRetrieval:
    """Test detail retrieval MCP tools."""

    @pytest.mark.asyncio
    async def test_get_track_success(self, sample_track, mock_service):
        """Test successful track retrieval."""
        mock_service.get_track.return_value = sample_track

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_get_track("track_123")

            assert result["success"] is True
            assert result["track"]["id"] == "12345"
            assert result["track"]["title"] == "Test Song"

    @pytest.mark.asyncio
    async def test_get_track_not_found(self, mock_service):
        """Test track not found."""
        mock_service.get_track.return_value = None

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_get_track("nonexistent")

            assert result["success"] is False
            assert "Track not found" in result["error"]

    @pytest.mark.asyncio
    async def test_get_album_success(self, sample_album, mock_service):
        """Test successful album retrieval."""
        mock_service.get_album.return_value = sample_album

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_get_album("album_123", True)

            assert result["success"] is True
            assert result["album"]["id"] == "11111"
            assert result["album"]["title"] == "Test Album"

    @pytest.mark.asyncio
    async def test_get_album_not_found(self, mock_service):
        """Test album not found."""
        mock_service.get_album.return_value = None

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_get_album("nonexistent", False)

            assert result["success"] is False
            assert "Album not found" in result["error"]

    @pytest.mark.asyncio
    async def test_get_artist_success(self, sample_artist, mock_service):
        """Test successful artist retrieval."""
        mock_service.get_artist.return_value = sample_artist

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_get_artist("artist_123")

            assert result["success"] is True
            assert result["artist"]["id"] == "67890"
            assert result["artist"]["name"] == "Test Artist"

    @pytest.mark.asyncio
    async def test_get_artist_not_found(self, mock_service):
        """Test artist not found."""
        mock_service.get_artist.return_value = None

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_get_artist("nonexistent")

            assert result["success"] is False
            assert "Artist not found" in result["error"]


class TestErrorHandling:
    """Test error handling across all MCP tools."""

    @pytest.mark.asyncio
    async def test_auth_error_handling(self):
        """Test authentication error handling in various tools."""
        auth_error = TidalAuthError("Authentication required")

        with patch('src.tidal_mcp.server.ensure_service', side_effect=auth_error):
            # Test different tools handle auth errors correctly
            result = await server.tidal_search("test", "tracks")
            assert "Authentication required" in result["error"]

            result = await server.tidal_get_favorites()
            assert "Authentication required" in result["error"]

            result = await server.tidal_create_playlist("test", "test")
            assert "Authentication required" in result["error"]

    @pytest.mark.asyncio
    async def test_general_exception_handling(self):
        """Test general exception handling in various tools."""
        general_error = Exception("API Error")

        with patch('src.tidal_mcp.server.ensure_service', side_effect=general_error):
            # Test different tools handle general errors correctly
            result = await server.tidal_get_track("test")
            assert "Failed to get track" in result["error"]

            result = await server.tidal_get_album("test")
            assert "Failed to get album" in result["error"]

            result = await server.tidal_get_artist("test")
            assert "Failed to get artist" in result["error"]


class TestMainFunction:
    """Test the main entry point function."""

    def test_main_function_exists(self):
        """Test that main function exists and is callable."""
        assert callable(server.main)

    @patch('src.tidal_mcp.server.mcp.run')
    @patch('src.tidal_mcp.server.logging.basicConfig')
    def test_main_function_configures_logging(self, mock_basic_config, mock_run, monkeypatch):
        """Test that main function configures logging correctly."""
        # Temporarily remove TESTING environment variable to test production mode
        monkeypatch.delenv('TESTING', raising=False)

        server.main()

        # Verify logging configuration
        mock_basic_config.assert_called_once()
        call_args = mock_basic_config.call_args
        assert call_args[1]["level"] == server.logging.INFO
        assert "%(asctime)s - %(name)s - %(levelname)s - %(message)s" in call_args[1]["format"]

        # Verify MCP server starts without banner
        mock_run.assert_called_once_with(show_banner=False)

    @patch('src.tidal_mcp.server.logging.basicConfig')
    def test_main_function_testing_mode(self, mock_basic_config, monkeypatch):
        """Test that main function returns early in testing mode."""
        # Ensure TESTING environment variable is set
        monkeypatch.setenv('TESTING', '1')

        # Mock the mcp.run method to verify it's not called
        with patch.object(server.mcp, 'run') as mock_run:
            server.main()

            # Verify logging configuration still happens
            mock_basic_config.assert_called_once()

            # Verify MCP server does NOT start in testing mode
            mock_run.assert_not_called()


class TestGlobalStateManagement:
    """Test global state management."""

    def test_global_instances_initialization(self):
        """Test that global instances are initially None."""
        # Reset to initial state
        server.auth_manager = None
        server.tidal_service = None

        assert server.auth_manager is None
        assert server.tidal_service is None

    def test_global_instances_persistence(self):
        """Test that global instances persist across calls."""
        mock_auth = Mock()
        mock_service = Mock()

        server.auth_manager = mock_auth
        server.tidal_service = mock_service

        assert server.auth_manager == mock_auth
        assert server.tidal_service == mock_service


@pytest.mark.integration
class TestToolIntegration:
    """Integration tests for MCP tool interactions."""

    @pytest.mark.asyncio
    async def test_login_then_search_flow(self, sample_track, mock_env_vars):
        """Test login followed by search workflow."""
        # Mock successful login
        with patch('src.tidal_mcp.server.TidalAuth') as mock_auth_class, \
             patch('src.tidal_mcp.server.TidalService') as mock_service_class:

            mock_auth = AsyncMock()
            mock_auth.authenticate.return_value = True
            mock_auth.get_user_info.return_value = {"id": "123", "username": "test"}
            mock_auth.is_authenticated.return_value = True
            mock_auth_class.return_value = mock_auth

            mock_service = AsyncMock()
            mock_service.search_tracks.return_value = [sample_track]
            mock_service_class.return_value = mock_service

            # First login
            login_result = await server.tidal_login()
            assert login_result["success"] is True

            # Then search (should reuse auth)
            search_result = await server.tidal_search("test", "tracks")
            assert search_result["content_type"] == "tracks"
            assert len(search_result["results"]["tracks"]) == 1

    @pytest.mark.asyncio
    async def test_create_playlist_then_add_tracks(self, sample_playlist, mock_env_vars):
        """Test playlist creation followed by adding tracks."""
        mock_auth = Mock()
        mock_auth.is_authenticated.return_value = True
        mock_service = AsyncMock()
        mock_service.create_playlist.return_value = sample_playlist
        mock_service.add_tracks_to_playlist.return_value = True

        server.auth_manager = mock_auth
        server.tidal_service = mock_service

        # Create playlist
        create_result = await server.tidal_create_playlist("Test Playlist", "Description")
        assert create_result["success"] is True

        # Add tracks to playlist
        add_result = await server.tidal_add_to_playlist("playlist_123", ["track1", "track2"])
        assert add_result["success"] is True
        assert "Added 2 tracks" in add_result["message"]
