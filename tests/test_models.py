"""
Tests for Tidal Data Models

Comprehensive unit tests for data models including Artist, Album, Track,
Playlist, and SearchResults. Tests cover initialization, serialization,
validation, and edge cases.
"""

from datetime import datetime

import pytest

from tidal_mcp.models import Album, Artist, Playlist, SearchResults, Track


class TestArtist:
    """Test Artist model."""

    def test_artist_creation_minimal(self):
        """Test artist creation with minimal parameters."""
        artist = Artist(id="123", name="Test Artist")

        assert artist.id == "123"
        assert artist.name == "Test Artist"
        assert artist.url is None
        assert artist.picture is None
        assert artist.popularity is None

    def test_artist_creation_full(self):
        """Test artist creation with all parameters."""
        artist = Artist(
            id="456",
            name="Full Artist",
            url="https://tidal.com/artist/456",
            picture="https://example.com/picture.jpg",
            popularity=85,
        )

        assert artist.id == "456"
        assert artist.name == "Full Artist"
        assert artist.url == "https://tidal.com/artist/456"
        assert artist.picture == "https://example.com/picture.jpg"
        assert artist.popularity == 85

    def test_artist_from_api_data_complete(self):
        """Test artist creation from complete API data."""
        api_data = {
            "id": 789,
            "name": "API Artist",
            "url": "https://tidal.com/browse/artist/789",
            "picture": "https://resources.tidal.com/images/artist_pic.jpg",
            "popularity": 92,
        }

        artist = Artist.from_api_data(api_data)

        assert artist.id == "789"
        assert artist.name == "API Artist"
        assert artist.url == "https://tidal.com/browse/artist/789"
        assert artist.picture == "https://resources.tidal.com/images/artist_pic.jpg"
        assert artist.popularity == 92

    def test_artist_from_api_data_minimal(self):
        """Test artist creation from minimal API data."""
        api_data = {"id": 101, "name": "Minimal Artist"}

        artist = Artist.from_api_data(api_data)

        assert artist.id == "101"
        assert artist.name == "Minimal Artist"
        assert artist.url is None
        assert artist.picture is None
        assert artist.popularity is None

    def test_artist_from_api_data_empty(self):
        """Test artist creation from empty API data."""
        api_data = {}

        artist = Artist.from_api_data(api_data)

        assert artist.id == ""
        assert artist.name == ""
        assert artist.url is None
        assert artist.picture is None
        assert artist.popularity is None

    def test_artist_to_dict(self):
        """Test artist to dictionary conversion."""
        artist = Artist(
            id="999",
            name="Dict Artist",
            url="https://example.com",
            picture="https://pic.com/image.jpg",
            popularity=75,
        )

        result = artist.to_dict()

        expected = {
            "id": "999",
            "name": "Dict Artist",
            "url": "https://example.com",
            "picture": "https://pic.com/image.jpg",
            "popularity": 75,
        }

        assert result == expected

    def test_artist_to_dict_with_none_values(self):
        """Test artist to dictionary with None values."""
        artist = Artist(id="888", name="None Artist")

        result = artist.to_dict()

        expected = {
            "id": "888",
            "name": "None Artist",
            "url": None,
            "picture": None,
            "popularity": None,
        }

        assert result == expected


class TestAlbum:
    """Test Album model."""

    def test_album_creation_minimal(self):
        """Test album creation with minimal parameters."""
        album = Album(id="123", title="Test Album")

        assert album.id == "123"
        assert album.title == "Test Album"
        assert album.artists == []
        assert album.release_date is None
        assert album.duration is None
        assert album.number_of_tracks is None
        assert album.cover is None
        assert album.url is None
        assert album.explicit is False

    def test_album_creation_with_artists(self):
        """Test album creation with artists."""
        artist1 = Artist(id="1", name="Artist 1")
        artist2 = Artist(id="2", name="Artist 2")

        album = Album(
            id="456",
            title="Multi-Artist Album",
            artists=[artist1, artist2],
            release_date="2023-01-15",
            duration=3600,
            number_of_tracks=12,
            cover="https://cover.com/album.jpg",
            url="https://tidal.com/album/456",
            explicit=True,
        )

        assert len(album.artists) == 2
        assert album.artists[0].name == "Artist 1"
        assert album.artists[1].name == "Artist 2"
        assert album.release_date == "2023-01-15"
        assert album.duration == 3600
        assert album.number_of_tracks == 12
        assert album.cover == "https://cover.com/album.jpg"
        assert album.url == "https://tidal.com/album/456"
        assert album.explicit is True

    def test_album_from_api_data_with_artists_list(self):
        """Test album creation from API data with artists list."""
        api_data = {
            "id": 789,
            "title": "API Album",
            "artists": [
                {"id": 1, "name": "Main Artist"},
                {"id": 2, "name": "Featured Artist"},
            ],
            "releaseDate": "2023-05-20",
            "duration": 2400,
            "numberOfTracks": 8,
            "cover": "https://api.tidal.com/cover.jpg",
            "url": "https://tidal.com/browse/album/789",
            "explicit": False,
        }

        album = Album.from_api_data(api_data)

        assert album.id == "789"
        assert album.title == "API Album"
        assert len(album.artists) == 2
        assert album.artists[0].name == "Main Artist"
        assert album.artists[1].name == "Featured Artist"
        assert album.release_date == "2023-05-20"
        assert album.duration == 2400
        assert album.number_of_tracks == 8
        assert album.explicit is False

    def test_album_from_api_data_with_single_artist(self):
        """Test album creation from API data with single artist."""
        api_data = {
            "id": 101,
            "title": "Single Artist Album",
            "artist": {"id": 1, "name": "Solo Artist"},
            "releaseDate": "2022-12-01",
        }

        album = Album.from_api_data(api_data)

        assert album.id == "101"
        assert album.title == "Single Artist Album"
        assert len(album.artists) == 1
        assert album.artists[0].name == "Solo Artist"

    def test_album_to_dict(self):
        """Test album to dictionary conversion."""
        artist = Artist(id="1", name="Test Artist")
        album = Album(
            id="555",
            title="Dict Album",
            artists=[artist],
            release_date="2023-03-10",
            duration=2800,
            number_of_tracks=10,
            cover="https://cover.jpg",
            url="https://tidal.com/album/555",
            explicit=True,
        )

        result = album.to_dict()

        assert result["id"] == "555"
        assert result["title"] == "Dict Album"
        assert len(result["artists"]) == 1
        assert result["artists"][0]["name"] == "Test Artist"
        assert result["release_date"] == "2023-03-10"
        assert result["duration"] == 2800
        assert result["number_of_tracks"] == 10
        assert result["explicit"] is True


class TestTrack:
    """Test Track model."""

    def test_track_creation_minimal(self):
        """Test track creation with minimal parameters."""
        track = Track(id="123", title="Test Track")

        assert track.id == "123"
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

    def test_track_creation_full(self):
        """Test track creation with all parameters."""
        artist = Artist(id="1", name="Track Artist")
        album = Album(id="2", title="Track Album", artists=[artist])

        track = Track(
            id="456",
            title="Full Track",
            artists=[artist],
            album=album,
            duration=245,
            track_number=3,
            disc_number=1,
            url="https://tidal.com/track/456",
            stream_url="https://stream.tidal.com/track/456",
            explicit=True,
            quality="LOSSLESS",
        )

        assert track.id == "456"
        assert track.title == "Full Track"
        assert len(track.artists) == 1
        assert track.artists[0].name == "Track Artist"
        assert track.album.title == "Track Album"
        assert track.duration == 245
        assert track.track_number == 3
        assert track.disc_number == 1
        assert track.explicit is True
        assert track.quality == "LOSSLESS"

    def test_track_from_api_data_complete(self):
        """Test track creation from complete API data."""
        api_data = {
            "id": 789,
            "title": "API Track",
            "artists": [{"id": 1, "name": "API Artist"}],
            "album": {
                "id": 2,
                "title": "API Album",
                "artists": [{"id": 1, "name": "API Artist"}],
            },
            "duration": 220,
            "trackNumber": 5,
            "discNumber": 2,
            "url": "https://tidal.com/browse/track/789",
            "streamUrl": "https://fa723fc0-cf.tidal.com/track.flac",
            "explicit": True,
            "quality": "HI_RES",
        }

        track = Track.from_api_data(api_data)

        assert track.id == "789"
        assert track.title == "API Track"
        assert len(track.artists) == 1
        assert track.artists[0].name == "API Artist"
        assert track.album.title == "API Album"
        assert track.duration == 220
        assert track.track_number == 5
        assert track.disc_number == 2
        assert track.explicit is True
        assert track.quality == "HI_RES"

    def test_track_formatted_duration(self):
        """Test track formatted duration property."""
        # Test normal duration
        track = Track(id="1", title="Track", duration=245)  # 4:05
        assert track.formatted_duration == "4:05"

        # Test zero duration
        track_zero = Track(id="2", title="Track", duration=0)
        assert track_zero.formatted_duration == "0:00"

        # Test None duration
        track_none = Track(id="3", title="Track", duration=None)
        assert track_none.formatted_duration == "0:00"

        # Test duration with seconds < 10
        track_short = Track(id="4", title="Track", duration=125)  # 2:05
        assert track_short.formatted_duration == "2:05"

    def test_track_artist_names(self):
        """Test track artist names property."""
        artist1 = Artist(id="1", name="First Artist")
        artist2 = Artist(id="2", name="Second Artist")

        # Test single artist
        track_single = Track(id="1", title="Track", artists=[artist1])
        assert track_single.artist_names == "First Artist"

        # Test multiple artists
        track_multi = Track(id="2", title="Track", artists=[artist1, artist2])
        assert track_multi.artist_names == "First Artist, Second Artist"

        # Test no artists
        track_none = Track(id="3", title="Track", artists=[])
        assert track_none.artist_names == ""

    def test_track_to_dict(self):
        """Test track to dictionary conversion."""
        artist = Artist(id="1", name="Test Artist")
        album = Album(id="2", title="Test Album", artists=[artist])

        track = Track(
            id="999",
            title="Dict Track",
            artists=[artist],
            album=album,
            duration=300,
            track_number=7,
            disc_number=1,
            url="https://tidal.com/track/999",
            stream_url="https://stream.tidal.com/999",
            explicit=False,
            quality="LOSSLESS",
        )

        result = track.to_dict()

        assert result["id"] == "999"
        assert result["title"] == "Dict Track"
        assert len(result["artists"]) == 1
        assert result["artists"][0]["name"] == "Test Artist"
        assert result["album"]["title"] == "Test Album"
        assert result["duration"] == 300
        assert result["track_number"] == 7
        assert result["disc_number"] == 1
        assert result["explicit"] is False
        assert result["quality"] == "LOSSLESS"

    def test_track_to_dict_no_album(self):
        """Test track to dictionary with no album."""
        track = Track(id="888", title="No Album Track")

        result = track.to_dict()

        assert result["album"] is None


class TestPlaylist:
    """Test Playlist model."""

    def test_playlist_creation_minimal(self):
        """Test playlist creation with minimal parameters."""
        playlist = Playlist(id="123", title="Test Playlist")

        assert playlist.id == "123"
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

    def test_playlist_creation_full(self):
        """Test playlist creation with all parameters."""
        track1 = Track(id="1", title="Track 1", duration=200)
        track2 = Track(id="2", title="Track 2", duration=180)
        created = datetime(2023, 1, 1, 12, 0, 0)
        updated = datetime(2023, 6, 15, 15, 30, 0)

        playlist = Playlist(
            id="456",
            title="Full Playlist",
            description="A complete test playlist",
            creator="Test User",
            tracks=[track1, track2],
            number_of_tracks=2,
            duration=380,
            created_at=created,
            updated_at=updated,
            image="https://image.com/playlist.jpg",
            url="https://tidal.com/playlist/456",
            public=False,
        )

        assert playlist.id == "456"
        assert playlist.title == "Full Playlist"
        assert playlist.description == "A complete test playlist"
        assert playlist.creator == "Test User"
        assert len(playlist.tracks) == 2
        assert playlist.tracks[0].title == "Track 1"
        assert playlist.number_of_tracks == 2
        assert playlist.duration == 380
        assert playlist.created_at == created
        assert playlist.updated_at == updated
        assert playlist.public is False

    def test_playlist_from_api_data_complete(self):
        """Test playlist creation from complete API data."""
        api_data = {
            "uuid": "playlist-uuid-123",
            "title": "API Playlist",
            "description": "From API",
            "creator": {"name": "API User"},
            "tracks": [
                {
                    "id": 1,
                    "title": "API Track",
                    "artists": [{"id": 1, "name": "API Artist"}],
                    "duration": 210,
                }
            ],
            "numberOfTracks": 1,
            "duration": 210,
            "created": "2023-01-01T00:00:00Z",
            "lastUpdated": "2023-06-01T12:00:00Z",
            "image": "https://api.image.com/playlist.jpg",
            "url": "https://tidal.com/browse/playlist/uuid-123",
            "publicPlaylist": True,
        }

        playlist = Playlist.from_api_data(api_data)

        assert playlist.id == "playlist-uuid-123"
        assert playlist.title == "API Playlist"
        assert playlist.description == "From API"
        assert playlist.creator == "API User"
        assert len(playlist.tracks) == 1
        assert playlist.tracks[0].title == "API Track"
        assert playlist.number_of_tracks == 1
        assert playlist.duration == 210
        assert playlist.created_at is not None
        assert playlist.updated_at is not None
        assert playlist.public is True

    def test_playlist_from_api_data_minimal(self):
        """Test playlist creation from minimal API data."""
        api_data = {"id": "simple-playlist", "title": "Simple Playlist"}

        playlist = Playlist.from_api_data(api_data)

        assert playlist.id == "simple-playlist"
        assert playlist.title == "Simple Playlist"
        assert playlist.creator is None
        assert len(playlist.tracks) == 0

    def test_playlist_from_api_data_invalid_dates(self):
        """Test playlist creation with invalid date formats."""
        api_data = {
            "uuid": "date-test",
            "title": "Date Test Playlist",
            "created": "invalid-date",
            "lastUpdated": "also-invalid",
        }

        playlist = Playlist.from_api_data(api_data)

        assert playlist.created_at is None
        assert playlist.updated_at is None

    def test_playlist_formatted_duration(self):
        """Test playlist formatted duration property."""
        # Test duration under 1 hour
        playlist_short = Playlist(id="1", title="Short", duration=1800)  # 30:00
        assert playlist_short.formatted_duration == "30:00"

        # Test duration over 1 hour
        playlist_long = Playlist(id="2", title="Long", duration=3665)  # 1:01:05
        assert playlist_long.formatted_duration == "1:01:05"

        # Test zero duration
        playlist_zero = Playlist(id="3", title="Zero", duration=0)
        assert playlist_zero.formatted_duration == "0:00"

        # Test None duration
        playlist_none = Playlist(id="4", title="None", duration=None)
        assert playlist_none.formatted_duration == "0:00"

    def test_playlist_to_dict(self):
        """Test playlist to dictionary conversion."""
        track = Track(id="1", title="Playlist Track", duration=200)
        created = datetime(2023, 1, 1, 12, 0, 0)
        updated = datetime(2023, 6, 1, 18, 45, 30)

        playlist = Playlist(
            id="dict-test",
            title="Dict Playlist",
            description="Test description",
            creator="Dict Creator",
            tracks=[track],
            number_of_tracks=1,
            duration=200,
            created_at=created,
            updated_at=updated,
            image="https://image.jpg",
            url="https://tidal.com/playlist/dict-test",
            public=True,
        )

        result = playlist.to_dict()

        assert result["id"] == "dict-test"
        assert result["title"] == "Dict Playlist"
        assert result["description"] == "Test description"
        assert result["creator"] == "Dict Creator"
        assert len(result["tracks"]) == 1
        assert result["tracks"][0]["title"] == "Playlist Track"
        assert result["number_of_tracks"] == 1
        assert result["duration"] == 200
        assert result["created_at"] == created.isoformat()
        assert result["updated_at"] == updated.isoformat()
        assert result["public"] is True

    def test_playlist_to_dict_none_dates(self):
        """Test playlist to dictionary with None dates."""
        playlist = Playlist(id="none-dates", title="None Dates")

        result = playlist.to_dict()

        assert result["created_at"] is None
        assert result["updated_at"] is None


class TestSearchResults:
    """Test SearchResults model."""

    def test_search_results_creation_empty(self):
        """Test search results creation with default empty lists."""
        results = SearchResults()

        assert results.tracks == []
        assert results.albums == []
        assert results.artists == []
        assert results.playlists == []
        assert results.total_results == 0

    def test_search_results_creation_with_data(self):
        """Test search results creation with data."""
        track = Track(id="1", title="Result Track")
        album = Album(id="2", title="Result Album")
        artist = Artist(id="3", name="Result Artist")
        playlist = Playlist(id="4", title="Result Playlist")

        results = SearchResults(
            tracks=[track],
            albums=[album],
            artists=[artist],
            playlists=[playlist],
        )

        assert len(results.tracks) == 1
        assert len(results.albums) == 1
        assert len(results.artists) == 1
        assert len(results.playlists) == 1
        assert results.total_results == 4

    def test_search_results_total_results(self):
        """Test search results total_results property."""
        # Test with mixed results
        results = SearchResults(
            tracks=[Track(id="1", title="T1"), Track(id="2", title="T2")],
            albums=[Album(id="3", title="A1")],
            artists=[],  # Empty
            playlists=[
                Playlist(id="4", title="P1"),
                Playlist(id="5", title="P2"),
                Playlist(id="6", title="P3"),
            ],
        )

        assert results.total_results == 6  # 2 + 1 + 0 + 3

    def test_search_results_to_dict(self):
        """Test search results to dictionary conversion."""
        track = Track(id="1", title="Dict Track")
        album = Album(id="2", title="Dict Album")
        artist = Artist(id="3", name="Dict Artist")
        playlist = Playlist(id="4", title="Dict Playlist")

        results = SearchResults(
            tracks=[track],
            albums=[album],
            artists=[artist],
            playlists=[playlist],
        )

        result_dict = results.to_dict()

        assert len(result_dict["tracks"]) == 1
        assert result_dict["tracks"][0]["title"] == "Dict Track"
        assert len(result_dict["albums"]) == 1
        assert result_dict["albums"][0]["title"] == "Dict Album"
        assert len(result_dict["artists"]) == 1
        assert result_dict["artists"][0]["name"] == "Dict Artist"
        assert len(result_dict["playlists"]) == 1
        assert result_dict["playlists"][0]["title"] == "Dict Playlist"

    def test_search_results_to_dict_empty(self):
        """Test search results to dictionary with empty results."""
        results = SearchResults()

        result_dict = results.to_dict()

        assert result_dict["tracks"] == []
        assert result_dict["albums"] == []
        assert result_dict["artists"] == []
        assert result_dict["playlists"] == []


class TestModelEdgeCases:
    """Test edge cases and error conditions."""

    def test_model_with_invalid_api_data_types(self):
        """Test model creation with invalid API data types."""
        # Test with None API data
        artist = Artist.from_api_data(None)
        assert artist.id == ""
        assert artist.name == ""

        # Test with non-dict API data
        artist2 = Artist.from_api_data("invalid")
        assert artist2.id == ""
        assert artist2.name == ""

    def test_nested_model_conversion(self):
        """Test complex nested model conversions."""
        api_data = {
            "id": 100,
            "title": "Complex Track",
            "artists": [
                {"id": 1, "name": "Main Artist", "popularity": 95},
                {"id": 2, "name": "Featured Artist", "popularity": 80},
            ],
            "album": {
                "id": 50,
                "title": "Complex Album",
                "artists": [{"id": 1, "name": "Album Artist"}],
                "releaseDate": "2023-01-01",
                "numberOfTracks": 12,
            },
            "duration": 240,
            "trackNumber": 3,
            "explicit": True,
        }

        track = Track.from_api_data(api_data)

        # Verify nested artist conversion
        assert len(track.artists) == 2
        assert track.artists[0].name == "Main Artist"
        assert track.artists[0].popularity == 95
        assert track.artists[1].name == "Featured Artist"

        # Verify nested album conversion
        assert track.album is not None
        assert track.album.title == "Complex Album"
        assert len(track.album.artists) == 1
        assert track.album.artists[0].name == "Album Artist"
        assert track.album.number_of_tracks == 12

    def test_model_with_missing_required_fields(self):
        """Test model behavior with missing required fields in API data."""
        # Track without required fields
        incomplete_api_data = {"duration": 200}  # Missing id and title

        track = Track.from_api_data(incomplete_api_data)

        assert track.id == ""  # Should default to empty string
        assert track.title == ""  # Should default to empty string
        assert track.duration == 200  # Should preserve provided value

    def test_circular_reference_handling(self):
        """Test handling of potential circular references in conversions."""
        # Create track with album that references the same artist
        api_data = {
            "id": 1,
            "title": "Circular Track",
            "artists": [{"id": 10, "name": "Shared Artist"}],
            "album": {
                "id": 2,
                "title": "Circular Album",
                "artists": [{"id": 10, "name": "Shared Artist"}],  # Same artist
            },
        }

        track = Track.from_api_data(api_data)

        # Verify the conversion works without infinite recursion
        assert track.artists[0].name == "Shared Artist"
        assert track.album.artists[0].name == "Shared Artist"

        # Verify to_dict works
        track_dict = track.to_dict()
        assert track_dict["artists"][0]["name"] == "Shared Artist"
        assert track_dict["album"]["artists"][0]["name"] == "Shared Artist"


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
