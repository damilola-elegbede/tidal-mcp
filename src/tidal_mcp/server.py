"""
Tidal MCP Server Implementation with FastMCP

This module contains the complete MCP server implementation for Tidal
integration using the FastMCP framework. It provides comprehensive tools
for music discovery, playlist management, and user library operations.
"""

import logging
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from .auth import TidalAuth, TidalAuthError
from .service import TidalService
# Models and utilities imported indirectly through service layer

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Tidal Music Integration")

# Global instances
auth_manager: Optional[TidalAuth] = None
tidal_service: Optional[TidalService] = None


async def ensure_service() -> TidalService:
    """Ensure Tidal service is initialized and authenticated."""
    global auth_manager, tidal_service

    if not auth_manager:
        # Check for custom client credentials in environment
        import os

        client_id = os.getenv("TIDAL_CLIENT_ID")
        client_secret = os.getenv("TIDAL_CLIENT_SECRET")
        auth_manager = TidalAuth(client_id=client_id, client_secret=client_secret)

    if not tidal_service:
        tidal_service = TidalService(auth_manager)

    # Ensure authentication
    if not auth_manager.is_authenticated():
        raise TidalAuthError("Not authenticated. Please run tidal_login first.")

    return tidal_service


@mcp.tool()
async def tidal_login() -> Dict[str, Any]:
    """
    Authenticate with Tidal using OAuth2 flow.

    This tool initiates the Tidal authentication process. It will open a
    browser
    window for you to log in with your Tidal credentials. The authentication
    tokens will be saved for future use.

    Returns:
        Authentication status and user information
    """
    global auth_manager, tidal_service

    try:
        auth_manager = TidalAuth()
        success = await auth_manager.authenticate()

        if success:
            tidal_service = TidalService(auth_manager)
            user_info = auth_manager.get_user_info()

            return {
                "success": True,
                "message": "Successfully authenticated with Tidal",
                "user": user_info,
            }
        else:
            return {
                "success": False,
                "message": "Authentication failed. Please try again.",
                "user": None,
            }

    except Exception as e:
        logger.error(f"Login failed: {e}")
        return {
            "success": False,
            "message": f"Authentication error: {str(e)}",
            "user": None,
        }


@mcp.tool()
async def tidal_search(
    query: str, content_type: str = "all", limit: int = 20, offset: int = 0
) -> Dict[str, Any]:
    """
    Search for content on Tidal.

    Args:
        query: Search query string (required)
        content_type: Type of content to search - "tracks", "albums",
            "artists", "playlists", or "all" (default: "all")
        limit: Maximum number of results per type (default: 20, max: 50)
        offset: Pagination offset (default: 0)

    Returns:
        Search results organized by content type
    """
    try:
        service = await ensure_service()
        limit = min(max(1, limit), 50)  # Clamp between 1 and 50
        offset = max(0, offset)

        if content_type == "tracks":
            tracks = await service.search_tracks(query, limit, offset)
            return {
                "query": query,
                "content_type": content_type,
                "results": {"tracks": [track.to_dict() for track in tracks]},
                "total_results": len(tracks),
            }

        elif content_type == "albums":
            albums = await service.search_albums(query, limit, offset)
            return {
                "query": query,
                "content_type": content_type,
                "results": {"albums": [album.to_dict() for album in albums]},
                "total_results": len(albums),
            }

        elif content_type == "artists":
            artists = await service.search_artists(query, limit, offset)
            return {
                "query": query,
                "content_type": content_type,
                "results": {"artists": [artist.to_dict() for artist in artists]},
                "total_results": len(artists),
            }

        elif content_type == "playlists":
            playlists = await service.search_playlists(query, limit, offset)
            return {
                "query": query,
                "content_type": content_type,
                "results": {
                    "playlists": [playlist.to_dict() for playlist in playlists]
                },
                "total_results": len(playlists),
            }

        else:  # "all" or any other value
            search_results = await service.search_all(query, limit)
            return {
                "query": query,
                "content_type": "all",
                "results": search_results.to_dict(),
                "total_results": search_results.total_results,
            }

    except TidalAuthError as e:
        return {"error": f"Authentication required: {str(e)}"}
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {"error": f"Search failed: {str(e)}"}


@mcp.tool()
async def tidal_get_playlist(
    playlist_id: str, include_tracks: bool = True
) -> Dict[str, Any]:
    """
    Get detailed information about a Tidal playlist.

    Args:
        playlist_id: Tidal playlist ID or UUID (required)
        include_tracks: Whether to include the full track list
            (default: True)

    Returns:
        Playlist details including tracks if requested
    """
    try:
        service = await ensure_service()
        playlist = await service.get_playlist(playlist_id, include_tracks)

        if playlist:
            return {"success": True, "playlist": playlist.to_dict()}
        else:
            return {"success": False, "error": f"Playlist not found: {playlist_id}"}

    except TidalAuthError as e:
        return {"error": f"Authentication required: {str(e)}"}
    except Exception as e:
        logger.error(f"Get playlist failed: {e}")
        return {"error": f"Failed to get playlist: {str(e)}"}


@mcp.tool()
async def tidal_create_playlist(title: str, description: str = "") -> Dict[str, Any]:
    """
    Create a new Tidal playlist.

    Args:
        title: Playlist title (required)
        description: Playlist description (optional)

    Returns:
        Created playlist information
    """
    try:
        service = await ensure_service()
        playlist = await service.create_playlist(title, description)

        if playlist:
            return {
                "success": True,
                "message": f"Created playlist '{title}'",
                "playlist": playlist.to_dict(),
            }
        else:
            return {"success": False, "error": f"Failed to create playlist '{title}'"}

    except TidalAuthError as e:
        return {"error": f"Authentication required: {str(e)}"}
    except Exception as e:
        logger.error(f"Create playlist failed: {e}")
        return {"error": f"Failed to create playlist: {str(e)}"}


@mcp.tool()
async def tidal_add_to_playlist(
    playlist_id: str, track_ids: List[str]
) -> Dict[str, Any]:
    """
    Add tracks to a Tidal playlist.

    Args:
        playlist_id: Target playlist ID or UUID (required)
        track_ids: List of track IDs to add (required)

    Returns:
        Operation result with success status
    """
    try:
        service = await ensure_service()

        if not track_ids:
            return {"success": False, "error": "No track IDs provided"}

        success = await service.add_tracks_to_playlist(playlist_id, track_ids)

        if success:
            return {
                "success": True,
                "message": (f"Added {len(track_ids)} tracks to playlist {playlist_id}"),
            }
        else:
            return {
                "success": False,
                "error": f"Failed to add tracks to playlist {playlist_id}",
            }

    except TidalAuthError as e:
        return {"error": f"Authentication required: {str(e)}"}
    except Exception as e:
        logger.error(f"Add to playlist failed: {e}")
        return {"error": f"Failed to add tracks to playlist: {str(e)}"}


@mcp.tool()
async def tidal_remove_from_playlist(
    playlist_id: str, track_indices: List[int]
) -> Dict[str, Any]:
    """
    Remove tracks from a Tidal playlist by their position.

    Args:
        playlist_id: Target playlist ID or UUID (required)
        track_indices: List of track indices to remove (0-based)
            (required)

    Returns:
        Operation result with success status
    """
    try:
        service = await ensure_service()

        if not track_indices:
            return {"success": False, "error": "No track indices provided"}

        success = await service.remove_tracks_from_playlist(playlist_id, track_indices)

        if success:
            return {
                "success": True,
                "message": (
                    f"Removed {len(track_indices)} tracks from playlist {playlist_id}"
                ),
            }
        else:
            return {
                "success": False,
                "error": f"Failed to remove tracks from playlist {playlist_id}",
            }

    except TidalAuthError as e:
        return {"error": f"Authentication required: {str(e)}"}
    except Exception as e:
        logger.error(f"Remove from playlist failed: {e}")
        return {"error": f"Failed to remove tracks from playlist: {str(e)}"}


@mcp.tool()
async def tidal_get_favorites(
    content_type: str = "tracks", limit: int = 50, offset: int = 0
) -> Dict[str, Any]:
    """
    Get user's favorite content from Tidal.

    Args:
        content_type: Type of favorites - "tracks", "albums",
            "artists", or "playlists" (default: "tracks")
        limit: Maximum number of results (default: 50, max: 100)
        offset: Pagination offset (default: 0)

    Returns:
        List of favorite items
    """
    try:
        service = await ensure_service()
        limit = min(max(1, limit), 100)  # Clamp between 1 and 100
        offset = max(0, offset)

        favorites = await service.get_user_favorites(content_type, limit, offset)

        # Convert to dictionaries
        favorites_dict = []
        for item in favorites:
            if hasattr(item, "to_dict"):
                favorites_dict.append(item.to_dict())
            else:
                favorites_dict.append(item)

        return {
            "content_type": content_type,
            "favorites": favorites_dict,
            "total_results": len(favorites_dict),
        }

    except TidalAuthError as e:
        return {"error": f"Authentication required: {str(e)}"}
    except Exception as e:
        logger.error(f"Get favorites failed: {e}")
        return {"error": f"Failed to get favorites: {str(e)}"}


@mcp.tool()
async def tidal_add_favorite(item_id: str, content_type: str) -> Dict[str, Any]:
    """
    Add an item to user's Tidal favorites.

    Args:
        item_id: ID of the item to add (required)
        content_type: Type of content - "track", "album",
            "artist", or "playlist" (required)

    Returns:
        Operation result with success status
    """
    try:
        service = await ensure_service()
        success = await service.add_to_favorites(item_id, content_type)

        if success:
            return {
                "success": True,
                "message": (f"Added {content_type} {item_id} to favorites"),
            }
        else:
            return {
                "success": False,
                "error": (f"Failed to add {content_type} {item_id} to favorites"),
            }

    except TidalAuthError as e:
        return {"error": f"Authentication required: {str(e)}"}
    except Exception as e:
        logger.error(f"Add favorite failed: {e}")
        return {"error": f"Failed to add to favorites: {str(e)}"}


@mcp.tool()
async def tidal_remove_favorite(item_id: str, content_type: str) -> Dict[str, Any]:
    """
    Remove an item from user's Tidal favorites.

    Args:
        item_id: ID of the item to remove (required)
        content_type: Type of content - "track", "album",
            "artist", or "playlist" (required)

    Returns:
        Operation result with success status
    """
    try:
        service = await ensure_service()
        success = await service.remove_from_favorites(item_id, content_type)

        if success:
            return {
                "success": True,
                "message": (f"Removed {content_type} {item_id} from favorites"),
            }
        else:
            return {
                "success": False,
                "error": (f"Failed to remove {content_type} {item_id} from favorites"),
            }

    except TidalAuthError as e:
        return {"error": f"Authentication required: {str(e)}"}
    except Exception as e:
        logger.error(f"Remove favorite failed: {e}")
        return {"error": f"Failed to remove from favorites: {str(e)}"}


@mcp.tool()
async def tidal_get_recommendations(limit: int = 50) -> Dict[str, Any]:
    """
    Get personalized track recommendations from Tidal.

    Args:
        limit: Maximum number of recommended tracks
            (default: 50, max: 100)

    Returns:
        List of recommended tracks
    """
    try:
        service = await ensure_service()
        limit = min(max(1, limit), 100)  # Clamp between 1 and 100

        tracks = await service.get_recommended_tracks(limit)

        return {
            "recommendations": [track.to_dict() for track in tracks],
            "total_results": len(tracks),
        }

    except TidalAuthError as e:
        return {"error": f"Authentication required: {str(e)}"}
    except Exception as e:
        logger.error(f"Get recommendations failed: {e}")
        return {"error": f"Failed to get recommendations: {str(e)}"}


@mcp.tool()
async def tidal_get_track_radio(track_id: str, limit: int = 50) -> Dict[str, Any]:
    """
    Get radio tracks based on a seed track.

    Args:
        track_id: Seed track ID for radio generation (required)
        limit: Maximum number of radio tracks
            (default: 50, max: 100)

    Returns:
        List of radio tracks similar to the seed track
    """
    try:
        service = await ensure_service()
        limit = min(max(1, limit), 100)  # Clamp between 1 and 100

        tracks = await service.get_track_radio(track_id, limit)

        return {
            "seed_track_id": track_id,
            "radio_tracks": [track.to_dict() for track in tracks],
            "total_results": len(tracks),
        }

    except TidalAuthError as e:
        return {"error": f"Authentication required: {str(e)}"}
    except Exception as e:
        logger.error(f"Get track radio failed: {e}")
        return {"error": f"Failed to get track radio: {str(e)}"}


@mcp.tool()
async def tidal_get_user_playlists(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """
    Get user's Tidal playlists.

    Args:
        limit: Maximum number of playlists (default: 50, max: 100)
        offset: Pagination offset (default: 0)

    Returns:
        List of user's playlists
    """
    try:
        service = await ensure_service()
        limit = min(max(1, limit), 100)  # Clamp between 1 and 100
        offset = max(0, offset)

        playlists = await service.get_user_playlists(limit, offset)

        return {
            "playlists": [playlist.to_dict() for playlist in playlists],
            "total_results": len(playlists),
        }

    except TidalAuthError as e:
        return {"error": f"Authentication required: {str(e)}"}
    except Exception as e:
        logger.error(f"Get user playlists failed: {e}")
        return {"error": f"Failed to get user playlists: {str(e)}"}


@mcp.tool()
async def tidal_get_track(track_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific track.

    Args:
        track_id: Tidal track ID (required)

    Returns:
        Detailed track information
    """
    try:
        service = await ensure_service()
        track = await service.get_track(track_id)

        if track:
            return {"success": True, "track": track.to_dict()}
        else:
            return {"success": False, "error": f"Track not found: {track_id}"}

    except TidalAuthError as e:
        return {"error": f"Authentication required: {str(e)}"}
    except Exception as e:
        logger.error(f"Get track failed: {e}")
        return {"error": f"Failed to get track: {str(e)}"}


@mcp.tool()
async def tidal_get_album(album_id: str, include_tracks: bool = True) -> Dict[str, Any]:
    """
    Get detailed information about a specific album.

    Args:
        album_id: Tidal album ID (required)
        include_tracks: Whether to include the track list
            (default: True)

    Returns:
        Detailed album information with optional track list
    """
    try:
        service = await ensure_service()
        album = await service.get_album(album_id, include_tracks)

        if album:
            return {"success": True, "album": album.to_dict()}
        else:
            return {"success": False, "error": f"Album not found: {album_id}"}

    except TidalAuthError as e:
        return {"error": f"Authentication required: {str(e)}"}
    except Exception as e:
        logger.error(f"Get album failed: {e}")
        return {"error": f"Failed to get album: {str(e)}"}


@mcp.tool()
async def tidal_get_artist(artist_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific artist.

    Args:
        artist_id: Tidal artist ID (required)

    Returns:
        Detailed artist information
    """
    try:
        service = await ensure_service()
        artist = await service.get_artist(artist_id)

        if artist:
            return {"success": True, "artist": artist.to_dict()}
        else:
            return {"success": False, "error": f"Artist not found: {artist_id}"}

    except TidalAuthError as e:
        return {"error": f"Authentication required: {str(e)}"}
    except Exception as e:
        logger.error(f"Get artist failed: {e}")
        return {"error": f"Failed to get artist: {str(e)}"}


def main():
    """Main entry point for the Tidal MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("Starting Tidal MCP Server with FastMCP")

    # Run the FastMCP server
    mcp.run()


if __name__ == "__main__":
    main()
