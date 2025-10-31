"""
Comprehensive tests for Tidal Service Layer

Tests business logic, API interactions, data conversion, and service operations.
Focuses on achieving high coverage for the service layer functionality.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import tidalapi

from src.tidal_mcp.auth import TidalAuth, TidalAuthError
from src.tidal_mcp.models import Album, Artist, Playlist, SearchResults, Track
from src.tidal_mcp.service import TidalService, async_to_sync


class TestTidalServiceInitialization:
    """Test TidalService initialization and configuration."""

    def test_service_initialization(self):
        """Test service initialization with auth."""
        mock_auth = MagicMock(spec=TidalAuth)
        service = TidalService(mock_auth)

        assert service.auth == mock_auth
        assert service._cache == {}
        assert service._cache_ttl == 300

    @pytest.mark.asyncio
    async def test_ensure_authenticated_success(self):
        """Test ensure_authenticated with valid token."""
        mock_auth = MagicMock(spec=TidalAuth)
        mock_auth.ensure_valid_token = AsyncMock(return_value=True)
        service = TidalService(mock_auth)

        await service.ensure_authenticated()
        mock_auth.ensure_valid_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_authenticated_failure(self):
        """Test ensure_authenticated with invalid token."""
        mock_auth = MagicMock(spec=TidalAuth)
        mock_auth.ensure_valid_token = AsyncMock(return_value=False)
        service = TidalService(mock_auth)

        with pytest.raises(TidalAuthError, match="Authentication required"):
            await service.ensure_authenticated()

    def test_get_session(self):
        """Test getting Tidal session."""
        mock_auth = MagicMock(spec=TidalAuth)
        mock_session = MagicMock(spec=tidalapi.Session)
        mock_auth.get_tidal_session.return_value = mock_session
        service = TidalService(mock_auth)

        session = service.get_session()
        assert session == mock_session
        mock_auth.get_tidal_session.assert_called_once()


class TestAsyncToSyncDecorator:
    """Test the async_to_sync decorator functionality."""

    @pytest.mark.asyncio
    async def test_async_to_sync_decorator(self):
        """Test async_to_sync decorator wraps sync functions correctly."""

        def sync_function(value):
            return value * 2

        wrapped_function = async_to_sync(sync_function)
        result = await wrapped_function(5)
        assert result == 10

    @pytest.mark.asyncio
    async def test_async_to_sync_with_exception(self):
        """Test async_to_sync decorator handles exceptions."""

        def sync_function_with_error():
            raise ValueError("Test error")

        wrapped_function = async_to_sync(sync_function_with_error)

        with pytest.raises(ValueError, match="Test error"):
            await wrapped_function()


class TestSearchFunctionality:
    """Test search functionality for different content types."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_auth = MagicMock(spec=TidalAuth)
        self.mock_auth.ensure_valid_token = AsyncMock(return_value=True)
        self.mock_session = MagicMock(spec=tidalapi.Session)
        self.mock_auth.get_tidal_session.return_value = self.mock_session
        self.service = TidalService(self.mock_auth)

    @pytest.mark.asyncio
    @patch("src.tidal_mcp.service.sanitize_query")
    async def test_search_tracks_success(self, mock_sanitize):
        """Test successful track search."""
        mock_sanitize.return_value = "clean query"

        # Mock tidal track
        mock_tidal_track = MagicMock()
        mock_tidal_track.id = 123
        mock_tidal_track.name = "Test Track"
        mock_tidal_track.artists = []

        # Mock search result
        self.mock_session.search.return_value = {"tracks": [mock_tidal_track]}

        with patch.object(self.service, "_convert_tidal_track") as mock_convert:
            mock_track = Track(id="123", title="Test Track")
            mock_convert.return_value = mock_track

            result = await self.service.search_tracks("test query", 10, 5)

            assert len(result) == 1
            assert result[0].title == "Test Track"
            mock_sanitize.assert_called_once_with("test query")
            mock_convert.assert_called_once_with(mock_tidal_track)

    @pytest.mark.asyncio
    @patch("src.tidal_mcp.service.sanitize_query")
    async def test_search_tracks_empty_query(self, mock_sanitize):
        """Test track search with empty/invalid query."""
        mock_sanitize.return_value = ""

        result = await self.service.search_tracks("", 10, 0)

        assert result == []
        self.mock_session.search.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.tidal_mcp.service.sanitize_query")
    async def test_search_tracks_with_offset_limit(self, mock_sanitize):
        """Test track search with offset and limit."""
        mock_sanitize.return_value = "query"

        # Create multiple mock tracks
        mock_tracks = []
        for i in range(10):
            mock_track = MagicMock()
            mock_track.id = i
            mock_track.name = f"Track {i}"
            mock_tracks.append(mock_track)

        self.mock_session.search.return_value = {"tracks": mock_tracks}

        with patch.object(self.service, "_convert_tidal_track") as mock_convert:
            mock_convert.return_value = Track(id="1", title="Test")

            # Search with offset 3, limit 2
            result = await self.service.search_tracks("query", 2, 3)

            # Should call search but limit results in post-processing
            self.mock_session.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_tracks_conversion_error(self):
        """Test track search with conversion error."""
        # Mock tidal track that causes conversion error
        mock_tidal_track = MagicMock()
        mock_tidal_track.id = 123

        self.mock_session.search.return_value = {"tracks": [mock_tidal_track]}

        with patch("src.tidal_mcp.service.sanitize_query", return_value="query"):
            with patch.object(self.service, "_convert_tidal_track") as mock_convert:
                mock_convert.side_effect = Exception("Conversion error")

                result = await self.service.search_tracks("query")

                # Should return empty list, not raise exception
                assert result == []

    @pytest.mark.asyncio
    async def test_search_albums_success(self):
        """Test successful album search."""
        mock_tidal_album = MagicMock()
        mock_tidal_album.id = 456
        mock_tidal_album.name = "Test Album"

        self.mock_session.search.return_value = {"albums": [mock_tidal_album]}

        with patch("src.tidal_mcp.service.sanitize_query", return_value="query"):
            with patch.object(self.service, "_convert_tidal_album") as mock_convert:
                mock_album = Album(id="456", title="Test Album")
                mock_convert.return_value = mock_album

                result = await self.service.search_albums("query", 5, 0)

                assert len(result) == 1
                assert result[0].title == "Test Album"

    @pytest.mark.asyncio
    async def test_search_artists_success(self):
        """Test successful artist search."""
        mock_tidal_artist = MagicMock()
        mock_tidal_artist.id = 789
        mock_tidal_artist.name = "Test Artist"

        self.mock_session.search.return_value = {"artists": [mock_tidal_artist]}

        with patch("src.tidal_mcp.service.sanitize_query", return_value="query"):
            with patch.object(self.service, "_convert_tidal_artist") as mock_convert:
                mock_artist = Artist(id="789", name="Test Artist")
                mock_convert.return_value = mock_artist

                result = await self.service.search_artists("query")

                assert len(result) == 1
                assert result[0].name == "Test Artist"

    @pytest.mark.asyncio
    async def test_search_playlists_success(self):
        """Test successful playlist search."""
        mock_tidal_playlist = MagicMock()
        mock_tidal_playlist.uuid = "abc-123"
        mock_tidal_playlist.name = "Test Playlist"

        self.mock_session.search.return_value = {"playlists": [mock_tidal_playlist]}

        with patch("src.tidal_mcp.service.sanitize_query", return_value="query"):
            with patch.object(self.service, "_convert_tidal_playlist") as mock_convert:
                mock_playlist = Playlist(id="abc-123", title="Test Playlist")
                mock_convert.return_value = mock_playlist

                result = await self.service.search_playlists("query")

                assert len(result) == 1
                assert result[0].title == "Test Playlist"

    @pytest.mark.asyncio
    async def test_search_all_content_types(self):
        """Test searching all content types concurrently."""
        with patch.object(self.service, "search_tracks") as mock_tracks:
            with patch.object(self.service, "search_albums") as mock_albums:
                with patch.object(self.service, "search_artists") as mock_artists:
                    with patch.object(
                        self.service, "search_playlists"
                    ) as mock_playlists:
                        # Mock return values
                        mock_tracks.return_value = [Track(id="1", title="Track")]
                        mock_albums.return_value = [Album(id="2", title="Album")]
                        mock_artists.return_value = [Artist(id="3", name="Artist")]
                        mock_playlists.return_value = [
                            Playlist(id="4", title="Playlist")
                        ]

                        result = await self.service.search_all("query", 10)

                        assert len(result.tracks) == 1
                        assert len(result.albums) == 1
                        assert len(result.artists) == 1
                        assert len(result.playlists) == 1
                        assert result.total_results == 4

                        # Verify all search methods were called
                        mock_tracks.assert_called_once_with("query", limit=10)
                        mock_albums.assert_called_once_with("query", limit=10)
                        mock_artists.assert_called_once_with("query", limit=10)
                        mock_playlists.assert_called_once_with("query", limit=10)

    @pytest.mark.asyncio
    async def test_search_all_with_exception(self):
        """Test search_all handles exceptions gracefully."""
        with patch.object(self.service, "search_tracks") as mock_tracks:
            mock_tracks.side_effect = Exception("Search error")

            result = await self.service.search_all("query")

            # Should return empty SearchResults, not raise exception
            assert isinstance(result, SearchResults)
            assert result.total_results == 0


class TestPlaylistManagement:
    """Test playlist management functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_auth = MagicMock(spec=TidalAuth)
        self.mock_auth.ensure_valid_token = AsyncMock(return_value=True)
        self.mock_session = MagicMock(spec=tidalapi.Session)
        self.mock_auth.get_tidal_session.return_value = self.mock_session
        self.service = TidalService(self.mock_auth)

    @pytest.mark.asyncio
    @patch("src.tidal_mcp.service.validate_tidal_id")
    async def test_get_playlist_success(self, mock_validate):
        """Test getting playlist successfully."""
        mock_validate.return_value = True

        mock_tidal_playlist = MagicMock()
        mock_tidal_playlist.uuid = "abc-123"
        mock_tidal_playlist.name = "Test Playlist"

        self.mock_session.playlist.return_value = mock_tidal_playlist

        with patch.object(self.service, "_convert_tidal_playlist") as mock_convert:
            mock_playlist = Playlist(id="abc-123", title="Test Playlist")
            mock_convert.return_value = mock_playlist

            result = await self.service.get_playlist("abc-123", True)

            assert result.title == "Test Playlist"
            mock_convert.assert_called_once_with(
                mock_tidal_playlist, include_tracks=True
            )

    @pytest.mark.asyncio
    @patch("src.tidal_mcp.service.validate_tidal_id")
    async def test_get_playlist_invalid_id(self, mock_validate):
        """Test getting playlist with invalid ID."""
        mock_validate.return_value = False

        with patch.object(self.service, "_is_uuid", return_value=False):
            result = await self.service.get_playlist("invalid-id")

            assert result is None
            self.mock_session.playlist.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.tidal_mcp.service.validate_tidal_id")
    async def test_get_playlist_not_found(self, mock_validate):
        """Test getting non-existent playlist."""
        mock_validate.return_value = True
        self.mock_session.playlist.return_value = None

        result = await self.service.get_playlist("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_create_playlist_success(self):
        """Test creating playlist successfully."""
        mock_user = MagicMock()
        mock_tidal_playlist = MagicMock()
        mock_user.create_playlist.return_value = mock_tidal_playlist
        self.mock_session.user = mock_user

        with patch.object(self.service, "_convert_tidal_playlist") as mock_convert:
            mock_playlist = Playlist(id="new-123", title="New Playlist")
            mock_convert.return_value = mock_playlist

            result = await self.service.create_playlist("New Playlist", "Description")

            assert result.title == "New Playlist"
            mock_user.create_playlist.assert_called_once_with(
                "New Playlist", "Description"
            )

    @pytest.mark.asyncio
    async def test_create_playlist_empty_title(self):
        """Test creating playlist with empty title."""
        result = await self.service.create_playlist("   ")

        assert result is None
        # Should not call create_playlist on user
        self.mock_session.user.create_playlist.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_playlist_failure(self):
        """Test playlist creation failure."""
        mock_user = MagicMock()
        mock_user.create_playlist.return_value = None
        self.mock_session.user = mock_user

        result = await self.service.create_playlist("Failed Playlist")

        assert result is None

    @pytest.mark.asyncio
    @patch("src.tidal_mcp.service.validate_tidal_id")
    async def test_add_tracks_to_playlist_success(self, mock_validate):
        """Test adding tracks to playlist successfully."""
        mock_validate.return_value = True

        mock_playlist = MagicMock()
        mock_playlist.add.return_value = True
        self.mock_session.playlist.return_value = mock_playlist

        # Mock track retrieval
        mock_track = MagicMock()
        self.mock_session.track.return_value = mock_track

        track_ids = ["123", "124"]
        result = await self.service.add_tracks_to_playlist("playlist-123", track_ids)

        assert result is True
        mock_playlist.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_tracks_to_playlist_empty_list(self):
        """Test adding empty track list to playlist."""
        result = await self.service.add_tracks_to_playlist("playlist-123", [])

        assert result is False

    @pytest.mark.asyncio
    @patch("src.tidal_mcp.service.validate_tidal_id")
    async def test_add_tracks_to_playlist_invalid_playlist_id(self, mock_validate):
        """Test adding tracks with invalid playlist ID."""
        mock_validate.return_value = False

        with patch.object(self.service, "_is_uuid", return_value=False):
            result = await self.service.add_tracks_to_playlist("invalid", ["123"])

            assert result is False

    @pytest.mark.asyncio
    @patch("src.tidal_mcp.service.validate_tidal_id")
    async def test_remove_tracks_from_playlist_success(self, mock_validate):
        """Test removing tracks from playlist successfully."""
        mock_validate.return_value = True

        mock_playlist = MagicMock()
        self.mock_session.playlist.return_value = mock_playlist

        track_indices = [2, 0, 5]  # Should be sorted in reverse order
        result = await self.service.remove_tracks_from_playlist(
            "playlist-123", track_indices
        )

        assert result is True
        # Verify remove_by_index called in reverse order
        expected_calls = [((5,),), ((2,),), ((0,),)]
        assert mock_playlist.remove_by_index.call_args_list == expected_calls

    @pytest.mark.asyncio
    async def test_remove_tracks_from_playlist_empty_indices(self):
        """Test removing with empty indices list."""
        result = await self.service.remove_tracks_from_playlist("playlist-123", [])

        assert result is False

    @pytest.mark.asyncio
    @patch("src.tidal_mcp.service.validate_tidal_id")
    async def test_delete_playlist_success(self, mock_validate):
        """Test deleting playlist successfully."""
        mock_validate.return_value = True

        mock_playlist = MagicMock()
        mock_playlist.delete.return_value = True
        self.mock_session.playlist.return_value = mock_playlist

        result = await self.service.delete_playlist("playlist-123")

        assert result is True
        mock_playlist.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_playlists_success(self):
        """Test getting user playlists successfully."""
        mock_user = MagicMock()
        mock_tidal_playlists = [MagicMock(), MagicMock()]
        mock_user.playlists.return_value = mock_tidal_playlists
        self.mock_session.user = mock_user

        with patch.object(self.service, "_convert_tidal_playlist") as mock_convert:
            mock_playlist = Playlist(id="pl1", title="Playlist")
            mock_convert.return_value = mock_playlist

            result = await self.service.get_user_playlists(10, 0)

            assert len(result) == 2
            assert mock_convert.call_count == 2

    @pytest.mark.asyncio
    async def test_get_playlist_tracks(self):
        """Test getting tracks from a playlist."""
        mock_playlist = MagicMock()
        mock_tidal_tracks = [MagicMock(), MagicMock()]
        mock_playlist.tracks.return_value = mock_tidal_tracks
        self.mock_session.playlist.return_value = mock_playlist

        with patch("src.tidal_mcp.service.validate_tidal_id", return_value=True):
            with patch.object(self.service, "_convert_tidal_track") as mock_convert:
                mock_track = Track(id="track1", title="Track")
                mock_convert.return_value = mock_track

                result = await self.service.get_playlist_tracks("playlist-123", 50, 0)

                assert len(result) == 2
                assert mock_convert.call_count == 2


class TestFavoritesManagement:
    """Test favorites management functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_auth = MagicMock(spec=TidalAuth)
        self.mock_auth.ensure_valid_token = AsyncMock(return_value=True)
        self.mock_session = MagicMock(spec=tidalapi.Session)
        self.mock_auth.get_tidal_session.return_value = self.mock_session
        self.service = TidalService(self.mock_auth)

    @pytest.mark.asyncio
    async def test_get_user_favorites_tracks(self):
        """Test getting user favorite tracks."""
        mock_user = MagicMock()
        mock_favorites = MagicMock()
        mock_tracks = [MagicMock(), MagicMock()]
        mock_favorites.tracks.return_value = mock_tracks
        mock_user.favorites = mock_favorites
        self.mock_session.user = mock_user

        with patch.object(self.service, "_convert_tidal_track") as mock_convert:
            mock_track = Track(id="track1", title="Track")
            mock_convert.return_value = mock_track

            result = await self.service.get_user_favorites("tracks", 10, 0)

            assert len(result) == 2
            assert mock_convert.call_count == 2

    @pytest.mark.asyncio
    async def test_get_user_favorites_albums(self):
        """Test getting user favorite albums."""
        mock_user = MagicMock()
        mock_favorites = MagicMock()
        mock_albums = [MagicMock()]
        mock_favorites.albums.return_value = mock_albums
        mock_user.favorites = mock_favorites
        self.mock_session.user = mock_user

        with patch.object(self.service, "_convert_tidal_album") as mock_convert:
            mock_album = Album(id="album1", title="Album")
            mock_convert.return_value = mock_album

            result = await self.service.get_user_favorites("albums", 10, 0)

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_user_favorites_invalid_type(self):
        """Test getting favorites with invalid content type."""
        result = await self.service.get_user_favorites("invalid_type", 10, 0)

        assert result == []

    @pytest.mark.asyncio
    @patch("src.tidal_mcp.service.validate_tidal_id")
    async def test_add_to_favorites_track(self, mock_validate):
        """Test adding track to favorites."""
        mock_validate.return_value = True

        mock_user = MagicMock()
        mock_favorites = MagicMock()
        mock_favorites.add_track.return_value = True
        mock_user.favorites = mock_favorites
        self.mock_session.user = mock_user

        mock_track = MagicMock()
        self.mock_session.track.return_value = mock_track

        result = await self.service.add_to_favorites("123", "track")

        assert result is True
        mock_favorites.add_track.assert_called_once_with(mock_track)

    @pytest.mark.asyncio
    @patch("src.tidal_mcp.service.validate_tidal_id")
    async def test_add_to_favorites_invalid_id(self, mock_validate):
        """Test adding to favorites with invalid ID."""
        mock_validate.return_value = False

        result = await self.service.add_to_favorites("invalid", "track")

        assert result is False

    @pytest.mark.asyncio
    @patch("src.tidal_mcp.service.validate_tidal_id")
    async def test_remove_from_favorites_album(self, mock_validate):
        """Test removing album from favorites."""
        mock_validate.return_value = True

        mock_user = MagicMock()
        mock_favorites = MagicMock()
        mock_favorites.remove_album.return_value = True
        mock_user.favorites = mock_favorites
        self.mock_session.user = mock_user

        mock_album = MagicMock()
        self.mock_session.album.return_value = mock_album

        result = await self.service.remove_from_favorites("456", "album")

        assert result is True
        mock_favorites.remove_album.assert_called_once_with(mock_album)

    @pytest.mark.asyncio
    async def test_add_to_favorites_invalid_content_type(self):
        """Test adding to favorites with invalid content type."""
        result = await self.service.add_to_favorites("123", "invalid_type")

        assert result is False


class TestRecommendationsAndRadio:
    """Test recommendations and radio functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_auth = MagicMock(spec=TidalAuth)
        self.mock_auth.ensure_valid_token = AsyncMock(return_value=True)
        self.mock_session = MagicMock(spec=tidalapi.Session)
        self.mock_auth.get_tidal_session.return_value = self.mock_session
        self.service = TidalService(self.mock_auth)

    @pytest.mark.asyncio
    @patch("src.tidal_mcp.service.validate_tidal_id")
    async def test_get_track_radio_success(self, mock_validate):
        """Test getting track radio successfully."""
        mock_validate.return_value = True

        mock_track = MagicMock()
        mock_radio_tracks = [MagicMock(), MagicMock()]
        mock_track.get_track_radio.return_value = mock_radio_tracks
        self.mock_session.track.return_value = mock_track

        with patch.object(self.service, "_convert_tidal_track") as mock_convert:
            mock_converted_track = Track(id="radio1", title="Radio Track")
            mock_convert.return_value = mock_converted_track

            result = await self.service.get_track_radio("123", 20)

            assert len(result) == 2
            assert mock_convert.call_count == 2

    @pytest.mark.asyncio
    @patch("src.tidal_mcp.service.validate_tidal_id")
    async def test_get_track_radio_invalid_id(self, mock_validate):
        """Test getting track radio with invalid ID."""
        mock_validate.return_value = False

        result = await self.service.get_track_radio("invalid", 20)

        assert result == []

    @pytest.mark.asyncio
    @patch("src.tidal_mcp.service.validate_tidal_id")
    async def test_get_artist_radio_success(self, mock_validate):
        """Test getting artist radio successfully."""
        mock_validate.return_value = True

        mock_artist = MagicMock()
        mock_radio_tracks = [MagicMock()]
        mock_artist.get_radio.return_value = mock_radio_tracks
        self.mock_session.artist.return_value = mock_artist

        with patch.object(self.service, "_convert_tidal_track") as mock_convert:
            mock_converted_track = Track(id="radio1", title="Radio Track")
            mock_convert.return_value = mock_converted_track

            result = await self.service.get_artist_radio("789", 10)

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_recommended_tracks_from_favorites(self):
        """Test getting recommendations from user favorites."""
        mock_user = MagicMock()
        mock_favorites = MagicMock()

        # Mock favorite tracks
        mock_favorite_track = MagicMock()
        mock_radio_tracks = [MagicMock()]
        mock_favorite_track.get_track_radio.return_value = mock_radio_tracks
        mock_favorites.tracks.return_value = [mock_favorite_track]

        mock_user.favorites = mock_favorites
        self.mock_session.user = mock_user

        with patch.object(self.service, "_convert_tidal_track") as mock_convert:
            mock_converted_track = Track(id="rec1", title="Recommended Track")
            mock_convert.return_value = mock_converted_track

            result = await self.service.get_recommended_tracks(10)

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_recommended_tracks_from_featured(self):
        """Test getting recommendations from featured content."""
        mock_user = MagicMock()
        mock_favorites = MagicMock()
        mock_favorites.tracks.side_effect = Exception("No favorites")
        mock_user.favorites = mock_favorites
        self.mock_session.user = mock_user

        # Mock featured content
        mock_featured = MagicMock()
        mock_featured.tracks = [MagicMock()]
        self.mock_session.featured.return_value = mock_featured

        with patch.object(self.service, "_convert_tidal_track") as mock_convert:
            mock_converted_track = Track(id="featured1", title="Featured Track")
            mock_convert.return_value = mock_converted_track

            result = await self.service.get_recommended_tracks(5)

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_recommended_tracks_fallback(self):
        """Test getting recommendations with all fallbacks failing."""
        mock_user = MagicMock()
        mock_favorites = MagicMock()
        mock_favorites.tracks.side_effect = Exception("No favorites")
        mock_user.favorites = mock_favorites
        self.mock_session.user = mock_user

        # Mock featured content failure
        self.mock_session.featured.side_effect = Exception("No featured")

        result = await self.service.get_recommended_tracks(5)

        assert result == []


class TestContentDetailRetrieval:
    """Test detailed content retrieval functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_auth = MagicMock(spec=TidalAuth)
        self.mock_auth.ensure_valid_token = AsyncMock(return_value=True)
        self.mock_session = MagicMock(spec=tidalapi.Session)
        self.mock_auth.get_tidal_session.return_value = self.mock_session
        self.service = TidalService(self.mock_auth)

    @pytest.mark.asyncio
    @patch("src.tidal_mcp.service.validate_tidal_id")
    async def test_get_track_success(self, mock_validate):
        """Test getting track details successfully."""
        mock_validate.return_value = True

        mock_tidal_track = MagicMock()
        self.mock_session.track.return_value = mock_tidal_track

        with patch.object(self.service, "_convert_tidal_track") as mock_convert:
            mock_track = Track(id="123", title="Test Track")
            mock_convert.return_value = mock_track

            result = await self.service.get_track("123")

            assert result.title == "Test Track"

    @pytest.mark.asyncio
    @patch("src.tidal_mcp.service.validate_tidal_id")
    async def test_get_track_invalid_id(self, mock_validate):
        """Test getting track with invalid ID."""
        mock_validate.return_value = False

        result = await self.service.get_track("invalid")

        assert result is None

    @pytest.mark.asyncio
    @patch("src.tidal_mcp.service.validate_tidal_id")
    async def test_get_album_with_tracks(self, mock_validate):
        """Test getting album with tracks included."""
        mock_validate.return_value = True

        mock_tidal_album = MagicMock()
        self.mock_session.album.return_value = mock_tidal_album

        with patch.object(self.service, "_convert_tidal_album") as mock_convert:
            mock_album = Album(id="456", title="Test Album")
            mock_convert.return_value = mock_album

            result = await self.service.get_album("456", True)

            assert result.title == "Test Album"
            mock_convert.assert_called_once_with(mock_tidal_album, include_tracks=True)

    @pytest.mark.asyncio
    @patch("src.tidal_mcp.service.validate_tidal_id")
    async def test_get_artist_success(self, mock_validate):
        """Test getting artist successfully."""
        mock_validate.return_value = True

        mock_tidal_artist = MagicMock()
        self.mock_session.artist.return_value = mock_tidal_artist

        with patch.object(self.service, "_convert_tidal_artist") as mock_convert:
            mock_artist = Artist(id="789", name="Test Artist")
            mock_convert.return_value = mock_artist

            result = await self.service.get_artist("789")

            assert result.name == "Test Artist"

    @pytest.mark.asyncio
    @patch("src.tidal_mcp.service.validate_tidal_id")
    async def test_get_album_tracks(self, mock_validate):
        """Test getting tracks from an album."""
        mock_validate.return_value = True

        mock_album = MagicMock()
        mock_tidal_tracks = [MagicMock(), MagicMock()]
        mock_album.tracks.return_value = mock_tidal_tracks
        self.mock_session.album.return_value = mock_album

        with patch.object(self.service, "_convert_tidal_track") as mock_convert:
            mock_track = Track(id="track1", title="Track")
            mock_convert.return_value = mock_track

            result = await self.service.get_album_tracks("456", 50, 0)

            assert len(result) == 2

    @pytest.mark.asyncio
    @patch("src.tidal_mcp.service.validate_tidal_id")
    async def test_get_artist_albums(self, mock_validate):
        """Test getting albums by an artist."""
        mock_validate.return_value = True

        mock_artist = MagicMock()
        mock_tidal_albums = [MagicMock()]
        mock_artist.get_albums.return_value = mock_tidal_albums
        self.mock_session.artist.return_value = mock_artist

        with patch.object(self.service, "_convert_tidal_album") as mock_convert:
            mock_album = Album(id="album1", title="Album")
            mock_convert.return_value = mock_album

            result = await self.service.get_artist_albums("789", 20, 0)

            assert len(result) == 1

    @pytest.mark.asyncio
    @patch("src.tidal_mcp.service.validate_tidal_id")
    async def test_get_artist_top_tracks(self, mock_validate):
        """Test getting top tracks by an artist."""
        mock_validate.return_value = True

        mock_artist = MagicMock()
        mock_top_tracks = [MagicMock()]
        mock_artist.get_top_tracks.return_value = mock_top_tracks
        self.mock_session.artist.return_value = mock_artist

        with patch.object(self.service, "_convert_tidal_track") as mock_convert:
            mock_track = Track(id="top1", title="Top Track")
            mock_convert.return_value = mock_track

            result = await self.service.get_artist_top_tracks("789", 10)

            assert len(result) == 1


class TestUserProfile:
    """Test user profile functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_auth = MagicMock(spec=TidalAuth)
        self.mock_auth.ensure_valid_token = AsyncMock(return_value=True)
        self.service = TidalService(self.mock_auth)

    @pytest.mark.asyncio
    async def test_get_user_profile_success(self):
        """Test getting user profile successfully."""
        mock_user_info = {"id": "123", "username": "testuser", "country_code": "US"}
        self.mock_auth.get_user_info.return_value = mock_user_info

        result = await self.service.get_user_profile()

        assert result == mock_user_info
        self.mock_auth.get_user_info.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_profile_none(self):
        """Test getting user profile when None returned."""
        self.mock_auth.get_user_info.return_value = None

        result = await self.service.get_user_profile()

        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_profile_exception(self):
        """Test getting user profile with exception."""
        self.mock_auth.get_user_info.side_effect = Exception("Profile error")

        result = await self.service.get_user_profile()

        assert result is None


class TestModelConversion:
    """Test model conversion methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_auth = MagicMock(spec=TidalAuth)
        self.service = TidalService(self.mock_auth)

    @pytest.mark.asyncio
    async def test_convert_tidal_track_complete(self):
        """Test converting complete tidal track to Track model."""
        # Mock tidal track with all fields
        mock_tidal_track = MagicMock()
        mock_tidal_track.id = 123
        mock_tidal_track.name = "Test Track"
        mock_tidal_track.duration = 240
        mock_tidal_track.track_num = 5
        mock_tidal_track.volume_num = 1
        mock_tidal_track.explicit = True
        mock_tidal_track.audio_quality = "LOSSLESS"

        # Mock artists
        mock_artist = MagicMock()
        mock_artist.id = 456
        mock_artist.name = "Test Artist"
        mock_artist.picture = "artist.jpg"
        mock_artist.popularity = 85
        mock_tidal_track.artists = [mock_artist]

        # Mock album
        mock_album = MagicMock()
        mock_album.id = 789
        mock_album.name = "Test Album"
        mock_album.release_date = "2023-01-01"
        mock_album.duration = 3600
        mock_album.num_tracks = 12
        mock_album.image = "album.jpg"
        mock_album.explicit = False
        mock_album.artists = [mock_artist]
        mock_tidal_track.album = mock_album

        result = await self.service._convert_tidal_track(mock_tidal_track)

        assert result.id == "123"
        assert result.title == "Test Track"
        assert result.duration == 240
        assert result.track_number == 5
        assert result.disc_number == 1
        assert result.explicit is True
        assert result.quality == "LOSSLESS"
        assert len(result.artists) == 1
        assert result.artists[0].name == "Test Artist"
        assert result.album.title == "Test Album"

    @pytest.mark.asyncio
    async def test_convert_tidal_track_with_single_artist(self):
        """Test converting tidal track with single artist."""
        mock_tidal_track = MagicMock()
        mock_tidal_track.id = 123
        mock_tidal_track.name = "Test Track"

        # Single artist instead of list
        mock_artist = MagicMock()
        mock_artist.id = 456
        mock_artist.name = "Single Artist"
        mock_tidal_track.artist = mock_artist
        mock_tidal_track.artists = None

        # No album
        mock_tidal_track.album = None

        result = await self.service._convert_tidal_track(mock_tidal_track)

        assert len(result.artists) == 1
        assert result.artists[0].name == "Single Artist"
        assert result.album is None

    @pytest.mark.asyncio
    async def test_convert_tidal_track_with_exception(self):
        """Test converting tidal track with exception."""
        mock_tidal_track = MagicMock()
        mock_tidal_track.id.side_effect = Exception("Conversion error")

        result = await self.service._convert_tidal_track(mock_tidal_track)

        assert result is None

    @pytest.mark.asyncio
    async def test_convert_tidal_album_complete(self):
        """Test converting complete tidal album to Album model."""
        mock_tidal_album = MagicMock()
        mock_tidal_album.id = 456
        mock_tidal_album.name = "Test Album"
        mock_tidal_album.release_date = "2023-01-01"
        mock_tidal_album.duration = 3600
        mock_tidal_album.num_tracks = 12
        mock_tidal_album.image = "album.jpg"
        mock_tidal_album.explicit = False

        # Mock artists
        mock_artist = MagicMock()
        mock_artist.id = 123
        mock_artist.name = "Album Artist"
        mock_tidal_album.artists = [mock_artist]

        result = await self.service._convert_tidal_album(mock_tidal_album)

        assert result.id == "456"
        assert result.title == "Test Album"
        assert result.release_date == "2023-01-01"
        assert result.duration == 3600
        assert result.number_of_tracks == 12
        assert result.cover == "album.jpg"
        assert result.explicit is False
        assert len(result.artists) == 1
        assert result.artists[0].name == "Album Artist"

    @pytest.mark.asyncio
    async def test_convert_tidal_artist_complete(self):
        """Test converting tidal artist to Artist model."""
        mock_tidal_artist = MagicMock()
        mock_tidal_artist.id = 789
        mock_tidal_artist.name = "Test Artist"
        mock_tidal_artist.picture = "artist.jpg"
        mock_tidal_artist.popularity = 90

        result = await self.service._convert_tidal_artist(mock_tidal_artist)

        assert result.id == "789"
        assert result.name == "Test Artist"
        assert result.picture == "artist.jpg"
        assert result.popularity == 90

    @pytest.mark.asyncio
    async def test_convert_tidal_playlist_with_tracks(self):
        """Test converting tidal playlist with tracks."""
        mock_tidal_playlist = MagicMock()
        mock_tidal_playlist.uuid = "abc-123"
        mock_tidal_playlist.name = "Test Playlist"
        mock_tidal_playlist.description = "A test playlist"
        mock_tidal_playlist.num_tracks = 5
        mock_tidal_playlist.duration = 1200
        mock_tidal_playlist.created = "2023-01-01"
        mock_tidal_playlist.last_updated = "2023-01-02"
        mock_tidal_playlist.image = "playlist.jpg"
        mock_tidal_playlist.public = True

        # Mock creator
        mock_tidal_playlist.creator = {"name": "Playlist Creator"}

        # Mock tracks method
        mock_track = MagicMock()
        mock_track.id = 123
        mock_track.name = "Playlist Track"
        mock_tidal_playlist.tracks.return_value = [mock_track]

        with patch.object(self.service, "_convert_tidal_track") as mock_convert_track:
            mock_converted_track = Track(id="123", title="Playlist Track")
            mock_convert_track.return_value = mock_converted_track

            result = await self.service._convert_tidal_playlist(
                mock_tidal_playlist, True
            )

            assert result.id == "abc-123"
            assert result.title == "Test Playlist"
            assert result.description == "A test playlist"
            assert result.creator == "Playlist Creator"
            assert len(result.tracks) == 1
            assert result.tracks[0].title == "Playlist Track"

    @pytest.mark.asyncio
    async def test_convert_tidal_playlist_without_tracks(self):
        """Test converting tidal playlist without tracks."""
        mock_tidal_playlist = MagicMock()
        mock_tidal_playlist.uuid = "abc-123"
        mock_tidal_playlist.name = "Test Playlist"

        result = await self.service._convert_tidal_playlist(mock_tidal_playlist, False)

        assert result.id == "abc-123"
        assert result.title == "Test Playlist"
        assert result.tracks == []

    def test_is_uuid_valid(self):
        """Test UUID validation."""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        invalid_uuid = "not-a-uuid"

        assert self.service._is_uuid(valid_uuid) is True
        assert self.service._is_uuid(invalid_uuid) is False
        assert self.service._is_uuid("") is False

    def test_is_uuid_case_insensitive(self):
        """Test UUID validation is case insensitive."""
        upper_uuid = "550E8400-E29B-41D4-A716-446655440000"
        lower_uuid = "550e8400-e29b-41d4-a716-446655440000"

        assert self.service._is_uuid(upper_uuid) is True
        assert self.service._is_uuid(lower_uuid) is True


class TestServiceErrorHandling:
    """Test error handling throughout the service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_auth = MagicMock(spec=TidalAuth)
        self.mock_auth.ensure_valid_token = AsyncMock(return_value=True)
        self.mock_session = MagicMock(spec=tidalapi.Session)
        self.mock_auth.get_tidal_session.return_value = self.mock_session
        self.service = TidalService(self.mock_auth)

    @pytest.mark.asyncio
    async def test_search_tracks_with_session_error(self):
        """Test search tracks handles session errors gracefully."""
        self.mock_session.search.side_effect = Exception("Session error")

        with patch("src.tidal_mcp.service.sanitize_query", return_value="query"):
            result = await self.service.search_tracks("query")

            assert result == []

    @pytest.mark.asyncio
    async def test_get_playlist_with_session_error(self):
        """Test get playlist handles session errors gracefully."""
        self.mock_session.playlist.side_effect = Exception("Session error")

        with patch("src.tidal_mcp.service.validate_tidal_id", return_value=True):
            result = await self.service.get_playlist("playlist-123")

            assert result is None

    @pytest.mark.asyncio
    async def test_create_playlist_with_session_error(self):
        """Test create playlist handles session errors gracefully."""
        mock_user = MagicMock()
        mock_user.create_playlist.side_effect = Exception("Session error")
        self.mock_session.user = mock_user

        result = await self.service.create_playlist("Test Playlist")

        assert result is None

    @pytest.mark.asyncio
    async def test_add_tracks_to_playlist_with_session_error(self):
        """Test add tracks to playlist handles session errors gracefully."""
        self.mock_session.playlist.side_effect = Exception("Session error")

        with patch("src.tidal_mcp.service.validate_tidal_id", return_value=True):
            result = await self.service.add_tracks_to_playlist(
                "playlist-123", ["track-456"]
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_get_user_favorites_with_session_error(self):
        """Test get user favorites handles session errors gracefully."""
        mock_user = MagicMock()
        mock_favorites = MagicMock()
        mock_favorites.tracks.side_effect = Exception("Session error")
        mock_user.favorites = mock_favorites
        self.mock_session.user = mock_user

        result = await self.service.get_user_favorites("tracks")

        assert result == []
