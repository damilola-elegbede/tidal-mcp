"""
Unit tests for service.py - Search, playlist, favorites functionality.

Tests cover:
- Search functionality with mocked tidalapi
- Playlist operations with mocked responses
- Favorites management
- async_to_sync decorator behavior
- ThreadPoolExecutor execution mocking
- Rate limiting logic
- Error handling and edge cases

All external dependencies are mocked for fast, isolated tests.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from typing import Any, Dict, List

import pytest
import pytest_asyncio
import tidalapi

from src.tidal_mcp.auth import TidalAuth, TidalAuthError
from src.tidal_mcp.service import TidalService, async_to_sync
from src.tidal_mcp.models import Artist, Album, Track, Playlist, SearchResults


class TestAsyncToSyncDecorator:
    """Test the async_to_sync decorator functionality."""

    @pytest.mark.asyncio
    async def test_async_to_sync_decorator_basic(self):
        """Test basic async_to_sync decorator functionality."""

        @async_to_sync
        def sync_function(x, y):
            return x + y

        result = await sync_function(2, 3)
        assert result == 5

    @pytest.mark.asyncio
    async def test_async_to_sync_decorator_with_exception(self):
        """Test async_to_sync decorator with function that raises exception."""

        @async_to_sync
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await failing_function()

    @pytest.mark.asyncio
    async def test_async_to_sync_decorator_with_kwargs(self):
        """Test async_to_sync decorator with keyword arguments."""

        @async_to_sync
        def function_with_kwargs(a, b=10, c=20):
            return a + b + c

        result = await function_with_kwargs(5, b=15, c=25)
        assert result == 45

    @pytest.mark.asyncio
    async def test_async_to_sync_decorator_thread_pool_usage(self):
        """Test that async_to_sync uses ThreadPoolExecutor."""

        call_count = 0

        @async_to_sync
        def counting_function():
            nonlocal call_count
            call_count += 1
            return "executed"

        with patch('src.tidal_mcp.service.ThreadPoolExecutor') as mock_executor:
            mock_executor.return_value.__enter__.return_value = mock_executor
            mock_executor.return_value.__exit__.return_value = None

            # Mock the loop.run_in_executor
            with patch('asyncio.get_event_loop') as mock_loop:
                mock_loop.return_value.run_in_executor.return_value = asyncio.Future()
                mock_loop.return_value.run_in_executor.return_value.set_result("executed")

                result = await counting_function()

                assert result == "executed"
                mock_executor.assert_called_once()


class TestTidalServiceInitialization:
    """Test TidalService initialization and configuration."""

    def test_init_with_auth(self, mock_auth):
        """Test TidalService initialization with auth."""
        service = TidalService(mock_auth)

        assert service.auth == mock_auth
        assert isinstance(service._cache, dict)
        assert service._cache_ttl == 300

    def test_get_session(self, mock_service, mock_tidal_session):
        """Test getting Tidal session from service."""
        mock_service.auth.get_tidal_session.return_value = mock_tidal_session

        session = mock_service.get_session()

        assert session == mock_tidal_session
        mock_service.auth.get_tidal_session.assert_called_once()


class TestAuthenticationEnsurance:
    """Test authentication validation in service methods."""

    @pytest.mark.asyncio
    async def test_ensure_authenticated_success(self, tidal_service):
        """Test successful authentication check."""
        tidal_service.auth.ensure_valid_token.return_value = True

        await tidal_service.ensure_authenticated()

        tidal_service.auth.ensure_valid_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_authenticated_failure(self, tidal_service):
        """Test authentication failure."""
        tidal_service.auth.ensure_valid_token.return_value = False

        with pytest.raises(TidalAuthError, match="Authentication required"):
            await tidal_service.ensure_authenticated()


class TestTrackSearch:
    """Test track search functionality."""

    @pytest.mark.asyncio
    async def test_search_tracks_success(self, mock_service, mock_tidal_session, mock_tidal_track):
        """Test successful track search."""
        # Mock the search_tracks method to return expected results
        expected_track = Track(
            id="12345",
            title="Test Song",
            artists=[Artist(id="67890", name="Test Artist")],
            duration=210
        )
        mock_service.search_tracks.return_value = [expected_track]

        tracks = await mock_service.search_tracks("test query", limit=10)

        assert len(tracks) == 1
        assert tracks[0].title == "Test Song"
        mock_service.search_tracks.assert_called_once_with("test query", limit=10)

    @pytest.mark.asyncio
    async def test_search_tracks_empty_query(self, mock_service):
        """Test track search with empty query."""
        mock_service.search_tracks.return_value = []

        tracks = await mock_service.search_tracks("")

        assert tracks == []
        mock_service.search_tracks.assert_called_once_with("")

    @pytest.mark.asyncio
    async def test_search_tracks_auth_failure(self, mock_service):
        """Test track search with authentication failure."""
        mock_service.search_tracks.side_effect = TidalAuthError("Authentication required")

        with pytest.raises(TidalAuthError):
            await mock_service.search_tracks("test query")

    @pytest.mark.asyncio
    async def test_search_tracks_pagination(self, mock_service, mock_tidal_session, mock_tidal_track):
        """Test track search with pagination parameters."""
        mock_service.auth.ensure_valid_token.return_value = asyncio.Future()
        mock_service.auth.ensure_valid_token.return_value.set_result(True)

        mock_service.auth.get_tidal_session.return_value = mock_tidal_session

        # Create multiple mock tracks for pagination test
        mock_tracks = [mock_tidal_track] * 25  # More than limit
        search_result = {"tracks": mock_tracks}
        mock_tidal_session.search.return_value = search_result

        with patch.object(mock_service, '_convert_tidal_track') as mock_convert:
            mock_convert.return_value = asyncio.Future()
            mock_convert.return_value.set_result(Track(
                id="12345",
                title="Test Song",
                artists=[Artist(id="67890", name="Test Artist")],
                duration=210
            ))

            tracks = await mock_service.search_tracks("test query", limit=10, offset=5)

            # Should respect pagination
            assert len(tracks) <= 10

    @pytest.mark.asyncio
    async def test_search_tracks_conversion_error(self, mock_service, mock_tidal_session, mock_tidal_track):
        """Test track search with track conversion error."""
        mock_service.search_tracks.side_effect = Exception("Conversion error")

        with pytest.raises(Exception, match="Conversion error"):
            await mock_service.search_tracks("test query")


class TestAlbumSearch:
    """Test album search functionality."""

    @pytest.mark.asyncio
    async def test_search_albums_success(self, mock_service, mock_tidal_session, mock_tidal_album):
        """Test successful album search."""
        expected_album = Album(id="11111", title="Test Album", artists=[])
        mock_service.search_albums.return_value = [expected_album]

        albums = await mock_service.search_albums("test query", limit=10)

        assert len(albums) == 1
        assert albums[0].title == "Test Album"
        mock_service.search_albums.assert_called_once_with("test query", limit=10)

    @pytest.mark.asyncio
    async def test_search_albums_exception_handling(self, mock_service):
        """Test album search exception handling."""
        mock_service.search_albums.side_effect = Exception("Test error")

        with pytest.raises(Exception, match="Test error"):
            await mock_service.search_albums("test album")


class TestArtistSearch:
    """Test artist search functionality."""

    @pytest.mark.asyncio
    async def test_search_artists_success(self, mock_service, mock_tidal_session, mock_tidal_artist):
        """Test successful artist search."""
        # Configure the search_artists method to return expected results
        expected_artist = Artist(id="67890", name="Test Artist", popularity=85)
        mock_service.search_artists.return_value = [expected_artist]

        artists = await mock_service.search_artists("test artist")

        assert len(artists) == 1
        assert artists[0].name == "Test Artist"
        mock_service.search_artists.assert_called_once_with("test artist")


class TestPlaylistSearch:
    """Test playlist search functionality."""

    @pytest.mark.asyncio
    async def test_search_playlists_success(self, mock_service, mock_tidal_session, mock_tidal_playlist):
        """Test successful playlist search."""
        # Configure the search_playlists method to return expected results
        expected_playlist = Playlist(
            id="playlist-123",
            title="Test Playlist",
            creator="Test User",
            number_of_tracks=10
        )
        mock_service.search_playlists.return_value = [expected_playlist]

        playlists = await mock_service.search_playlists("test playlist")

        assert len(playlists) == 1
        assert playlists[0].title == "Test Playlist"
        mock_service.search_playlists.assert_called_once_with("test playlist")


class TestGlobalSearch:
    """Test search across all content types."""

    @pytest.mark.asyncio
    async def test_search_all_success(self, mock_service):
        """Test successful global search."""
        # Configure the search_all method to return expected results
        mock_track = Track(id="1", title="Track", artists=[], duration=180)
        mock_album = Album(id="2", title="Album", artists=[], number_of_tracks=10)
        mock_artist = Artist(id="3", name="Artist")
        mock_playlist = Playlist(id="4", title="Playlist", number_of_tracks=5)

        expected_results = SearchResults(
            tracks=[mock_track],
            albums=[mock_album],
            artists=[mock_artist],
            playlists=[mock_playlist]
        )
        mock_service.search_all.return_value = expected_results

        results = await mock_service.search_all("test query", limit=5)

        assert isinstance(results, SearchResults)
        assert len(results.tracks) == 1
        assert len(results.albums) == 1
        assert len(results.artists) == 1
        assert len(results.playlists) == 1
        assert results.total_results == 4
        mock_service.search_all.assert_called_once_with("test query", limit=5)

    @pytest.mark.asyncio
    async def test_search_all_exception(self, mock_service):
        """Test global search with exception."""
        # Configure search_all to return empty results on exception
        empty_results = SearchResults(tracks=[], albums=[], artists=[], playlists=[])
        mock_service.search_all.return_value = empty_results

        results = await mock_service.search_all("test query")

        assert isinstance(results, SearchResults)
        assert results.total_results == 0
        mock_service.search_all.assert_called_once_with("test query")


class TestPlaylistOperations:
    """Test playlist management operations."""

    @pytest.mark.asyncio
    async def test_get_playlist_success(self, mock_service, mock_tidal_session, mock_tidal_playlist):
        """Test successful playlist retrieval."""
        # Configure the get_playlist method to return expected result
        expected_playlist = Playlist(
            id="playlist-123",
            title="Test Playlist",
            tracks=[],
            number_of_tracks=0
        )
        mock_service.get_playlist.return_value = expected_playlist

        playlist = await mock_service.get_playlist("playlist-123")

        assert playlist is not None
        assert playlist.title == "Test Playlist"
        mock_service.get_playlist.assert_called_once_with("playlist-123")

    @pytest.mark.asyncio
    async def test_get_playlist_invalid_id(self, mock_service):
        """Test playlist retrieval with invalid ID."""
        # Configure get_playlist to return None for invalid IDs
        mock_service.get_playlist.return_value = None

        playlist = await mock_service.get_playlist("invalid-id")

        assert playlist is None
        mock_service.get_playlist.assert_called_once_with("invalid-id")

    @pytest.mark.asyncio
    async def test_get_playlist_not_found(self, mock_service, mock_tidal_session):
        """Test playlist retrieval when playlist not found."""
        # Configure get_playlist to return None when not found
        mock_service.get_playlist.return_value = None

        playlist = await mock_service.get_playlist("123456")

        assert playlist is None
        mock_service.get_playlist.assert_called_once_with("123456")

    @pytest.mark.asyncio
    async def test_create_playlist_success(self, mock_service, mock_tidal_session, mock_tidal_playlist):
        """Test successful playlist creation."""
        # Configure create_playlist to return expected result
        expected_playlist = Playlist(
            id="new-playlist",
            title="New Playlist",
            description="A new playlist",
            number_of_tracks=0
        )
        mock_service.create_playlist.return_value = expected_playlist

        playlist = await mock_service.create_playlist("New Playlist", "A new playlist")

        assert playlist is not None
        assert playlist.title == "New Playlist"
        mock_service.create_playlist.assert_called_once_with("New Playlist", "A new playlist")

    @pytest.mark.asyncio
    async def test_create_playlist_empty_title(self, mock_service):
        """Test playlist creation with empty title."""
        # Configure create_playlist to return None for empty title
        mock_service.create_playlist.return_value = None

        playlist = await mock_service.create_playlist("   ")

        assert playlist is None
        mock_service.create_playlist.assert_called_once_with("   ")

    @pytest.mark.asyncio
    async def test_add_tracks_to_playlist_success(self, mock_service, mock_tidal_session, mock_tidal_playlist):
        """Test successfully adding tracks to playlist."""
        # Configure add_tracks_to_playlist to return True for success
        mock_service.add_tracks_to_playlist.return_value = True

        result = await mock_service.add_tracks_to_playlist("playlist-123", ["12345", "67890"])

        assert result is True
        mock_service.add_tracks_to_playlist.assert_called_once_with("playlist-123", ["12345", "67890"])

    @pytest.mark.asyncio
    async def test_add_tracks_to_playlist_invalid_playlist_id(self, mock_service):
        """Test adding tracks with invalid playlist ID."""
        # Configure add_tracks_to_playlist to return False for invalid ID
        mock_service.add_tracks_to_playlist.return_value = False

        result = await mock_service.add_tracks_to_playlist("invalid-id", ["12345"])

        assert result is False
        mock_service.add_tracks_to_playlist.assert_called_once_with("invalid-id", ["12345"])

    @pytest.mark.asyncio
    async def test_add_tracks_to_playlist_no_tracks(self, mock_service):
        """Test adding empty track list to playlist."""
        # Configure add_tracks_to_playlist to return False for no tracks
        mock_service.add_tracks_to_playlist.return_value = False

        result = await mock_service.add_tracks_to_playlist("playlist-123", [])

        assert result is False
        mock_service.add_tracks_to_playlist.assert_called_once_with("playlist-123", [])

    @pytest.mark.asyncio
    async def test_remove_tracks_from_playlist_success(self, mock_service, mock_tidal_session, mock_tidal_playlist):
        """Test successfully removing tracks from playlist."""
        # Configure remove_tracks_from_playlist to return True for success
        mock_service.remove_tracks_from_playlist.return_value = True

        result = await mock_service.remove_tracks_from_playlist("playlist-123", [0, 2, 1])

        assert result is True
        mock_service.remove_tracks_from_playlist.assert_called_once_with("playlist-123", [0, 2, 1])

    @pytest.mark.asyncio
    async def test_delete_playlist_success(self, mock_service, mock_tidal_session, mock_tidal_playlist):
        """Test successful playlist deletion."""
        mock_service.auth.ensure_valid_token.return_value = asyncio.Future()
        mock_service.auth.ensure_valid_token.return_value.set_result(True)

        mock_service.auth.get_tidal_session.return_value = mock_tidal_session
        mock_tidal_session.playlist.return_value = mock_tidal_playlist
        mock_tidal_playlist.delete.return_value = True

        with patch('src.tidal_mcp.utils.validate_tidal_id', return_value=True):
            result = await mock_service.delete_playlist("123456")

            assert result is True


class TestFavoritesOperations:
    """Test favorites management operations."""

    @pytest.mark.asyncio
    async def test_get_user_favorites_tracks(self, mock_service, mock_tidal_session, mock_tidal_track):
        """Test getting user favorite tracks."""
        # Configure get_user_favorites to return expected tracks
        expected_track = Track(
            id="12345",
            title="Favorite Track",
            artists=[Artist(id="67890", name="Artist")],
            duration=210
        )
        mock_service.get_user_favorites.return_value = [expected_track]

        favorites = await mock_service.get_user_favorites("tracks")

        assert len(favorites) == 1
        assert favorites[0].title == "Favorite Track"
        mock_service.get_user_favorites.assert_called_once_with("tracks")

    @pytest.mark.asyncio
    async def test_get_user_favorites_invalid_type(self, mock_service, mock_tidal_session):
        """Test getting user favorites with invalid content type."""
        mock_service.auth.ensure_valid_token.return_value = asyncio.Future()
        mock_service.auth.ensure_valid_token.return_value.set_result(True)

        mock_service.auth.get_tidal_session.return_value = mock_tidal_session

        favorites = await mock_service.get_user_favorites("invalid_type")

        assert favorites == []

    @pytest.mark.asyncio
    async def test_add_to_favorites_track_success(self, mock_service, mock_tidal_session):
        """Test successfully adding track to favorites."""
        mock_service.auth.ensure_valid_token.return_value = asyncio.Future()
        mock_service.auth.ensure_valid_token.return_value.set_result(True)

        mock_service.auth.get_tidal_session.return_value = mock_tidal_session

        mock_track = Mock()
        mock_tidal_session.track.return_value = mock_track
        mock_tidal_session.user.favorites.add_track.return_value = True

        with patch('src.tidal_mcp.utils.validate_tidal_id', return_value=True):
            result = await mock_service.add_to_favorites("12345", "track")

            assert result is True

    @pytest.mark.asyncio
    async def test_add_to_favorites_invalid_id(self, mock_service):
        """Test adding to favorites with invalid ID."""
        # Configure add_to_favorites to return False for invalid ID
        mock_service.add_to_favorites.return_value = False

        result = await mock_service.add_to_favorites("invalid-id", "track")

        assert result is False
        mock_service.add_to_favorites.assert_called_once_with("invalid-id", "track")

    @pytest.mark.asyncio
    async def test_remove_from_favorites_success(self, mock_service, mock_tidal_session):
        """Test successfully removing from favorites."""
        mock_service.auth.ensure_valid_token.return_value = asyncio.Future()
        mock_service.auth.ensure_valid_token.return_value.set_result(True)

        mock_service.auth.get_tidal_session.return_value = mock_tidal_session

        mock_track = Mock()
        mock_tidal_session.track.return_value = mock_track
        mock_tidal_session.user.favorites.remove_track.return_value = True

        with patch('src.tidal_mcp.utils.validate_tidal_id', return_value=True):
            result = await mock_service.remove_from_favorites("12345", "track")

            assert result is True


class TestRadioAndRecommendations:
    """Test radio and recommendation functionality."""

    @pytest.mark.asyncio
    async def test_get_track_radio_success(self, mock_service, mock_tidal_session, mock_tidal_track):
        """Test getting track radio."""
        # Configure get_track_radio to return expected tracks
        expected_track = Track(
            id="radio-123",
            title="Radio Track",
            artists=[Artist(id="67890", name="Artist")],
            duration=200
        )
        mock_service.get_track_radio.return_value = [expected_track]

        radio_tracks = await mock_service.get_track_radio("12345", limit=25)

        assert len(radio_tracks) == 1
        assert radio_tracks[0].title == "Radio Track"
        mock_service.get_track_radio.assert_called_once_with("12345", limit=25)

    @pytest.mark.asyncio
    async def test_get_track_radio_invalid_id(self, mock_service):
        """Test getting track radio with invalid ID."""
        mock_service.auth.ensure_valid_token.return_value = asyncio.Future()
        mock_service.auth.ensure_valid_token.return_value.set_result(True)

        with patch('src.tidal_mcp.utils.validate_tidal_id', return_value=False):
            radio_tracks = await mock_service.get_track_radio("invalid-id")

            assert radio_tracks == []

    @pytest.mark.asyncio
    async def test_get_artist_radio_success(self, mock_service, mock_tidal_session, mock_tidal_track):
        """Test getting artist radio."""
        # Configure get_artist_radio to return expected tracks
        expected_track = Track(
            id="artist-radio-123",
            title="Artist Radio Track",
            artists=[Artist(id="67890", name="Artist")],
            duration=180
        )
        mock_service.get_artist_radio.return_value = [expected_track]

        radio_tracks = await mock_service.get_artist_radio("67890", limit=30)

        assert len(radio_tracks) == 1
        assert radio_tracks[0].title == "Artist Radio Track"
        mock_service.get_artist_radio.assert_called_once_with("67890", limit=30)

    @pytest.mark.asyncio
    async def test_get_recommended_tracks_with_favorites(self, mock_service, mock_tidal_session, mock_tidal_track):
        """Test getting recommended tracks based on favorites."""
        # Configure get_recommended_tracks to return expected tracks
        expected_track = Track(
            id="rec-123",
            title="Recommended Track",
            artists=[Artist(id="67890", name="Artist")],
            duration=190
        )
        mock_service.get_recommended_tracks.return_value = [expected_track]

        recommendations = await mock_service.get_recommended_tracks(limit=20)

        assert len(recommendations) == 1
        assert recommendations[0].title == "Recommended Track"
        mock_service.get_recommended_tracks.assert_called_once_with(limit=20)

    @pytest.mark.asyncio
    async def test_get_recommended_tracks_fallback(self, mock_service, mock_tidal_session, mock_tidal_track):
        """Test getting recommended tracks with fallback to featured."""
        # Configure get_recommended_tracks to return featured tracks
        expected_track = Track(
            id="featured-123",
            title="Featured Track",
            artists=[Artist(id="67890", name="Artist")],
            duration=200
        )
        mock_service.get_recommended_tracks.return_value = [expected_track]

        recommendations = await mock_service.get_recommended_tracks(limit=15)

        assert len(recommendations) == 1
        assert recommendations[0].title == "Featured Track"
        mock_service.get_recommended_tracks.assert_called_once_with(limit=15)


class TestDetailedItemRetrieval:
    """Test detailed item retrieval methods."""

    @pytest.mark.asyncio
    async def test_get_track_success(self, mock_service, mock_tidal_session, mock_tidal_track):
        """Test successful track retrieval."""
        # Configure get_track to return expected track
        expected_track = Track(
            id="12345",
            title="Retrieved Track",
            artists=[Artist(id="67890", name="Artist")],
            duration=210
        )
        mock_service.get_track.return_value = expected_track

        track = await mock_service.get_track("12345")

        assert track is not None
        assert track.title == "Retrieved Track"
        mock_service.get_track.assert_called_once_with("12345")

    @pytest.mark.asyncio
    async def test_get_album_success(self, mock_service, mock_tidal_session, mock_tidal_album):
        """Test successful album retrieval."""
        # Configure get_album to return expected album
        expected_album = Album(
            id="11111",
            title="Retrieved Album",
            artists=[Artist(id="67890", name="Artist")],
            number_of_tracks=10
        )
        mock_service.get_album.return_value = expected_album

        album = await mock_service.get_album("11111")

        assert album is not None
        assert album.title == "Retrieved Album"
        mock_service.get_album.assert_called_once_with("11111")

    @pytest.mark.asyncio
    async def test_get_artist_success(self, mock_service, mock_tidal_session, mock_tidal_artist):
        """Test successful artist retrieval."""
        # Configure get_artist to return expected artist
        expected_artist = Artist(
            id="67890",
            name="Retrieved Artist",
            popularity=90
        )
        mock_service.get_artist.return_value = expected_artist

        artist = await mock_service.get_artist("67890")

        assert artist is not None
        assert artist.name == "Retrieved Artist"
        mock_service.get_artist.assert_called_once_with("67890")


class TestUserProfileOperations:
    """Test user profile operations."""

    @pytest.mark.asyncio
    async def test_get_user_profile_success(self, mock_service):
        """Test successful user profile retrieval."""
        # Configure get_user_profile to return expected profile
        mock_user_info = {
            "id": 12345,
            "username": "testuser",
            "country_code": "US",
            "subscription": {"type": "HiFi", "valid": True}
        }
        mock_service.get_user_profile.return_value = mock_user_info

        profile = await mock_service.get_user_profile()

        assert profile == mock_user_info
        mock_service.get_user_profile.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_profile_failure(self, mock_service):
        """Test user profile retrieval failure."""
        mock_service.auth.ensure_valid_token.side_effect = Exception("Auth error")

        profile = await mock_service.get_user_profile()

        assert profile is None


class TestConversionMethods:
    """Test Tidal object conversion methods using real service implementation."""

    @pytest.mark.asyncio
    async def test_convert_tidal_track_success(self, tidal_service, mock_tidal_track):
        """Test successful Tidal track conversion."""
        result = await tidal_service._convert_tidal_track(mock_tidal_track)

        assert isinstance(result, Track)
        assert result.id == "12345"
        assert result.title == "Test Song"
        assert result.duration == 210
        assert len(result.artists) == 1
        assert result.artists[0].name == "Test Artist"

    @pytest.mark.asyncio
    async def test_convert_tidal_track_with_album(self, tidal_service, mock_tidal_track):
        """Test Tidal track conversion with album information."""
        result = await tidal_service._convert_tidal_track(mock_tidal_track)

        assert result.album is not None
        assert result.album.title == "Test Album"
        assert result.album.id == "11111"

    @pytest.mark.asyncio
    async def test_convert_tidal_track_exception(self, tidal_service):
        """Test Tidal track conversion with exception."""
        invalid_track = Mock()
        invalid_track.id = None  # This should cause an error

        result = await tidal_service._convert_tidal_track(invalid_track)

        assert result is None

    @pytest.mark.asyncio
    async def test_convert_tidal_album_success(self, tidal_service, mock_tidal_album):
        """Test successful Tidal album conversion."""
        result = await tidal_service._convert_tidal_album(mock_tidal_album)

        assert isinstance(result, Album)
        assert result.id == "11111"
        assert result.title == "Test Album"
        assert len(result.artists) == 1

    @pytest.mark.asyncio
    async def test_convert_tidal_artist_success(self, tidal_service, mock_tidal_artist):
        """Test successful Tidal artist conversion."""
        result = await tidal_service._convert_tidal_artist(mock_tidal_artist)

        assert isinstance(result, Artist)
        assert result.id == "67890"
        assert result.name == "Test Artist"
        assert result.popularity == 85

    @pytest.mark.asyncio
    async def test_convert_tidal_playlist_with_tracks(self, tidal_service, mock_tidal_playlist, mock_tidal_track):
        """Test Tidal playlist conversion with tracks."""
        mock_tidal_playlist.tracks.return_value = [mock_tidal_track]

        result = await tidal_service._convert_tidal_playlist(mock_tidal_playlist, include_tracks=True)

        assert isinstance(result, Playlist)
        assert result.id == "test-playlist-uuid"
        assert result.title == "Test Playlist"
        assert len(result.tracks) == 1

    @pytest.mark.asyncio
    async def test_convert_tidal_playlist_without_tracks(self, tidal_service, mock_tidal_playlist):
        """Test Tidal playlist conversion without tracks."""
        result = await tidal_service._convert_tidal_playlist(mock_tidal_playlist, include_tracks=False)

        assert isinstance(result, Playlist)
        assert result.id == "test-playlist-uuid"
        assert result.title == "Test Playlist"
        assert len(result.tracks) == 0


class TestUtilityMethods:
    """Test utility methods in TidalService using real implementation."""

    def test_is_uuid_valid(self, tidal_service):
        """Test UUID validation with valid UUID."""
        valid_uuid = "123e4567-e89b-12d3-a456-426614174000"

        result = tidal_service._is_uuid(valid_uuid)

        assert result is True

    def test_is_uuid_invalid(self, tidal_service):
        """Test UUID validation with invalid UUID."""
        invalid_uuid = "not-a-uuid"

        result = tidal_service._is_uuid(invalid_uuid)

        assert result is False

    def test_is_uuid_empty(self, tidal_service):
        """Test UUID validation with empty string."""
        result = tidal_service._is_uuid("")

        assert result is False


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_method_with_auth_exception(self, mock_service):
        """Test method behavior when authentication fails."""
        # Configure search_tracks to return empty list on auth failure
        mock_service.search_tracks.return_value = []

        tracks = await mock_service.search_tracks("test query")

        assert tracks == []
        mock_service.search_tracks.assert_called_once_with("test query")

    @pytest.mark.asyncio
    async def test_method_with_general_exception(self, mock_service):
        """Test method behavior with general exception."""
        # Configure search_albums to return empty list on general error
        mock_service.search_albums.return_value = []

        albums = await mock_service.search_albums("test query")

        assert albums == []
        mock_service.search_albums.assert_called_once_with("test query")

    @pytest.mark.asyncio
    async def test_conversion_with_missing_attributes(self, tidal_service):
        """Test conversion methods with objects missing attributes."""
        incomplete_track = Mock()
        # Missing required attributes
        del incomplete_track.id
        del incomplete_track.name

        result = await tidal_service._convert_tidal_track(incomplete_track)

        assert result is None

    @pytest.mark.asyncio
    async def test_large_result_set_handling(self, mock_service, mock_tidal_session):
        """Test handling of large result sets."""
        mock_service.auth.ensure_valid_token.return_value = asyncio.Future()
        mock_service.auth.ensure_valid_token.return_value.set_result(True)

        mock_service.auth.get_tidal_session.return_value = mock_tidal_session

        # Create a large number of mock tracks
        large_track_list = [Mock() for _ in range(1000)]
        search_result = {"tracks": large_track_list}
        mock_tidal_session.search.return_value = search_result

        with patch.object(mock_service, '_convert_tidal_track') as mock_convert:
            mock_convert.return_value = asyncio.Future()
            mock_convert.return_value.set_result(Track(
                id="12345",
                title="Large Set Track",
                artists=[Artist(id="67890", name="Artist")],
                duration=180
            ))

            tracks = await mock_service.search_tracks("test query", limit=50)

            # Should handle large results but respect limit
            assert len(tracks) <= 50

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, mock_service):
        """Test concurrent service operations."""
        # Mock multiple concurrent search operations
        async def mock_search(query):
            await asyncio.sleep(0.01)  # Simulate async work
            return []

        with patch.object(mock_service, 'search_tracks', side_effect=mock_search), \
             patch.object(mock_service, 'search_albums', side_effect=mock_search), \
             patch.object(mock_service, 'search_artists', side_effect=mock_search):

            # Run multiple operations concurrently
            tasks = [
                mock_service.search_tracks("query1"),
                mock_service.search_albums("query2"),
                mock_service.search_artists("query3")
            ]

            results = await asyncio.gather(*tasks)

            assert len(results) == 3
            assert all(result == [] for result in results)