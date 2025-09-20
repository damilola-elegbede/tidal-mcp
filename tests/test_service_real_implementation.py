"""
Comprehensive tests for the REAL service.py implementation to increase coverage.

These tests use the actual TidalService class with mocked external dependencies.
Focus on testing business logic, error handling, and data conversion.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.tidal_mcp.auth import TidalAuth
from src.tidal_mcp.models import Album, Artist, Playlist, SearchResults, Track
from src.tidal_mcp.service import TidalService


class TestRealTidalServiceImplementation:
    """Test the actual TidalService implementation."""

    @pytest.mark.asyncio
    async def test_search_tracks_real_implementation(self):
        """Test the actual search_tracks method implementation."""
        # Create real TidalService with mocked auth
        mock_auth = Mock(spec=TidalAuth)
        mock_auth.ensure_valid_token = AsyncMock(return_value=True)

        # Mock session and search result
        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        # Create mock tidal track with all necessary attributes
        mock_tidal_track = Mock()
        mock_tidal_track.id = 123456
        mock_tidal_track.name = "Test Song"
        mock_tidal_track.duration = 210
        mock_tidal_track.track_num = 1
        mock_tidal_track.volume_num = 1
        mock_tidal_track.explicit = False
        mock_tidal_track.audio_quality = "LOSSLESS"

        # Mock artist
        mock_artist = Mock()
        mock_artist.id = 67890
        mock_artist.name = "Test Artist"
        mock_artist.picture = None
        mock_artist.popularity = None
        mock_tidal_track.artist = mock_artist
        mock_tidal_track.artists = [mock_artist]

        # Mock album
        mock_album = Mock()
        mock_album.id = 11111
        mock_album.name = "Test Album"
        mock_album.release_date = "2023-01-01"
        mock_album.duration = 2400
        mock_album.num_tracks = 12
        mock_album.image = None
        mock_album.explicit = False
        mock_album.artist = mock_artist
        mock_album.artists = [mock_artist]
        mock_tidal_track.album = mock_album

        search_result = {"tracks": [mock_tidal_track]}
        mock_session.search.return_value = search_result

        # Create REAL service instance
        service = TidalService(mock_auth)

        # Mock sanitize_query to return the query as-is
        with patch('src.tidal_mcp.service.sanitize_query', return_value="test query"):
            tracks = await service.search_tracks("test query", limit=10)

        # Verify the real implementation worked
        assert len(tracks) == 1
        assert tracks[0].title == "Test Song"
        assert tracks[0].id == "123456"
        assert len(tracks[0].artists) == 1
        assert tracks[0].artists[0].name == "Test Artist"
        mock_session.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_albums_real_implementation(self):
        """Test the actual search_albums method implementation."""
        mock_auth = Mock(spec=TidalAuth)
        mock_auth.ensure_valid_token = AsyncMock(return_value=True)

        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        # Create mock tidal album
        mock_tidal_album = Mock()
        mock_tidal_album.id = 11111
        mock_tidal_album.name = "Test Album"
        mock_tidal_album.release_date = "2023-01-01"
        mock_tidal_album.duration = 2400
        mock_tidal_album.num_tracks = 12
        mock_tidal_album.image = None
        mock_tidal_album.explicit = False

        # Mock artist
        mock_artist = Mock()
        mock_artist.id = 67890
        mock_artist.name = "Test Artist"
        mock_artist.picture = None
        mock_artist.popularity = None
        mock_tidal_album.artist = mock_artist
        mock_tidal_album.artists = [mock_artist]

        search_result = {"albums": [mock_tidal_album]}
        mock_session.search.return_value = search_result

        # Create REAL service instance
        service = TidalService(mock_auth)

        with patch('src.tidal_mcp.service.sanitize_query', return_value="test album"):
            albums = await service.search_albums("test album")

        assert len(albums) == 1
        assert albums[0].title == "Test Album"
        assert albums[0].id == "11111"
        assert len(albums[0].artists) == 1

    @pytest.mark.asyncio
    async def test_search_artists_real_implementation(self):
        """Test the actual search_artists method implementation."""
        mock_auth = Mock(spec=TidalAuth)
        mock_auth.ensure_valid_token = AsyncMock(return_value=True)

        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        # Create mock tidal artist
        mock_tidal_artist = Mock()
        mock_tidal_artist.id = 67890
        mock_tidal_artist.name = "Test Artist"
        mock_tidal_artist.picture = None
        mock_tidal_artist.popularity = 85

        search_result = {"artists": [mock_tidal_artist]}
        mock_session.search.return_value = search_result

        # Create REAL service instance
        service = TidalService(mock_auth)

        with patch('src.tidal_mcp.service.sanitize_query', return_value="test artist"):
            artists = await service.search_artists("test artist")

        assert len(artists) == 1
        assert artists[0].name == "Test Artist"
        assert artists[0].id == "67890"
        assert artists[0].popularity == 85

    @pytest.mark.asyncio
    async def test_search_playlists_real_implementation(self):
        """Test the actual search_playlists method implementation."""
        mock_auth = Mock(spec=TidalAuth)
        mock_auth.ensure_valid_token = AsyncMock(return_value=True)

        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        # Create mock tidal playlist
        mock_tidal_playlist = Mock()
        mock_tidal_playlist.uuid = "test-playlist-uuid"
        mock_tidal_playlist.id = "test-playlist-uuid"
        mock_tidal_playlist.name = "Test Playlist"
        mock_tidal_playlist.description = "A test playlist"
        mock_tidal_playlist.num_tracks = 10
        mock_tidal_playlist.duration = 2100
        mock_tidal_playlist.created = "2023-01-01T00:00:00Z"
        mock_tidal_playlist.last_updated = "2023-01-02T00:00:00Z"
        mock_tidal_playlist.image = None
        mock_tidal_playlist.public = True
        mock_tidal_playlist.creator = {"name": "Test User"}

        search_result = {"playlists": [mock_tidal_playlist]}
        mock_session.search.return_value = search_result

        # Create REAL service instance
        service = TidalService(mock_auth)

        with patch('src.tidal_mcp.service.sanitize_query', return_value="test playlist"):
            playlists = await service.search_playlists("test playlist")

        assert len(playlists) == 1
        assert playlists[0].title == "Test Playlist"
        assert playlists[0].id == "test-playlist-uuid"

    @pytest.mark.asyncio
    async def test_search_all_real_implementation(self):
        """Test the actual search_all method implementation."""
        mock_auth = Mock(spec=TidalAuth)

        # Create REAL service instance
        service = TidalService(mock_auth)

        # Mock individual search methods to return specific results
        with patch.object(service, 'search_tracks') as mock_search_tracks, \
             patch.object(service, 'search_albums') as mock_search_albums, \
             patch.object(service, 'search_artists') as mock_search_artists, \
             patch.object(service, 'search_playlists') as mock_search_playlists:

            # Set up return values
            mock_track = Track(id="1", title="Track", artists=[], duration=180)
            mock_album = Album(id="2", title="Album", artists=[], number_of_tracks=10)
            mock_artist = Artist(id="3", name="Artist")
            mock_playlist = Playlist(id="4", title="Playlist", number_of_tracks=5)

            mock_search_tracks.return_value = [mock_track]
            mock_search_albums.return_value = [mock_album]
            mock_search_artists.return_value = [mock_artist]
            mock_search_playlists.return_value = [mock_playlist]

            results = await service.search_all("test query", limit=5)

            assert isinstance(results, SearchResults)
            assert len(results.tracks) == 1
            assert len(results.albums) == 1
            assert len(results.artists) == 1
            assert len(results.playlists) == 1
            assert results.total_results == 4

    @pytest.mark.asyncio
    async def test_get_playlist_real_implementation(self):
        """Test the actual get_playlist method implementation."""
        mock_auth = Mock(spec=TidalAuth)
        mock_auth.ensure_valid_token = AsyncMock(return_value=True)

        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        # Create mock tidal playlist
        mock_tidal_playlist = Mock()
        mock_tidal_playlist.uuid = "test-playlist-uuid"
        mock_tidal_playlist.name = "Test Playlist"
        mock_tidal_playlist.description = "A test playlist"
        mock_tidal_playlist.num_tracks = 0
        mock_tidal_playlist.duration = 0
        mock_tidal_playlist.created = "2023-01-01T00:00:00Z"
        mock_tidal_playlist.last_updated = "2023-01-02T00:00:00Z"
        mock_tidal_playlist.image = None
        mock_tidal_playlist.public = True
        mock_tidal_playlist.creator = {"name": "Test User"}

        mock_session.playlist.return_value = mock_tidal_playlist

        # Create REAL service instance
        service = TidalService(mock_auth)

        with patch('src.tidal_mcp.service.validate_tidal_id', return_value=True):
            playlist = await service.get_playlist("123456")

        assert playlist is not None
        assert playlist.title == "Test Playlist"
        assert playlist.id == "test-playlist-uuid"

    @pytest.mark.asyncio
    async def test_create_playlist_real_implementation(self):
        """Test the actual create_playlist method implementation."""
        mock_auth = Mock(spec=TidalAuth)
        mock_auth.ensure_valid_token = AsyncMock(return_value=True)

        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        # Mock created playlist
        mock_tidal_playlist = Mock()
        mock_tidal_playlist.uuid = "new-playlist-uuid"
        mock_tidal_playlist.name = "New Playlist"
        mock_tidal_playlist.description = "A new playlist"
        mock_tidal_playlist.num_tracks = 0
        mock_tidal_playlist.duration = 0
        mock_tidal_playlist.created = "2023-01-01T00:00:00Z"
        mock_tidal_playlist.last_updated = "2023-01-01T00:00:00Z"
        mock_tidal_playlist.image = None
        mock_tidal_playlist.public = True
        mock_tidal_playlist.creator = {"name": "Test User"}

        mock_session.user.create_playlist.return_value = mock_tidal_playlist

        # Create REAL service instance
        service = TidalService(mock_auth)
        playlist = await service.create_playlist("New Playlist", "A new playlist")

        assert playlist is not None
        assert playlist.title == "New Playlist"
        assert playlist.description == "A new playlist"

    @pytest.mark.asyncio
    async def test_add_tracks_to_playlist_real_implementation(self):
        """Test the actual add_tracks_to_playlist method implementation."""
        mock_auth = Mock(spec=TidalAuth)
        mock_auth.ensure_valid_token = AsyncMock(return_value=True)

        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        # Mock playlist
        mock_playlist = Mock()
        mock_playlist.add.return_value = True
        mock_session.playlist.return_value = mock_playlist

        # Mock tracks
        mock_track = Mock()
        mock_session.track.return_value = mock_track

        # Create REAL service instance
        service = TidalService(mock_auth)

        with patch('src.tidal_mcp.service.validate_tidal_id', return_value=True):
            result = await service.add_tracks_to_playlist("playlist-123", ["12345", "67890"])

        assert result is True

    @pytest.mark.asyncio
    async def test_get_user_favorites_real_implementation(self):
        """Test the actual get_user_favorites method implementation."""
        mock_auth = Mock(spec=TidalAuth)
        mock_auth.ensure_valid_token = AsyncMock(return_value=True)

        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        # Create mock favorite track
        mock_tidal_track = Mock()
        mock_tidal_track.id = 12345
        mock_tidal_track.name = "Favorite Track"
        mock_tidal_track.duration = 210
        mock_tidal_track.track_num = 1
        mock_tidal_track.volume_num = 1
        mock_tidal_track.explicit = False
        mock_tidal_track.audio_quality = "LOSSLESS"

        # Mock artist
        mock_artist = Mock()
        mock_artist.id = 67890
        mock_artist.name = "Artist"
        mock_artist.picture = None
        mock_artist.popularity = None
        mock_tidal_track.artist = mock_artist
        mock_tidal_track.artists = [mock_artist]

        # Mock album
        mock_album = Mock()
        mock_album.id = 11111
        mock_album.name = "Album"
        mock_album.release_date = None
        mock_album.duration = None
        mock_album.num_tracks = None
        mock_album.image = None
        mock_album.explicit = False
        mock_album.artist = mock_artist
        mock_album.artists = [mock_artist]
        mock_tidal_track.album = mock_album

        mock_session.user.favorites.tracks.return_value = [mock_tidal_track]

        # Create REAL service instance
        service = TidalService(mock_auth)
        favorites = await service.get_user_favorites("tracks")

        assert len(favorites) == 1
        assert favorites[0].title == "Favorite Track"

    @pytest.mark.asyncio
    async def test_add_to_favorites_real_implementation(self):
        """Test the actual add_to_favorites method implementation."""
        mock_auth = Mock(spec=TidalAuth)
        mock_auth.ensure_valid_token = AsyncMock(return_value=True)

        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        # Mock track and favorites
        mock_track = Mock()
        mock_session.track.return_value = mock_track
        mock_session.user.favorites.add_track.return_value = True

        # Create REAL service instance
        service = TidalService(mock_auth)

        with patch('src.tidal_mcp.service.validate_tidal_id', return_value=True):
            result = await service.add_to_favorites("12345", "track")

        assert result is True

    @pytest.mark.asyncio
    async def test_get_track_radio_real_implementation(self):
        """Test the actual get_track_radio method implementation."""
        mock_auth = Mock(spec=TidalAuth)
        mock_auth.ensure_valid_token = AsyncMock(return_value=True)

        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        # Create mock radio track
        mock_radio_track = Mock()
        mock_radio_track.id = 99999
        mock_radio_track.name = "Radio Track"
        mock_radio_track.duration = 200
        mock_radio_track.track_num = 1
        mock_radio_track.volume_num = 1
        mock_radio_track.explicit = False
        mock_radio_track.audio_quality = "LOSSLESS"

        # Mock artist
        mock_artist = Mock()
        mock_artist.id = 67890
        mock_artist.name = "Artist"
        mock_artist.picture = None
        mock_artist.popularity = None
        mock_radio_track.artist = mock_artist
        mock_radio_track.artists = [mock_artist]

        # Mock album
        mock_album = Mock()
        mock_album.id = 11111
        mock_album.name = "Album"
        mock_album.release_date = None
        mock_album.duration = None
        mock_album.num_tracks = None
        mock_album.image = None
        mock_album.explicit = False
        mock_album.artist = mock_artist
        mock_album.artists = [mock_artist]
        mock_radio_track.album = mock_album

        # Mock seed track
        mock_seed_track = Mock()
        mock_seed_track.get_track_radio.return_value = [mock_radio_track]
        mock_session.track.return_value = mock_seed_track

        # Create REAL service instance
        service = TidalService(mock_auth)

        with patch('src.tidal_mcp.service.validate_tidal_id', return_value=True):
            radio_tracks = await service.get_track_radio("12345", limit=25)

        assert len(radio_tracks) == 1
        assert radio_tracks[0].title == "Radio Track"

    @pytest.mark.asyncio
    async def test_get_recommended_tracks_real_implementation(self):
        """Test the actual get_recommended_tracks method implementation."""
        mock_auth = Mock(spec=TidalAuth)
        mock_auth.ensure_valid_token = AsyncMock(return_value=True)

        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        # Mock no favorites, use featured tracks
        mock_session.user.favorites.tracks.return_value = []

        # Mock featured tracks
        mock_featured_track = Mock()
        mock_featured_track.id = 77777
        mock_featured_track.name = "Featured Track"
        mock_featured_track.duration = 200
        mock_featured_track.track_num = 1
        mock_featured_track.volume_num = 1
        mock_featured_track.explicit = False
        mock_featured_track.audio_quality = "LOSSLESS"

        # Mock artist
        mock_artist = Mock()
        mock_artist.id = 67890
        mock_artist.name = "Artist"
        mock_artist.picture = None
        mock_artist.popularity = None
        mock_featured_track.artist = mock_artist
        mock_featured_track.artists = [mock_artist]

        # Mock album
        mock_album = Mock()
        mock_album.id = 11111
        mock_album.name = "Album"
        mock_album.release_date = None
        mock_album.duration = None
        mock_album.num_tracks = None
        mock_album.image = None
        mock_album.explicit = False
        mock_album.artist = mock_artist
        mock_album.artists = [mock_artist]
        mock_featured_track.album = mock_album

        mock_featured = Mock()
        mock_featured.tracks = [mock_featured_track]
        mock_session.featured.return_value = mock_featured

        # Create REAL service instance
        service = TidalService(mock_auth)
        recommendations = await service.get_recommended_tracks(limit=15)

        assert len(recommendations) == 1
        assert recommendations[0].title == "Featured Track"

    @pytest.mark.asyncio
    async def test_get_track_real_implementation(self):
        """Test the actual get_track method implementation."""
        mock_auth = Mock(spec=TidalAuth)
        mock_auth.ensure_valid_token = AsyncMock(return_value=True)

        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        # Create mock track
        mock_tidal_track = Mock()
        mock_tidal_track.id = 12345
        mock_tidal_track.name = "Retrieved Track"
        mock_tidal_track.duration = 210
        mock_tidal_track.track_num = 1
        mock_tidal_track.volume_num = 1
        mock_tidal_track.explicit = False
        mock_tidal_track.audio_quality = "LOSSLESS"

        # Mock artist
        mock_artist = Mock()
        mock_artist.id = 67890
        mock_artist.name = "Artist"
        mock_artist.picture = None
        mock_artist.popularity = None
        mock_tidal_track.artist = mock_artist
        mock_tidal_track.artists = [mock_artist]

        # Mock album
        mock_album = Mock()
        mock_album.id = 11111
        mock_album.name = "Album"
        mock_album.release_date = None
        mock_album.duration = None
        mock_album.num_tracks = None
        mock_album.image = None
        mock_album.explicit = False
        mock_album.artist = mock_artist
        mock_album.artists = [mock_artist]
        mock_tidal_track.album = mock_album

        mock_session.track.return_value = mock_tidal_track

        # Create REAL service instance
        service = TidalService(mock_auth)

        with patch('src.tidal_mcp.service.validate_tidal_id', return_value=True):
            track = await service.get_track("12345")

        assert track is not None
        assert track.title == "Retrieved Track"
        assert track.id == "12345"

    @pytest.mark.asyncio
    async def test_get_user_profile_real_implementation(self):
        """Test the actual get_user_profile method implementation."""
        mock_auth = Mock(spec=TidalAuth)
        mock_auth.ensure_valid_token = AsyncMock(return_value=True)

        mock_user_info = {
            "id": 12345,
            "username": "testuser",
            "country_code": "US",
            "subscription": {"type": "HiFi", "valid": True}
        }
        mock_auth.get_user_info.return_value = mock_user_info

        # Create REAL service instance
        service = TidalService(mock_auth)
        profile = await service.get_user_profile()

        assert profile == mock_user_info

    def test_is_uuid_real_implementation(self):
        """Test the actual _is_uuid method implementation."""
        mock_auth = Mock(spec=TidalAuth)

        # Create REAL service instance
        service = TidalService(mock_auth)

        # Test valid UUID
        valid_uuid = "123e4567-e89b-12d3-a456-426614174000"
        assert service._is_uuid(valid_uuid) is True

        # Test invalid UUID
        invalid_uuid = "not-a-uuid"
        assert service._is_uuid(invalid_uuid) is False

        # Test empty string
        assert service._is_uuid("") is False

    @pytest.mark.asyncio
    async def test_conversion_methods_real_implementation(self):
        """Test the actual conversion methods implementation."""
        mock_auth = Mock(spec=TidalAuth)

        # Create REAL service instance
        service = TidalService(mock_auth)

        # Test track conversion with full data
        mock_tidal_track = Mock()
        mock_tidal_track.id = 12345
        mock_tidal_track.name = "Test Song"
        mock_tidal_track.duration = 210
        mock_tidal_track.track_num = 1
        mock_tidal_track.volume_num = 1
        mock_tidal_track.explicit = False
        mock_tidal_track.audio_quality = "LOSSLESS"

        # Full artist data
        mock_artist = Mock()
        mock_artist.id = 67890
        mock_artist.name = "Test Artist"
        mock_artist.picture = "https://example.com/artist.jpg"
        mock_artist.popularity = 85
        mock_tidal_track.artist = mock_artist
        mock_tidal_track.artists = [mock_artist]

        # Full album data
        mock_album = Mock()
        mock_album.id = 11111
        mock_album.name = "Test Album"
        mock_album.release_date = "2023-01-01"
        mock_album.duration = 2400
        mock_album.num_tracks = 12
        mock_album.image = "https://example.com/album.jpg"
        mock_album.explicit = False
        mock_album.artist = mock_artist
        mock_album.artists = [mock_artist]
        mock_tidal_track.album = mock_album

        track = await service._convert_tidal_track(mock_tidal_track)

        assert isinstance(track, Track)
        assert track.id == "12345"
        assert track.title == "Test Song"
        assert track.duration == 210
        assert len(track.artists) == 1
        assert track.artists[0].name == "Test Artist"
        assert track.album is not None
        assert track.album.title == "Test Album"

    @pytest.mark.asyncio
    async def test_conversion_error_handling_real_implementation(self):
        """Test conversion methods handle errors gracefully in real implementation."""
        mock_auth = Mock(spec=TidalAuth)

        # Create REAL service instance
        service = TidalService(mock_auth)

        # Test with object that will cause conversion error
        invalid_track = Mock()
        # Delete required attribute to cause error
        del invalid_track.id

        track = await service._convert_tidal_track(invalid_track)
        assert track is None

    @pytest.mark.asyncio
    async def test_search_error_handling_real_implementation(self):
        """Test search methods handle errors gracefully in real implementation."""
        mock_auth = Mock(spec=TidalAuth)
        mock_auth.ensure_valid_token = AsyncMock(side_effect=Exception("General error"))

        # Create REAL service instance
        service = TidalService(mock_auth)
        tracks = await service.search_tracks("test query")

        assert tracks == []

    @pytest.mark.asyncio
    async def test_empty_query_handling_real_implementation(self):
        """Test search methods handle empty queries in real implementation."""
        mock_auth = Mock(spec=TidalAuth)
        mock_auth.ensure_valid_token = AsyncMock(return_value=True)

        # Create REAL service instance
        service = TidalService(mock_auth)

        with patch('src.tidal_mcp.service.sanitize_query', return_value=""):
            tracks = await service.search_tracks("")

        assert tracks == []

    @pytest.mark.asyncio
    async def test_pagination_real_implementation(self):
        """Test pagination in search methods with real implementation."""
        mock_auth = Mock(spec=TidalAuth)
        mock_auth.ensure_valid_token = AsyncMock(return_value=True)

        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        # Create 25 mock tracks to test pagination
        mock_tracks = []
        for i in range(25):
            mock_track = Mock()
            mock_track.id = i
            mock_track.name = f"Song {i}"
            mock_track.duration = 180
            mock_track.track_num = 1
            mock_track.volume_num = 1
            mock_track.explicit = False
            mock_track.audio_quality = "LOSSLESS"

            # Simple artist mock
            mock_artist = Mock()
            mock_artist.id = 999
            mock_artist.name = "Artist"
            mock_artist.picture = None
            mock_artist.popularity = None
            mock_track.artist = mock_artist
            mock_track.artists = [mock_artist]

            # Simple album mock
            mock_album = Mock()
            mock_album.id = 888
            mock_album.name = "Album"
            mock_album.release_date = None
            mock_album.duration = None
            mock_album.num_tracks = None
            mock_album.image = None
            mock_album.explicit = False
            mock_album.artist = mock_artist
            mock_album.artists = [mock_artist]
            mock_track.album = mock_album

            mock_tracks.append(mock_track)

        search_result = {"tracks": mock_tracks}
        mock_session.search.return_value = search_result

        # Create REAL service instance
        service = TidalService(mock_auth)

        with patch('src.tidal_mcp.service.sanitize_query', return_value="test"):
            tracks = await service.search_tracks("test", limit=10, offset=5)

        # Should get tracks 5-14 (10 tracks starting from offset 5)
        assert len(tracks) == 10
        assert tracks[0].title == "Song 5"

    @pytest.mark.asyncio
    async def test_get_user_playlists_real_implementation(self):
        """Test the actual get_user_playlists method implementation."""
        mock_auth = Mock(spec=TidalAuth)
        mock_auth.ensure_valid_token = AsyncMock(return_value=True)

        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        # Create mock playlist
        mock_tidal_playlist = Mock()
        mock_tidal_playlist.uuid = "user-playlist-uuid"
        mock_tidal_playlist.name = "My Playlist"
        mock_tidal_playlist.description = "User's playlist"
        mock_tidal_playlist.num_tracks = 5
        mock_tidal_playlist.duration = 1200
        mock_tidal_playlist.created = "2023-01-01T00:00:00Z"
        mock_tidal_playlist.last_updated = "2023-01-02T00:00:00Z"
        mock_tidal_playlist.image = None
        mock_tidal_playlist.public = True
        mock_tidal_playlist.creator = {"name": "Test User"}

        mock_session.user.playlists.return_value = [mock_tidal_playlist]

        # Create REAL service instance
        service = TidalService(mock_auth)
        playlists = await service.get_user_playlists()

        assert len(playlists) == 1
        assert playlists[0].title == "My Playlist"

    @pytest.mark.asyncio
    async def test_get_album_tracks_real_implementation(self):
        """Test the actual get_album_tracks method implementation."""
        mock_auth = Mock(spec=TidalAuth)
        mock_auth.ensure_valid_token = AsyncMock(return_value=True)

        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        # Mock album with tracks
        mock_album = Mock()

        # Mock track
        mock_tidal_track = Mock()
        mock_tidal_track.id = 12345
        mock_tidal_track.name = "Album Track"
        mock_tidal_track.duration = 180
        mock_tidal_track.track_num = 1
        mock_tidal_track.volume_num = 1
        mock_tidal_track.explicit = False
        mock_tidal_track.audio_quality = "LOSSLESS"

        # Mock artist
        mock_artist = Mock()
        mock_artist.id = 67890
        mock_artist.name = "Artist"
        mock_artist.picture = None
        mock_artist.popularity = None
        mock_tidal_track.artist = mock_artist
        mock_tidal_track.artists = [mock_artist]

        # Mock album for track
        mock_track_album = Mock()
        mock_track_album.id = 11111
        mock_track_album.name = "Album"
        mock_track_album.release_date = None
        mock_track_album.duration = None
        mock_track_album.num_tracks = None
        mock_track_album.image = None
        mock_track_album.explicit = False
        mock_track_album.artist = mock_artist
        mock_track_album.artists = [mock_artist]
        mock_tidal_track.album = mock_track_album

        mock_album.tracks.return_value = [mock_tidal_track]
        mock_session.album.return_value = mock_album

        # Create REAL service instance
        service = TidalService(mock_auth)

        with patch('src.tidal_mcp.service.validate_tidal_id', return_value=True):
            tracks = await service.get_album_tracks("11111")

        assert len(tracks) == 1
        assert tracks[0].title == "Album Track"

    @pytest.mark.asyncio
    async def test_get_artist_albums_real_implementation(self):
        """Test the actual get_artist_albums method implementation."""
        mock_auth = Mock(spec=TidalAuth)
        mock_auth.ensure_valid_token = AsyncMock(return_value=True)

        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        # Mock artist
        mock_artist = Mock()

        # Mock album
        mock_tidal_album = Mock()
        mock_tidal_album.id = 11111
        mock_tidal_album.name = "Artist Album"
        mock_tidal_album.release_date = "2023-01-01"
        mock_tidal_album.duration = 2400
        mock_tidal_album.num_tracks = 12
        mock_tidal_album.image = None
        mock_tidal_album.explicit = False

        # Mock album artist
        mock_album_artist = Mock()
        mock_album_artist.id = 67890
        mock_album_artist.name = "Artist"
        mock_album_artist.picture = None
        mock_album_artist.popularity = None
        mock_tidal_album.artist = mock_album_artist
        mock_tidal_album.artists = [mock_album_artist]

        mock_artist.get_albums.return_value = [mock_tidal_album]
        mock_session.artist.return_value = mock_artist

        # Create REAL service instance
        service = TidalService(mock_auth)

        with patch('src.tidal_mcp.service.validate_tidal_id', return_value=True):
            albums = await service.get_artist_albums("67890")

        assert len(albums) == 1
        assert albums[0].title == "Artist Album"

    @pytest.mark.asyncio
    async def test_get_artist_top_tracks_real_implementation(self):
        """Test the actual get_artist_top_tracks method implementation."""
        mock_auth = Mock(spec=TidalAuth)
        mock_auth.ensure_valid_token = AsyncMock(return_value=True)

        mock_session = Mock()
        mock_auth.get_tidal_session.return_value = mock_session

        # Mock artist
        mock_artist = Mock()

        # Mock top track
        mock_tidal_track = Mock()
        mock_tidal_track.id = 12345
        mock_tidal_track.name = "Top Track"
        mock_tidal_track.duration = 210
        mock_tidal_track.track_num = 1
        mock_tidal_track.volume_num = 1
        mock_tidal_track.explicit = False
        mock_tidal_track.audio_quality = "LOSSLESS"

        # Mock artist for track
        mock_track_artist = Mock()
        mock_track_artist.id = 67890
        mock_track_artist.name = "Artist"
        mock_track_artist.picture = None
        mock_track_artist.popularity = None
        mock_tidal_track.artist = mock_track_artist
        mock_tidal_track.artists = [mock_track_artist]

        # Mock album for track
        mock_track_album = Mock()
        mock_track_album.id = 11111
        mock_track_album.name = "Album"
        mock_track_album.release_date = None
        mock_track_album.duration = None
        mock_track_album.num_tracks = None
        mock_track_album.image = None
        mock_track_album.explicit = False
        mock_track_album.artist = mock_track_artist
        mock_track_album.artists = [mock_track_artist]
        mock_tidal_track.album = mock_track_album

        mock_artist.get_top_tracks.return_value = [mock_tidal_track]
        mock_session.artist.return_value = mock_artist

        # Create REAL service instance
        service = TidalService(mock_auth)

        with patch('src.tidal_mcp.service.validate_tidal_id', return_value=True):
            tracks = await service.get_artist_top_tracks("67890")

        assert len(tracks) == 1
        assert tracks[0].title == "Top Track"
