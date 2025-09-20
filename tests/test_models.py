"""
Unit tests for models.py - Data validation, serialization, API response parsing.

Tests cover:
- Data model serialization/deserialization
- Validation logic
- API response parsing
- Edge cases and error handling
- Property methods and computed fields
- Model relationships and nested data

All tests are fast, isolated, and don't require external dependencies.
"""

import json
from datetime import datetime
from typing import Any, Dict

import pytest

from src.tidal_mcp.models import Artist, Album, Track, Playlist, SearchResults


class TestArtistModel:
    """Test Artist model functionality."""

    def test_artist_creation_basic(self):
        """Test basic Artist model creation."""
        artist = Artist(
            id="12345",
            name="Test Artist"
        )

        assert artist.id == "12345"
        assert artist.name == "Test Artist"
        assert artist.url is None
        assert artist.picture is None
        assert artist.popularity is None

    def test_artist_creation_full(self):
        """Test Artist model creation with all fields."""
        artist = Artist(
            id="67890",
            name="Full Artist",
            url="https://tidal.com/artist/67890",
            picture="https://example.com/artist.jpg",
            popularity=95
        )

        assert artist.id == "67890"
        assert artist.name == "Full Artist"
        assert artist.url == "https://tidal.com/artist/67890"
        assert artist.picture == "https://example.com/artist.jpg"
        assert artist.popularity == 95

    def test_artist_from_api_data_basic(self):
        """Test Artist creation from basic API data."""
        api_data = {
            "id": 12345,
            "name": "API Artist"
        }

        artist = Artist.from_api_data(api_data)

        assert artist.id == "12345"
        assert artist.name == "API Artist"
        assert artist.url is None
        assert artist.picture is None
        assert artist.popularity is None

    def test_artist_from_api_data_full(self):
        """Test Artist creation from complete API data."""
        api_data = {
            "id": 67890,
            "name": "Complete API Artist",
            "url": "https://tidal.com/artist/67890",
            "picture": "https://example.com/artist.jpg",
            "popularity": 85
        }

        artist = Artist.from_api_data(api_data)

        assert artist.id == "67890"
        assert artist.name == "Complete API Artist"
        assert artist.url == "https://tidal.com/artist/67890"
        assert artist.picture == "https://example.com/artist.jpg"
        assert artist.popularity == 85

    def test_artist_from_api_data_none(self):
        """Test Artist creation from None API data."""
        artist = Artist.from_api_data(None)

        assert artist.id == ""
        assert artist.name == ""
        assert artist.url is None
        assert artist.picture is None
        assert artist.popularity is None

    def test_artist_from_api_data_empty_dict(self):
        """Test Artist creation from empty dictionary."""
        artist = Artist.from_api_data({})

        assert artist.id == ""
        assert artist.name == ""
        assert artist.url is None
        assert artist.picture is None
        assert artist.popularity is None

    def test_artist_from_api_data_invalid_type(self):
        """Test Artist creation from invalid data type."""
        artist = Artist.from_api_data("invalid_data")

        assert artist.id == ""
        assert artist.name == ""
        assert artist.url is None
        assert artist.picture is None
        assert artist.popularity is None

    def test_artist_to_dict(self):
        """Test Artist serialization to dictionary."""
        artist = Artist(
            id="12345",
            name="Dict Artist",
            url="https://tidal.com/artist/12345",
            picture="https://example.com/artist.jpg",
            popularity=75
        )

        artist_dict = artist.to_dict()

        expected = {
            "id": "12345",
            "name": "Dict Artist",
            "url": "https://tidal.com/artist/12345",
            "picture": "https://example.com/artist.jpg",
            "popularity": 75
        }

        assert artist_dict == expected

    def test_artist_to_dict_minimal(self):
        """Test Artist serialization with minimal data."""
        artist = Artist(id="123", name="Minimal Artist")

        artist_dict = artist.to_dict()

        expected = {
            "id": "123",
            "name": "Minimal Artist",
            "url": None,
            "picture": None,
            "popularity": None
        }

        assert artist_dict == expected


class TestAlbumModel:
    """Test Album model functionality."""

    def test_album_creation_basic(self, sample_artist):
        """Test basic Album model creation."""
        album = Album(
            id="11111",
            title="Test Album",
            artists=[sample_artist]
        )

        assert album.id == "11111"
        assert album.title == "Test Album"
        assert len(album.artists) == 1
        assert album.artists[0] == sample_artist
        assert album.release_date is None
        assert album.duration is None
        assert album.number_of_tracks is None
        assert album.cover is None
        assert album.url is None
        assert album.explicit is False

    def test_album_creation_full(self, sample_artist):
        """Test Album model creation with all fields."""
        album = Album(
            id="22222",
            title="Full Album",
            artists=[sample_artist],
            release_date="2023-01-15",
            duration=3600,
            number_of_tracks=15,
            cover="https://example.com/album.jpg",
            url="https://tidal.com/album/22222",
            explicit=True
        )

        assert album.id == "22222"
        assert album.title == "Full Album"
        assert album.release_date == "2023-01-15"
        assert album.duration == 3600
        assert album.number_of_tracks == 15
        assert album.cover == "https://example.com/album.jpg"
        assert album.url == "https://tidal.com/album/22222"
        assert album.explicit is True

    def test_album_from_api_data_with_artists_array(self):
        """Test Album creation from API data with artists array."""
        api_data = {
            "id": 33333,
            "title": "API Album",
            "artists": [
                {"id": 1, "name": "Artist 1"},
                {"id": 2, "name": "Artist 2"}
            ],
            "releaseDate": "2023-02-20",
            "duration": 2400,
            "numberOfTracks": 10,
            "cover": "https://example.com/cover.jpg",
            "url": "https://tidal.com/album/33333",
            "explicit": False
        }

        album = Album.from_api_data(api_data)

        assert album.id == "33333"
        assert album.title == "API Album"
        assert len(album.artists) == 2
        assert album.artists[0].name == "Artist 1"
        assert album.artists[1].name == "Artist 2"
        assert album.release_date == "2023-02-20"
        assert album.duration == 2400
        assert album.number_of_tracks == 10
        assert album.cover == "https://example.com/cover.jpg"
        assert album.url == "https://tidal.com/album/33333"
        assert album.explicit is False

    def test_album_from_api_data_with_single_artist(self):
        """Test Album creation from API data with single artist."""
        api_data = {
            "id": 44444,
            "title": "Single Artist Album",
            "artist": {"id": 99, "name": "Solo Artist"},
            "releaseDate": "2023-03-01"
        }

        album = Album.from_api_data(api_data)

        assert album.id == "44444"
        assert album.title == "Single Artist Album"
        assert len(album.artists) == 1
        assert album.artists[0].name == "Solo Artist"
        assert album.release_date == "2023-03-01"

    def test_album_from_api_data_none(self):
        """Test Album creation from None API data."""
        album = Album.from_api_data(None)

        assert album.id == ""
        assert album.title == ""
        assert album.artists == []
        assert album.release_date is None

    def test_album_to_dict(self, sample_artist):
        """Test Album serialization to dictionary."""
        album = Album(
            id="55555",
            title="Dict Album",
            artists=[sample_artist],
            release_date="2023-04-10",
            duration=1800,
            number_of_tracks=8,
            cover="https://example.com/dict-album.jpg",
            url="https://tidal.com/album/55555",
            explicit=True
        )

        album_dict = album.to_dict()

        assert album_dict["id"] == "55555"
        assert album_dict["title"] == "Dict Album"
        assert len(album_dict["artists"]) == 1
        assert album_dict["artists"][0]["name"] == sample_artist.name
        assert album_dict["release_date"] == "2023-04-10"
        assert album_dict["duration"] == 1800
        assert album_dict["number_of_tracks"] == 8
        assert album_dict["cover"] == "https://example.com/dict-album.jpg"
        assert album_dict["url"] == "https://tidal.com/album/55555"
        assert album_dict["explicit"] is True

    def test_album_empty_artists_list(self):
        """Test Album with empty artists list."""
        album = Album(id="66666", title="No Artists Album", artists=[])

        assert len(album.artists) == 0

        album_dict = album.to_dict()
        assert album_dict["artists"] == []


class TestTrackModel:
    """Test Track model functionality."""

    def test_track_creation_basic(self, sample_artist):
        """Test basic Track model creation."""
        track = Track(
            id="98765",
            title="Test Track",
            artists=[sample_artist]
        )

        assert track.id == "98765"
        assert track.title == "Test Track"
        assert len(track.artists) == 1
        assert track.artists[0] == sample_artist
        assert track.album is None
        assert track.duration is None
        assert track.track_number is None
        assert track.disc_number is None
        assert track.url is None
        assert track.stream_url is None
        assert track.explicit is False
        assert track.quality is None

    def test_track_creation_full(self, sample_artist, sample_album):
        """Test Track model creation with all fields."""
        track = Track(
            id="87654",
            title="Full Track",
            artists=[sample_artist],
            album=sample_album,
            duration=245,
            track_number=3,
            disc_number=1,
            url="https://tidal.com/track/87654",
            stream_url="https://stream.tidal.com/track/87654",
            explicit=True,
            quality="LOSSLESS"
        )

        assert track.id == "87654"
        assert track.title == "Full Track"
        assert track.album == sample_album
        assert track.duration == 245
        assert track.track_number == 3
        assert track.disc_number == 1
        assert track.url == "https://tidal.com/track/87654"
        assert track.stream_url == "https://stream.tidal.com/track/87654"
        assert track.explicit is True
        assert track.quality == "LOSSLESS"

    def test_track_from_api_data_complete(self):
        """Test Track creation from complete API data."""
        api_data = {
            "id": 76543,
            "title": "API Track",
            "artists": [{"id": 123, "name": "Track Artist"}],
            "album": {
                "id": 456,
                "title": "Track Album",
                "artists": [{"id": 123, "name": "Album Artist"}]
            },
            "duration": 210,
            "trackNumber": 2,
            "discNumber": 1,
            "url": "https://tidal.com/track/76543",
            "streamUrl": "https://stream.tidal.com/track/76543",
            "explicit": True,
            "quality": "HIGH"
        }

        track = Track.from_api_data(api_data)

        assert track.id == "76543"
        assert track.title == "API Track"
        assert len(track.artists) == 1
        assert track.artists[0].name == "Track Artist"
        assert track.album is not None
        assert track.album.title == "Track Album"
        assert track.duration == 210
        assert track.track_number == 2
        assert track.disc_number == 1
        assert track.url == "https://tidal.com/track/76543"
        assert track.stream_url == "https://stream.tidal.com/track/76543"
        assert track.explicit is True
        assert track.quality == "HIGH"

    def test_track_from_api_data_with_single_artist(self):
        """Test Track creation from API data with single artist."""
        api_data = {
            "id": 65432,
            "title": "Single Artist Track",
            "artist": {"id": 789, "name": "Solo Track Artist"},
            "duration": 180
        }

        track = Track.from_api_data(api_data)

        assert track.id == "65432"
        assert track.title == "Single Artist Track"
        assert len(track.artists) == 1
        assert track.artists[0].name == "Solo Track Artist"
        assert track.duration == 180

    def test_track_from_api_data_none(self):
        """Test Track creation from None API data."""
        track = Track.from_api_data(None)

        assert track.id == ""
        assert track.title == ""
        assert track.artists == []
        assert track.album is None

    def test_track_formatted_duration_valid(self, sample_artist):
        """Test Track formatted duration property with valid duration."""
        track = Track(
            id="123",
            title="Duration Track",
            artists=[sample_artist],
            duration=245  # 4 minutes, 5 seconds
        )

        assert track.formatted_duration == "4:05"

    def test_track_formatted_duration_zero(self, sample_artist):
        """Test Track formatted duration property with zero duration."""
        track = Track(
            id="124",
            title="Zero Duration Track",
            artists=[sample_artist],
            duration=0
        )

        assert track.formatted_duration == "0:00"

    def test_track_formatted_duration_none(self, sample_artist):
        """Test Track formatted duration property with None duration."""
        track = Track(
            id="125",
            title="No Duration Track",
            artists=[sample_artist],
            duration=None
        )

        assert track.formatted_duration == "0:00"

    def test_track_formatted_duration_long(self, sample_artist):
        """Test Track formatted duration property with long duration."""
        track = Track(
            id="126",
            title="Long Track",
            artists=[sample_artist],
            duration=3661  # 1 hour, 1 minute, 1 second
        )

        assert track.formatted_duration == "61:01"

    def test_track_artist_names_multiple(self):
        """Test Track artist_names property with multiple artists."""
        artist1 = Artist(id="1", name="Artist One")
        artist2 = Artist(id="2", name="Artist Two")
        artist3 = Artist(id="3", name="Artist Three")

        track = Track(
            id="127",
            title="Multi Artist Track",
            artists=[artist1, artist2, artist3]
        )

        assert track.artist_names == "Artist One, Artist Two, Artist Three"

    def test_track_artist_names_single(self, sample_artist):
        """Test Track artist_names property with single artist."""
        track = Track(
            id="128",
            title="Single Artist Track",
            artists=[sample_artist]
        )

        assert track.artist_names == sample_artist.name

    def test_track_artist_names_empty(self):
        """Test Track artist_names property with no artists."""
        track = Track(
            id="129",
            title="No Artists Track",
            artists=[]
        )

        assert track.artist_names == ""

    def test_track_to_dict(self, sample_artist, sample_album):
        """Test Track serialization to dictionary."""
        track = Track(
            id="54321",
            title="Dict Track",
            artists=[sample_artist],
            album=sample_album,
            duration=195,
            track_number=5,
            disc_number=2,
            url="https://tidal.com/track/54321",
            stream_url="https://stream.tidal.com/track/54321",
            explicit=False,
            quality="LOSSLESS"
        )

        track_dict = track.to_dict()

        assert track_dict["id"] == "54321"
        assert track_dict["title"] == "Dict Track"
        assert len(track_dict["artists"]) == 1
        assert track_dict["artists"][0]["name"] == sample_artist.name
        assert track_dict["album"]["title"] == sample_album.title
        assert track_dict["duration"] == 195
        assert track_dict["track_number"] == 5
        assert track_dict["disc_number"] == 2
        assert track_dict["url"] == "https://tidal.com/track/54321"
        assert track_dict["stream_url"] == "https://stream.tidal.com/track/54321"
        assert track_dict["explicit"] is False
        assert track_dict["quality"] == "LOSSLESS"

    def test_track_to_dict_no_album(self, sample_artist):
        """Test Track serialization without album."""
        track = Track(
            id="55555",
            title="No Album Track",
            artists=[sample_artist],
            album=None
        )

        track_dict = track.to_dict()

        assert track_dict["album"] is None


class TestPlaylistModel:
    """Test Playlist model functionality."""

    def test_playlist_creation_basic(self):
        """Test basic Playlist model creation."""
        playlist = Playlist(
            id="playlist-123",
            title="Test Playlist"
        )

        assert playlist.id == "playlist-123"
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

    def test_playlist_creation_full(self, sample_track):
        """Test Playlist model creation with all fields."""
        created_at = datetime(2023, 1, 1, 12, 0, 0)
        updated_at = datetime(2023, 1, 2, 15, 30, 0)

        playlist = Playlist(
            id="playlist-456",
            title="Full Playlist",
            description="A complete test playlist",
            creator="Test Creator",
            tracks=[sample_track],
            number_of_tracks=1,
            duration=210,
            created_at=created_at,
            updated_at=updated_at,
            image="https://example.com/playlist.jpg",
            url="https://tidal.com/playlist/playlist-456",
            public=False
        )

        assert playlist.id == "playlist-456"
        assert playlist.title == "Full Playlist"
        assert playlist.description == "A complete test playlist"
        assert playlist.creator == "Test Creator"
        assert len(playlist.tracks) == 1
        assert playlist.tracks[0] == sample_track
        assert playlist.number_of_tracks == 1
        assert playlist.duration == 210
        assert playlist.created_at == created_at
        assert playlist.updated_at == updated_at
        assert playlist.image == "https://example.com/playlist.jpg"
        assert playlist.url == "https://tidal.com/playlist/playlist-456"
        assert playlist.public is False

    def test_playlist_from_api_data_complete(self):
        """Test Playlist creation from complete API data."""
        api_data = {
            "uuid": "playlist-789",
            "title": "API Playlist",
            "description": "From API",
            "creator": {"name": "API Creator"},
            "tracks": [
                {
                    "id": 111,
                    "title": "Track 1",
                    "artists": [{"id": 222, "name": "Artist 1"}],
                    "duration": 180
                }
            ],
            "numberOfTracks": 1,
            "duration": 180,
            "created": "2023-01-01T12:00:00Z",
            "lastUpdated": "2023-01-02T15:30:00Z",
            "image": "https://example.com/api-playlist.jpg",
            "url": "https://tidal.com/playlist/playlist-789",
            "publicPlaylist": True
        }

        playlist = Playlist.from_api_data(api_data)

        assert playlist.id == "playlist-789"
        assert playlist.title == "API Playlist"
        assert playlist.description == "From API"
        assert playlist.creator == "API Creator"
        assert len(playlist.tracks) == 1
        assert playlist.tracks[0].title == "Track 1"
        assert playlist.number_of_tracks == 1
        assert playlist.duration == 180
        assert playlist.created_at is not None
        assert playlist.updated_at is not None
        assert playlist.image == "https://example.com/api-playlist.jpg"
        assert playlist.url == "https://tidal.com/playlist/playlist-789"
        assert playlist.public is True

    def test_playlist_from_api_data_fallback_id(self):
        """Test Playlist creation from API data using fallback ID."""
        api_data = {
            "id": "fallback-id",
            "title": "Fallback ID Playlist"
        }

        playlist = Playlist.from_api_data(api_data)

        assert playlist.id == "fallback-id"
        assert playlist.title == "Fallback ID Playlist"

    def test_playlist_from_api_data_invalid_dates(self):
        """Test Playlist creation from API data with invalid dates."""
        api_data = {
            "uuid": "playlist-invalid-dates",
            "title": "Invalid Dates Playlist",
            "created": "invalid-date-format",
            "lastUpdated": "also-invalid"
        }

        playlist = Playlist.from_api_data(api_data)

        assert playlist.id == "playlist-invalid-dates"
        assert playlist.title == "Invalid Dates Playlist"
        assert playlist.created_at is None
        assert playlist.updated_at is None

    def test_playlist_from_api_data_none(self):
        """Test Playlist creation from None API data."""
        playlist = Playlist.from_api_data(None)

        assert playlist.id == ""
        assert playlist.title == ""
        assert playlist.tracks == []

    def test_playlist_formatted_duration_short(self):
        """Test Playlist formatted duration property for short duration."""
        playlist = Playlist(
            id="short-playlist",
            title="Short Playlist",
            duration=245  # 4 minutes, 5 seconds
        )

        assert playlist.formatted_duration == "4:05"

    def test_playlist_formatted_duration_long(self):
        """Test Playlist formatted duration property for long duration."""
        playlist = Playlist(
            id="long-playlist",
            title="Long Playlist",
            duration=7265  # 2 hours, 1 minute, 5 seconds
        )

        assert playlist.formatted_duration == "2:01:05"

    def test_playlist_formatted_duration_zero(self):
        """Test Playlist formatted duration property for zero duration."""
        playlist = Playlist(
            id="empty-playlist",
            title="Empty Playlist",
            duration=0
        )

        assert playlist.formatted_duration == "0:00"

    def test_playlist_formatted_duration_none(self):
        """Test Playlist formatted duration property for None duration."""
        playlist = Playlist(
            id="no-duration-playlist",
            title="No Duration Playlist",
            duration=None
        )

        assert playlist.formatted_duration == "0:00"

    def test_playlist_to_dict(self, sample_track):
        """Test Playlist serialization to dictionary."""
        created_at = datetime(2023, 1, 1, 12, 0, 0)
        updated_at = datetime(2023, 1, 2, 15, 30, 0)

        playlist = Playlist(
            id="dict-playlist",
            title="Dict Playlist",
            description="For serialization",
            creator="Dict Creator",
            tracks=[sample_track],
            number_of_tracks=1,
            duration=210,
            created_at=created_at,
            updated_at=updated_at,
            image="https://example.com/dict-playlist.jpg",
            url="https://tidal.com/playlist/dict-playlist",
            public=True
        )

        playlist_dict = playlist.to_dict()

        assert playlist_dict["id"] == "dict-playlist"
        assert playlist_dict["title"] == "Dict Playlist"
        assert playlist_dict["description"] == "For serialization"
        assert playlist_dict["creator"] == "Dict Creator"
        assert len(playlist_dict["tracks"]) == 1
        assert playlist_dict["tracks"][0]["title"] == sample_track.title
        assert playlist_dict["number_of_tracks"] == 1
        assert playlist_dict["duration"] == 210
        assert playlist_dict["created_at"] == created_at.isoformat()
        assert playlist_dict["updated_at"] == updated_at.isoformat()
        assert playlist_dict["image"] == "https://example.com/dict-playlist.jpg"
        assert playlist_dict["url"] == "https://tidal.com/playlist/dict-playlist"
        assert playlist_dict["public"] is True

    def test_playlist_to_dict_none_dates(self):
        """Test Playlist serialization with None dates."""
        playlist = Playlist(
            id="no-dates-playlist",
            title="No Dates Playlist",
            created_at=None,
            updated_at=None
        )

        playlist_dict = playlist.to_dict()

        assert playlist_dict["created_at"] is None
        assert playlist_dict["updated_at"] is None


class TestSearchResultsModel:
    """Test SearchResults model functionality."""

    def test_search_results_creation_empty(self):
        """Test SearchResults creation with empty results."""
        results = SearchResults()

        assert results.tracks == []
        assert results.albums == []
        assert results.artists == []
        assert results.playlists == []
        assert results.total_results == 0

    def test_search_results_creation_with_data(self, sample_track, sample_album, sample_artist, sample_playlist):
        """Test SearchResults creation with data."""
        results = SearchResults(
            tracks=[sample_track],
            albums=[sample_album],
            artists=[sample_artist],
            playlists=[sample_playlist]
        )

        assert len(results.tracks) == 1
        assert len(results.albums) == 1
        assert len(results.artists) == 1
        assert len(results.playlists) == 1
        assert results.total_results == 4

    def test_search_results_total_results_calculation(self, sample_track, sample_album):
        """Test SearchResults total_results calculation."""
        # Create multiple items of different types
        track1 = Track(id="1", title="Track 1", artists=[])
        track2 = Track(id="2", title="Track 2", artists=[])

        album1 = Album(id="1", title="Album 1", artists=[])
        album2 = Album(id="2", title="Album 2", artists=[])
        album3 = Album(id="3", title="Album 3", artists=[])

        artist1 = Artist(id="1", name="Artist 1")

        results = SearchResults(
            tracks=[track1, track2],
            albums=[album1, album2, album3],
            artists=[artist1],
            playlists=[]
        )

        assert results.total_results == 6  # 2 + 3 + 1 + 0

    def test_search_results_to_dict(self, sample_track, sample_album, sample_artist, sample_playlist):
        """Test SearchResults serialization to dictionary."""
        results = SearchResults(
            tracks=[sample_track],
            albums=[sample_album],
            artists=[sample_artist],
            playlists=[sample_playlist]
        )

        results_dict = results.to_dict()

        assert "tracks" in results_dict
        assert "albums" in results_dict
        assert "artists" in results_dict
        assert "playlists" in results_dict

        assert len(results_dict["tracks"]) == 1
        assert len(results_dict["albums"]) == 1
        assert len(results_dict["artists"]) == 1
        assert len(results_dict["playlists"]) == 1

        assert results_dict["tracks"][0]["title"] == sample_track.title
        assert results_dict["albums"][0]["title"] == sample_album.title
        assert results_dict["artists"][0]["name"] == sample_artist.name
        assert results_dict["playlists"][0]["title"] == sample_playlist.title

    def test_search_results_to_dict_empty(self):
        """Test SearchResults serialization with empty results."""
        results = SearchResults()

        results_dict = results.to_dict()

        assert results_dict == {
            "tracks": [],
            "albums": [],
            "artists": [],
            "playlists": []
        }


class TestModelEdgeCases:
    """Test edge cases and error handling for all models."""

    def test_artist_id_conversion_from_int(self):
        """Test Artist ID conversion from integer."""
        api_data = {"id": 12345, "name": "Int ID Artist"}

        artist = Artist.from_api_data(api_data)

        assert artist.id == "12345"
        assert isinstance(artist.id, str)

    def test_album_id_conversion_from_int(self):
        """Test Album ID conversion from integer."""
        api_data = {"id": 67890, "title": "Int ID Album"}

        album = Album.from_api_data(api_data)

        assert album.id == "67890"
        assert isinstance(album.id, str)

    def test_track_id_conversion_from_int(self):
        """Test Track ID conversion from integer."""
        api_data = {"id": 54321, "title": "Int ID Track"}

        track = Track.from_api_data(api_data)

        assert track.id == "54321"
        assert isinstance(track.id, str)

    def test_playlist_id_conversion_from_int(self):
        """Test Playlist ID conversion from integer with fallback."""
        api_data = {"id": 98765, "title": "Int ID Playlist"}

        playlist = Playlist.from_api_data(api_data)

        assert playlist.id == "98765"
        assert isinstance(playlist.id, str)

    def test_nested_model_creation_complex(self):
        """Test complex nested model creation from API data."""
        api_data = {
            "id": 12345,
            "title": "Complex Track",
            "artists": [
                {"id": 1, "name": "Primary Artist", "popularity": 95},
                {"id": 2, "name": "Featured Artist", "popularity": 80}
            ],
            "album": {
                "id": 67890,
                "title": "Complex Album",
                "artists": [
                    {"id": 1, "name": "Primary Artist"},
                    {"id": 3, "name": "Album Collaborator"}
                ],
                "releaseDate": "2023-05-15",
                "numberOfTracks": 12,
                "explicit": True
            },
            "duration": 195,
            "trackNumber": 4,
            "discNumber": 1,
            "explicit": False,
            "quality": "LOSSLESS"
        }

        track = Track.from_api_data(api_data)

        # Verify track
        assert track.id == "12345"
        assert track.title == "Complex Track"
        assert len(track.artists) == 2
        assert track.artists[0].name == "Primary Artist"
        assert track.artists[1].name == "Featured Artist"

        # Verify nested album
        assert track.album is not None
        assert track.album.id == "67890"
        assert track.album.title == "Complex Album"
        assert len(track.album.artists) == 2
        assert track.album.artists[0].name == "Primary Artist"
        assert track.album.artists[1].name == "Album Collaborator"
        assert track.album.explicit is True

        # Verify track-specific fields
        assert track.duration == 195
        assert track.track_number == 4
        assert track.disc_number == 1
        assert track.explicit is False
        assert track.quality == "LOSSLESS"

    def test_model_serialization_json_compatibility(self, sample_track, sample_album, sample_artist, sample_playlist):
        """Test that model serialization is JSON-compatible."""
        # Test individual models
        artist_dict = sample_artist.to_dict()
        album_dict = sample_album.to_dict()
        track_dict = sample_track.to_dict()
        playlist_dict = sample_playlist.to_dict()

        # Verify JSON serialization works
        artist_json = json.dumps(artist_dict)
        album_json = json.dumps(album_dict)
        track_json = json.dumps(track_dict)
        playlist_json = json.dumps(playlist_dict)

        # Verify deserialization works
        assert json.loads(artist_json) == artist_dict
        assert json.loads(album_json) == album_dict
        assert json.loads(track_json) == track_dict
        assert json.loads(playlist_json) == playlist_dict

        # Test SearchResults
        results = SearchResults(
            tracks=[sample_track],
            albums=[sample_album],
            artists=[sample_artist],
            playlists=[sample_playlist]
        )

        results_dict = results.to_dict()
        results_json = json.dumps(results_dict)
        assert json.loads(results_json) == results_dict

    def test_model_defaults_and_optional_fields(self):
        """Test model behavior with default and optional fields."""
        # Test minimal Artist
        artist = Artist(id="min", name="Minimal")
        assert artist.url is None
        assert artist.picture is None
        assert artist.popularity is None

        # Test minimal Album
        album = Album(id="min", title="Minimal", artists=[])
        assert album.release_date is None
        assert album.duration is None
        assert album.number_of_tracks is None
        assert album.cover is None
        assert album.url is None
        assert album.explicit is False

        # Test minimal Track
        track = Track(id="min", title="Minimal", artists=[])
        assert track.album is None
        assert track.duration is None
        assert track.track_number is None
        assert track.disc_number is None
        assert track.url is None
        assert track.stream_url is None
        assert track.explicit is False
        assert track.quality is None

        # Test minimal Playlist
        playlist = Playlist(id="min", title="Minimal")
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

    def test_model_field_type_validation(self):
        """Test that models handle type conversion appropriately."""
        # Test Artist with various data types
        artist = Artist(id=123, name="Type Test")  # ID as int
        assert artist.id == 123  # Dataclass keeps original type
        assert isinstance(artist.id, int)

        # Test boolean fields
        album = Album(id="test", title="Test", artists=[], explicit="true")
        # Note: dataclass doesn't do automatic type conversion
        # The explicit field will remain as string "true"
        assert album.explicit == "true"

        # Test that numeric fields accept various types
        track = Track(id="test", title="Test", artists=[], duration="180")
        assert track.duration == "180"  # Remains as string without conversion