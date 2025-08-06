"""
Tidal Data Models

Data models representing Tidal music entities like tracks, albums, artists, and playlists.
Provides structured data access and serialization for the MCP server.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class Artist:
    """Represents a Tidal artist."""

    id: str
    name: str
    url: Optional[str] = None
    picture: Optional[str] = None
    popularity: Optional[int] = None

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Artist':
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
            id=str(data.get('id', '')),
            name=data.get('name', ''),
            url=data.get('url'),
            picture=data.get('picture'),
            popularity=data.get('popularity')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert artist to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'picture': self.picture,
            'popularity': self.popularity
        }


@dataclass
class Album:
    """Represents a Tidal album."""

    id: str
    title: str
    artists: List[Artist] = field(default_factory=list)
    release_date: Optional[str] = None
    duration: Optional[int] = None  # Duration in seconds
    number_of_tracks: Optional[int] = None
    cover: Optional[str] = None
    url: Optional[str] = None
    explicit: bool = False

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Album':
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
        if 'artists' in data:
            artists = [Artist.from_api_data(artist) for artist in data['artists']]
        elif 'artist' in data:
            artists = [Artist.from_api_data(data['artist'])]

        return cls(
            id=str(data.get('id', '')),
            title=data.get('title', ''),
            artists=artists,
            release_date=data.get('releaseDate'),
            duration=data.get('duration'),
            number_of_tracks=data.get('numberOfTracks'),
            cover=data.get('cover'),
            url=data.get('url'),
            explicit=data.get('explicit', False)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert album to dictionary representation."""
        return {
            'id': self.id,
            'title': self.title,
            'artists': [artist.to_dict() for artist in self.artists],
            'release_date': self.release_date,
            'duration': self.duration,
            'number_of_tracks': self.number_of_tracks,
            'cover': self.cover,
            'url': self.url,
            'explicit': self.explicit
        }


@dataclass
class Track:
    """Represents a Tidal track."""

    id: str
    title: str
    artists: List[Artist] = field(default_factory=list)
    album: Optional[Album] = None
    duration: Optional[int] = None  # Duration in seconds
    track_number: Optional[int] = None
    disc_number: Optional[int] = None
    url: Optional[str] = None
    stream_url: Optional[str] = None
    explicit: bool = False
    quality: Optional[str] = None  # e.g., "LOSSLESS", "HIGH", "LOW"

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Track':
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
        if 'artists' in data:
            artists = [Artist.from_api_data(artist) for artist in data['artists']]
        elif 'artist' in data:
            artists = [Artist.from_api_data(data['artist'])]

        album = None
        if 'album' in data:
            album = Album.from_api_data(data['album'])

        return cls(
            id=str(data.get('id', '')),
            title=data.get('title', ''),
            artists=artists,
            album=album,
            duration=data.get('duration'),
            track_number=data.get('trackNumber'),
            disc_number=data.get('discNumber'),
            url=data.get('url'),
            stream_url=data.get('streamUrl'),
            explicit=data.get('explicit', False),
            quality=data.get('quality')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert track to dictionary representation."""
        return {
            'id': self.id,
            'title': self.title,
            'artists': [artist.to_dict() for artist in self.artists],
            'album': self.album.to_dict() if self.album else None,
            'duration': self.duration,
            'track_number': self.track_number,
            'disc_number': self.disc_number,
            'url': self.url,
            'stream_url': self.stream_url,
            'explicit': self.explicit,
            'quality': self.quality
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
    description: Optional[str] = None
    creator: Optional[str] = None
    tracks: List[Track] = field(default_factory=list)
    number_of_tracks: Optional[int] = None
    duration: Optional[int] = None  # Total duration in seconds
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    image: Optional[str] = None
    url: Optional[str] = None
    public: bool = True

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Playlist':
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
        if 'tracks' in data:
            tracks = [Track.from_api_data(track) for track in data['tracks']]

        created_at = None
        if 'created' in data:
            try:
                created_at = datetime.fromisoformat(data['created'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass

        updated_at = None
        if 'lastUpdated' in data:
            try:
                updated_at = datetime.fromisoformat(data['lastUpdated'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass

        return cls(
            id=str(data.get('uuid', data.get('id', ''))),
            title=data.get('title', ''),
            description=data.get('description'),
            creator=data.get('creator', {}).get('name') if data.get('creator') else None,
            tracks=tracks,
            number_of_tracks=data.get('numberOfTracks'),
            duration=data.get('duration'),
            created_at=created_at,
            updated_at=updated_at,
            image=data.get('image'),
            url=data.get('url'),
            public=data.get('publicPlaylist', True)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert playlist to dictionary representation."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'creator': self.creator,
            'tracks': [track.to_dict() for track in self.tracks],
            'number_of_tracks': self.number_of_tracks,
            'duration': self.duration,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'image': self.image,
            'url': self.url,
            'public': self.public
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

    tracks: List[Track] = field(default_factory=list)
    albums: List[Album] = field(default_factory=list)
    artists: List[Artist] = field(default_factory=list)
    playlists: List[Playlist] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert search results to dictionary representation."""
        return {
            'tracks': [track.to_dict() for track in self.tracks],
            'albums': [album.to_dict() for album in self.albums],
            'artists': [artist.to_dict() for artist in self.artists],
            'playlists': [playlist.to_dict() for playlist in self.playlists]
        }

    @property
    def total_results(self) -> int:
        """Get total number of results across all types."""
        return len(self.tracks) + len(self.albums) + len(self.artists) + len(self.playlists)
