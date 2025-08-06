"""
Tests for Tidal Service Layer

Comprehensive unit tests for the TidalService class covering search
functionality, playlist management, favorites, recommendations, and
error handling.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
import tidalapi

from tidal_mcp.auth import TidalAuth, TidalAuthError
from tidal_mcp.models import Album, Artist, Playlist, Track
from tidal_mcp.service import TidalService, async_to_sync


@pytest.fixture
def mock_auth():
    """Create a mock TidalAuth instance."""
    auth = Mock(spec=TidalAuth)
    auth.ensure_valid_token = AsyncMock(return_value=True)
    auth.get_tidal_session = Mock()
    return auth


@pytest.fixture
def mock_tidal_session():
    """Create a mock tidalapi session."""
    session = Mock(spec=tidalapi.Session)

    # Mock user
    user = Mock()
    user.id = 12345
    user.country_code = "US"
    user.favorites = Mock()
    user.playlists = Mock()
    user.create_playlist = Mock()
    session.user = user

    # Mock search methods
    session.search = Mock()
    session.track = Mock()
    session.album = Mock()
    session.artist = Mock()
    session.playlist = Mock()
    session.featured = Mock()

    return session


@pytest.fixture
def service(mock_auth, mock_tidal_session):
    """Create TidalService instance for testing."""
    mock_auth.get_tidal_session.return_value = mock_tidal_session
    return TidalService(auth=mock_auth)


@pytest.fixture
def sample_tidal_track():
    """Create a sample tidalapi track for testing."""
    track = Mock()
    track.id = 123456
    track.name = "Test Track"
    track.duration = 240
    track.track_num = 1
    track.volume_num = 1
    track.explicit = False
    track.audio_quality = "LOSSLESS"

    # Mock artist
    artist = Mock()
    artist.id = 789
    artist.name = "Test Artist"
    artist.picture = "artist_pic_url"
    artist.popularity = 85
    track.artist = artist
    track.artists = [artist]

    # Mock album
    album = Mock()
    album.id = 456
    album.name = "Test Album"
    album.release_date = "2023-01-01"
    album.duration = 3600
    album.num_tracks = 12
    album.image = "album_cover_url"
    album.explicit = False
    album.artist = artist
    album.artists = [artist]
    track.album = album

    return track


@pytest.fixture
def sample_tidal_album():
    """Create a sample tidalapi album for testing."""
    album = Mock()
    album.id = 456
    album.name = "Test Album"
    album.release_date = "2023-01-01"
    album.duration = 3600
    album.num_tracks = 12
    album.image = "album_cover_url"
    album.explicit = False

    # Mock artist
    artist = Mock()
    artist.id = 789
    artist.name = "Test Artist"
    artist.picture = "artist_pic_url"
    artist.popularity = 85
    album.artist = artist
    album.artists = [artist]

    return album


@pytest.fixture
def sample_tidal_artist():
    """Create a sample tidalapi artist for testing."""
    artist = Mock()
    artist.id = 789
    artist.name = "Test Artist"
    artist.picture = "artist_pic_url"
    artist.popularity = 85
    return artist


@pytest.fixture
def sample_tidal_playlist():
    """Create a sample tidalapi playlist for testing."""
    playlist = Mock()
    playlist.uuid = "12345678-1234-1234-1234-123456789abc"
    playlist.id = "12345678-1234-1234-1234-123456789abc"
    playlist.name = "Test Playlist"
    playlist.description = "A test playlist"
    playlist.num_tracks = 10
    playlist.duration = 2400
    playlist.image = "playlist_image_url"
    playlist.public = True
    playlist.created = "2023-01-01T00:00:00Z"
    playlist.last_updated = "2023-01-02T00:00:00Z"

    # Mock creator
    creator = Mock()
    creator.name = "Test User"
    playlist.creator = {"name": "Test User"}

    # Mock tracks method
    playlist.tracks = Mock(return_value=[])
    playlist.add = Mock(return_value=True)
    playlist.remove_by_index = Mock(return_value=True)
    playlist.delete = Mock(return_value=True)

    return playlist


@pytest.mark.unit
class TestTidalService:
    """Test cases for TidalService class."""

    def test_init(self, mock_auth):
        """Test TidalService initialization."""
        service = TidalService(auth=mock_auth)
        assert service.auth == mock_auth
        assert service._cache == {}
        assert service._cache_ttl == 300

    @pytest.mark.asyncio
    async def test_ensure_authenticated_success(self, service, mock_auth):
        """Test successful authentication check."""
        mock_auth.ensure_valid_token.return_value = True
        await service.ensure_authenticated()
        mock_auth.ensure_valid_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_authenticated_failure(self, service, mock_auth):
        """Test authentication failure."""
        mock_auth.ensure_valid_token.return_value = False

        with pytest.raises(TidalAuthError, match="Authentication required"):
            await service.ensure_authenticated()

    def test_get_session(self, service, mock_auth, mock_tidal_session):
        """Test getting Tidal session."""
        session = service.get_session()
        assert session == mock_tidal_session
        mock_auth.get_tidal_session.assert_called_once()


@pytest.mark.unit
class TestSearchFunctionality:
    """Test search functionality."""

    @pytest.mark.asyncio
    async def test_search_tracks_success(
        self, service, mock_tidal_session, sample_tidal_track
    ):
        """Test successful track search."""
        # Mock search result
        mock_tidal_session.search.return_value = {"tracks": [sample_tidal_track]}

        with patch.object(
            service, "_convert_tidal_track", new_callable=AsyncMock
        ) as mock_convert:
            mock_track = Track(
                id="123456",
                title="Test Track",
                artists=[Artist(id="789", name="Test Artist")],
                duration=240,
            )
            mock_convert.return_value = mock_track

            results = await service.search_tracks("test query", limit=10)

            assert len(results) == 1
            assert results[0] == mock_track
            mock_tidal_session.search.assert_called_once()
            mock_convert.assert_called_once_with(sample_tidal_track)

    @pytest.mark.asyncio
    async def test_search_tracks_empty_query(self, service):
        """Test track search with empty query."""
        with patch("tidal_mcp.utils.sanitize_query", return_value=""):
            results = await service.search_tracks("")
            assert results == []

    @pytest.mark.asyncio
    async def test_search_tracks_no_results(self, service, mock_tidal_session):
        """Test track search with no results."""
        mock_tidal_session.search.return_value = {"tracks": []}

        results = await service.search_tracks("nonexistent")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_tracks_with_pagination(
        self, service, mock_tidal_session, sample_tidal_track
    ):
        """Test track search with pagination."""
        # Create multiple tracks
        tracks = [sample_tidal_track] * 5
        mock_tidal_session.search.return_value = {"tracks": tracks}

        with patch.object(
            service, "_convert_tidal_track", new_callable=AsyncMock
        ) as mock_convert:
            mock_track = Track(
                id="123456", title="Test Track", artists=[], duration=240
            )
            mock_convert.return_value = mock_track

            results = await service.search_tracks("test", limit=3, offset=1)

            # Should return 3 tracks starting from index 1
            assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_albums_success(
        self, service, mock_tidal_session, sample_tidal_album
    ):
        """Test successful album search."""
        mock_tidal_session.search.return_value = {"albums": [sample_tidal_album]}

        with patch.object(
            service, "_convert_tidal_album", new_callable=AsyncMock
        ) as mock_convert:
            mock_album = Album(
                id="456",
                title="Test Album",
                artists=[Artist(id="789", name="Test Artist")],
            )
            mock_convert.return_value = mock_album

            results = await service.search_albums("test album")

            assert len(results) == 1
            assert results[0] == mock_album

    @pytest.mark.asyncio
    async def test_search_artists_success(
        self, service, mock_tidal_session, sample_tidal_artist
    ):
        """Test successful artist search."""
        mock_tidal_session.search.return_value = {"artists": [sample_tidal_artist]}

        with patch.object(
            service, "_convert_tidal_artist", new_callable=AsyncMock
        ) as mock_convert:
            mock_artist = Artist(id="789", name="Test Artist", popularity=85)
            mock_convert.return_value = mock_artist

            results = await service.search_artists("test artist")

            assert len(results) == 1
            assert results[0] == mock_artist

    @pytest.mark.asyncio
    async def test_search_playlists_success(
        self, service, mock_tidal_session, sample_tidal_playlist
    ):
        """Test successful playlist search."""
        mock_tidal_session.search.return_value = {"playlists": [sample_tidal_playlist]}

        with patch.object(
            service, "_convert_tidal_playlist", new_callable=AsyncMock
        ) as mock_convert:
            mock_playlist = Playlist(
                id="12345678-1234-1234-1234-123456789abc",
                title="Test Playlist",
                creator="Test User",
            )
            mock_convert.return_value = mock_playlist

            results = await service.search_playlists("test playlist")

            assert len(results) == 1
            assert results[0] == mock_playlist

    @pytest.mark.asyncio
    async def test_search_all_success(self, service):
        """Test search across all content types."""
        mock_track = Track(id="1", title="Track", artists=[], duration=240)
        mock_album = Album(id="2", title="Album", artists=[])
        mock_artist = Artist(id="3", name="Artist")
        mock_playlist = Playlist(id="4", title="Playlist")

        with (
            patch.object(
                service,
                "search_tracks",
                new_callable=AsyncMock,
                return_value=[mock_track],
            ),
            patch.object(
                service,
                "search_albums",
                new_callable=AsyncMock,
                return_value=[mock_album],
            ),
            patch.object(
                service,
                "search_artists",
                new_callable=AsyncMock,
                return_value=[mock_artist],
            ),
            patch.object(
                service,
                "search_playlists",
                new_callable=AsyncMock,
                return_value=[mock_playlist],
            ),
        ):
            results = await service.search_all("test query", limit=5)

            assert len(results.tracks) == 1
            assert len(results.albums) == 1
            assert len(results.artists) == 1
            assert len(results.playlists) == 1
            assert results.total_results == 4

    @pytest.mark.asyncio
    async def test_search_error_handling(self, service, mock_tidal_session):
        """Test search error handling."""
        mock_tidal_session.search.side_effect = Exception("Search failed")

        results = await service.search_tracks("test")
        assert results == []


@pytest.mark.unit
class TestPlaylistManagement:
    """Test playlist management functionality."""

    @pytest.mark.asyncio
    async def test_get_playlist_success(
        self, service, mock_tidal_session, sample_tidal_playlist
    ):
        """Test successful playlist retrieval."""
        mock_tidal_session.playlist.return_value = sample_tidal_playlist

        with patch.object(
            service, "_convert_tidal_playlist", new_callable=AsyncMock
        ) as mock_convert:
            mock_playlist = Playlist(
                id="12345678-1234-1234-1234-123456789abc",
                title="Test Playlist",
                tracks=[],
            )
            mock_convert.return_value = mock_playlist

            result = await service.get_playlist("12345678-1234-1234-1234-123456789abc")

            assert result == mock_playlist
            mock_tidal_session.playlist.assert_called_once_with(
                "12345678-1234-1234-1234-123456789abc"
            )
            mock_convert.assert_called_once_with(
                sample_tidal_playlist, include_tracks=True
            )

    @pytest.mark.asyncio
    async def test_get_playlist_not_found(self, service, mock_tidal_session):
        """Test playlist retrieval when playlist not found."""
        mock_tidal_session.playlist.return_value = None

        result = await service.get_playlist("nonexistent-playlist")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_playlist_invalid_id(self, service):
        """Test playlist retrieval with invalid ID."""
        with (
            patch("tidal_mcp.utils.validate_tidal_id", return_value=False),
            patch.object(service, "_is_uuid", return_value=False),
        ):
            result = await service.get_playlist("invalid-id")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_playlist_tracks_success(
        self,
        service,
        mock_tidal_session,
        sample_tidal_playlist,
        sample_tidal_track,
    ):
        """Test successful playlist tracks retrieval."""
        sample_tidal_playlist.tracks.return_value = [sample_tidal_track]
        mock_tidal_session.playlist.return_value = sample_tidal_playlist

        with patch.object(
            service, "_convert_tidal_track", new_callable=AsyncMock
        ) as mock_convert:
            mock_track = Track(
                id="123456", title="Test Track", artists=[], duration=240
            )
            mock_convert.return_value = mock_track

            results = await service.get_playlist_tracks(
                "12345678-1234-1234-1234-123456789abc"
            )

            assert len(results) == 1
            assert results[0] == mock_track

    @pytest.mark.asyncio
    async def test_create_playlist_success(
        self, service, mock_tidal_session, sample_tidal_playlist
    ):
        """Test successful playlist creation."""
        mock_tidal_session.user.create_playlist.return_value = sample_tidal_playlist

        with patch.object(
            service, "_convert_tidal_playlist", new_callable=AsyncMock
        ) as mock_convert:
            mock_playlist = Playlist(
                id="12345678-1234-1234-1234-123456789abc",
                title="My New Playlist",
                description="Test description",
            )
            mock_convert.return_value = mock_playlist

            result = await service.create_playlist(
                "My New Playlist", "Test description"
            )

            assert result == mock_playlist
            mock_tidal_session.user.create_playlist.assert_called_once_with(
                "My New Playlist", "Test description"
            )

    @pytest.mark.asyncio
    async def test_create_playlist_empty_title(self, service):
        """Test playlist creation with empty title."""
        result = await service.create_playlist("")
        assert result is None

        result = await service.create_playlist("   ")  # Whitespace only
        assert result is None

    @pytest.mark.asyncio
    async def test_add_tracks_to_playlist_success(
        self,
        service,
        mock_tidal_session,
        sample_tidal_playlist,
        sample_tidal_track,
    ):
        """Test successful track addition to playlist."""
        mock_tidal_session.playlist.return_value = sample_tidal_playlist
        mock_tidal_session.track.return_value = sample_tidal_track
        sample_tidal_playlist.add.return_value = True

        with patch("tidal_mcp.utils.validate_tidal_id", return_value=True):
            result = await service.add_tracks_to_playlist(
                "12345678-1234-1234-1234-123456789abc", ["123456"]
            )

            assert result is True
            sample_tidal_playlist.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_tracks_to_playlist_invalid_playlist(self, service):
        """Test adding tracks to invalid playlist."""
        with (
            patch("tidal_mcp.utils.validate_tidal_id", return_value=False),
            patch.object(service, "_is_uuid", return_value=False),
        ):
            result = await service.add_tracks_to_playlist(
                "invalid-playlist", ["123456"]
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_add_tracks_to_playlist_no_tracks(self, service):
        """Test adding empty track list to playlist."""
        result = await service.add_tracks_to_playlist(
            "12345678-1234-1234-1234-123456789abc", []
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_remove_tracks_from_playlist_success(
        self, service, mock_tidal_session, sample_tidal_playlist
    ):
        """Test successful track removal from playlist."""
        mock_tidal_session.playlist.return_value = sample_tidal_playlist
        sample_tidal_playlist.remove_by_index.return_value = True

        with patch("tidal_mcp.utils.validate_tidal_id", return_value=True):
            result = await service.remove_tracks_from_playlist(
                "12345678-1234-1234-1234-123456789abc", [0, 2, 1]
            )

            assert result is True
            # Should be called in reverse order to avoid index shifting
            expected_calls = [2, 1, 0]
            remove_calls = sample_tidal_playlist.remove_by_index.call_args_list
            actual_calls = [call[0][0] for call in remove_calls]
            assert actual_calls == expected_calls

    @pytest.mark.asyncio
    async def test_delete_playlist_success(
        self, service, mock_tidal_session, sample_tidal_playlist
    ):
        """Test successful playlist deletion."""
        mock_tidal_session.playlist.return_value = sample_tidal_playlist
        sample_tidal_playlist.delete.return_value = True

        with patch("tidal_mcp.utils.validate_tidal_id", return_value=True):
            result = await service.delete_playlist(
                "12345678-1234-1234-1234-123456789abc"
            )

            assert result is True
            sample_tidal_playlist.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_playlists_success(
        self, service, mock_tidal_session, sample_tidal_playlist
    ):
        """Test successful user playlists retrieval."""
        mock_tidal_session.user.playlists.return_value = [sample_tidal_playlist]

        with patch.object(
            service, "_convert_tidal_playlist", new_callable=AsyncMock
        ) as mock_convert:
            mock_playlist = Playlist(
                id="12345678-1234-1234-1234-123456789abc", title="Test Playlist"
            )
            mock_convert.return_value = mock_playlist

            results = await service.get_user_playlists()

            assert len(results) == 1
            assert results[0] == mock_playlist
            mock_convert.assert_called_once_with(
                sample_tidal_playlist, include_tracks=False
            )


@pytest.mark.unit
class TestFavoritesManagement:
    """Test favorites management functionality."""

    @pytest.mark.asyncio
    async def test_get_user_favorites_tracks(
        self, service, mock_tidal_session, sample_tidal_track
    ):
        """Test getting user's favorite tracks."""
        mock_tidal_session.user.favorites.tracks.return_value = [sample_tidal_track]

        with patch.object(
            service, "_convert_tidal_track", new_callable=AsyncMock
        ) as mock_convert:
            mock_track = Track(
                id="123456", title="Test Track", artists=[], duration=240
            )
            mock_convert.return_value = mock_track

            results = await service.get_user_favorites("tracks")

            assert len(results) == 1
            assert results[0] == mock_track

    @pytest.mark.asyncio
    async def test_get_user_favorites_invalid_type(self, service):
        """Test getting favorites with invalid content type."""
        results = await service.get_user_favorites("invalid_type")
        assert results == []

    @pytest.mark.asyncio
    async def test_add_to_favorites_track_success(
        self, service, mock_tidal_session, sample_tidal_track
    ):
        """Test successful track addition to favorites."""
        mock_tidal_session.track.return_value = sample_tidal_track
        mock_tidal_session.user.favorites.add_track.return_value = True

        with patch("tidal_mcp.utils.validate_tidal_id", return_value=True):
            result = await service.add_to_favorites("123456", "track")

            assert result is True
            favorites = mock_tidal_session.user.favorites
            favorites.add_track.assert_called_once_with(sample_tidal_track)

    @pytest.mark.asyncio
    async def test_add_to_favorites_invalid_id(self, service):
        """Test adding to favorites with invalid ID."""
        with patch("tidal_mcp.utils.validate_tidal_id", return_value=False):
            result = await service.add_to_favorites("invalid-id", "track")
            assert result is False

    @pytest.mark.asyncio
    async def test_remove_from_favorites_success(
        self, service, mock_tidal_session, sample_tidal_track
    ):
        """Test successful favorite removal."""
        mock_tidal_session.track.return_value = sample_tidal_track
        mock_tidal_session.user.favorites.remove_track.return_value = True

        with patch("tidal_mcp.utils.validate_tidal_id", return_value=True):
            result = await service.remove_from_favorites("123456", "track")

            assert result is True
            favorites = mock_tidal_session.user.favorites
            favorites.remove_track.assert_called_once_with(sample_tidal_track)


@pytest.mark.unit
class TestRecommendationsAndRadio:
    """Test recommendations and radio functionality."""

    @pytest.mark.asyncio
    async def test_get_track_radio_success(
        self, service, mock_tidal_session, sample_tidal_track
    ):
        """Test successful track radio retrieval."""
        # Create radio tracks
        radio_tracks = [sample_tidal_track] * 3
        sample_tidal_track.get_track_radio.return_value = radio_tracks
        mock_tidal_session.track.return_value = sample_tidal_track

        with patch.object(
            service, "_convert_tidal_track", new_callable=AsyncMock
        ) as mock_convert:
            mock_track = Track(
                id="123456", title="Radio Track", artists=[], duration=240
            )
            mock_convert.return_value = mock_track

            with patch("tidal_mcp.utils.validate_tidal_id", return_value=True):
                results = await service.get_track_radio("123456", limit=3)

                assert len(results) == 3
                assert all(track == mock_track for track in results)

    @pytest.mark.asyncio
    async def test_get_artist_radio_success(
        self,
        service,
        mock_tidal_session,
        sample_tidal_artist,
        sample_tidal_track,
    ):
        """Test successful artist radio retrieval."""
        radio_tracks = [sample_tidal_track] * 2
        sample_tidal_artist.get_radio.return_value = radio_tracks
        mock_tidal_session.artist.return_value = sample_tidal_artist

        with patch.object(
            service, "_convert_tidal_track", new_callable=AsyncMock
        ) as mock_convert:
            mock_track = Track(
                id="123456", title="Radio Track", artists=[], duration=240
            )
            mock_convert.return_value = mock_track

            with patch("tidal_mcp.utils.validate_tidal_id", return_value=True):
                results = await service.get_artist_radio("789", limit=2)

                assert len(results) == 2
                assert all(track == mock_track for track in results)

    @pytest.mark.asyncio
    async def test_get_recommended_tracks_from_favorites(
        self, service, mock_tidal_session, sample_tidal_track
    ):
        """Test getting recommended tracks based on favorites."""
        # Mock user favorites
        favorite_tracks = [sample_tidal_track] * 5
        mock_tidal_session.user.favorites.tracks.return_value = favorite_tracks

        # Mock radio from favorite track
        radio_tracks = [sample_tidal_track] * 3
        sample_tidal_track.get_track_radio.return_value = radio_tracks

        with patch.object(
            service, "_convert_tidal_track", new_callable=AsyncMock
        ) as mock_convert:
            mock_track = Track(
                id="123456",
                title="Recommended Track",
                artists=[],
                duration=240,
            )
            mock_convert.return_value = mock_track

            results = await service.get_recommended_tracks(limit=3)

            assert len(results) == 3
            assert all(track == mock_track for track in results)

    @pytest.mark.asyncio
    async def test_get_recommended_tracks_fallback_to_featured(
        self, service, mock_tidal_session, sample_tidal_track
    ):
        """Test getting recommended tracks fallback to featured."""
        # Mock empty favorites
        mock_tidal_session.user.favorites.tracks.return_value = []

        # Mock featured content with tracks
        featured = Mock()
        featured.tracks = [sample_tidal_track] * 2
        mock_tidal_session.featured.return_value = featured

        with patch.object(
            service, "_convert_tidal_track", new_callable=AsyncMock
        ) as mock_convert:
            mock_track = Track(
                id="123456", title="Featured Track", artists=[], duration=240
            )
            mock_convert.return_value = mock_track

            results = await service.get_recommended_tracks(limit=2)

            assert len(results) == 2
            assert all(track == mock_track for track in results)


@pytest.mark.unit
class TestDetailedItemRetrieval:
    """Test detailed item retrieval functionality."""

    @pytest.mark.asyncio
    async def test_get_track_success(
        self, service, mock_tidal_session, sample_tidal_track
    ):
        """Test successful track retrieval."""
        mock_tidal_session.track.return_value = sample_tidal_track

        with patch.object(
            service, "_convert_tidal_track", new_callable=AsyncMock
        ) as mock_convert:
            mock_track = Track(
                id="123456", title="Test Track", artists=[], duration=240
            )
            mock_convert.return_value = mock_track

            with patch("tidal_mcp.utils.validate_tidal_id", return_value=True):
                result = await service.get_track("123456")

                assert result == mock_track
                mock_tidal_session.track.assert_called_once_with("123456")

    @pytest.mark.asyncio
    async def test_get_track_not_found(self, service, mock_tidal_session):
        """Test track retrieval when track not found."""
        mock_tidal_session.track.return_value = None

        with patch("tidal_mcp.utils.validate_tidal_id", return_value=True):
            result = await service.get_track("nonexistent")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_album_success(
        self, service, mock_tidal_session, sample_tidal_album
    ):
        """Test successful album retrieval."""
        mock_tidal_session.album.return_value = sample_tidal_album

        with patch.object(
            service, "_convert_tidal_album", new_callable=AsyncMock
        ) as mock_convert:
            mock_album = Album(id="456", title="Test Album", artists=[])
            mock_convert.return_value = mock_album

            with patch("tidal_mcp.utils.validate_tidal_id", return_value=True):
                result = await service.get_album("456", include_tracks=False)

                assert result == mock_album
                mock_convert.assert_called_once_with(
                    sample_tidal_album, include_tracks=False
                )

    @pytest.mark.asyncio
    async def test_get_artist_success(
        self, service, mock_tidal_session, sample_tidal_artist
    ):
        """Test successful artist retrieval."""
        mock_tidal_session.artist.return_value = sample_tidal_artist

        with patch.object(
            service, "_convert_tidal_artist", new_callable=AsyncMock
        ) as mock_convert:
            mock_artist = Artist(id="789", name="Test Artist")
            mock_convert.return_value = mock_artist

            with patch("tidal_mcp.utils.validate_tidal_id", return_value=True):
                result = await service.get_artist("789")

                assert result == mock_artist
                mock_tidal_session.artist.assert_called_once_with("789")

    @pytest.mark.asyncio
    async def test_get_album_tracks_success(
        self,
        service,
        mock_tidal_session,
        sample_tidal_album,
        sample_tidal_track,
    ):
        """Test successful album tracks retrieval."""
        sample_tidal_album.tracks.return_value = [sample_tidal_track]
        mock_tidal_session.album.return_value = sample_tidal_album

        with patch.object(
            service, "_convert_tidal_track", new_callable=AsyncMock
        ) as mock_convert:
            mock_track = Track(
                id="123456", title="Album Track", artists=[], duration=240
            )
            mock_convert.return_value = mock_track

            with patch("tidal_mcp.utils.validate_tidal_id", return_value=True):
                results = await service.get_album_tracks("456")

                assert len(results) == 1
                assert results[0] == mock_track

    @pytest.mark.asyncio
    async def test_get_artist_albums_success(
        self,
        service,
        mock_tidal_session,
        sample_tidal_artist,
        sample_tidal_album,
    ):
        """Test successful artist albums retrieval."""
        sample_tidal_artist.get_albums.return_value = [sample_tidal_album]
        mock_tidal_session.artist.return_value = sample_tidal_artist

        with patch.object(
            service, "_convert_tidal_album", new_callable=AsyncMock
        ) as mock_convert:
            mock_album = Album(id="456", title="Artist Album", artists=[])
            mock_convert.return_value = mock_album

            with patch("tidal_mcp.utils.validate_tidal_id", return_value=True):
                results = await service.get_artist_albums("789")

                assert len(results) == 1
                assert results[0] == mock_album

    @pytest.mark.asyncio
    async def test_get_artist_top_tracks_success(
        self,
        service,
        mock_tidal_session,
        sample_tidal_artist,
        sample_tidal_track,
    ):
        """Test successful artist top tracks retrieval."""
        sample_tidal_artist.get_top_tracks.return_value = [sample_tidal_track]
        mock_tidal_session.artist.return_value = sample_tidal_artist

        with patch.object(
            service, "_convert_tidal_track", new_callable=AsyncMock
        ) as mock_convert:
            mock_track = Track(id="123456", title="Top Track", artists=[], duration=240)
            mock_convert.return_value = mock_track

            with patch("tidal_mcp.utils.validate_tidal_id", return_value=True):
                results = await service.get_artist_top_tracks("789")

                assert len(results) == 1
                assert results[0] == mock_track


@pytest.mark.unit
class TestUserProfile:
    """Test user profile functionality."""

    @pytest.mark.asyncio
    async def test_get_user_profile_success(self, service, mock_auth):
        """Test successful user profile retrieval."""
        user_info = {
            "id": 12345,
            "username": "testuser",
            "country_code": "US",
            "subscription": {"type": "HiFi", "valid": True},
        }
        mock_auth.get_user_info.return_value = user_info

        result = await service.get_user_profile()

        assert result == user_info
        mock_auth.get_user_info.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_profile_no_info(self, service, mock_auth):
        """Test user profile retrieval when no info available."""
        mock_auth.get_user_info.return_value = None

        result = await service.get_user_profile()
        assert result is None


@pytest.mark.unit
class TestConversionMethods:
    """Test conversion methods for Tidal objects."""

    @pytest.mark.asyncio
    async def test_convert_tidal_track_success(self, service, sample_tidal_track):
        """Test successful track conversion."""
        result = await service._convert_tidal_track(sample_tidal_track)

        assert isinstance(result, Track)
        assert result.id == "123456"
        assert result.title == "Test Track"
        assert result.duration == 240
        assert result.track_number == 1
        assert result.disc_number == 1
        assert not result.explicit
        assert result.quality == "LOSSLESS"

        # Test artist conversion
        assert len(result.artists) == 1
        assert result.artists[0].id == "789"
        assert result.artists[0].name == "Test Artist"

        # Test album conversion
        assert result.album is not None
        assert result.album.id == "456"
        assert result.album.title == "Test Album"

    @pytest.mark.asyncio
    async def test_convert_tidal_track_error(self, service):
        """Test track conversion error handling."""
        # Create a malformed track object
        bad_track = Mock()
        bad_track.id = None  # This should cause an error

        result = await service._convert_tidal_track(bad_track)
        assert result is None

    @pytest.mark.asyncio
    async def test_convert_tidal_album_success(self, service, sample_tidal_album):
        """Test successful album conversion."""
        result = await service._convert_tidal_album(sample_tidal_album)

        assert isinstance(result, Album)
        assert result.id == "456"
        assert result.title == "Test Album"
        assert result.release_date == "2023-01-01"
        assert result.duration == 3600
        assert result.number_of_tracks == 12
        assert result.cover == "album_cover_url"

        # Test artist conversion
        assert len(result.artists) == 1
        assert result.artists[0].id == "789"
        assert result.artists[0].name == "Test Artist"

    @pytest.mark.asyncio
    async def test_convert_tidal_artist_success(self, service, sample_tidal_artist):
        """Test successful artist conversion."""
        result = await service._convert_tidal_artist(sample_tidal_artist)

        assert isinstance(result, Artist)
        assert result.id == "789"
        assert result.name == "Test Artist"
        assert result.picture == "artist_pic_url"
        assert result.popularity == 85

    @pytest.mark.asyncio
    async def test_convert_tidal_playlist_success(self, service, sample_tidal_playlist):
        """Test successful playlist conversion."""
        # Mock the tracks method to return empty list for simplicity
        sample_tidal_playlist.tracks.return_value = []

        result = await service._convert_tidal_playlist(
            sample_tidal_playlist, include_tracks=False
        )

        assert isinstance(result, Playlist)
        assert result.id == "12345678-1234-1234-1234-123456789abc"
        assert result.title == "Test Playlist"
        assert result.description == "A test playlist"
        assert result.creator == "Test User"
        assert result.number_of_tracks == 10
        assert result.duration == 2400
        assert result.public is True

    def test_is_uuid_valid(self, service):
        """Test UUID validation."""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        assert service._is_uuid(valid_uuid) is True

        invalid_uuid = "not-a-uuid"
        assert service._is_uuid(invalid_uuid) is False

        empty_string = ""
        assert service._is_uuid(empty_string) is False


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_authentication_failure_handling(self, service, mock_auth):
        """Test handling of authentication failures."""
        mock_auth.ensure_valid_token.side_effect = Exception("Auth error")

        results = await service.search_tracks("test")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_exception_handling(self, service, mock_tidal_session):
        """Test handling of search exceptions."""
        mock_tidal_session.search.side_effect = Exception("Search API error")

        results = await service.search_tracks("test")
        assert results == []

    @pytest.mark.asyncio
    async def test_conversion_error_handling(
        self, service, mock_tidal_session, sample_tidal_track
    ):
        """Test handling of conversion errors."""
        mock_tidal_session.search.return_value = {"tracks": [sample_tidal_track]}

        with patch.object(
            service,
            "_convert_tidal_track",
            new_callable=AsyncMock,
            side_effect=Exception("Conversion error"),
        ):
            results = await service.search_tracks("test")
            # Should skip tracks that fail conversion
            assert results == []

    @pytest.mark.asyncio
    async def test_playlist_operation_error_handling(self, service, mock_tidal_session):
        """Test handling of playlist operation errors."""
        mock_tidal_session.playlist.side_effect = Exception("Playlist API error")

        result = await service.get_playlist("test-playlist")
        assert result is None


@pytest.mark.unit
class TestAsyncToSyncDecorator:
    """Test the async_to_sync decorator."""

    @pytest.mark.asyncio
    async def test_async_to_sync_decorator(self):
        """Test the async_to_sync decorator functionality."""

        @async_to_sync
        def sync_function(x, y):
            return x + y

        result = await sync_function(2, 3)
        assert result == 5

    @pytest.mark.asyncio
    async def test_async_to_sync_with_exception(self):
        """Test async_to_sync decorator with exception."""

        @async_to_sync
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await failing_function()


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
