"""
Tidal Data Models

Data models representing Tidal music entities like tracks, albums, artists,
and playlists. Provides structured data access and serialization for the
MCP server.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Artist:
    """Represents a Tidal artist."""

    id: str
    name: str
    url: str | None = None
    picture: str | None = None
    popularity: int | None = None

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> "Artist":
        """
        Create Artist instance from Tidal API response data.

        Args:
            data: Raw API response data

        Returns:
            Artist instance
        """
        if data is None or not isinstance(data, dict):
            data = {}

        return cls(
            id=str(data.get("id", "")),
            name=data.get("name", ""),
            url=data.get("url"),
            picture=data.get("picture"),
            popularity=data.get("popularity"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert artist to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "picture": self.picture,
            "popularity": self.popularity,
        }


@dataclass
class Album:
    """Represents a Tidal album."""

    id: str
    title: str
    artists: list[Artist] = field(default_factory=list)
    release_date: str | None = None
    duration: int | None = None  # Duration in seconds
    number_of_tracks: int | None = None
    cover: str | None = None
    url: str | None = None
    explicit: bool = False

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> "Album":
        """
        Create Album instance from Tidal API response data.

        Args:
            data: Raw API response data

        Returns:
            Album instance
        """
        if data is None or not isinstance(data, dict):
            data = {}
        artists = []
        if "artists" in data:
            artists = [Artist.from_api_data(artist) for artist in data["artists"]]
        elif "artist" in data:
            artists = [Artist.from_api_data(data["artist"])]

        return cls(
            id=str(data.get("id", "")),
            title=data.get("title", ""),
            artists=artists,
            release_date=data.get("releaseDate"),
            duration=data.get("duration"),
            number_of_tracks=data.get("numberOfTracks"),
            cover=data.get("cover"),
            url=data.get("url"),
            explicit=data.get("explicit", False),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert album to dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "artists": [artist.to_dict() for artist in self.artists],
            "release_date": self.release_date,
            "duration": self.duration,
            "number_of_tracks": self.number_of_tracks,
            "cover": self.cover,
            "url": self.url,
            "explicit": self.explicit,
        }


@dataclass
class Track:
    """Represents a Tidal track."""

    id: str
    title: str
    artists: list[Artist] = field(default_factory=list)
    album: Album | None = None
    duration: int | None = None  # Duration in seconds
    track_number: int | None = None
    disc_number: int | None = None
    url: str | None = None
    stream_url: str | None = None
    explicit: bool = False
    quality: str | None = None  # e.g., "LOSSLESS", "HIGH", "LOW"

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> "Track":
        """
        Create Track instance from Tidal API response data.

        Args:
            data: Raw API response data

        Returns:
            Track instance
        """
        if data is None or not isinstance(data, dict):
            data = {}
        artists = []
        if "artists" in data:
            artists = [Artist.from_api_data(artist) for artist in data["artists"]]
        elif "artist" in data:
            artists = [Artist.from_api_data(data["artist"])]

        album = None
        if "album" in data:
            album = Album.from_api_data(data["album"])

        return cls(
            id=str(data.get("id", "")),
            title=data.get("title", ""),
            artists=artists,
            album=album,
            duration=data.get("duration"),
            track_number=data.get("trackNumber"),
            disc_number=data.get("discNumber"),
            url=data.get("url"),
            stream_url=data.get("streamUrl"),
            explicit=data.get("explicit", False),
            quality=data.get("quality"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert track to dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "artists": [artist.to_dict() for artist in self.artists],
            "album": self.album.to_dict() if self.album else None,
            "duration": self.duration,
            "track_number": self.track_number,
            "disc_number": self.disc_number,
            "url": self.url,
            "stream_url": self.stream_url,
            "explicit": self.explicit,
            "quality": self.quality,
        }

    @property
    def formatted_duration(self) -> str:
        """Get formatted duration string (e.g., "3:45")."""
        if not self.duration:
            return "0:00"

        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes}:{seconds:02d}"

    @property
    def artist_names(self) -> str:
        """Get comma-separated artist names."""
        return ", ".join(artist.name for artist in self.artists)


@dataclass
class Playlist:
    """Represents a Tidal playlist."""

    id: str
    title: str
    description: str | None = None
    creator: str | None = None
    tracks: list[Track] = field(default_factory=list)
    number_of_tracks: int | None = None
    duration: int | None = None  # Total duration in seconds
    created_at: datetime | None = None
    updated_at: datetime | None = None
    image: str | None = None
    url: str | None = None
    public: bool = True

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> "Playlist":
        """
        Create Playlist instance from Tidal API response data.

        Args:
            data: Raw API response data

        Returns:
            Playlist instance
        """
        if data is None or not isinstance(data, dict):
            data = {}
        tracks = []
        if "tracks" in data:
            tracks = [Track.from_api_data(track) for track in data["tracks"]]

        created_at = None
        if "created" in data:
            try:
                created_at = datetime.fromisoformat(
                    data["created"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                pass

        updated_at = None
        if "lastUpdated" in data:
            try:
                updated_at = datetime.fromisoformat(
                    data["lastUpdated"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                pass

        return cls(
            id=str(data.get("uuid", data.get("id", ""))),
            title=data.get("title", ""),
            description=data.get("description"),
            creator=(
                data.get("creator", {}).get("name") if data.get("creator") else None
            ),
            tracks=tracks,
            number_of_tracks=data.get("numberOfTracks"),
            duration=data.get("duration"),
            created_at=created_at,
            updated_at=updated_at,
            image=data.get("image"),
            url=data.get("url"),
            public=data.get("publicPlaylist", True),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert playlist to dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "creator": self.creator,
            "tracks": [track.to_dict() for track in self.tracks],
            "number_of_tracks": self.number_of_tracks,
            "duration": self.duration,
            "created_at": (self.created_at.isoformat() if self.created_at else None),
            "updated_at": (self.updated_at.isoformat() if self.updated_at else None),
            "image": self.image,
            "url": self.url,
            "public": self.public,
        }

    @property
    def formatted_duration(self) -> str:
        """Get formatted total duration string."""
        if not self.duration:
            return "0:00"

        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"


@dataclass
class SearchResults:
    """Container for search results across different content types."""

    tracks: list[Track] = field(default_factory=list)
    albums: list[Album] = field(default_factory=list)
    artists: list[Artist] = field(default_factory=list)
    playlists: list[Playlist] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert search results to dictionary representation."""
        return {
            "tracks": [track.to_dict() for track in self.tracks],
            "albums": [album.to_dict() for album in self.albums],
            "artists": [artist.to_dict() for artist in self.artists],
            "playlists": [playlist.to_dict() for playlist in self.playlists],
        }

    @property
    def total_results(self) -> int:
        """Get total number of results across all types."""
        return (
            len(self.tracks)
            + len(self.albums)
            + len(self.artists)
            + len(self.playlists)
        )
