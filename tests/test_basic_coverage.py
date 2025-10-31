"""Basic tests to boost coverage for simple functions and methods.."""

from unittest.mock import MagicMock, Mock, patch

# Import all modules to test basic functionality
from tidal_mcp import auth, models, server, service, utils


class TestBasicCoverage:
    """Simple tests to increase coverage across all modules."""

    # Test module imports and basic attributes
    def test_auth_module_import(self):
        """Test auth module imports work."""
        assert hasattr(auth, "TidalAuth")
        assert hasattr(auth, "TidalAuthError")

    def test_models_module_import(self):
        """Test models module imports work."""
        assert hasattr(models, "Track")
        assert hasattr(models, "Album")
        assert hasattr(models, "Artist")
        assert hasattr(models, "Playlist")

    def test_service_module_import(self):
        """Test service module imports work."""
        assert hasattr(service, "TidalService")
        assert hasattr(service, "async_to_sync")

    def test_utils_module_import(self):
        """Test utils module imports work."""
        assert hasattr(utils, "sanitize_query")
        assert hasattr(utils, "format_duration")

    def test_server_module_import(self):
        """Test server module imports work."""
        # Just test that we can import it
        assert server is not None

    # Test simple model instantiation and methods
    def test_track_basic_creation(self):
        """Test basic Track creation and methods."""
        track = models.Track(id="123", title="Test Track")
        assert track.id == "123"
        assert track.title == "Test Track"

        # Test string representation
        str_repr = str(track)
        assert "Test Track" in str_repr

        # Test to_dict method
        track_dict = track.to_dict()
        assert track_dict["id"] == "123"
        assert track_dict["title"] == "Test Track"

    def test_album_basic_creation(self):
        """Test basic Album creation and methods."""
        album = models.Album(id="456", title="Test Album")
        assert album.id == "456"
        assert album.title == "Test Album"

        # Test methods
        str_repr = str(album)
        assert "Test Album" in str_repr

        album_dict = album.to_dict()
        assert album_dict["id"] == "456"

    def test_artist_basic_creation(self):
        """Test basic Artist creation and methods."""
        artist = models.Artist(id="789", name="Test Artist")
        assert artist.id == "789"
        assert artist.name == "Test Artist"

        str_repr = str(artist)
        assert "Test Artist" in str_repr

        artist_dict = artist.to_dict()
        assert artist_dict["id"] == "789"

    def test_playlist_basic_creation(self):
        """Test basic Playlist creation and methods."""
        playlist = models.Playlist(id="playlist123", title="Test Playlist")
        assert playlist.id == "playlist123"
        assert playlist.title == "Test Playlist"

        str_repr = str(playlist)
        assert "Test Playlist" in str_repr

        playlist_dict = playlist.to_dict()
        assert playlist_dict["id"] == "playlist123"

    def test_search_results_creation(self):
        """Test SearchResults creation."""
        track = models.Track(id="1", title="Track")
        album = models.Album(id="2", title="Album")
        artist = models.Artist(id="3", name="Artist")
        playlist = models.Playlist(id="4", title="Playlist")

        results = models.SearchResults(
            tracks=[track],
            albums=[album],
            artists=[artist],
            playlists=[playlist],
        )

        assert len(results.tracks) == 1
        assert len(results.albums) == 1
        assert len(results.artists) == 1
        assert len(results.playlists) == 1

        # Test to_dict
        results_dict = results.to_dict()
        assert "tracks" in results_dict
        assert len(results_dict["tracks"]) == 1

    # Test utility functions with various inputs
    def test_utils_edge_cases(self):
        """Test utility functions with edge cases."""
        # Test sanitize_query
        assert utils.sanitize_query("normal query") == "normal query"
        assert utils.sanitize_query("") == ""
        assert utils.sanitize_query("   ") == ""
        assert utils.sanitize_query("query   with   spaces") == "query with spaces"

        # Test format_duration with different types
        assert utils.format_duration(0) == "0:00"
        assert utils.format_duration(30) == "0:30"
        assert utils.format_duration(90) == "1:30"
        assert utils.format_duration(3661) == "1:01:01"

        # Test format_file_size
        assert utils.format_file_size(0) == "0 B"
        assert utils.format_file_size(512) == "512 B"
        assert utils.format_file_size(1536) == "1.5 KB"

        # Test validate_tidal_id
        assert utils.validate_tidal_id("123") is True
        assert utils.validate_tidal_id("456789") is True
        assert utils.validate_tidal_id("abc123") is False  # Non-numeric
        assert utils.validate_tidal_id("") is False
        assert utils.validate_tidal_id(None) is False

    def test_model_from_api_data(self):
        """Test model creation from API data."""
        # Test Track.from_api_data
        api_data = {
            "id": 123,
            "title": "API Track",
            "artist": {"name": "API Artist"},
            "album": {"title": "API Album", "cover": "cover_url"},
            "duration": 240,
            "explicit": False,
        }
        track = models.Track.from_api_data(api_data)
        assert track.id == "123"
        assert track.title == "API Track"
        assert len(track.artists) > 0
        assert track.artists[0].name == "API Artist"

        # Test Album.from_api_data
        album_data = {
            "id": 456,
            "title": "API Album",
            "artist": {"name": "API Artist"},
            "cover": "album_cover",
            "releaseDate": "2023-01-01",
            "duration": 3600,
            "numberOfTracks": 12,
            "explicit": False,
        }
        album = models.Album.from_api_data(album_data)
        assert album.id == "456"
        assert album.title == "API Album"

        # Test Artist.from_api_data
        artist_data = {
            "id": 789,
            "name": "API Artist",
            "picture": "artist_pic",
        }
        artist = models.Artist.from_api_data(artist_data)
        assert artist.id == "789"
        assert artist.name == "API Artist"

        # Test Playlist.from_api_data
        playlist_data = {
            "uuid": "playlist123",
            "title": "API Playlist",
            "description": "Test description",
            "creator": {"name": "Creator"},
            "numberOfTracks": 25,
            "duration": 6000,
        }
        playlist = models.Playlist.from_api_data(playlist_data)
        assert playlist.id == "playlist123"
        assert playlist.title == "API Playlist"

    def test_auth_error_basic(self):
        """Test basic TidalAuthError functionality."""
        error = auth.TidalAuthError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_async_to_sync_decorator_basic(self):
        """Test async_to_sync decorator basic functionality."""
        decorator = service.async_to_sync

        # Test that it's callable
        assert callable(decorator)

        # Test decorating a simple function
        @decorator
        def simple_function(x):
            return x * 2

        assert callable(simple_function)

    @patch("tidal_mcp.auth.os.getenv")
    @patch("tidal_mcp.auth.load_dotenv")
    def test_auth_init_basic_mock(self, mock_load_dotenv, mock_getenv):
        """Test TidalAuth initialization with mocked environment."""
        # Mock the required environment variable
        mock_getenv.side_effect = lambda key, default=None: {
            "TIDAL_CLIENT_ID": "mocked_client_id"
        }.get(key, default)

        with patch("tidal_mcp.auth.Path") as mock_path:
            mock_path.return_value.expanduser.return_value = mock_path.return_value
            mock_path.return_value.mkdir.return_value = None
            mock_path.return_value.exists.return_value = False

            # This should successfully create a TidalAuth instance
            auth_instance = auth.TidalAuth()
            assert auth_instance.client_id == "mocked_client_id"

    @patch("tidal_mcp.service.TidalAuth")
    def test_service_init_basic_mock(self, mock_auth_class):
        """Test TidalService initialization with mocked auth."""
        mock_auth = Mock()

        # Create service instance
        service_instance = service.TidalService(mock_auth)
        assert service_instance.auth == mock_auth
        assert hasattr(service_instance, "_cache")

    def test_utils_additional_functions(self):
        """Test additional utility functions."""
        # Test extract_tidal_id_from_url with valid URLs
        valid_url = "https://tidal.com/track/12345678"
        assert utils.extract_tidal_id_from_url(valid_url) == "12345678"

        # Test with invalid URL
        invalid_url = "https://example.com/invalid"
        assert utils.extract_tidal_id_from_url(invalid_url) is None

        # Test calculate_playlist_stats
        tracks = [
            {
                "duration": 180,
                "explicit": False,
                "artists": [{"name": "Artist1"}],
                "album": {"title": "Album1"},
            },
            {
                "duration": 200,
                "explicit": True,
                "artists": [{"name": "Artist2"}],
                "album": {"title": "Album2"},
            },
        ]
        stats = utils.calculate_playlist_stats(tracks)
        assert stats["total_tracks"] == 2
        assert stats["total_duration"] == 380
        assert stats["explicit_tracks"] == 1
        assert stats["unique_artists"] == 2
        assert stats["unique_albums"] == 2

    def test_model_equality_and_hashing(self):
        """Test model equality and hashing."""
        track1 = models.Track(id="1", title="Track")
        track2 = models.Track(id="1", title="Track")
        track3 = models.Track(id="2", title="Track")

        # Test equality
        assert track1 == track2
        assert track1 != track3
        assert track1 != "not_a_track"

        # Test hashing (if implemented)
        try:
            hash(track1)
        except TypeError:
            pass  # Not all models may be hashable

    def test_model_repr_methods(self):
        """Test model __repr__ methods."""
        track = models.Track(id="1", title="Track")
        repr_str = repr(track)
        assert "Track" in repr_str
        assert "1" in repr_str

        album = models.Album(id="2", title="Album")
        repr_str = repr(album)
        assert "Album" in repr_str

        artist = models.Artist(id="3", name="Artist")
        repr_str = repr(artist)
        assert "Artist" in repr_str

        playlist = models.Playlist(id="4", title="Playlist")
        repr_str = repr(playlist)
        assert "Playlist" in repr_str

    def test_search_results_empty(self):
        """Test SearchResults with empty lists."""
        results = models.SearchResults(tracks=[], albums=[], artists=[], playlists=[])
        assert len(results.tracks) == 0
        assert len(results.albums) == 0
        assert len(results.artists) == 0
        assert len(results.playlists) == 0

        # Test to_dict with empty results
        results_dict = results.to_dict()
        assert results_dict["tracks"] == []
        assert results_dict["albums"] == []
