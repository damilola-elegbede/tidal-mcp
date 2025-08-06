"""
Tests for Tidal MCP Server Tools

Comprehensive unit tests for all FastMCP @mcp.tool() functions defined
in server.py. Tests cover authentication, parameter validation, error
handling, and response formatting.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from tidal_mcp.auth import TidalAuth, TidalAuthError
from tidal_mcp.models import Album, Artist, Playlist, SearchResults, Track
from tidal_mcp.server import (
    ensure_service,
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
from tidal_mcp.service import TidalService


@pytest.fixture
def mock_auth():
    """Create a mock TidalAuth instance."""
    auth = Mock(spec=TidalAuth)
    auth.is_authenticated.return_value = True
    auth.authenticate = AsyncMock(return_value=True)
    auth.get_user_info.return_value = {
        "id": 12345,
        "username": "testuser",
        "country_code": "US",
        "subscription": {"type": "HiFi", "valid": True},
    }
    return auth


@pytest.fixture
def mock_service():
    """Create a mock TidalService instance."""
    service = Mock(spec=TidalService)

    # Mock search methods
    service.search_tracks = AsyncMock(return_value=[])
    service.search_albums = AsyncMock(return_value=[])
    service.search_artists = AsyncMock(return_value=[])
    service.search_playlists = AsyncMock(return_value=[])
    service.search_all = AsyncMock(return_value=SearchResults())

    # Mock playlist methods
    service.get_playlist = AsyncMock(return_value=None)
    service.create_playlist = AsyncMock(return_value=None)
    service.add_tracks_to_playlist = AsyncMock(return_value=True)
    service.remove_tracks_from_playlist = AsyncMock(return_value=True)
    service.get_user_playlists = AsyncMock(return_value=[])

    # Mock favorites methods
    service.get_user_favorites = AsyncMock(return_value=[])
    service.add_to_favorites = AsyncMock(return_value=True)
    service.remove_from_favorites = AsyncMock(return_value=True)

    # Mock recommendations and radio
    service.get_recommended_tracks = AsyncMock(return_value=[])
    service.get_track_radio = AsyncMock(return_value=[])

    # Mock detailed item retrieval
    service.get_track = AsyncMock(return_value=None)
    service.get_album = AsyncMock(return_value=None)
    service.get_artist = AsyncMock(return_value=None)

    return service


class TestEnsureService:
    """Test ensure_service function."""

    @pytest.mark.asyncio
    async def test_ensure_service_first_call(self):
        """Test ensure_service creates instances on first call."""
        # Reset global instances
        import tidal_mcp.server as server_module

        server_module.auth_manager = None
        server_module.tidal_service = None

        with (
            patch.dict("os.environ", {}, clear=True),
            patch("tidal_mcp.server.TidalAuth") as MockAuth,
            patch("tidal_mcp.server.TidalService") as MockService,
        ):
            mock_auth = Mock()
            mock_auth.is_authenticated.return_value = True
            MockAuth.return_value = mock_auth

            mock_service = Mock()
            MockService.return_value = mock_service

            result = await ensure_service()

            assert result == mock_service
            MockAuth.assert_called_once_with(client_id=None, client_secret=None)
            MockService.assert_called_once_with(mock_auth)

    @pytest.mark.asyncio
    async def test_ensure_service_with_env_credentials(self):
        """Test ensure_service uses environment credentials."""
        import tidal_mcp.server as server_module

        server_module.auth_manager = None
        server_module.tidal_service = None

        with (
            patch.dict(
                "os.environ",
                {
                    "TIDAL_CLIENT_ID": "env_client_id",
                    "TIDAL_CLIENT_SECRET": "env_client_secret",
                },
            ),
            patch("tidal_mcp.server.TidalAuth") as MockAuth,
            patch("tidal_mcp.server.TidalService") as MockService,
        ):
            mock_auth = Mock()
            mock_auth.is_authenticated.return_value = True
            MockAuth.return_value = mock_auth

            mock_service = Mock()
            MockService.return_value = mock_service

            await ensure_service()

            MockAuth.assert_called_once_with(
                client_id="env_client_id", client_secret="env_client_secret"
            )

    @pytest.mark.asyncio
    async def test_ensure_service_not_authenticated(self):
        """Test ensure_service raises error when not authenticated."""
        import tidal_mcp.server as server_module

        server_module.auth_manager = None
        server_module.tidal_service = None

        with patch("tidal_mcp.server.TidalAuth") as MockAuth:
            mock_auth = Mock()
            mock_auth.is_authenticated.return_value = False
            MockAuth.return_value = mock_auth

            with pytest.raises(TidalAuthError, match="Not authenticated"):
                await ensure_service()

    @pytest.mark.asyncio
    async def test_ensure_service_reuse_existing(self):
        """Test ensure_service reuses existing instances."""
        import tidal_mcp.server as server_module

        mock_auth = Mock()
        mock_auth.is_authenticated.return_value = True
        mock_service = Mock()

        server_module.auth_manager = mock_auth
        server_module.tidal_service = mock_service

        result = await ensure_service()

        assert result == mock_service


class TestTidalLogin:
    """Test tidal_login tool."""

    @pytest.mark.asyncio
    async def test_tidal_login_success(self, mock_auth):
        """Test successful login."""
        with (
            patch("tidal_mcp.server.TidalAuth", return_value=mock_auth),
            patch("tidal_mcp.server.TidalService") as MockService,
        ):
            mock_service = Mock()
            MockService.return_value = mock_service

            result = await tidal_login.fn()

            assert result["success"] is True
            assert "Successfully authenticated" in result["message"]
            assert result["user"]["id"] == 12345
            mock_auth.authenticate.assert_called_once()

    @pytest.mark.asyncio
    async def test_tidal_login_failure(self):
        """Test login failure."""
        mock_auth = Mock()
        mock_auth.authenticate = AsyncMock(return_value=False)

        with patch("tidal_mcp.server.TidalAuth", return_value=mock_auth):
            result = await tidal_login.fn()

            assert result["success"] is False
            assert "Authentication failed" in result["message"]
            assert result["user"] is None

    @pytest.mark.asyncio
    async def test_tidal_login_exception(self):
        """Test login with exception."""
        mock_auth = Mock()
        mock_auth.authenticate = AsyncMock(side_effect=Exception("Network error"))

        with patch("tidal_mcp.server.TidalAuth", return_value=mock_auth):
            result = await tidal_login.fn()

            assert result["success"] is False
            assert "Authentication error" in result["message"]
            assert "Network error" in result["message"]


class TestTidalSearch:
    """Test tidal_search tool."""

    @pytest.mark.asyncio
    async def test_search_tracks(self, mock_service):
        """Test searching for tracks."""
        track = Track(id="123", title="Test Track", artists=[], duration=240)
        mock_service.search_tracks.return_value = [track]

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_search.fn("test query", "tracks", 10, 0)

            assert result["query"] == "test query"
            assert result["content_type"] == "tracks"
            assert len(result["results"]["tracks"]) == 1
            assert result["total_results"] == 1
            mock_service.search_tracks.assert_called_once_with("test query", 10, 0)

    @pytest.mark.asyncio
    async def test_search_albums(self, mock_service):
        """Test searching for albums."""
        album = Album(id="456", title="Test Album", artists=[])
        mock_service.search_albums.return_value = [album]

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_search.fn("test query", "albums", 10, 0)

            assert result["content_type"] == "albums"
            assert len(result["results"]["albums"]) == 1
            mock_service.search_albums.assert_called_once_with("test query", 10, 0)

    @pytest.mark.asyncio
    async def test_search_artists(self, mock_service):
        """Test searching for artists."""
        artist = Artist(id="789", name="Test Artist")
        mock_service.search_artists.return_value = [artist]

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_search.fn("test query", "artists", 10, 0)

            assert result["content_type"] == "artists"
            assert len(result["results"]["artists"]) == 1
            mock_service.search_artists.assert_called_once_with("test query", 10, 0)

    @pytest.mark.asyncio
    async def test_search_playlists(self, mock_service):
        """Test searching for playlists."""
        playlist = Playlist(id="playlist123", title="Test Playlist")
        mock_service.search_playlists.return_value = [playlist]

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_search.fn("test query", "playlists", 10, 0)

            assert result["content_type"] == "playlists"
            assert len(result["results"]["playlists"]) == 1
            mock_service.search_playlists.assert_called_once_with("test query", 10, 0)

    @pytest.mark.asyncio
    async def test_search_all(self, mock_service):
        """Test searching across all content types."""
        search_results = SearchResults(
            tracks=[Track(id="123", title="Track", artists=[], duration=240)],
            albums=[Album(id="456", title="Album", artists=[])],
            artists=[Artist(id="789", name="Artist")],
            playlists=[Playlist(id="playlist123", title="Playlist")],
        )
        mock_service.search_all.return_value = search_results

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_search.fn("test query", "all", 20)

            assert result["content_type"] == "all"
            assert result["total_results"] == 4
            mock_service.search_all.assert_called_once_with("test query", 20)

    @pytest.mark.asyncio
    async def test_search_parameter_clamping(self, mock_service):
        """Test search parameter validation and clamping."""
        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            # Test limit clamping
            # Should clamp to 50
            await tidal_search.fn("query", "tracks", 100, 0)
            mock_service.search_tracks.assert_called_with("query", 50, 0)

            # Test negative offset
            # Should clamp to 0
            await tidal_search.fn("query", "tracks", 10, -5)
            mock_service.search_tracks.assert_called_with("query", 10, 0)

    @pytest.mark.asyncio
    async def test_search_auth_error(self):
        """Test search with authentication error."""
        with patch(
            "tidal_mcp.server.ensure_service",
            side_effect=TidalAuthError("Not authenticated"),
        ):
            result = await tidal_search.fn("test query", "tracks")

            assert "error" in result
            assert "Authentication required" in result["error"]

    @pytest.mark.asyncio
    async def test_search_general_exception(self, mock_service):
        """Test search with general exception."""
        mock_service.search_tracks.side_effect = Exception("API error")

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_search.fn("test query", "tracks")

            assert "error" in result
            assert "Search failed" in result["error"]


class TestPlaylistTools:
    """Test playlist management tools."""

    @pytest.mark.asyncio
    async def test_get_playlist_success(self, mock_service):
        """Test successful playlist retrieval."""
        playlist = Playlist(id="playlist123", title="Test Playlist")
        mock_service.get_playlist.return_value = playlist

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_get_playlist.fn("playlist123", True)

            assert result["success"] is True
            assert result["playlist"]["id"] == "playlist123"
            mock_service.get_playlist.assert_called_once_with("playlist123", True)

    @pytest.mark.asyncio
    async def test_get_playlist_not_found(self, mock_service):
        """Test playlist not found."""
        mock_service.get_playlist.return_value = None

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_get_playlist.fn("nonexistent")

            assert result["success"] is False
            assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_create_playlist_success(self, mock_service):
        """Test successful playlist creation."""
        playlist = Playlist(id="new_playlist", title="New Playlist")
        mock_service.create_playlist.return_value = playlist

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_create_playlist.fn("New Playlist", "Description")

            assert result["success"] is True
            assert "Created playlist" in result["message"]
            assert result["playlist"]["title"] == "New Playlist"
            mock_service.create_playlist.assert_called_once_with(
                "New Playlist", "Description"
            )

    @pytest.mark.asyncio
    async def test_create_playlist_failure(self, mock_service):
        """Test playlist creation failure."""
        mock_service.create_playlist.return_value = None

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_create_playlist.fn("Failed Playlist")

            assert result["success"] is False
            assert "Failed to create" in result["error"]

    @pytest.mark.asyncio
    async def test_add_to_playlist_success(self, mock_service):
        """Test successful track addition to playlist."""
        mock_service.add_tracks_to_playlist.return_value = True

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_add_to_playlist.fn("playlist123", ["track1", "track2"])

            assert result["success"] is True
            assert "Added 2 tracks" in result["message"]
            mock_service.add_tracks_to_playlist.assert_called_once_with(
                "playlist123", ["track1", "track2"]
            )

    @pytest.mark.asyncio
    async def test_add_to_playlist_no_tracks(self, mock_service):
        """Test adding empty track list to playlist."""
        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_add_to_playlist.fn("playlist123", [])

            assert result["success"] is False
            assert "No track IDs provided" in result["error"]

    @pytest.mark.asyncio
    async def test_add_to_playlist_failure(self, mock_service):
        """Test failed track addition to playlist."""
        mock_service.add_tracks_to_playlist.return_value = False

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_add_to_playlist.fn("playlist123", ["track1"])

            assert result["success"] is False
            assert "Failed to add tracks" in result["error"]

    @pytest.mark.asyncio
    async def test_remove_from_playlist_success(self, mock_service):
        """Test successful track removal from playlist."""
        mock_service.remove_tracks_from_playlist.return_value = True

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_remove_from_playlist.fn("playlist123", [0, 2, 1])

            assert result["success"] is True
            assert "Removed 3 tracks" in result["message"]
            mock_service.remove_tracks_from_playlist.assert_called_once_with(
                "playlist123", [0, 2, 1]
            )

    @pytest.mark.asyncio
    async def test_remove_from_playlist_no_indices(self, mock_service):
        """Test removing with empty indices list."""
        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_remove_from_playlist.fn("playlist123", [])

            assert result["success"] is False
            assert "No track indices provided" in result["error"]

    @pytest.mark.asyncio
    async def test_get_user_playlists(self, mock_service):
        """Test getting user playlists."""
        playlists = [
            Playlist(id="p1", title="Playlist 1"),
            Playlist(id="p2", title="Playlist 2"),
        ]
        mock_service.get_user_playlists.return_value = playlists

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_get_user_playlists.fn(30, 5)

            assert len(result["playlists"]) == 2
            assert result["total_results"] == 2
            mock_service.get_user_playlists.assert_called_once_with(30, 5)


class TestFavoritesTools:
    """Test favorites management tools."""

    @pytest.mark.asyncio
    async def test_get_favorites_tracks(self, mock_service):
        """Test getting favorite tracks."""
        tracks = [Track(id="t1", title="Track 1", artists=[], duration=240)]
        mock_service.get_user_favorites.return_value = tracks

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_get_favorites.fn("tracks", 25, 10)

            assert result["content_type"] == "tracks"
            assert len(result["favorites"]) == 1
            assert result["total_results"] == 1
            mock_service.get_user_favorites.assert_called_once_with("tracks", 25, 10)

    @pytest.mark.asyncio
    async def test_get_favorites_parameter_clamping(self, mock_service):
        """Test favorites parameter validation."""
        mock_service.get_user_favorites.return_value = []

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            # Test limit clamping to max 100
            await tidal_get_favorites.fn("tracks", 150, 0)
            mock_service.get_user_favorites.assert_called_with("tracks", 100, 0)

            # Test negative offset clamping
            await tidal_get_favorites.fn("tracks", 50, -10)
            mock_service.get_user_favorites.assert_called_with("tracks", 50, 0)

    @pytest.mark.asyncio
    async def test_add_favorite_success(self, mock_service):
        """Test successful favorite addition."""
        mock_service.add_to_favorites.return_value = True

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_add_favorite.fn("track123", "track")

            assert result["success"] is True
            assert "Added track track123 to favorites" in result["message"]
            mock_service.add_to_favorites.assert_called_once_with("track123", "track")

    @pytest.mark.asyncio
    async def test_add_favorite_failure(self, mock_service):
        """Test failed favorite addition."""
        mock_service.add_to_favorites.return_value = False

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_add_favorite.fn("track123", "track")

            assert result["success"] is False
            assert "Failed to add" in result["error"]

    @pytest.mark.asyncio
    async def test_remove_favorite_success(self, mock_service):
        """Test successful favorite removal."""
        mock_service.remove_from_favorites.return_value = True

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_remove_favorite.fn("album456", "album")

            assert result["success"] is True
            assert "Removed album album456 from favorites" in result["message"]
            mock_service.remove_from_favorites.assert_called_once_with(
                "album456", "album"
            )


class TestRecommendationTools:
    """Test recommendation and radio tools."""

    @pytest.mark.asyncio
    async def test_get_recommendations(self, mock_service):
        """Test getting recommendations."""
        tracks = [
            Track(id="r1", title="Rec 1", artists=[], duration=180),
            Track(id="r2", title="Rec 2", artists=[], duration=200),
        ]
        mock_service.get_recommended_tracks.return_value = tracks

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_get_recommendations.fn(75)

            assert len(result["recommendations"]) == 2
            assert result["total_results"] == 2
            mock_service.get_recommended_tracks.assert_called_once_with(75)

    @pytest.mark.asyncio
    async def test_get_recommendations_parameter_clamping(self, mock_service):
        """Test recommendations parameter clamping."""
        mock_service.get_recommended_tracks.return_value = []

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            # Test limit clamping to max 100
            await tidal_get_recommendations.fn(150)
            mock_service.get_recommended_tracks.assert_called_once_with(100)

    @pytest.mark.asyncio
    async def test_get_track_radio(self, mock_service):
        """Test getting track radio."""
        radio_tracks = [
            Track(id="radio1", title="Radio 1", artists=[], duration=220),
            Track(id="radio2", title="Radio 2", artists=[], duration=190),
        ]
        mock_service.get_track_radio.return_value = radio_tracks

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_get_track_radio.fn("seed123", 30)

            assert result["seed_track_id"] == "seed123"
            assert len(result["radio_tracks"]) == 2
            assert result["total_results"] == 2
            mock_service.get_track_radio.assert_called_once_with("seed123", 30)


class TestDetailedItemRetrieval:
    """Test detailed item retrieval tools."""

    @pytest.mark.asyncio
    async def test_get_track_success(self, mock_service):
        """Test successful track retrieval."""
        track = Track(id="track123", title="Detailed Track", artists=[], duration=250)
        mock_service.get_track.return_value = track

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_get_track.fn("track123")

            assert result["success"] is True
            assert result["track"]["id"] == "track123"
            assert result["track"]["title"] == "Detailed Track"
            mock_service.get_track.assert_called_once_with("track123")

    @pytest.mark.asyncio
    async def test_get_track_not_found(self, mock_service):
        """Test track not found."""
        mock_service.get_track.return_value = None

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_get_track.fn("nonexistent")

            assert result["success"] is False
            assert "Track not found" in result["error"]

    @pytest.mark.asyncio
    async def test_get_album_success(self, mock_service):
        """Test successful album retrieval."""
        album = Album(id="album456", title="Detailed Album", artists=[])
        mock_service.get_album.return_value = album

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_get_album.fn("album456", False)

            assert result["success"] is True
            assert result["album"]["id"] == "album456"
            assert result["album"]["title"] == "Detailed Album"
            mock_service.get_album.assert_called_once_with("album456", False)

    @pytest.mark.asyncio
    async def test_get_artist_success(self, mock_service):
        """Test successful artist retrieval."""
        artist = Artist(id="artist789", name="Detailed Artist", popularity=90)
        mock_service.get_artist.return_value = artist

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_get_artist.fn("artist789")

            assert result["success"] is True
            assert result["artist"]["id"] == "artist789"
            assert result["artist"]["name"] == "Detailed Artist"
            mock_service.get_artist.assert_called_once_with("artist789")


class TestErrorHandling:
    """Test comprehensive error handling across all tools."""

    @pytest.mark.asyncio
    async def test_authentication_errors(self):
        """Test authentication error handling across tools."""
        tools_to_test = [
            (tidal_search.fn, ("query", "tracks")),
            (tidal_get_playlist.fn, ("playlist123",)),
            (tidal_create_playlist.fn, ("title",)),
            (tidal_add_to_playlist.fn, ("playlist123", ["track1"])),
            (tidal_remove_from_playlist.fn, ("playlist123", [0])),
            (tidal_get_favorites.fn, ("tracks",)),
            (tidal_add_favorite.fn, ("item123", "track")),
            (tidal_remove_favorite.fn, ("item123", "track")),
            (tidal_get_recommendations.fn, (50,)),
            (tidal_get_track_radio.fn, ("track123", 25)),
            (tidal_get_user_playlists.fn, (50, 0)),
            (tidal_get_track.fn, ("track123",)),
            (tidal_get_album.fn, ("album456",)),
            (tidal_get_artist.fn, ("artist789",)),
        ]

        for tool_func, args in tools_to_test:
            with patch(
                "tidal_mcp.server.ensure_service",
                side_effect=TidalAuthError("Not authenticated"),
            ):
                result = await tool_func(*args)

                assert "error" in result
                assert "Authentication required" in result["error"]

    @pytest.mark.asyncio
    async def test_general_exceptions(self, mock_service):
        """Test general exception handling."""
        mock_service.search_tracks.side_effect = Exception("Unexpected error")

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_search.fn("query", "tracks")

            assert "error" in result
            assert "Search failed" in result["error"]

    @pytest.mark.asyncio
    async def test_tool_specific_exceptions(self, mock_service):
        """Test tool-specific exception handling."""
        # Test playlist creation exception
        mock_service.create_playlist.side_effect = Exception("Playlist creation failed")

        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            result = await tidal_create_playlist.fn("Test Playlist")

            assert "error" in result
            assert "Failed to create playlist" in result["error"]


class TestParameterValidation:
    """Test parameter validation and edge cases."""

    @pytest.mark.asyncio
    async def test_empty_parameters(self, mock_service):
        """Test tools with empty parameters."""
        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            # Test empty query search
            result = await tidal_search.fn("", "tracks")
            assert result["query"] == ""

            # Test empty playlist title
            result = await tidal_create_playlist.fn("")
            # Should be handled by service layer

            # Test empty track list
            result = await tidal_add_to_playlist.fn("playlist123", [])
            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_boundary_values(self, mock_service):
        """Test boundary value handling."""
        with patch("tidal_mcp.server.ensure_service", return_value=mock_service):
            # Test minimum and maximum limits
            await tidal_search.fn("query", "tracks", 1, 0)  # Minimum limit
            mock_service.search_tracks.assert_called_with("query", 1, 0)

            # Should clamp to 50
            await tidal_search.fn("query", "tracks", 100, 0)
            mock_service.search_tracks.assert_called_with("query", 50, 0)

            # Test recommendations boundary
            await tidal_get_recommendations.fn(1)  # Minimum
            mock_service.get_recommended_tracks.assert_called_with(1)

            # Should clamp to 100
            await tidal_get_recommendations.fn(200)
            mock_service.get_recommended_tracks.assert_called_with(100)


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
