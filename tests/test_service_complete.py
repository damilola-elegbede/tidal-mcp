"""Comprehensive tests for TidalService class to achieve high coverage."""

import asyncio
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from tidal_mcp.models import Album, Artist, Playlist, SearchResults, Track
from tidal_mcp.service import TidalService


class TestTidalServiceComprehensive:
    """Comprehensive test suite for TidalService class."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock Tidal session."""
        session = Mock()
        session.user = Mock()
        session.user.id = "test_user_123"
        session.user.favorites = Mock()
        session.user.playlists = Mock()
        session.search = Mock()
        session.load_oauth_session = Mock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        """Create TidalService instance with mocked session."""
        service = TidalService()
        service._session = mock_session
        return service

    @pytest.fixture
    def mock_track(self):
        """Create a mock track object."""
        track = Mock()
        track.id = 123456
        track.name = "Test Track"
        track.artist = Mock()
        track.artist.name = "Test Artist"
        track.album = Mock()
        track.album.name = "Test Album"
        track.album.cover = "cover_url"
        track.duration = 240
        track.explicit = False
        return track

    @pytest.fixture
    def mock_album(self):
        """Create a mock album object."""
        album = Mock()
        album.id = 789012
        album.name = "Test Album"
        album.artist = Mock()
        album.artist.name = "Test Artist"
        album.cover = "album_cover_url"
        album.release_date = "2023-01-01"
        album.duration = 3600
        album.num_tracks = 12
        album.explicit = False
        return album

    @pytest.fixture
    def mock_artist(self):
        """Create a mock artist object."""
        artist = Mock()
        artist.id = 345678
        artist.name = "Test Artist"
        artist.picture = "artist_picture_url"
        return artist

    @pytest.fixture
    def mock_playlist(self):
        """Create a mock playlist object."""
        playlist = Mock()
        playlist.id = "playlist_123"
        playlist.name = "Test Playlist"
        playlist.description = "Test Description"
        playlist.creator = Mock()
        playlist.creator.name = "Test Creator"
        playlist.num_tracks = 25
        playlist.duration = 6000
        return playlist

    # Initialization tests
    def test_init(self):
        """Test TidalService initialization."""
        service = TidalService()
        assert service._session is None

    def test_init_with_session(self, mock_session):
        """Test TidalService initialization with session."""
        service = TidalService(mock_session)
        assert service._session == mock_session

    # Session management tests
    def test_session_property(self, service, mock_session):
        """Test session property getter."""
        assert service.session == mock_session

    def test_session_property_none(self):
        """Test session property when no session."""
        service = TidalService()
        assert service.session is None

    def test_is_authenticated_true(self, service, mock_session):
        """Test is_authenticated when session exists."""
        assert service.is_authenticated() is True

    def test_is_authenticated_false(self):
        """Test is_authenticated when no session."""
        service = TidalService()
        assert service.is_authenticated() is False

    # Search functionality tests
    @pytest.mark.asyncio
    async def test_search_tracks_success(self, service, mock_session, mock_track):
        """Test successful track search."""
        mock_session.search.return_value = Mock()
        mock_session.search.return_value.tracks = [mock_track]

        result = await service.search_tracks("test query")

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Track)
        mock_session.search.assert_called_once_with("test query", limit=50)

    @pytest.mark.asyncio
    async def test_search_tracks_empty(self, service, mock_session):
        """Test track search with no results."""
        mock_session.search.return_value = Mock()
        mock_session.search.return_value.tracks = []

        result = await service.search_tracks("no results")

        assert result == []

    @pytest.mark.asyncio
    async def test_search_tracks_exception(self, service, mock_session):
        """Test track search with exception."""
        mock_session.search.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            await service.search_tracks("error query")

    @pytest.mark.asyncio
    async def test_search_albums_success(self, service, mock_session, mock_album):
        """Test successful album search."""
        mock_session.search.return_value = Mock()
        mock_session.search.return_value.albums = [mock_album]

        result = await service.search_albums("test album")

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Album)

    @pytest.mark.asyncio
    async def test_search_artists_success(self, service, mock_session, mock_artist):
        """Test successful artist search."""
        mock_session.search.return_value = Mock()
        mock_session.search.return_value.artists = [mock_artist]

        result = await service.search_artists("test artist")

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Artist)

    @pytest.mark.asyncio
    async def test_search_playlists_success(self, service, mock_session, mock_playlist):
        """Test successful playlist search."""
        mock_session.search.return_value = Mock()
        mock_session.search.return_value.playlists = [mock_playlist]

        result = await service.search_playlists("test playlist")

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Playlist)

    @pytest.mark.asyncio
    async def test_search_all_success(
        self, service, mock_session, mock_track, mock_album, mock_artist, mock_playlist
    ):
        """Test successful search all content."""
        search_result = Mock()
        search_result.tracks = [mock_track]
        search_result.albums = [mock_album]
        search_result.artists = [mock_artist]
        search_result.playlists = [mock_playlist]
        mock_session.search.return_value = search_result

        result = await service.search_all("test query")

        assert isinstance(result, SearchResults)
        assert len(result.tracks) == 1
        assert len(result.albums) == 1
        assert len(result.artists) == 1
        assert len(result.playlists) == 1

    # User library tests
    @pytest.mark.asyncio
    async def test_get_user_playlists_success(
        self, service, mock_session, mock_playlist
    ):
        """Test successful user playlists retrieval."""
        mock_session.user.playlists.return_value = [mock_playlist]

        result = await service.get_user_playlists()

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Playlist)

    @pytest.mark.asyncio
    async def test_get_user_playlists_empty(self, service, mock_session):
        """Test user playlists with no results."""
        mock_session.user.playlists.return_value = []

        result = await service.get_user_playlists()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_user_favorite_tracks_success(
        self, service, mock_session, mock_track
    ):
        """Test successful user favorite tracks retrieval."""
        mock_session.user.favorites.tracks.return_value = [mock_track]

        result = await service.get_user_favorite_tracks()

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Track)

    @pytest.mark.asyncio
    async def test_get_user_favorite_albums_success(
        self, service, mock_session, mock_album
    ):
        """Test successful user favorite albums retrieval."""
        mock_session.user.favorites.albums.return_value = [mock_album]

        result = await service.get_user_favorite_albums()

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Album)

    @pytest.mark.asyncio
    async def test_get_user_favorite_artists_success(
        self, service, mock_session, mock_artist
    ):
        """Test successful user favorite artists retrieval."""
        mock_session.user.favorites.artists.return_value = [mock_artist]

        result = await service.get_user_favorite_artists()

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Artist)

    # Favorites management tests
    @pytest.mark.asyncio
    async def test_add_track_to_favorites_success(self, service, mock_session):
        """Test successful track addition to favorites."""
        mock_session.user.favorites.add_track.return_value = True

        result = await service.add_track_to_favorites(123456)

        assert result is True
        mock_session.user.favorites.add_track.assert_called_once_with(123456)

    @pytest.mark.asyncio
    async def test_add_track_to_favorites_failure(self, service, mock_session):
        """Test failed track addition to favorites."""
        mock_session.user.favorites.add_track.return_value = False

        result = await service.add_track_to_favorites(123456)

        assert result is False

    @pytest.mark.asyncio
    async def test_remove_track_from_favorites_success(self, service, mock_session):
        """Test successful track removal from favorites."""
        mock_session.user.favorites.remove_track.return_value = True

        result = await service.remove_track_from_favorites(123456)

        assert result is True
        mock_session.user.favorites.remove_track.assert_called_once_with(123456)

    @pytest.mark.asyncio
    async def test_add_album_to_favorites_success(self, service, mock_session):
        """Test successful album addition to favorites."""
        mock_session.user.favorites.add_album.return_value = True

        result = await service.add_album_to_favorites(789012)

        assert result is True

    @pytest.mark.asyncio
    async def test_add_artist_to_favorites_success(self, service, mock_session):
        """Test successful artist addition to favorites."""
        mock_session.user.favorites.add_artist.return_value = True

        result = await service.add_artist_to_favorites(345678)

        assert result is True

    # Playlist operations tests
    @pytest.mark.asyncio
    async def test_get_playlist_success(self, service, mock_session, mock_playlist):
        """Test successful playlist retrieval."""
        mock_session.playlist.return_value = mock_playlist

        result = await service.get_playlist("playlist_123")

        assert isinstance(result, Playlist)
        mock_session.playlist.assert_called_once_with("playlist_123")

    @pytest.mark.asyncio
    async def test_get_playlist_not_found(self, service, mock_session):
        """Test playlist retrieval when not found."""
        mock_session.playlist.return_value = None

        result = await service.get_playlist("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_create_playlist_success(self, service, mock_session, mock_playlist):
        """Test successful playlist creation."""
        mock_session.user.create_playlist.return_value = mock_playlist

        result = await service.create_playlist("New Playlist", "Test Description")

        assert isinstance(result, Playlist)
        mock_session.user.create_playlist.assert_called_once_with(
            "New Playlist", "Test Description"
        )

    @pytest.mark.asyncio
    async def test_create_playlist_failure(self, service, mock_session):
        """Test failed playlist creation."""
        mock_session.user.create_playlist.side_effect = Exception("Creation failed")

        with pytest.raises(Exception, match="Creation failed"):
            await service.create_playlist("Failed Playlist")

    @pytest.mark.asyncio
    async def test_delete_playlist_success(self, service, mock_session):
        """Test successful playlist deletion."""
        mock_session.user.delete_playlist.return_value = True

        result = await service.delete_playlist("playlist_123")

        assert result is True
        mock_session.user.delete_playlist.assert_called_once_with("playlist_123")

    @pytest.mark.asyncio
    async def test_add_tracks_to_playlist_success(self, service, mock_session):
        """Test successful tracks addition to playlist."""
        mock_playlist = Mock()
        mock_playlist.add_tracks.return_value = True
        mock_session.playlist.return_value = mock_playlist

        result = await service.add_tracks_to_playlist("playlist_123", [123456, 789012])

        assert result is True
        mock_playlist.add_tracks.assert_called_once_with([123456, 789012])

    @pytest.mark.asyncio
    async def test_remove_tracks_from_playlist_success(self, service, mock_session):
        """Test successful tracks removal from playlist."""
        mock_playlist = Mock()
        mock_playlist.remove_tracks.return_value = True
        mock_session.playlist.return_value = mock_playlist

        result = await service.remove_tracks_from_playlist("playlist_123", [123456])

        assert result is True
        mock_playlist.remove_tracks.assert_called_once_with([123456])

    # Album and track retrieval tests
    @pytest.mark.asyncio
    async def test_get_album_success(self, service, mock_session, mock_album):
        """Test successful album retrieval."""
        mock_session.album.return_value = mock_album

        result = await service.get_album(789012)

        assert isinstance(result, Album)
        mock_session.album.assert_called_once_with(789012)

    @pytest.mark.asyncio
    async def test_get_album_tracks_success(self, service, mock_session, mock_track):
        """Test successful album tracks retrieval."""
        mock_album = Mock()
        mock_album.tracks.return_value = [mock_track]
        mock_session.album.return_value = mock_album

        result = await service.get_album_tracks(789012)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Track)

    @pytest.mark.asyncio
    async def test_get_track_success(self, service, mock_session, mock_track):
        """Test successful track retrieval."""
        mock_session.track.return_value = mock_track

        result = await service.get_track(123456)

        assert isinstance(result, Track)
        mock_session.track.assert_called_once_with(123456)

    @pytest.mark.asyncio
    async def test_get_artist_success(self, service, mock_session, mock_artist):
        """Test successful artist retrieval."""
        mock_session.artist.return_value = mock_artist

        result = await service.get_artist(345678)

        assert isinstance(result, Artist)
        mock_session.artist.assert_called_once_with(345678)

    @pytest.mark.asyncio
    async def test_get_artist_albums_success(self, service, mock_session, mock_album):
        """Test successful artist albums retrieval."""
        mock_artist = Mock()
        mock_artist.get_albums.return_value = [mock_album]
        mock_session.artist.return_value = mock_artist

        result = await service.get_artist_albums(345678)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Album)

    @pytest.mark.asyncio
    async def test_get_artist_top_tracks_success(
        self, service, mock_session, mock_track
    ):
        """Test successful artist top tracks retrieval."""
        mock_artist = Mock()
        mock_artist.get_top_tracks.return_value = [mock_track]
        mock_session.artist.return_value = mock_artist

        result = await service.get_artist_top_tracks(345678)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Track)

    # Recommendations tests
    @pytest.mark.asyncio
    async def test_get_track_recommendations_success(
        self, service, mock_session, mock_track
    ):
        """Test successful track recommendations."""
        mock_session.track_radio.return_value = [mock_track]

        result = await service.get_track_recommendations(123456)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Track)

    @pytest.mark.asyncio
    async def test_get_artist_radio_success(self, service, mock_session, mock_track):
        """Test successful artist radio."""
        mock_session.artist_radio.return_value = [mock_track]

        result = await service.get_artist_radio(345678)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Track)

    # Playback tests
    @pytest.mark.asyncio
    async def test_get_current_track_success(self, service, mock_session, mock_track):
        """Test successful current track retrieval."""
        mock_session.get_current_track.return_value = mock_track

        result = await service.get_current_track()

        assert isinstance(result, Track)

    @pytest.mark.asyncio
    async def test_get_current_track_none(self, service, mock_session):
        """Test current track when none playing."""
        mock_session.get_current_track.return_value = None

        result = await service.get_current_track()

        assert result is None

    @pytest.mark.asyncio
    async def test_play_track_success(self, service, mock_session):
        """Test successful track playback."""
        mock_session.play_track.return_value = True

        result = await service.play_track(123456)

        assert result is True
        mock_session.play_track.assert_called_once_with(123456)

    @pytest.mark.asyncio
    async def test_play_album_success(self, service, mock_session):
        """Test successful album playback."""
        mock_session.play_album.return_value = True

        result = await service.play_album(789012)

        assert result is True
        mock_session.play_album.assert_called_once_with(789012)

    # Error handling tests
    @pytest.mark.asyncio
    async def test_search_with_session_none(self):
        """Test search operations when session is None."""
        service = TidalService()

        with pytest.raises(AttributeError):
            await service.search_tracks("test")

    @pytest.mark.asyncio
    async def test_user_operations_with_session_none(self):
        """Test user operations when session is None."""
        service = TidalService()

        with pytest.raises(AttributeError):
            await service.get_user_playlists()

    # Utility method tests
    def test_get_track_url(self, service):
        """Test track URL generation."""
        url = service.get_track_url(123456)
        assert url == "https://tidal.com/track/123456"

    def test_get_album_url(self, service):
        """Test album URL generation."""
        url = service.get_album_url(789012)
        assert url == "https://tidal.com/album/789012"

    def test_get_artist_url(self, service):
        """Test artist URL generation."""
        url = service.get_artist_url(345678)
        assert url == "https://tidal.com/artist/345678"

    def test_get_playlist_url(self, service):
        """Test playlist URL generation."""
        url = service.get_playlist_url("playlist_123")
        assert url == "https://tidal.com/playlist/playlist_123"

    # Async wrapper tests
    @pytest.mark.asyncio
    async def test_async_wrapper_success(self, service, mock_session):
        """Test async wrapper for sync operations."""
        mock_session.some_sync_method.return_value = "success"

        # This tests the internal async wrapper pattern
        result = await service._async_wrapper(
            mock_session.some_sync_method, "arg1", key="value"
        )

        assert result == "success"
        mock_session.some_sync_method.assert_called_once_with("arg1", key="value")

    @pytest.mark.asyncio
    async def test_async_wrapper_exception(self, service, mock_session):
        """Test async wrapper with exception."""
        mock_session.failing_method.side_effect = Exception("Sync error")

        with pytest.raises(Exception, match="Sync error"):
            await service._async_wrapper(mock_session.failing_method)

    # Integration-style tests
    @pytest.mark.asyncio
    async def test_search_and_add_to_favorites_workflow(
        self, service, mock_session, mock_track
    ):
        """Test complete workflow: search track and add to favorites."""
        # Setup search
        mock_session.search.return_value = Mock()
        mock_session.search.return_value.tracks = [mock_track]

        # Setup favorites
        mock_session.user.favorites.add_track.return_value = True

        # Execute workflow
        tracks = await service.search_tracks("test song")
        if tracks:
            result = await service.add_track_to_favorites(tracks[0].id)
            assert result is True

    @pytest.mark.asyncio
    async def test_create_playlist_and_add_tracks_workflow(
        self, service, mock_session, mock_playlist
    ):
        """Test complete workflow: create playlist and add tracks."""
        # Setup playlist creation
        mock_session.user.create_playlist.return_value = mock_playlist

        # Setup track addition
        mock_playlist.add_tracks.return_value = True
        mock_session.playlist.return_value = mock_playlist

        # Execute workflow
        playlist = await service.create_playlist("Test Playlist")
        result = await service.add_tracks_to_playlist(playlist.id, [123456, 789012])

        assert isinstance(playlist, Playlist)
        assert result is True

    # Edge case tests
    @pytest.mark.asyncio
    async def test_search_with_empty_query(self, service, mock_session):
        """Test search with empty query."""
        mock_session.search.return_value = Mock()
        mock_session.search.return_value.tracks = []

        result = await service.search_tracks("")

        assert result == []
        mock_session.search.assert_called_once_with("", limit=50)

    @pytest.mark.asyncio
    async def test_search_with_large_limit(self, service, mock_session, mock_track):
        """Test search with large limit."""
        mock_session.search.return_value = Mock()
        mock_session.search.return_value.tracks = [mock_track] * 100

        result = await service.search_tracks("test", limit=100)

        assert len(result) == 100
        mock_session.search.assert_called_once_with("test", limit=100)

    def test_repr(self, service):
        """Test string representation."""
        repr_str = repr(service)
        assert "TidalService" in repr_str

    def test_str(self, service):
        """Test string conversion."""
        str_repr = str(service)
        assert "TidalService" in str_repr
