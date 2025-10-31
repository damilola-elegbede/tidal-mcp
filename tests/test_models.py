"""
Comprehensive tests for Tidal Data Models

Tests data model creation, serialization, validation, and API data conversion.
Focuses on achieving high coverage for all model classes and methods.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from src.tidal_mcp.models import Album, Artist, Playlist, SearchResults, Track


class TestArtistModel:
    """Test Artist model functionality."""

    def test_artist_creation_with_all_fields(self):
        """Test creating artist with all fields."""
        artist = Artist(
            id="123",
            name="Test Artist",
            url="https://tidal.com/artist/123",
            picture="https://example.com/picture.jpg",
            popularity=85,
        )

        assert artist.id == "123"
        assert artist.name == "Test Artist"
        assert artist.url == "https://tidal.com/artist/123"
        assert artist.picture == "https://example.com/picture.jpg"
        assert artist.popularity == 85

    def test_artist_creation_with_minimal_fields(self):
        """Test creating artist with only required fields."""
        artist = Artist(id="123", name="Test Artist")

        assert artist.id == "123"
        assert artist.name == "Test Artist"
        assert artist.url is None
        assert artist.picture is None
        assert artist.popularity is None

    def test_artist_from_api_data_complete(self):
        """Test creating artist from complete API data."""
        api_data = {
            "id": 123,
            "name": "Test Artist",
            "url": "https://tidal.com/artist/123",
            "picture": "https://example.com/picture.jpg",
            "popularity": 85,
        }

        artist = Artist.from_api_data(api_data)

        assert artist.id == "123"  # Should be converted to string
        assert artist.name == "Test Artist"
        assert artist.url == "https://tidal.com/artist/123"
        assert artist.picture == "https://example.com/picture.jpg"
        assert artist.popularity == 85

    def test_artist_from_api_data_minimal(self):
        """Test creating artist from minimal API data."""
        api_data = {"id": 123, "name": "Test Artist"}

        artist = Artist.from_api_data(api_data)

        assert artist.id == "123"
        assert artist.name == "Test Artist"
        assert artist.url is None
        assert artist.picture is None
        assert artist.popularity is None

    def test_artist_from_api_data_empty(self):
        """Test creating artist from empty/None API data."""
        artist = Artist.from_api_data(None)
        assert artist.id == ""
        assert artist.name == ""

        artist = Artist.from_api_data({})
        assert artist.id == ""
        assert artist.name == ""

    def test_artist_from_api_data_invalid_type(self):
        """Test creating artist from invalid API data type."""
        artist = Artist.from_api_data("invalid")
        assert artist.id == ""
        assert artist.name == ""

    def test_artist_to_dict(self):
        """Test converting artist to dictionary."""
        artist = Artist(
            id="123",
            name="Test Artist",
            url="https://tidal.com/artist/123",
            picture="https://example.com/picture.jpg",
            popularity=85,
        )

        artist_dict = artist.to_dict()

        expected = {
            "id": "123",
            "name": "Test Artist",
            "url": "https://tidal.com/artist/123",
            "picture": "https://example.com/picture.jpg",
            "popularity": 85,
        }

        assert artist_dict == expected


class TestAlbumModel:
    """Test Album model functionality."""

    def test_album_creation_with_all_fields(self):
        """Test creating album with all fields."""
        artists = [Artist(id="123", name="Test Artist")]
        album = Album(
            id="456",
            title="Test Album",
            artists=artists,
            release_date="2023-01-01",
            duration=3600,
            number_of_tracks=12,
            cover="https://example.com/cover.jpg",
            url="https://tidal.com/album/456",
            explicit=True,
        )

        assert album.id == "456"
        assert album.title == "Test Album"
        assert len(album.artists) == 1
        assert album.artists[0].name == "Test Artist"
        assert album.release_date == "2023-01-01"
        assert album.duration == 3600
        assert album.number_of_tracks == 12
        assert album.cover == "https://example.com/cover.jpg"
        assert album.url == "https://tidal.com/album/456"
        assert album.explicit is True

    def test_album_creation_with_defaults(self):
        """Test creating album with default values."""
        album = Album(id="456", title="Test Album")

        assert album.id == "456"
        assert album.title == "Test Album"
        assert album.artists == []
        assert album.release_date is None
        assert album.duration is None
        assert album.number_of_tracks is None
        assert album.cover is None
        assert album.url is None
        assert album.explicit is False

    def test_album_from_api_data_with_artists_list(self):
        """Test creating album from API data with artists list."""
        api_data = {
            "id": 456,
            "title": "Test Album",
            "artists": [
                {"id": 123, "name": "Artist 1"},
                {"id": 124, "name": "Artist 2"},
            ],
            "releaseDate": "2023-01-01",
            "duration": 3600,
            "numberOfTracks": 12,
            "cover": "https://example.com/cover.jpg",
            "url": "https://tidal.com/album/456",
            "explicit": True,
        }

        album = Album.from_api_data(api_data)

        assert album.id == "456"
        assert album.title == "Test Album"
        assert len(album.artists) == 2
        assert album.artists[0].name == "Artist 1"
        assert album.artists[1].name == "Artist 2"
        assert album.release_date == "2023-01-01"
        assert album.duration == 3600
        assert album.number_of_tracks == 12
        assert album.explicit is True

    def test_album_from_api_data_with_single_artist(self):
        """Test creating album from API data with single artist."""
        api_data = {
            "id": 456,
            "title": "Test Album",
            "artist": {"id": 123, "name": "Single Artist"},
        }

        album = Album.from_api_data(api_data)

        assert len(album.artists) == 1
        assert album.artists[0].name == "Single Artist"

    def test_album_from_api_data_empty(self):
        """Test creating album from empty API data."""
        album = Album.from_api_data(None)
        assert album.id == ""
        assert album.title == ""

        album = Album.from_api_data({})
        assert album.id == ""
        assert album.title == ""

    def test_album_to_dict(self):
        """Test converting album to dictionary."""
        artists = [Artist(id="123", name="Test Artist")]
        album = Album(
            id="456",
            title="Test Album",
            artists=artists,
            release_date="2023-01-01",
            duration=3600,
            number_of_tracks=12,
            cover="https://example.com/cover.jpg",
            url="https://tidal.com/album/456",
            explicit=True,
        )

        album_dict = album.to_dict()

        assert album_dict["id"] == "456"
        assert album_dict["title"] == "Test Album"
        assert len(album_dict["artists"]) == 1
        assert album_dict["artists"][0]["name"] == "Test Artist"
        assert album_dict["explicit"] is True


class TestTrackModel:
    """Test Track model functionality."""

    def test_track_creation_with_all_fields(self):
        """Test creating track with all fields."""
        artists = [Artist(id="123", name="Test Artist")]
        album = Album(id="456", title="Test Album")
        track = Track(
            id="789",
            title="Test Track",
            artists=artists,
            album=album,
            duration=240,
            track_number=5,
            disc_number=1,
            url="https://tidal.com/track/789",
            stream_url="https://stream.tidal.com/track/789",
            explicit=True,
            quality="LOSSLESS",
        )

        assert track.id == "789"
        assert track.title == "Test Track"
        assert len(track.artists) == 1
        assert track.album.title == "Test Album"
        assert track.duration == 240
        assert track.track_number == 5
        assert track.disc_number == 1
        assert track.explicit is True
        assert track.quality == "LOSSLESS"

    def test_track_creation_with_defaults(self):
        """Test creating track with default values."""
        track = Track(id="789", title="Test Track")

        assert track.id == "789"
        assert track.title == "Test Track"
        assert track.artists == []
        assert track.album is None
        assert track.duration is None
        assert track.track_number is None
        assert track.disc_number is None
        assert track.url is None
        assert track.stream_url is None
        assert track.explicit is False
        assert track.quality is None

    def test_track_from_api_data_complete(self):
        """Test creating track from complete API data."""
        api_data = {
            "id": 789,
            "title": "Test Track",
            "artists": [{"id": 123, "name": "Test Artist"}],
            "album": {"id": 456, "title": "Test Album"},
            "duration": 240,
            "trackNumber": 5,
            "discNumber": 1,
            "url": "https://tidal.com/track/789",
            "streamUrl": "https://stream.tidal.com/track/789",
            "explicit": True,
            "quality": "LOSSLESS",
        }

        track = Track.from_api_data(api_data)

        assert track.id == "789"
        assert track.title == "Test Track"
        assert len(track.artists) == 1
        assert track.album.title == "Test Album"
        assert track.duration == 240
        assert track.track_number == 5
        assert track.disc_number == 1
        assert track.explicit is True
        assert track.quality == "LOSSLESS"

    def test_track_from_api_data_with_single_artist(self):
        """Test creating track from API data with single artist."""
        api_data = {
            "id": 789,
            "title": "Test Track",
            "artist": {"id": 123, "name": "Single Artist"},
        }

        track = Track.from_api_data(api_data)

        assert len(track.artists) == 1
        assert track.artists[0].name == "Single Artist"

    def test_track_from_api_data_empty(self):
        """Test creating track from empty API data."""
        track = Track.from_api_data(None)
        assert track.id == ""
        assert track.title == ""

        track = Track.from_api_data({})
        assert track.id == ""
        assert track.title == ""

    def test_track_to_dict(self):
        """Test converting track to dictionary."""
        artists = [Artist(id="123", name="Test Artist")]
        album = Album(id="456", title="Test Album")
        track = Track(
            id="789",
            title="Test Track",
            artists=artists,
            album=album,
            duration=240,
            explicit=True,
        )

        track_dict = track.to_dict()

        assert track_dict["id"] == "789"
        assert track_dict["title"] == "Test Track"
        assert len(track_dict["artists"]) == 1
        assert track_dict["album"]["title"] == "Test Album"
        assert track_dict["duration"] == 240
        assert track_dict["explicit"] is True

    def test_track_to_dict_without_album(self):
        """Test converting track to dictionary without album."""
        track = Track(id="789", title="Test Track")
        track_dict = track.to_dict()

        assert track_dict["album"] is None

    def test_track_formatted_duration(self):
        """Test track formatted duration property."""
        track = Track(id="789", title="Test Track", duration=240)
        assert track.formatted_duration == "4:00"

        track = Track(id="789", title="Test Track", duration=125)
        assert track.formatted_duration == "2:05"

        track = Track(id="789", title="Test Track", duration=None)
        assert track.formatted_duration == "0:00"

        track = Track(id="789", title="Test Track", duration=0)
        assert track.formatted_duration == "0:00"

    def test_track_artist_names(self):
        """Test track artist names property."""
        artists = [
            Artist(id="123", name="Artist 1"),
            Artist(id="124", name="Artist 2"),
            Artist(id="125", name="Artist 3"),
        ]
        track = Track(id="789", title="Test Track", artists=artists)

        assert track.artist_names == "Artist 1, Artist 2, Artist 3"

        track_no_artists = Track(id="789", title="Test Track")
        assert track_no_artists.artist_names == ""


class TestPlaylistModel:
    """Test Playlist model functionality."""

    def test_playlist_creation_with_all_fields(self):
        """Test creating playlist with all fields."""
        tracks = [Track(id="789", title="Test Track")]
        created_at = datetime(2023, 1, 1, 12, 0, 0)
        updated_at = datetime(2023, 1, 2, 12, 0, 0)

        playlist = Playlist(
            id="abc-123",
            title="Test Playlist",
            description="A test playlist",
            creator="Test Creator",
            tracks=tracks,
            number_of_tracks=1,
            duration=240,
            created_at=created_at,
            updated_at=updated_at,
            image="https://example.com/image.jpg",
            url="https://tidal.com/playlist/abc-123",
            public=False,
        )

        assert playlist.id == "abc-123"
        assert playlist.title == "Test Playlist"
        assert playlist.description == "A test playlist"
        assert playlist.creator == "Test Creator"
        assert len(playlist.tracks) == 1
        assert playlist.number_of_tracks == 1
        assert playlist.duration == 240
        assert playlist.created_at == created_at
        assert playlist.updated_at == updated_at
        assert playlist.image == "https://example.com/image.jpg"
        assert playlist.url == "https://tidal.com/playlist/abc-123"
        assert playlist.public is False

    def test_playlist_creation_with_defaults(self):
        """Test creating playlist with default values."""
        playlist = Playlist(id="abc-123", title="Test Playlist")

        assert playlist.id == "abc-123"
        assert playlist.title == "Test Playlist"
        assert playlist.description is None
        assert playlist.creator is None
        assert playlist.tracks == []
        assert playlist.number_of_tracks is None
        assert playlist.duration is None
        assert playlist.created_at is None
        assert playlist.updated_at is None
        assert playlist.image is None
        assert playlist.url is None
        assert playlist.public is True

    def test_playlist_from_api_data_complete(self):
        """Test creating playlist from complete API data."""
        api_data = {
            "uuid": "abc-123",
            "title": "Test Playlist",
            "description": "A test playlist",
            "creator": {"name": "Test Creator"},
            "tracks": [{"id": 789, "title": "Test Track"}],
            "numberOfTracks": 1,
            "duration": 240,
            "created": "2023-01-01T12:00:00Z",
            "lastUpdated": "2023-01-02T12:00:00Z",
            "image": "https://example.com/image.jpg",
            "url": "https://tidal.com/playlist/abc-123",
            "publicPlaylist": False,
        }

        playlist = Playlist.from_api_data(api_data)

        assert playlist.id == "abc-123"
        assert playlist.title == "Test Playlist"
        assert playlist.description == "A test playlist"
        assert playlist.creator == "Test Creator"
        assert len(playlist.tracks) == 1
        assert playlist.number_of_tracks == 1
        assert playlist.duration == 240
        assert playlist.created_at is not None
        assert playlist.updated_at is not None
        assert playlist.image == "https://example.com/image.jpg"
        assert playlist.url == "https://tidal.com/playlist/abc-123"
        assert playlist.public is False

    def test_playlist_from_api_data_with_id_fallback(self):
        """Test creating playlist from API data with ID fallback."""
        api_data = {"id": "123", "title": "Test Playlist"}

        playlist = Playlist.from_api_data(api_data)
        assert playlist.id == "123"

    def test_playlist_from_api_data_invalid_dates(self):
        """Test creating playlist from API data with invalid dates."""
        api_data = {
            "uuid": "abc-123",
            "title": "Test Playlist",
            "created": "invalid-date",
            "lastUpdated": "also-invalid",
        }

        playlist = Playlist.from_api_data(api_data)

        assert playlist.id == "abc-123"
        assert playlist.title == "Test Playlist"
        assert playlist.created_at is None
        assert playlist.updated_at is None

    def test_playlist_from_api_data_empty(self):
        """Test creating playlist from empty API data."""
        playlist = Playlist.from_api_data(None)
        assert playlist.id == ""
        assert playlist.title == ""

        playlist = Playlist.from_api_data({})
        assert playlist.id == ""
        assert playlist.title == ""

    def test_playlist_to_dict(self):
        """Test converting playlist to dictionary."""
        tracks = [Track(id="789", title="Test Track")]
        created_at = datetime(2023, 1, 1, 12, 0, 0)
        updated_at = datetime(2023, 1, 2, 12, 0, 0)

        playlist = Playlist(
            id="abc-123",
            title="Test Playlist",
            description="A test playlist",
            creator="Test Creator",
            tracks=tracks,
            number_of_tracks=1,
            duration=240,
            created_at=created_at,
            updated_at=updated_at,
            image="https://example.com/image.jpg",
            url="https://tidal.com/playlist/abc-123",
            public=False,
        )

        playlist_dict = playlist.to_dict()

        assert playlist_dict["id"] == "abc-123"
        assert playlist_dict["title"] == "Test Playlist"
        assert playlist_dict["description"] == "A test playlist"
        assert playlist_dict["creator"] == "Test Creator"
        assert len(playlist_dict["tracks"]) == 1
        assert playlist_dict["number_of_tracks"] == 1
        assert playlist_dict["duration"] == 240
        assert playlist_dict["created_at"] == created_at.isoformat()
        assert playlist_dict["updated_at"] == updated_at.isoformat()
        assert playlist_dict["image"] == "https://example.com/image.jpg"
        assert playlist_dict["url"] == "https://tidal.com/playlist/abc-123"
        assert playlist_dict["public"] is False

    def test_playlist_to_dict_with_none_dates(self):
        """Test converting playlist to dictionary with None dates."""
        playlist = Playlist(id="abc-123", title="Test Playlist")
        playlist_dict = playlist.to_dict()

        assert playlist_dict["created_at"] is None
        assert playlist_dict["updated_at"] is None

    def test_playlist_formatted_duration(self):
        """Test playlist formatted duration property."""
        # Duration less than an hour
        playlist = Playlist(id="abc-123", title="Test Playlist", duration=240)
        assert playlist.formatted_duration == "4:00"

        # Duration with hours
        playlist = Playlist(id="abc-123", title="Test Playlist", duration=3665)
        assert playlist.formatted_duration == "1:01:05"

        # No duration
        playlist = Playlist(id="abc-123", title="Test Playlist", duration=None)
        assert playlist.formatted_duration == "0:00"

        # Zero duration
        playlist = Playlist(id="abc-123", title="Test Playlist", duration=0)
        assert playlist.formatted_duration == "0:00"


class TestSearchResultsModel:
    """Test SearchResults model functionality."""

    def test_search_results_creation_with_all_fields(self):
        """Test creating search results with all content types."""
        tracks = [Track(id="789", title="Test Track")]
        albums = [Album(id="456", title="Test Album")]
        artists = [Artist(id="123", name="Test Artist")]
        playlists = [Playlist(id="abc-123", title="Test Playlist")]

        results = SearchResults(
            tracks=tracks, albums=albums, artists=artists, playlists=playlists
        )

        assert len(results.tracks) == 1
        assert len(results.albums) == 1
        assert len(results.artists) == 1
        assert len(results.playlists) == 1

    def test_search_results_creation_with_defaults(self):
        """Test creating search results with default empty lists."""
        results = SearchResults()

        assert results.tracks == []
        assert results.albums == []
        assert results.artists == []
        assert results.playlists == []

    def test_search_results_to_dict(self):
        """Test converting search results to dictionary."""
        tracks = [Track(id="789", title="Test Track")]
        albums = [Album(id="456", title="Test Album")]
        artists = [Artist(id="123", name="Test Artist")]
        playlists = [Playlist(id="abc-123", title="Test Playlist")]

        results = SearchResults(
            tracks=tracks, albums=albums, artists=artists, playlists=playlists
        )

        results_dict = results.to_dict()

        assert len(results_dict["tracks"]) == 1
        assert len(results_dict["albums"]) == 1
        assert len(results_dict["artists"]) == 1
        assert len(results_dict["playlists"]) == 1
        assert results_dict["tracks"][0]["title"] == "Test Track"
        assert results_dict["albums"][0]["title"] == "Test Album"
        assert results_dict["artists"][0]["name"] == "Test Artist"
        assert results_dict["playlists"][0]["title"] == "Test Playlist"

    def test_search_results_total_results(self):
        """Test total results property."""
        tracks = [Track(id="789", title="Test Track")]
        albums = [Album(id="456", title="Test Album")]
        artists = [Artist(id="123", name="Test Artist")]
        playlists = [
            Playlist(id="abc-123", title="Test Playlist 1"),
            Playlist(id="def-456", title="Test Playlist 2"),
        ]

        results = SearchResults(
            tracks=tracks, albums=albums, artists=artists, playlists=playlists
        )

        assert results.total_results == 5  # 1 + 1 + 1 + 2

        empty_results = SearchResults()
        assert empty_results.total_results == 0


class TestModelDataValidation:
    """Test model data validation and edge cases."""

    def test_api_data_with_non_dict_values(self):
        """Test model creation with non-dictionary API data."""
        # Test with string
        artist = Artist.from_api_data("not a dict")
        assert artist.id == ""
        assert artist.name == ""

        # Test with list
        album = Album.from_api_data(["not", "a", "dict"])
        assert album.id == ""
        assert album.title == ""

        # Test with number
        track = Track.from_api_data(12345)
        assert track.id == ""
        assert track.title == ""

    def test_api_data_with_missing_required_fields(self):
        """Test model creation with missing required fields."""
        # Artist without ID
        api_data = {"name": "Test Artist"}
        artist = Artist.from_api_data(api_data)
        assert artist.id == ""
        assert artist.name == "Test Artist"

        # Album without title
        api_data = {"id": 123}
        album = Album.from_api_data(api_data)
        assert album.id == "123"
        assert album.title == ""

    def test_api_data_type_conversion(self):
        """Test proper type conversion from API data."""
        # Numeric IDs should be converted to strings
        api_data = {"id": 123, "name": "Test Artist"}
        artist = Artist.from_api_data(api_data)
        assert artist.id == "123"
        assert isinstance(artist.id, str)

        # Boolean values should be handled correctly
        api_data = {"id": 456, "title": "Test Album", "explicit": "true"}
        album = Album.from_api_data(api_data)
        assert album.explicit == "true"  # String value preserved

    def test_nested_model_creation(self):
        """Test creation of models with nested model dependencies."""
        # Track with album that has artists
        api_data = {
            "id": 789,
            "title": "Test Track",
            "album": {
                "id": 456,
                "title": "Test Album",
                "artists": [
                    {"id": 123, "name": "Artist 1"},
                    {"id": 124, "name": "Artist 2"},
                ],
            },
            "artists": [{"id": 125, "name": "Track Artist"}],
        }

        track = Track.from_api_data(api_data)

        assert track.id == "789"
        assert track.title == "Test Track"
        assert track.album.title == "Test Album"
        assert len(track.album.artists) == 2
        assert track.album.artists[0].name == "Artist 1"
        assert track.album.artists[1].name == "Artist 2"
        assert len(track.artists) == 1
        assert track.artists[0].name == "Track Artist"

    def test_empty_collections_handling(self):
        """Test handling of empty collections in API data."""
        # Empty artists list
        api_data = {"id": 456, "title": "Test Album", "artists": []}
        album = Album.from_api_data(api_data)
        assert album.artists == []

        # Empty tracks list in playlist
        api_data = {"uuid": "abc-123", "title": "Test Playlist", "tracks": []}
        playlist = Playlist.from_api_data(api_data)
        assert playlist.tracks == []
