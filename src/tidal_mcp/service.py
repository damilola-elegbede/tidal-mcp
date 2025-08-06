"""
Tidal Service Layer

Business logic and API interaction layer for Tidal music streaming service.
Provides high-level methods for music discovery, playlist management, and playback control.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import asdict
import tidalapi
from concurrent.futures import ThreadPoolExecutor
import functools

from .auth import TidalAuth, TidalAuthError
from .models import Track, Album, Artist, Playlist, SearchResults
from .utils import format_duration, sanitize_query, validate_tidal_id, safe_get

logger = logging.getLogger(__name__)


def async_to_sync(func):
    """Decorator to run sync tidalapi calls in thread pool."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, func, *args, **kwargs)
    return wrapper


class TidalService:
    """
    Main service class for Tidal API interactions.
    
    Provides methods for:
    - Music search and discovery
    - Playlist management
    - User library access
    - Playback control
    - Recommendations
    """
    
    def __init__(self, auth: TidalAuth):
        """
        Initialize Tidal service.
        
        Args:
            auth: TidalAuth instance for authentication
        """
        self.auth = auth
        self._cache = {}  # Simple in-memory cache
        self._cache_ttl = 300  # 5 minutes
    
    async def ensure_authenticated(self) -> None:
        """Ensure we have a valid authenticated session."""
        if not await self.auth.ensure_valid_token():
            raise TidalAuthError("Authentication required")
    
    def get_session(self) -> tidalapi.Session:
        """Get the authenticated Tidal session."""
        return self.auth.get_tidal_session()
    
    # Search functionality
    async def search_tracks(self, query: str, limit: int = 20, offset: int = 0) -> List[Track]:
        """
        Search for tracks on Tidal.
        
        Args:
            query: Search query string
            limit: Maximum number of results (1-50)
            offset: Pagination offset
            
        Returns:
            List of Track objects
        """
        try:
            await self.ensure_authenticated()
            session = self.get_session()
            
            sanitized_query = sanitize_query(query)
            if not sanitized_query:
                return []
            
            logger.info(f"Searching for tracks: '{sanitized_query}' (limit: {limit}, offset: {offset})")
            
            # Use thread pool for sync tidalapi call
            @async_to_sync
            def _search():
                search_result = session.search(sanitized_query, models=[tidalapi.Track])
                tracks = search_result.get('tracks', [])
                
                # Apply offset and limit
                start = offset
                end = offset + limit
                return tracks[start:end] if tracks else []
            
            tidal_tracks = await _search()
            
            # Convert to our Track model
            tracks = []
            for tidal_track in tidal_tracks:
                try:
                    track = await self._convert_tidal_track(tidal_track)
                    if track:
                        tracks.append(track)
                except Exception as e:
                    logger.warning(f"Failed to convert track {getattr(tidal_track, 'id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Found {len(tracks)} tracks for query '{sanitized_query}'")
            return tracks
            
        except Exception as e:
            logger.error(f"Track search failed for '{query}': {e}")
            return []
    
    async def search_albums(self, query: str, limit: int = 20, offset: int = 0) -> List[Album]:
        """
        Search for albums on Tidal.
        
        Args:
            query: Search query string
            limit: Maximum number of results (1-50)
            offset: Pagination offset
            
        Returns:
            List of Album objects
        """
        try:
            await self.ensure_authenticated()
            session = self.get_session()
            
            sanitized_query = sanitize_query(query)
            if not sanitized_query:
                return []
            
            logger.info(f"Searching for albums: '{sanitized_query}' (limit: {limit}, offset: {offset})")
            
            @async_to_sync
            def _search():
                search_result = session.search(sanitized_query, models=[tidalapi.Album])
                albums = search_result.get('albums', [])
                
                # Apply offset and limit
                start = offset
                end = offset + limit
                return albums[start:end] if albums else []
            
            tidal_albums = await _search()
            
            # Convert to our Album model
            albums = []
            for tidal_album in tidal_albums:
                try:
                    album = await self._convert_tidal_album(tidal_album)
                    if album:
                        albums.append(album)
                except Exception as e:
                    logger.warning(f"Failed to convert album {getattr(tidal_album, 'id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Found {len(albums)} albums for query '{sanitized_query}'")
            return albums
            
        except Exception as e:
            logger.error(f"Album search failed for '{query}': {e}")
            return []
    
    async def search_artists(self, query: str, limit: int = 20, offset: int = 0) -> List[Artist]:
        """
        Search for artists on Tidal.
        
        Args:
            query: Search query string
            limit: Maximum number of results (1-50)
            offset: Pagination offset
            
        Returns:
            List of Artist objects
        """
        try:
            await self.ensure_authenticated()
            session = self.get_session()
            
            sanitized_query = sanitize_query(query)
            if not sanitized_query:
                return []
            
            logger.info(f"Searching for artists: '{sanitized_query}' (limit: {limit}, offset: {offset})")
            
            @async_to_sync
            def _search():
                search_result = session.search(sanitized_query, models=[tidalapi.Artist])
                artists = search_result.get('artists', [])
                
                # Apply offset and limit
                start = offset
                end = offset + limit
                return artists[start:end] if artists else []
            
            tidal_artists = await _search()
            
            # Convert to our Artist model
            artists = []
            for tidal_artist in tidal_artists:
                try:
                    artist = await self._convert_tidal_artist(tidal_artist)
                    if artist:
                        artists.append(artist)
                except Exception as e:
                    logger.warning(f"Failed to convert artist {getattr(tidal_artist, 'id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Found {len(artists)} artists for query '{sanitized_query}'")
            return artists
            
        except Exception as e:
            logger.error(f"Artist search failed for '{query}': {e}")
            return []
    
    async def search_playlists(self, query: str, limit: int = 20, offset: int = 0) -> List[Playlist]:
        """
        Search for playlists on Tidal.
        
        Args:
            query: Search query string
            limit: Maximum number of results (1-50)
            offset: Pagination offset
            
        Returns:
            List of Playlist objects
        """
        try:
            await self.ensure_authenticated()
            session = self.get_session()
            
            sanitized_query = sanitize_query(query)
            if not sanitized_query:
                return []
            
            logger.info(f"Searching for playlists: '{sanitized_query}' (limit: {limit}, offset: {offset})")
            
            @async_to_sync
            def _search():
                search_result = session.search(sanitized_query, models=[tidalapi.Playlist])
                playlists = search_result.get('playlists', [])
                
                # Apply offset and limit
                start = offset
                end = offset + limit
                return playlists[start:end] if playlists else []
            
            tidal_playlists = await _search()
            
            # Convert to our Playlist model
            playlists = []
            for tidal_playlist in tidal_playlists:
                try:
                    playlist = await self._convert_tidal_playlist(tidal_playlist)
                    if playlist:
                        playlists.append(playlist)
                except Exception as e:
                    logger.warning(f"Failed to convert playlist {getattr(tidal_playlist, 'uuid', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Found {len(playlists)} playlists for query '{sanitized_query}'")
            return playlists
            
        except Exception as e:
            logger.error(f"Playlist search failed for '{query}': {e}")
            return []
    
    async def search_all(self, query: str, limit: int = 10) -> SearchResults:
        """
        Search across all content types.
        
        Args:
            query: Search query string
            limit: Maximum results per type
            
        Returns:
            SearchResults object with all content types
        """
        try:
            # Run all searches concurrently
            tasks = [
                self.search_tracks(query, limit=limit),
                self.search_albums(query, limit=limit),
                self.search_artists(query, limit=limit),
                self.search_playlists(query, limit=limit)
            ]
            
            tracks, albums, artists, playlists = await asyncio.gather(*tasks)
            
            return SearchResults(
                tracks=tracks,
                albums=albums,
                artists=artists,
                playlists=playlists
            )
            
        except Exception as e:
            logger.error(f"Global search failed for '{query}': {e}")
            return SearchResults()
    
    # Playlist management
    async def get_playlist(self, playlist_id: str, include_tracks: bool = True) -> Optional[Playlist]:
        """
        Get playlist details and optionally tracks.
        
        Args:
            playlist_id: Tidal playlist ID or UUID
            include_tracks: Whether to include track list
            
        Returns:
            Playlist object or None if not found
        """
        try:
            await self.ensure_authenticated()
            session = self.get_session()
            
            if not validate_tidal_id(playlist_id) and not self._is_uuid(playlist_id):
                logger.error(f"Invalid playlist ID format: {playlist_id}")
                return None
            
            logger.info(f"Fetching playlist: {playlist_id} (include_tracks: {include_tracks})")
            
            @async_to_sync
            def _get_playlist():
                return session.playlist(playlist_id)
            
            tidal_playlist = await _get_playlist()
            if not tidal_playlist:
                logger.warning(f"Playlist not found: {playlist_id}")
                return None
            
            playlist = await self._convert_tidal_playlist(tidal_playlist, include_tracks=include_tracks)
            logger.info(f"Retrieved playlist '{playlist.title}' with {len(playlist.tracks)} tracks")
            return playlist
            
        except Exception as e:
            logger.error(f"Failed to get playlist {playlist_id}: {e}")
            return None
    
    async def get_playlist_tracks(self, playlist_id: str, limit: int = 100, offset: int = 0) -> List[Track]:
        """
        Get tracks from a playlist.
        
        Args:
            playlist_id: Tidal playlist ID or UUID
            limit: Maximum number of tracks (1-100)
            offset: Pagination offset
            
        Returns:
            List of Track objects
        """
        try:
            await self.ensure_authenticated()
            session = self.get_session()
            
            if not validate_tidal_id(playlist_id) and not self._is_uuid(playlist_id):
                logger.error(f"Invalid playlist ID format: {playlist_id}")
                return []
            
            logger.info(f"Fetching tracks from playlist: {playlist_id} (limit: {limit}, offset: {offset})")
            
            @async_to_sync
            def _get_tracks():
                playlist = session.playlist(playlist_id)
                if not playlist:
                    return []
                
                tracks = playlist.tracks()
                # Apply offset and limit
                start = offset
                end = offset + limit
                return tracks[start:end] if tracks else []
            
            tidal_tracks = await _get_tracks()
            
            # Convert to our Track model
            tracks = []
            for tidal_track in tidal_tracks:
                try:
                    track = await self._convert_tidal_track(tidal_track)
                    if track:
                        tracks.append(track)
                except Exception as e:
                    logger.warning(f"Failed to convert track {getattr(tidal_track, 'id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(tracks)} tracks from playlist {playlist_id}")
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to get playlist tracks {playlist_id}: {e}")
            return []
    
    async def create_playlist(self, title: str, description: str = "") -> Optional[Playlist]:
        """
        Create a new playlist.
        
        Args:
            title: Playlist title
            description: Playlist description
            
        Returns:
            Created Playlist object or None if failed
        """
        try:
            await self.ensure_authenticated()
            session = self.get_session()
            
            if not title.strip():
                logger.error("Playlist title cannot be empty")
                return None
            
            logger.info(f"Creating playlist: '{title}'")
            
            @async_to_sync
            def _create_playlist():
                return session.user.create_playlist(title, description)
            
            tidal_playlist = await _create_playlist()
            if not tidal_playlist:
                logger.error(f"Failed to create playlist '{title}'")
                return None
            
            playlist = await self._convert_tidal_playlist(tidal_playlist, include_tracks=False)
            logger.info(f"Created playlist '{title}' with ID {playlist.id}")
            return playlist
            
        except Exception as e:
            logger.error(f"Failed to create playlist '{title}': {e}")
            return None
    
    async def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> bool:
        """
        Add tracks to a playlist.
        
        Args:
            playlist_id: Target playlist ID or UUID
            track_ids: List of track IDs to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.ensure_authenticated()
            session = self.get_session()
            
            if not validate_tidal_id(playlist_id) and not self._is_uuid(playlist_id):
                logger.error(f"Invalid playlist ID format: {playlist_id}")
                return False
            
            if not track_ids:
                logger.error("No track IDs provided")
                return False
            
            # Validate track IDs
            valid_track_ids = [tid for tid in track_ids if validate_tidal_id(tid)]
            if not valid_track_ids:
                logger.error("No valid track IDs provided")
                return False
            
            logger.info(f"Adding {len(valid_track_ids)} tracks to playlist {playlist_id}")
            
            @async_to_sync
            def _add_tracks():
                playlist = session.playlist(playlist_id)
                if not playlist:
                    return False
                
                # Get track objects
                tracks = []
                for track_id in valid_track_ids:
                    try:
                        track = session.track(track_id)
                        if track:
                            tracks.append(track)
                    except Exception as e:
                        logger.warning(f"Failed to get track {track_id}: {e}")
                        continue
                
                if not tracks:
                    return False
                
                # Add tracks to playlist
                return playlist.add(tracks)
            
            success = await _add_tracks()
            if success:
                logger.info(f"Successfully added {len(valid_track_ids)} tracks to playlist {playlist_id}")
            else:
                logger.error(f"Failed to add tracks to playlist {playlist_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to add tracks to playlist {playlist_id}: {e}")
            return False
    
    async def remove_tracks_from_playlist(self, playlist_id: str, track_indices: List[int]) -> bool:
        """
        Remove tracks from a playlist by index.
        
        Args:
            playlist_id: Target playlist ID or UUID
            track_indices: List of track indices to remove (0-based)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.ensure_authenticated()
            session = self.get_session()
            
            if not validate_tidal_id(playlist_id) and not self._is_uuid(playlist_id):
                logger.error(f"Invalid playlist ID format: {playlist_id}")
                return False
            
            if not track_indices:
                logger.error("No track indices provided")
                return False
            
            logger.info(f"Removing tracks at indices {track_indices} from playlist {playlist_id}")
            
            @async_to_sync
            def _remove_tracks():
                playlist = session.playlist(playlist_id)
                if not playlist:
                    return False
                
                # Sort indices in reverse order to avoid index shifting issues
                sorted_indices = sorted(track_indices, reverse=True)
                
                # Remove tracks by index
                for index in sorted_indices:
                    try:
                        playlist.remove_by_index(index)
                    except Exception as e:
                        logger.warning(f"Failed to remove track at index {index}: {e}")
                        continue
                
                return True
            
            success = await _remove_tracks()
            if success:
                logger.info(f"Successfully removed tracks from playlist {playlist_id}")
            else:
                logger.error(f"Failed to remove tracks from playlist {playlist_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to remove tracks from playlist {playlist_id}: {e}")
            return False
    
    async def delete_playlist(self, playlist_id: str) -> bool:
        """
        Delete a playlist.
        
        Args:
            playlist_id: Playlist ID or UUID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.ensure_authenticated()
            session = self.get_session()
            
            if not validate_tidal_id(playlist_id) and not self._is_uuid(playlist_id):
                logger.error(f"Invalid playlist ID format: {playlist_id}")
                return False
            
            logger.info(f"Deleting playlist: {playlist_id}")
            
            @async_to_sync
            def _delete_playlist():
                playlist = session.playlist(playlist_id)
                if not playlist:
                    return False
                
                return playlist.delete()
            
            success = await _delete_playlist()
            if success:
                logger.info(f"Successfully deleted playlist {playlist_id}")
            else:
                logger.error(f"Failed to delete playlist {playlist_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete playlist {playlist_id}: {e}")
            return False
    
    async def get_user_playlists(self, limit: int = 50, offset: int = 0) -> List[Playlist]:
        """
        Get user's playlists.
        
        Args:
            limit: Maximum number of playlists (1-50)
            offset: Pagination offset
            
        Returns:
            List of Playlist objects
        """
        try:
            await self.ensure_authenticated()
            session = self.get_session()
            
            logger.info(f"Fetching user playlists (limit: {limit}, offset: {offset})")
            
            @async_to_sync
            def _get_playlists():
                playlists = session.user.playlists()
                # Apply offset and limit
                start = offset
                end = offset + limit
                return playlists[start:end] if playlists else []
            
            tidal_playlists = await _get_playlists()
            
            # Convert to our Playlist model
            playlists = []
            for tidal_playlist in tidal_playlists:
                try:
                    playlist = await self._convert_tidal_playlist(tidal_playlist, include_tracks=False)
                    if playlist:
                        playlists.append(playlist)
                except Exception as e:
                    logger.warning(f"Failed to convert playlist {getattr(tidal_playlist, 'uuid', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(playlists)} user playlists")
            return playlists
            
        except Exception as e:
            logger.error(f"Failed to get user playlists: {e}")
            return []
    
    # Library/Favorites management
    async def get_user_favorites(self, content_type: str = "tracks", limit: int = 50, offset: int = 0) -> List[Any]:
        """
        Get user's favorite tracks, albums, or artists.
        
        Args:
            content_type: Type of content ("tracks", "albums", "artists", "playlists")
            limit: Maximum number of items (1-50)
            offset: Pagination offset
            
        Returns:
            List of favorite items
        """
        try:
            await self.ensure_authenticated()
            session = self.get_session()
            
            logger.info(f"Fetching user favorites: {content_type} (limit: {limit}, offset: {offset})")
            
            @async_to_sync
            def _get_favorites():
                user = session.user
                if content_type == "tracks":
                    items = user.favorites.tracks()
                elif content_type == "albums":
                    items = user.favorites.albums()
                elif content_type == "artists":
                    items = user.favorites.artists()
                elif content_type == "playlists":
                    items = user.favorites.playlists()
                else:
                    return []
                
                # Apply offset and limit
                start = offset
                end = offset + limit
                return items[start:end] if items else []
            
            tidal_items = await _get_favorites()
            
            # Convert to appropriate model
            items = []
            for tidal_item in tidal_items:
                try:
                    if content_type == "tracks":
                        item = await self._convert_tidal_track(tidal_item)
                    elif content_type == "albums":
                        item = await self._convert_tidal_album(tidal_item)
                    elif content_type == "artists":
                        item = await self._convert_tidal_artist(tidal_item)
                    elif content_type == "playlists":
                        item = await self._convert_tidal_playlist(tidal_item, include_tracks=False)
                    else:
                        continue
                    
                    if item:
                        items.append(item)
                except Exception as e:
                    logger.warning(f"Failed to convert {content_type} item: {e}")
                    continue
            
            logger.info(f"Retrieved {len(items)} favorite {content_type}")
            return items
            
        except Exception as e:
            logger.error(f"Failed to get user favorites ({content_type}): {e}")
            return []
    
    async def add_to_favorites(self, item_id: str, content_type: str) -> bool:
        """
        Add item to user favorites.
        
        Args:
            item_id: ID of item to add
            content_type: Type of content ("track", "album", "artist", "playlist")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.ensure_authenticated()
            session = self.get_session()
            
            if not validate_tidal_id(item_id) and not (content_type == "playlist" and self._is_uuid(item_id)):
                logger.error(f"Invalid {content_type} ID format: {item_id}")
                return False
            
            logger.info(f"Adding {content_type} {item_id} to favorites")
            
            @async_to_sync
            def _add_to_favorites():
                user = session.user
                
                if content_type == "track":
                    track = session.track(item_id)
                    return user.favorites.add_track(track) if track else False
                elif content_type == "album":
                    album = session.album(item_id)
                    return user.favorites.add_album(album) if album else False
                elif content_type == "artist":
                    artist = session.artist(item_id)
                    return user.favorites.add_artist(artist) if artist else False
                elif content_type == "playlist":
                    playlist = session.playlist(item_id)
                    return user.favorites.add_playlist(playlist) if playlist else False
                else:
                    return False
            
            success = await _add_to_favorites()
            if success:
                logger.info(f"Successfully added {content_type} {item_id} to favorites")
            else:
                logger.error(f"Failed to add {content_type} {item_id} to favorites")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to add {content_type} {item_id} to favorites: {e}")
            return False
    
    async def remove_from_favorites(self, item_id: str, content_type: str) -> bool:
        """
        Remove item from user favorites.
        
        Args:
            item_id: ID of item to remove
            content_type: Type of content ("track", "album", "artist", "playlist")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.ensure_authenticated()
            session = self.get_session()
            
            if not validate_tidal_id(item_id) and not (content_type == "playlist" and self._is_uuid(item_id)):
                logger.error(f"Invalid {content_type} ID format: {item_id}")
                return False
            
            logger.info(f"Removing {content_type} {item_id} from favorites")
            
            @async_to_sync
            def _remove_from_favorites():
                user = session.user
                
                if content_type == "track":
                    track = session.track(item_id)
                    return user.favorites.remove_track(track) if track else False
                elif content_type == "album":
                    album = session.album(item_id)
                    return user.favorites.remove_album(album) if album else False
                elif content_type == "artist":
                    artist = session.artist(item_id)
                    return user.favorites.remove_artist(artist) if artist else False
                elif content_type == "playlist":
                    playlist = session.playlist(item_id)
                    return user.favorites.remove_playlist(playlist) if playlist else False
                else:
                    return False
            
            success = await _remove_from_favorites()
            if success:
                logger.info(f"Successfully removed {content_type} {item_id} from favorites")
            else:
                logger.error(f"Failed to remove {content_type} {item_id} from favorites")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to remove {content_type} {item_id} from favorites: {e}")
            return False
    
    # Recommendations and Radio
    async def get_track_radio(self, track_id: str, limit: int = 50) -> List[Track]:
        """
        Get radio tracks based on a seed track.
        
        Args:
            track_id: Seed track ID
            limit: Maximum number of tracks
            
        Returns:
            List of Track objects
        """
        try:
            await self.ensure_authenticated()
            session = self.get_session()
            
            if not validate_tidal_id(track_id):
                logger.error(f"Invalid track ID format: {track_id}")
                return []
            
            logger.info(f"Getting track radio for: {track_id} (limit: {limit})")
            
            @async_to_sync
            def _get_radio():
                track = session.track(track_id)
                if not track:
                    return []
                
                radio_tracks = track.get_track_radio()
                return radio_tracks[:limit] if radio_tracks else []
            
            tidal_tracks = await _get_radio()
            
            # Convert to our Track model
            tracks = []
            for tidal_track in tidal_tracks:
                try:
                    track = await self._convert_tidal_track(tidal_track)
                    if track:
                        tracks.append(track)
                except Exception as e:
                    logger.warning(f"Failed to convert radio track: {e}")
                    continue
            
            logger.info(f"Retrieved {len(tracks)} radio tracks")
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to get track radio for {track_id}: {e}")
            return []
    
    async def get_artist_radio(self, artist_id: str, limit: int = 50) -> List[Track]:
        """
        Get radio tracks based on an artist.
        
        Args:
            artist_id: Seed artist ID
            limit: Maximum number of tracks
            
        Returns:
            List of Track objects
        """
        try:
            await self.ensure_authenticated()
            session = self.get_session()
            
            if not validate_tidal_id(artist_id):
                logger.error(f"Invalid artist ID format: {artist_id}")
                return []
            
            logger.info(f"Getting artist radio for: {artist_id} (limit: {limit})")
            
            @async_to_sync
            def _get_radio():
                artist = session.artist(artist_id)
                if not artist:
                    return []
                
                radio_tracks = artist.get_radio()
                return radio_tracks[:limit] if radio_tracks else []
            
            tidal_tracks = await _get_radio()
            
            # Convert to our Track model
            tracks = []
            for tidal_track in tidal_tracks:
                try:
                    track = await self._convert_tidal_track(tidal_track)
                    if track:
                        tracks.append(track)
                except Exception as e:
                    logger.warning(f"Failed to convert radio track: {e}")
                    continue
            
            logger.info(f"Retrieved {len(tracks)} artist radio tracks")
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to get artist radio for {artist_id}: {e}")
            return []
    
    async def get_recommended_tracks(self, limit: int = 50) -> List[Track]:
        """
        Get personalized recommended tracks.
        
        Args:
            limit: Maximum number of tracks
            
        Returns:
            List of Track objects
        """
        try:
            await self.ensure_authenticated()
            session = self.get_session()
            
            logger.info(f"Getting recommended tracks (limit: {limit})")
            
            @async_to_sync
            def _get_recommendations():
                # Try to get personalized recommendations
                try:
                    tracks = session.user.favorites.tracks()
                    if tracks:
                        # Get radio from a random favorite track
                        import random
                        seed_track = random.choice(tracks[:10])  # Use one of top 10 favorites
                        return seed_track.get_track_radio()[:limit]
                except Exception:
                    pass
                
                # Fallback to featured tracks or charts
                try:
                    featured = session.featured()
                    if featured and hasattr(featured, 'tracks') and featured.tracks:
                        return featured.tracks[:limit]
                except Exception:
                    pass
                
                return []
            
            tidal_tracks = await _get_recommendations()
            
            # Convert to our Track model
            tracks = []
            for tidal_track in tidal_tracks:
                try:
                    track = await self._convert_tidal_track(tidal_track)
                    if track:
                        tracks.append(track)
                except Exception as e:
                    logger.warning(f"Failed to convert recommended track: {e}")
                    continue
            
            logger.info(f"Retrieved {len(tracks)} recommended tracks")
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to get recommended tracks: {e}")
            return []
    
    # Detailed item retrieval
    async def get_track(self, track_id: str) -> Optional[Track]:
        """
        Get detailed track information.
        
        Args:
            track_id: Tidal track ID
            
        Returns:
            Track object or None if not found
        """
        try:
            await self.ensure_authenticated()
            session = self.get_session()
            
            if not validate_tidal_id(track_id):
                logger.error(f"Invalid track ID format: {track_id}")
                return None
            
            logger.info(f"Fetching track: {track_id}")
            
            @async_to_sync
            def _get_track():
                return session.track(track_id)
            
            tidal_track = await _get_track()
            if not tidal_track:
                logger.warning(f"Track not found: {track_id}")
                return None
            
            track = await self._convert_tidal_track(tidal_track)
            logger.info(f"Retrieved track '{track.title}' by {track.artist_names}")
            return track
            
        except Exception as e:
            logger.error(f"Failed to get track {track_id}: {e}")
            return None
    
    async def get_album(self, album_id: str, include_tracks: bool = True) -> Optional[Album]:
        """
        Get detailed album information.
        
        Args:
            album_id: Tidal album ID
            include_tracks: Whether to include track list
            
        Returns:
            Album object or None if not found
        """
        try:
            await self.ensure_authenticated()
            session = self.get_session()
            
            if not validate_tidal_id(album_id):
                logger.error(f"Invalid album ID format: {album_id}")
                return None
            
            logger.info(f"Fetching album: {album_id} (include_tracks: {include_tracks})")
            
            @async_to_sync
            def _get_album():
                return session.album(album_id)
            
            tidal_album = await _get_album()
            if not tidal_album:
                logger.warning(f"Album not found: {album_id}")
                return None
            
            album = await self._convert_tidal_album(tidal_album, include_tracks=include_tracks)
            logger.info(f"Retrieved album '{album.title}' with {len(album.artists)} artists")
            return album
            
        except Exception as e:
            logger.error(f"Failed to get album {album_id}: {e}")
            return None
    
    async def get_artist(self, artist_id: str) -> Optional[Artist]:
        """
        Get detailed artist information.
        
        Args:
            artist_id: Tidal artist ID
            
        Returns:
            Artist object or None if not found
        """
        try:
            await self.ensure_authenticated()
            session = self.get_session()
            
            if not validate_tidal_id(artist_id):
                logger.error(f"Invalid artist ID format: {artist_id}")
                return None
            
            logger.info(f"Fetching artist: {artist_id}")
            
            @async_to_sync
            def _get_artist():
                return session.artist(artist_id)
            
            tidal_artist = await _get_artist()
            if not tidal_artist:
                logger.warning(f"Artist not found: {artist_id}")
                return None
            
            artist = await self._convert_tidal_artist(tidal_artist)
            logger.info(f"Retrieved artist '{artist.name}'")
            return artist
            
        except Exception as e:
            logger.error(f"Failed to get artist {artist_id}: {e}")
            return None
    
    async def get_album_tracks(self, album_id: str, limit: int = 100, offset: int = 0) -> List[Track]:
        """
        Get tracks from an album.
        
        Args:
            album_id: Tidal album ID
            limit: Maximum number of tracks
            offset: Pagination offset
            
        Returns:
            List of Track objects
        """
        try:
            await self.ensure_authenticated()
            session = self.get_session()
            
            if not validate_tidal_id(album_id):
                logger.error(f"Invalid album ID format: {album_id}")
                return []
            
            logger.info(f"Fetching tracks from album: {album_id} (limit: {limit}, offset: {offset})")
            
            @async_to_sync
            def _get_tracks():
                album = session.album(album_id)
                if not album:
                    return []
                
                tracks = album.tracks()
                # Apply offset and limit
                start = offset
                end = offset + limit
                return tracks[start:end] if tracks else []
            
            tidal_tracks = await _get_tracks()
            
            # Convert to our Track model
            tracks = []
            for tidal_track in tidal_tracks:
                try:
                    track = await self._convert_tidal_track(tidal_track)
                    if track:
                        tracks.append(track)
                except Exception as e:
                    logger.warning(f"Failed to convert track {getattr(tidal_track, 'id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(tracks)} tracks from album {album_id}")
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to get album tracks {album_id}: {e}")
            return []
    
    async def get_artist_albums(self, artist_id: str, limit: int = 50, offset: int = 0) -> List[Album]:
        """
        Get albums by an artist.
        
        Args:
            artist_id: Tidal artist ID
            limit: Maximum number of albums
            offset: Pagination offset
            
        Returns:
            List of Album objects
        """
        try:
            await self.ensure_authenticated()
            session = self.get_session()
            
            if not validate_tidal_id(artist_id):
                logger.error(f"Invalid artist ID format: {artist_id}")
                return []
            
            logger.info(f"Fetching albums by artist: {artist_id} (limit: {limit}, offset: {offset})")
            
            @async_to_sync
            def _get_albums():
                artist = session.artist(artist_id)
                if not artist:
                    return []
                
                albums = artist.get_albums()
                # Apply offset and limit
                start = offset
                end = offset + limit
                return albums[start:end] if albums else []
            
            tidal_albums = await _get_albums()
            
            # Convert to our Album model
            albums = []
            for tidal_album in tidal_albums:
                try:
                    album = await self._convert_tidal_album(tidal_album, include_tracks=False)
                    if album:
                        albums.append(album)
                except Exception as e:
                    logger.warning(f"Failed to convert album {getattr(tidal_album, 'id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(albums)} albums by artist {artist_id}")
            return albums
            
        except Exception as e:
            logger.error(f"Failed to get artist albums {artist_id}: {e}")
            return []
    
    async def get_artist_top_tracks(self, artist_id: str, limit: int = 20) -> List[Track]:
        """
        Get top tracks by an artist.
        
        Args:
            artist_id: Tidal artist ID
            limit: Maximum number of tracks
            
        Returns:
            List of Track objects
        """
        try:
            await self.ensure_authenticated()
            session = self.get_session()
            
            if not validate_tidal_id(artist_id):
                logger.error(f"Invalid artist ID format: {artist_id}")
                return []
            
            logger.info(f"Fetching top tracks by artist: {artist_id} (limit: {limit})")
            
            @async_to_sync
            def _get_top_tracks():
                artist = session.artist(artist_id)
                if not artist:
                    return []
                
                tracks = artist.get_top_tracks()
                return tracks[:limit] if tracks else []
            
            tidal_tracks = await _get_top_tracks()
            
            # Convert to our Track model
            tracks = []
            for tidal_track in tidal_tracks:
                try:
                    track = await self._convert_tidal_track(tidal_track)
                    if track:
                        tracks.append(track)
                except Exception as e:
                    logger.warning(f"Failed to convert track {getattr(tidal_track, 'id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(tracks)} top tracks by artist {artist_id}")
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to get artist top tracks {artist_id}: {e}")
            return []
    
    # User profile operations
    async def get_user_profile(self) -> Optional[Dict[str, Any]]:
        """
        Get current user profile information.
        
        Returns:
            User profile dictionary or None if not available
        """
        try:
            await self.ensure_authenticated()
            
            user_info = self.auth.get_user_info()
            if user_info:
                logger.info(f"Retrieved user profile for user {user_info.get('id')}")
            
            return user_info
            
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return None
    
    # Helper methods for conversion
    async def _convert_tidal_track(self, tidal_track) -> Optional[Track]:
        """Convert tidalapi Track to our Track model."""
        try:
            # Get artists
            artists = []
            if hasattr(tidal_track, 'artists') and tidal_track.artists:
                for artist in tidal_track.artists:
                    artists.append(Artist(
                        id=str(artist.id),
                        name=artist.name,
                        picture=getattr(artist, 'picture', None),
                        popularity=getattr(artist, 'popularity', None)
                    ))
            elif hasattr(tidal_track, 'artist') and tidal_track.artist:
                artists.append(Artist(
                    id=str(tidal_track.artist.id),
                    name=tidal_track.artist.name,
                    picture=getattr(tidal_track.artist, 'picture', None),
                    popularity=getattr(tidal_track.artist, 'popularity', None)
                ))
            
            # Get album info
            album = None
            if hasattr(tidal_track, 'album') and tidal_track.album:
                album_artists = []
                if hasattr(tidal_track.album, 'artists') and tidal_track.album.artists:
                    for artist in tidal_track.album.artists:
                        album_artists.append(Artist(
                            id=str(artist.id),
                            name=artist.name,
                            picture=getattr(artist, 'picture', None),
                            popularity=getattr(artist, 'popularity', None)
                        ))
                elif hasattr(tidal_track.album, 'artist') and tidal_track.album.artist:
                    album_artists.append(Artist(
                        id=str(tidal_track.album.artist.id),
                        name=tidal_track.album.artist.name,
                        picture=getattr(tidal_track.album.artist, 'picture', None),
                        popularity=getattr(tidal_track.album.artist, 'popularity', None)
                    ))
                
                album = Album(
                    id=str(tidal_track.album.id),
                    title=tidal_track.album.name,
                    artists=album_artists,
                    release_date=getattr(tidal_track.album, 'release_date', None),
                    duration=getattr(tidal_track.album, 'duration', None),
                    number_of_tracks=getattr(tidal_track.album, 'num_tracks', None),
                    cover=getattr(tidal_track.album, 'image', None),
                    explicit=getattr(tidal_track.album, 'explicit', False)
                )
            
            return Track(
                id=str(tidal_track.id),
                title=tidal_track.name,
                artists=artists,
                album=album,
                duration=getattr(tidal_track, 'duration', None),
                track_number=getattr(tidal_track, 'track_num', None),
                disc_number=getattr(tidal_track, 'volume_num', None),
                explicit=getattr(tidal_track, 'explicit', False),
                quality=getattr(tidal_track, 'audio_quality', None)
            )
            
        except Exception as e:
            logger.error(f"Failed to convert tidal track: {e}")
            return None
    
    async def _convert_tidal_album(self, tidal_album, include_tracks: bool = False) -> Optional[Album]:
        """Convert tidalapi Album to our Album model."""
        try:
            # Get artists
            artists = []
            if hasattr(tidal_album, 'artists') and tidal_album.artists:
                for artist in tidal_album.artists:
                    artists.append(Artist(
                        id=str(artist.id),
                        name=artist.name,
                        picture=getattr(artist, 'picture', None),
                        popularity=getattr(artist, 'popularity', None)
                    ))
            elif hasattr(tidal_album, 'artist') and tidal_album.artist:
                artists.append(Artist(
                    id=str(tidal_album.artist.id),
                    name=tidal_album.artist.name,
                    picture=getattr(tidal_album.artist, 'picture', None),
                    popularity=getattr(tidal_album.artist, 'popularity', None)
                ))
            
            return Album(
                id=str(tidal_album.id),
                title=tidal_album.name,
                artists=artists,
                release_date=getattr(tidal_album, 'release_date', None),
                duration=getattr(tidal_album, 'duration', None),
                number_of_tracks=getattr(tidal_album, 'num_tracks', None),
                cover=getattr(tidal_album, 'image', None),
                explicit=getattr(tidal_album, 'explicit', False)
            )
            
        except Exception as e:
            logger.error(f"Failed to convert tidal album: {e}")
            return None
    
    async def _convert_tidal_artist(self, tidal_artist) -> Optional[Artist]:
        """Convert tidalapi Artist to our Artist model."""
        try:
            return Artist(
                id=str(tidal_artist.id),
                name=tidal_artist.name,
                picture=getattr(tidal_artist, 'picture', None),
                popularity=getattr(tidal_artist, 'popularity', None)
            )
            
        except Exception as e:
            logger.error(f"Failed to convert tidal artist: {e}")
            return None
    
    async def _convert_tidal_playlist(self, tidal_playlist, include_tracks: bool = True) -> Optional[Playlist]:
        """Convert tidalapi Playlist to our Playlist model."""
        try:
            tracks = []
            if include_tracks and hasattr(tidal_playlist, 'tracks'):
                try:
                    @async_to_sync
                    def _get_tracks():
                        return tidal_playlist.tracks()
                    
                    tidal_tracks = await _get_tracks()
                    for tidal_track in tidal_tracks:
                        track = await self._convert_tidal_track(tidal_track)
                        if track:
                            tracks.append(track)
                except Exception as e:
                    logger.warning(f"Failed to get playlist tracks: {e}")
            
            return Playlist(
                id=str(getattr(tidal_playlist, 'uuid', getattr(tidal_playlist, 'id', ''))),
                title=tidal_playlist.name,
                description=getattr(tidal_playlist, 'description', None),
                creator=getattr(tidal_playlist, 'creator', {}).get('name') if hasattr(tidal_playlist, 'creator') else None,
                tracks=tracks,
                number_of_tracks=getattr(tidal_playlist, 'num_tracks', len(tracks)),
                duration=getattr(tidal_playlist, 'duration', None),
                created_at=getattr(tidal_playlist, 'created', None),
                updated_at=getattr(tidal_playlist, 'last_updated', None),
                image=getattr(tidal_playlist, 'image', None),
                public=getattr(tidal_playlist, 'public', True)
            )
            
        except Exception as e:
            logger.error(f"Failed to convert tidal playlist: {e}")
            return None
    
    def _is_uuid(self, value: str) -> bool:
        """Check if value is a valid UUID format."""
        import re
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        return bool(uuid_pattern.match(value))