"""
Tests for Tidal MCP Integration

End-to-end integration tests that combine authentication, service layer,
and external API interactions in realistic usage scenarios.
"""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import tidalapi

from tidal_mcp.auth import TidalAuth, TidalAuthError
from tidal_mcp.service import TidalService
from tidal_mcp.models import Track, Album, Artist, Playlist, SearchResults


@pytest.fixture
def temp_session_file():
    """Create a temporary session file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    yield temp_path
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def mock_tidal_session():
    """Create a comprehensive mock tidalapi session."""
    session = Mock(spec=tidalapi.Session)
    
    # Mock user with realistic data
    user = Mock()
    user.id = 12345
    user.country_code = 'US'
    user.username = 'testuser'
    user.subscription = {'type': 'HiFi', 'valid': True}
    
    # Mock favorites
    favorites = Mock()
    favorites.tracks = Mock(return_value=[])
    favorites.albums = Mock(return_value=[])
    favorites.artists = Mock(return_value=[])
    favorites.playlists = Mock(return_value=[])
    favorites.add_track = Mock(return_value=True)
    favorites.add_album = Mock(return_value=True)
    favorites.add_artist = Mock(return_value=True)
    favorites.add_playlist = Mock(return_value=True)
    favorites.remove_track = Mock(return_value=True)
    favorites.remove_album = Mock(return_value=True)
    favorites.remove_artist = Mock(return_value=True)
    favorites.remove_playlist = Mock(return_value=True)
    user.favorites = favorites
    
    # Mock user playlists
    user.playlists = Mock(return_value=[])
    user.create_playlist = Mock()
    
    session.user = user
    session.load_oauth_session.return_value = True
    
    # Mock API methods
    session.search = Mock(return_value={'tracks': [], 'albums': [], 'artists': [], 'playlists': []})
    session.track = Mock()
    session.album = Mock()
    session.artist = Mock()
    session.playlist = Mock()
    session.featured = Mock()
    
    return session


@pytest.fixture
def integrated_auth(temp_session_file, mock_tidal_session):
    """Create an integrated TidalAuth instance with mocked dependencies."""
    with patch.object(Path, 'home') as mock_home:
        mock_home.return_value = temp_session_file.parent
        
        auth = TidalAuth(client_id="test_client")
        auth.session_file = temp_session_file
        
        # Set up authenticated state
        auth.access_token = "test_access_token"
        auth.refresh_token = "test_refresh_token"
        auth.user_id = "12345"
        auth.country_code = "US"
        auth.token_expires_at = datetime.now() + timedelta(hours=1)
        auth.tidal_session = mock_tidal_session
        
        return auth


@pytest.fixture
def integrated_service(integrated_auth):
    """Create an integrated TidalService instance."""
    return TidalService(auth=integrated_auth)


def create_sample_tidal_track(track_id=123456, name="Test Track", artist_name="Test Artist"):
    """Create a sample tidalapi track for testing."""
    track = Mock()
    track.id = track_id
    track.name = name
    track.duration = 240
    track.track_num = 1
    track.volume_num = 1
    track.explicit = False
    track.audio_quality = "LOSSLESS"
    
    # Mock artist
    artist = Mock()
    artist.id = 789
    artist.name = artist_name
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


def create_sample_tidal_playlist(playlist_id="playlist-uuid-123", name="Test Playlist"):
    """Create a sample tidalapi playlist for testing."""
    playlist = Mock()
    playlist.uuid = playlist_id
    playlist.id = playlist_id
    playlist.name = name
    playlist.description = f"Description for {name}"
    playlist.num_tracks = 10
    playlist.duration = 2400
    playlist.image = "playlist_image_url"
    playlist.public = True
    playlist.created = "2023-01-01T00:00:00Z"
    playlist.last_updated = "2023-01-02T00:00:00Z"
    playlist.creator = {'name': 'Test User'}
    
    # Mock methods
    playlist.tracks = Mock(return_value=[])
    playlist.add = Mock(return_value=True)
    playlist.remove_by_index = Mock(return_value=True)
    playlist.delete = Mock(return_value=True)
    
    return playlist


class TestAuthenticationFlow:
    """Test complete authentication flows."""
    
    @pytest.mark.asyncio
    async def test_full_oauth_authentication_flow(self, temp_session_file, mock_tidal_session):
        """Test complete OAuth2 PKCE authentication flow."""
        with patch.object(Path, 'home') as mock_home:
            mock_home.return_value = temp_session_file.parent
            
            # Create auth instance
            auth = TidalAuth()
            auth.session_file = temp_session_file
            
            # Mock OAuth2 flow components
            with patch.object(auth, '_capture_auth_code', new_callable=AsyncMock, return_value='auth_code'), \
                 patch('webbrowser.open'), \
                 patch('tidalapi.Session', return_value=mock_tidal_session):
                
                # Mock token exchange response
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json = AsyncMock(return_value={
                    'access_token': 'new_access_token',
                    'refresh_token': 'new_refresh_token',
                    'expires_in': 3600
                })
                
                mock_session = AsyncMock()
                mock_session.post.return_value.__aenter__.return_value = mock_response
                
                with patch('aiohttp.ClientSession', return_value=mock_session):
                    # Perform authentication
                    result = await auth.authenticate()
                    
                    # Verify successful authentication
                    assert result is True
                    assert auth.access_token == 'new_access_token'
                    assert auth.refresh_token == 'new_refresh_token'
                    assert auth.user_id == "12345"
                    assert auth.country_code == "US"
                    assert auth.is_authenticated()
                    
                    # Verify session was saved
                    assert auth.session_file.exists()
                    with open(auth.session_file, 'r') as f:
                        session_data = json.load(f)
                        assert session_data['access_token'] == 'new_access_token'
                        assert session_data['user_id'] == "12345"
    
    @pytest.mark.asyncio
    async def test_session_persistence_and_reload(self, temp_session_file, mock_tidal_session):
        """Test session persistence and automatic reload."""
        with patch.object(Path, 'home') as mock_home:
            mock_home.return_value = temp_session_file.parent
            
            # Create and save session data
            session_data = {
                'access_token': 'saved_access_token',
                'refresh_token': 'saved_refresh_token',
                'user_id': '12345',
                'country_code': 'US',
                'expires_at': (datetime.now() + timedelta(hours=1)).isoformat()
            }
            
            with open(temp_session_file, 'w') as f:
                json.dump(session_data, f)
            
            # Create new auth instance - should load existing session
            with patch('tidalapi.Session', return_value=mock_tidal_session):
                auth = TidalAuth()
                auth.session_file = temp_session_file
                
                # Should have loaded session data
                assert auth.access_token == 'saved_access_token'
                assert auth.refresh_token == 'saved_refresh_token'
                assert auth.user_id == '12345'
                
                # Should be able to authenticate with existing session
                result = await auth.authenticate()
                assert result is True
    
    @pytest.mark.asyncio
    async def test_token_refresh_flow(self, integrated_auth, mock_tidal_session):
        """Test automatic token refresh flow."""
        # Set token to expired
        integrated_auth.token_expires_at = datetime.now() - timedelta(minutes=1)
        
        # Mock refresh response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'access_token': 'refreshed_access_token',
            'refresh_token': 'new_refresh_token',
            'expires_in': 3600
        })
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            # Ensure valid token should trigger refresh
            result = await integrated_auth.ensure_valid_token()
            
            assert result is True
            assert integrated_auth.access_token == 'refreshed_access_token'
            assert integrated_auth.refresh_token == 'new_refresh_token'
            assert integrated_auth.is_authenticated()


class TestSearchIntegration:
    """Test integrated search functionality."""
    
    @pytest.mark.asyncio
    async def test_comprehensive_search_workflow(self, integrated_service, mock_tidal_session):
        """Test complete search workflow across all content types."""
        # Mock search results
        sample_track = create_sample_tidal_track(123456, "Search Track", "Search Artist")
        sample_album = Mock()
        sample_album.id = 789
        sample_album.name = "Search Album"
        sample_album.artists = [sample_track.artist]
        sample_album.release_date = "2023-01-01"
        sample_album.duration = 3600
        sample_album.num_tracks = 12
        sample_album.image = "album_cover"
        sample_album.explicit = False
        
        sample_artist = sample_track.artist
        sample_playlist = create_sample_tidal_playlist("search-playlist", "Search Playlist")
        
        mock_tidal_session.search.return_value = {
            'tracks': [sample_track],
            'albums': [sample_album],
            'artists': [sample_artist],
            'playlists': [sample_playlist]
        }
        
        # Perform comprehensive search
        results = await integrated_service.search_all("test query", limit=5)
        
        # Verify results
        assert isinstance(results, SearchResults)
        assert len(results.tracks) == 1
        assert len(results.albums) == 1
        assert len(results.artists) == 1
        assert len(results.playlists) == 1
        assert results.total_results == 4
        
        # Verify track data
        track = results.tracks[0]
        assert track.id == "123456"
        assert track.title == "Search Track"
        assert track.duration == 240
        assert len(track.artists) == 1
        assert track.artists[0].name == "Search Artist"
        
        # Verify album data
        album = results.albums[0]
        assert album.id == "789"
        assert album.title == "Search Album"
        
        # Verify artist data
        artist = results.artists[0]
        assert artist.id == "789"
        assert artist.name == "Search Artist"
        
        # Verify playlist data
        playlist = results.playlists[0]
        assert playlist.id == "search-playlist"
        assert playlist.title == "Search Playlist"
    
    @pytest.mark.asyncio
    async def test_search_with_pagination(self, integrated_service, mock_tidal_session):
        """Test search with pagination support."""
        # Create multiple tracks
        tracks = [
            create_sample_tidal_track(i, f"Track {i}", f"Artist {i}")
            for i in range(10)
        ]
        
        mock_tidal_session.search.return_value = {'tracks': tracks}
        
        # Search with pagination
        page1 = await integrated_service.search_tracks("query", limit=3, offset=0)
        page2 = await integrated_service.search_tracks("query", limit=3, offset=3)
        
        assert len(page1) == 3
        assert len(page2) == 3
        assert page1[0].id != page2[0].id  # Different tracks
    
    @pytest.mark.asyncio
    async def test_search_error_recovery(self, integrated_service, mock_tidal_session):
        """Test search error handling and recovery."""
        # First call fails, second succeeds
        mock_tidal_session.search.side_effect = [
            Exception("Network error"),
            {'tracks': [create_sample_tidal_track()]}
        ]
        
        # First search should return empty results
        results1 = await integrated_service.search_tracks("query")
        assert results1 == []
        
        # Second search should succeed
        results2 = await integrated_service.search_tracks("query")
        assert len(results2) == 1


class TestPlaylistManagementIntegration:
    """Test integrated playlist management."""
    
    @pytest.mark.asyncio
    async def test_complete_playlist_lifecycle(self, integrated_service, mock_tidal_session):
        """Test complete playlist management lifecycle."""
        # Mock playlist creation
        new_playlist = create_sample_tidal_playlist("new-playlist", "My New Playlist")
        mock_tidal_session.user.create_playlist.return_value = new_playlist
        
        # 1. Create playlist
        created_playlist = await integrated_service.create_playlist("My New Playlist", "Test description")
        
        assert created_playlist is not None
        assert created_playlist.title == "My New Playlist"
        assert created_playlist.description == "Description for My New Playlist"
        mock_tidal_session.user.create_playlist.assert_called_once_with("My New Playlist", "Test description")
        
        # 2. Add tracks to playlist
        sample_track = create_sample_tidal_track(123456, "Added Track")
        mock_tidal_session.playlist.return_value = new_playlist
        mock_tidal_session.track.return_value = sample_track
        
        with patch('tidal_mcp.utils.validate_tidal_id', return_value=True):
            add_success = await integrated_service.add_tracks_to_playlist("new-playlist", ["123456"])
            assert add_success is True
            new_playlist.add.assert_called_once()
        
        # 3. Get playlist with tracks
        new_playlist.tracks.return_value = [sample_track]
        retrieved_playlist = await integrated_service.get_playlist("new-playlist", include_tracks=True)
        
        assert retrieved_playlist is not None
        assert len(retrieved_playlist.tracks) == 1
        assert retrieved_playlist.tracks[0].title == "Added Track"
        
        # 4. Remove tracks from playlist
        with patch('tidal_mcp.utils.validate_tidal_id', return_value=True):
            remove_success = await integrated_service.remove_tracks_from_playlist("new-playlist", [0])
            assert remove_success is True
            new_playlist.remove_by_index.assert_called_once_with(0)
        
        # 5. Delete playlist
        with patch('tidal_mcp.utils.validate_tidal_id', return_value=True):
            delete_success = await integrated_service.delete_playlist("new-playlist")
            assert delete_success is True
            new_playlist.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_user_playlists_management(self, integrated_service, mock_tidal_session):
        """Test user playlist retrieval and management."""
        # Mock user playlists
        user_playlists = [
            create_sample_tidal_playlist("playlist1", "My Playlist 1"),
            create_sample_tidal_playlist("playlist2", "My Playlist 2"),
            create_sample_tidal_playlist("playlist3", "My Playlist 3")
        ]
        mock_tidal_session.user.playlists.return_value = user_playlists
        
        # Get user playlists
        playlists = await integrated_service.get_user_playlists(limit=10)
        
        assert len(playlists) == 3
        assert all(isinstance(p, Playlist) for p in playlists)
        assert playlists[0].title == "My Playlist 1"
        assert playlists[1].title == "My Playlist 2"
        assert playlists[2].title == "My Playlist 3"
    
    @pytest.mark.asyncio
    async def test_playlist_tracks_operations(self, integrated_service, mock_tidal_session):
        """Test playlist track operations."""
        playlist = create_sample_tidal_playlist("test-playlist", "Test Playlist")
        tracks = [
            create_sample_tidal_track(1, "Track 1"),
            create_sample_tidal_track(2, "Track 2"),
            create_sample_tidal_track(3, "Track 3")
        ]
        
        playlist.tracks.return_value = tracks
        mock_tidal_session.playlist.return_value = playlist
        
        with patch('tidal_mcp.utils.validate_tidal_id', return_value=True):
            # Get playlist tracks
            retrieved_tracks = await integrated_service.get_playlist_tracks("test-playlist")
            
            assert len(retrieved_tracks) == 3
            assert all(isinstance(t, Track) for t in retrieved_tracks)
            assert retrieved_tracks[0].title == "Track 1"
            assert retrieved_tracks[1].title == "Track 2"
            assert retrieved_tracks[2].title == "Track 3"


class TestFavoritesIntegration:
    """Test integrated favorites management."""
    
    @pytest.mark.asyncio
    async def test_favorites_full_workflow(self, integrated_service, mock_tidal_session):
        """Test complete favorites management workflow."""
        # Mock favorite items
        favorite_track = create_sample_tidal_track(123, "Favorite Track")
        favorite_album = Mock()
        favorite_album.id = 456
        favorite_album.name = "Favorite Album"
        favorite_album.artists = [favorite_track.artist]
        favorite_album.release_date = "2023-01-01"
        favorite_album.duration = 3600
        favorite_album.num_tracks = 12
        favorite_album.image = "album_cover"
        favorite_album.explicit = False
        
        # Set up favorites
        mock_tidal_session.user.favorites.tracks.return_value = [favorite_track]
        mock_tidal_session.user.favorites.albums.return_value = [favorite_album]
        mock_tidal_session.user.favorites.artists.return_value = [favorite_track.artist]
        
        # 1. Get favorite tracks
        fav_tracks = await integrated_service.get_user_favorites("tracks")
        assert len(fav_tracks) == 1
        assert fav_tracks[0].title == "Favorite Track"
        
        # 2. Get favorite albums
        fav_albums = await integrated_service.get_user_favorites("albums")
        assert len(fav_albums) == 1
        assert fav_albums[0].title == "Favorite Album"
        
        # 3. Get favorite artists
        fav_artists = await integrated_service.get_user_favorites("artists")
        assert len(fav_artists) == 1
        assert fav_artists[0].name == "Test Artist"
        
        # 4. Add new track to favorites
        new_track = create_sample_tidal_track(789, "New Favorite")
        mock_tidal_session.track.return_value = new_track
        
        with patch('tidal_mcp.utils.validate_tidal_id', return_value=True):
            add_success = await integrated_service.add_to_favorites("789", "track")
            assert add_success is True
            mock_tidal_session.user.favorites.add_track.assert_called_once_with(new_track)
        
        # 5. Remove track from favorites
        with patch('tidal_mcp.utils.validate_tidal_id', return_value=True):
            remove_success = await integrated_service.remove_from_favorites("789", "track")
            assert remove_success is True
            mock_tidal_session.user.favorites.remove_track.assert_called_once_with(new_track)


class TestRecommendationsIntegration:
    """Test integrated recommendations and radio."""
    
    @pytest.mark.asyncio
    async def test_personalized_recommendations_flow(self, integrated_service, mock_tidal_session):
        """Test personalized recommendations based on user data."""
        # Mock user favorites for seed
        favorite_tracks = [
            create_sample_tidal_track(1, "Fav Track 1"),
            create_sample_tidal_track(2, "Fav Track 2")
        ]
        mock_tidal_session.user.favorites.tracks.return_value = favorite_tracks
        
        # Mock radio tracks from favorite
        radio_tracks = [
            create_sample_tidal_track(10, "Radio Track 1"),
            create_sample_tidal_track(11, "Radio Track 2"),
            create_sample_tidal_track(12, "Radio Track 3")
        ]
        favorite_tracks[0].get_track_radio.return_value = radio_tracks
        
        # Get recommendations
        recommendations = await integrated_service.get_recommended_tracks(limit=3)
        
        assert len(recommendations) == 3
        assert all(isinstance(t, Track) for t in recommendations)
        assert recommendations[0].title == "Radio Track 1"
    
    @pytest.mark.asyncio
    async def test_track_radio_flow(self, integrated_service, mock_tidal_session):
        """Test track-based radio functionality."""
        seed_track = create_sample_tidal_track(123, "Seed Track")
        radio_tracks = [
            create_sample_tidal_track(200, "Radio Track 1"),
            create_sample_tidal_track(201, "Radio Track 2")
        ]
        
        seed_track.get_track_radio.return_value = radio_tracks
        mock_tidal_session.track.return_value = seed_track
        
        with patch('tidal_mcp.utils.validate_tidal_id', return_value=True):
            radio = await integrated_service.get_track_radio("123", limit=2)
            
            assert len(radio) == 2
            assert radio[0].title == "Radio Track 1"
            assert radio[1].title == "Radio Track 2"
    
    @pytest.mark.asyncio
    async def test_artist_radio_flow(self, integrated_service, mock_tidal_session):
        """Test artist-based radio functionality."""
        artist = Mock()
        artist.id = 456
        artist.name = "Test Artist"
        artist.picture = "artist_pic"
        artist.popularity = 90
        
        radio_tracks = [
            create_sample_tidal_track(300, "Artist Radio 1"),
            create_sample_tidal_track(301, "Artist Radio 2")
        ]
        artist.get_radio.return_value = radio_tracks
        mock_tidal_session.artist.return_value = artist
        
        with patch('tidal_mcp.utils.validate_tidal_id', return_value=True):
            radio = await integrated_service.get_artist_radio("456", limit=2)
            
            assert len(radio) == 2
            assert radio[0].title == "Artist Radio 1"
            assert radio[1].title == "Artist Radio 2"


class TestDetailedContentRetrieval:
    """Test integrated detailed content retrieval."""
    
    @pytest.mark.asyncio
    async def test_complete_track_information_flow(self, integrated_service, mock_tidal_session):
        """Test complete track information retrieval."""
        track = create_sample_tidal_track(123456, "Detailed Track", "Detailed Artist")
        mock_tidal_session.track.return_value = track
        
        with patch('tidal_mcp.utils.validate_tidal_id', return_value=True):
            retrieved_track = await integrated_service.get_track("123456")
            
            assert retrieved_track is not None
            assert retrieved_track.id == "123456"
            assert retrieved_track.title == "Detailed Track"
            assert retrieved_track.duration == 240
            assert retrieved_track.track_number == 1
            assert retrieved_track.quality == "LOSSLESS"
            
            # Verify artist information
            assert len(retrieved_track.artists) == 1
            assert retrieved_track.artists[0].name == "Detailed Artist"
            
            # Verify album information
            assert retrieved_track.album is not None
            assert retrieved_track.album.title == "Test Album"
    
    @pytest.mark.asyncio
    async def test_album_with_tracks_flow(self, integrated_service, mock_tidal_session):
        """Test album retrieval with track information."""
        album = Mock()
        album.id = 456
        album.name = "Complete Album"
        album.release_date = "2023-01-01"
        album.duration = 3600
        album.num_tracks = 3
        album.image = "album_cover"
        album.explicit = False
        
        # Mock artist
        artist = Mock()
        artist.id = 789
        artist.name = "Album Artist"
        artist.picture = "artist_pic"
        artist.popularity = 85
        album.artist = artist
        album.artists = [artist]
        
        # Mock album tracks
        album_tracks = [
            create_sample_tidal_track(1, "Track 1", "Album Artist"),
            create_sample_tidal_track(2, "Track 2", "Album Artist"),
            create_sample_tidal_track(3, "Track 3", "Album Artist")
        ]
        album.tracks.return_value = album_tracks
        
        mock_tidal_session.album.return_value = album
        
        with patch('tidal_mcp.utils.validate_tidal_id', return_value=True):
            # Get album details
            retrieved_album = await integrated_service.get_album("456", include_tracks=True)
            
            assert retrieved_album is not None
            assert retrieved_album.id == "456"
            assert retrieved_album.title == "Complete Album"
            assert retrieved_album.number_of_tracks == 3
            
            # Get album tracks separately
            tracks = await integrated_service.get_album_tracks("456")
            assert len(tracks) == 3
            assert all(t.album.title == "Test Album" for t in tracks)
    
    @pytest.mark.asyncio
    async def test_artist_discography_flow(self, integrated_service, mock_tidal_session):
        """Test artist discography and top tracks retrieval."""
        artist = Mock()
        artist.id = 789
        artist.name = "Complete Artist"
        artist.picture = "artist_pic"
        artist.popularity = 95
        
        # Mock artist albums
        artist_albums = [
            Mock(id=1, name="Album 1", artists=[artist], release_date="2021-01-01", 
                 duration=3600, num_tracks=12, image="cover1", explicit=False),
            Mock(id=2, name="Album 2", artists=[artist], release_date="2022-01-01",
                 duration=3200, num_tracks=10, image="cover2", explicit=False)
        ]
        artist.get_albums.return_value = artist_albums
        
        # Mock top tracks
        top_tracks = [
            create_sample_tidal_track(100, "Top Track 1", "Complete Artist"),
            create_sample_tidal_track(101, "Top Track 2", "Complete Artist")
        ]
        artist.get_top_tracks.return_value = top_tracks
        
        mock_tidal_session.artist.return_value = artist
        
        with patch('tidal_mcp.utils.validate_tidal_id', return_value=True):
            # Get artist info
            retrieved_artist = await integrated_service.get_artist("789")
            assert retrieved_artist.name == "Complete Artist"
            assert retrieved_artist.popularity == 95
            
            # Get artist albums
            albums = await integrated_service.get_artist_albums("789")
            assert len(albums) == 2
            assert albums[0].title == "Album 1"
            assert albums[1].title == "Album 2"
            
            # Get top tracks
            tracks = await integrated_service.get_artist_top_tracks("789")
            assert len(tracks) == 2
            assert tracks[0].title == "Top Track 1"
            assert tracks[1].title == "Top Track 2"


class TestUserProfileIntegration:
    """Test integrated user profile functionality."""
    
    @pytest.mark.asyncio
    async def test_complete_user_profile_flow(self, integrated_service, integrated_auth):
        """Test complete user profile information retrieval."""
        # Get user profile through service
        profile = await integrated_service.get_user_profile()
        
        assert profile is not None
        assert profile['id'] == 12345
        assert profile['country_code'] == 'US'
        assert profile['subscription']['type'] == 'HiFi'
        assert profile['subscription']['valid'] is True


class TestErrorHandlingAndRecovery:
    """Test integrated error handling and recovery scenarios."""
    
    @pytest.mark.asyncio
    async def test_authentication_expiry_and_refresh(self, integrated_service, integrated_auth, mock_tidal_session):
        """Test handling of authentication expiry during operations."""
        # Set token to expire soon
        integrated_auth.token_expires_at = datetime.now() + timedelta(seconds=30)
        
        # Mock refresh response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'access_token': 'refreshed_token',
            'refresh_token': 'new_refresh_token',
            'expires_in': 3600
        })
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        # Mock search after refresh
        mock_tidal_session.search.return_value = {
            'tracks': [create_sample_tidal_track()]
        }
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            # Perform search - should trigger token refresh
            results = await integrated_service.search_tracks("test")
            
            # Should have refreshed token and completed search
            assert integrated_auth.access_token == 'refreshed_token'
            assert len(results) == 1
    
    @pytest.mark.asyncio
    async def test_network_error_recovery(self, integrated_service, mock_tidal_session):
        """Test recovery from network errors."""
        # First call fails with network error, second succeeds
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Network error")
            return {'tracks': [create_sample_tidal_track()]}
        
        mock_tidal_session.search.side_effect = side_effect
        
        # First search should fail gracefully
        results1 = await integrated_service.search_tracks("test")
        assert results1 == []
        
        # Second search should succeed
        results2 = await integrated_service.search_tracks("test")
        assert len(results2) == 1
    
    @pytest.mark.asyncio
    async def test_data_corruption_handling(self, integrated_service, mock_tidal_session):
        """Test handling of corrupted data from API."""
        # Mock corrupted track data
        corrupted_track = Mock()
        corrupted_track.id = None  # Invalid ID
        corrupted_track.name = None  # Invalid name
        
        valid_track = create_sample_tidal_track()
        
        mock_tidal_session.search.return_value = {
            'tracks': [corrupted_track, valid_track]  # Mix of corrupted and valid
        }
        
        # Should skip corrupted track and return only valid ones
        results = await integrated_service.search_tracks("test")
        assert len(results) == 1  # Only the valid track
        assert results[0].title == "Test Track"


class TestConcurrentOperations:
    """Test concurrent operations and thread safety."""
    
    @pytest.mark.asyncio
    async def test_concurrent_searches(self, integrated_service, mock_tidal_session):
        """Test multiple concurrent search operations."""
        # Mock different search results for each query
        def search_side_effect(query, models=None):
            track_id = hash(query) % 1000
            return {'tracks': [create_sample_tidal_track(track_id, f"Track for {query}")]}
        
        mock_tidal_session.search.side_effect = search_side_effect
        
        # Perform concurrent searches
        queries = ["query1", "query2", "query3", "query4", "query5"]
        search_tasks = [
            integrated_service.search_tracks(query)
            for query in queries
        ]
        
        results = await asyncio.gather(*search_tasks)
        
        # All searches should complete successfully
        assert len(results) == 5
        assert all(len(result) == 1 for result in results)
        
        # Results should be different for different queries
        track_ids = [result[0].id for result in results]
        assert len(set(track_ids)) == 5  # All unique
    
    @pytest.mark.asyncio
    async def test_concurrent_playlist_operations(self, integrated_service, mock_tidal_session):
        """Test concurrent playlist operations."""
        # Mock playlist operations
        playlists = [
            create_sample_tidal_playlist(f"playlist{i}", f"Test Playlist {i}")
            for i in range(3)
        ]
        
        mock_tidal_session.user.create_playlist.side_effect = playlists
        mock_tidal_session.playlist.side_effect = lambda pid: next(
            p for p in playlists if p.id == pid
        )
        
        # Perform concurrent playlist operations
        create_tasks = [
            integrated_service.create_playlist(f"Playlist {i}", f"Description {i}")
            for i in range(3)
        ]
        
        created_playlists = await asyncio.gather(*create_tasks)
        
        # All creations should succeed
        assert len(created_playlists) == 3
        assert all(p is not None for p in created_playlists)
        assert all(f"Test Playlist {i}" in p.title for i, p in enumerate(created_playlists))


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])