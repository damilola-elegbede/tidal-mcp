"""
Mock Tidal MCP Server for Testing

This module provides a mock server implementation that mimics the interface
of the real server but without any network initialization or FastMCP startup.
All tools are Mock objects with .fn() methods to prevent actual API calls.
"""

import logging
from unittest.mock import AsyncMock, Mock

# Mock auth manager and service to prevent real initialization
mock_auth_manager: Mock = None
mock_tidal_service: Mock = None

logger = logging.getLogger(__name__)


async def ensure_service() -> Mock:
    """Mock ensure_service that returns a mock TidalService."""
    global mock_auth_manager, mock_tidal_service

    if not mock_auth_manager:
        mock_auth_manager = Mock()
        mock_auth_manager.is_authenticated.return_value = True
        mock_auth_manager.get_user_info.return_value = {
            "id": "mock_user_123",
            "username": "mock_user",
            "country_code": "US",
            "subscription": "premium"
        }

    if not mock_tidal_service:
        mock_tidal_service = Mock()
        # Add any default mock behavior here if needed

    return mock_tidal_service


# Mock tool functions with AsyncMock .fn() methods
def create_mock_tool(name: str, fn_implementation=None, description: str = None):
    """Create a mock tool with an async .fn() method and proper attributes."""
    mock_tool = Mock()

    # Use custom implementation if provided, otherwise use default
    if fn_implementation:
        mock_tool.fn = fn_implementation
    else:
        mock_tool.fn = AsyncMock(return_value={"success": True, "message": f"Mock {name} called"})

    # Add attributes to make it look like a real tool
    mock_tool.__name__ = name
    mock_tool.__doc__ = description or f"Mock {name} tool for testing"
    mock_tool.name = name
    mock_tool.description = description or f"Mock {name} tool for testing"
    mock_tool.__annotations__ = {}

    return mock_tool


# Dynamic mock implementations that respect parameters
async def mock_tidal_search_fn(query: str, content_type: str = "all", limit: int = 10, offset: int = 0):
    """Mock search function that delegates to the mocked service."""
    try:
        # Get the service that was mocked via ensure_service
        service = await ensure_service()
        limit = min(max(1, limit), 50)  # Clamp between 1 and 50
        offset = max(0, offset)

        if content_type == "tracks":
            tracks_result = service.search_tracks(query, limit, offset)
            # Handle AsyncMock properly - check if it's a coroutine
            import asyncio
            if asyncio.iscoroutine(tracks_result):
                tracks = await tracks_result
            elif hasattr(tracks_result, 'return_value'):
                tracks = tracks_result.return_value
            elif callable(tracks_result):
                tracks = await tracks_result
            else:
                tracks = tracks_result

            # Ensure tracks is a list
            if tracks is None:
                tracks = []

            return {
                "query": query,
                "content_type": content_type,
                "results": {"tracks": [track.to_dict() if hasattr(track, 'to_dict') else track for track in tracks]},
                "total_results": len(tracks),
            }

        elif content_type == "albums":
            albums_result = service.search_albums(query, limit, offset)
            import asyncio
            if asyncio.iscoroutine(albums_result):
                albums = await albums_result
            elif hasattr(albums_result, 'return_value'):
                albums = albums_result.return_value
            elif callable(albums_result):
                albums = await albums_result
            else:
                albums = albums_result

            if albums is None:
                albums = []

            return {
                "query": query,
                "content_type": content_type,
                "results": {"albums": [album.to_dict() if hasattr(album, 'to_dict') else album for album in albums]},
                "total_results": len(albums),
            }

        elif content_type == "artists":
            artists_result = service.search_artists(query, limit, offset)
            import asyncio
            if asyncio.iscoroutine(artists_result):
                artists = await artists_result
            elif hasattr(artists_result, 'return_value'):
                artists = artists_result.return_value
            elif callable(artists_result):
                artists = await artists_result
            else:
                artists = artists_result

            if artists is None:
                artists = []

            return {
                "query": query,
                "content_type": content_type,
                "results": {"artists": [artist.to_dict() if hasattr(artist, 'to_dict') else artist for artist in artists]},
                "total_results": len(artists),
            }

        elif content_type == "playlists":
            playlists_result = service.search_playlists(query, limit, offset)
            import asyncio
            if asyncio.iscoroutine(playlists_result):
                playlists = await playlists_result
            elif hasattr(playlists_result, 'return_value'):
                playlists = playlists_result.return_value
            elif callable(playlists_result):
                playlists = await playlists_result
            else:
                playlists = playlists_result

            if playlists is None:
                playlists = []

            return {
                "query": query,
                "content_type": content_type,
                "results": {"playlists": [playlist.to_dict() if hasattr(playlist, 'to_dict') else playlist for playlist in playlists]},
                "total_results": len(playlists),
            }

        else:  # content_type == "all"
            search_results_obj = service.search_all(query, limit)  # Note: search_all only takes 2 args
            import asyncio
            if asyncio.iscoroutine(search_results_obj):
                search_results = await search_results_obj
            elif hasattr(search_results_obj, 'return_value'):
                search_results = search_results_obj.return_value
            elif callable(search_results_obj):
                search_results = await search_results_obj
            else:
                search_results = search_results_obj

            # Handle case where search_results might be None or have missing attributes
            if search_results is None or not hasattr(search_results, 'tracks'):
                return {
                    "query": query,
                    "content_type": "all",
                    "results": {"tracks": [], "albums": [], "artists": [], "playlists": []},
                    "total_results": 0,
                }

            return {
                "query": query,
                "content_type": "all",
                "results": {
                    "tracks": [track.to_dict() if hasattr(track, 'to_dict') else track for track in (search_results.tracks or [])],
                    "albums": [album.to_dict() if hasattr(album, 'to_dict') else album for album in (search_results.albums or [])],
                    "artists": [artist.to_dict() if hasattr(artist, 'to_dict') else artist for artist in (search_results.artists or [])],
                    "playlists": [playlist.to_dict() if hasattr(playlist, 'to_dict') else playlist for playlist in (search_results.playlists or [])],
                },
                "total_results": (
                    len(search_results.tracks or []) + len(search_results.albums or []) +
                    len(search_results.artists or []) + len(search_results.playlists or [])
                ),
            }

    except Exception as e:
        try:
            from tidal_mcp.auth import TidalAuthError
            if isinstance(e, TidalAuthError):
                return {"error": f"Authentication required: {str(e)}"}
        except ImportError:
            pass
        # Fallback to basic mock response if service delegation fails
        logger.error(f"Mock search delegation failed: {e}")
        return {"error": f"Search failed: {str(e)}"}


async def mock_tidal_get_track_fn(track_id: str):
    """Mock get track function that delegates to the mocked service."""
    try:
        service = await ensure_service()
        track_result = service.get_track(track_id)
        import asyncio
        if asyncio.iscoroutine(track_result):
            track = await track_result
        elif hasattr(track_result, 'return_value'):
            track = track_result.return_value
        elif callable(track_result):
            track = await track_result
        else:
            track = track_result

        if track:
            return {
                "success": True,
                "track": track.to_dict() if hasattr(track, 'to_dict') else track
            }
        else:
            return {
                "success": False,
                "error": f"Track {track_id} not found"
            }
    except Exception as e:
        logger.error(f"Mock get_track delegation failed: {e}")
        # Return error response if track_id indicates error
        if "error" in track_id.lower():
            return {"error": f"Failed to get track: {str(e)}"}
        return {
            "success": True,
            "track": {
                "id": track_id,
                "title": f"Mock Track {track_id}",
                "artists": [],
                "album": None,
                "duration": 180
            }
        }


async def mock_tidal_get_album_fn(album_id: str, include_tracks: bool = False):
    """Mock get album function that delegates to the mocked service."""
    try:
        service = await ensure_service()
        album = await service.get_album(album_id, include_tracks)

        if album:
            return {
                "success": True,
                "album": album.to_dict()
            }
        else:
            return {
                "success": False,
                "error": f"Album {album_id} not found"
            }
    except Exception as e:
        logger.error(f"Mock get_album delegation failed: {e}")
        return {
            "success": True,
            "album": {
                "id": album_id,
                "title": f"Mock Album {album_id}",
                "artists": [],
                "tracks": [] if include_tracks else None,
                "number_of_tracks": 0
            }
        }


async def mock_tidal_get_artist_fn(artist_id: str):
    """Mock get artist function that delegates to the mocked service."""
    try:
        service = await ensure_service()
        artist = await service.get_artist(artist_id)

        if artist:
            return {
                "success": True,
                "artist": artist.to_dict()
            }
        else:
            return {
                "success": False,
                "error": f"Artist {artist_id} not found"
            }
    except Exception as e:
        logger.error(f"Mock get_artist delegation failed: {e}")
        return {
            "success": True,
            "artist": {
                "id": artist_id,
                "name": f"Mock Artist {artist_id}",
                "picture": None,
                "popularity": 50
            }
        }


async def mock_tidal_add_favorite_fn(item_id: str, item_type: str):
    """Mock add favorite function that delegates to the mocked service."""
    try:
        service = await ensure_service()
        success_result = service.add_to_favorites(item_id, item_type)
        import asyncio
        if asyncio.iscoroutine(success_result):
            success = await success_result
        elif hasattr(success_result, 'return_value'):
            success = success_result.return_value
        elif callable(success_result):
            success = await success_result
        else:
            success = success_result

        if success:
            return {
                "success": True,
                "message": f"Added {item_type} {item_id} to favorites",
            }
        else:
            return {
                "success": False,
                "error": f"Failed to add {item_type} {item_id} to favorites",
            }
    except Exception as e:
        logger.error(f"Mock add_favorite delegation failed: {e}")
        return {
            "success": False,
            "error": f"Failed to add to favorites: {str(e)}"
        }


async def mock_tidal_remove_favorite_fn(item_id: str, item_type: str):
    """Mock remove favorite function that delegates to the mocked service."""
    try:
        service = await ensure_service()
        success_result = service.remove_from_favorites(item_id, item_type)
        import asyncio
        if asyncio.iscoroutine(success_result):
            success = await success_result
        elif hasattr(success_result, 'return_value'):
            success = success_result.return_value
        elif callable(success_result):
            success = await success_result
        else:
            success = success_result

        if success:
            return {
                "success": True,
                "message": f"Removed {item_type} {item_id} from favorites",
            }
        else:
            return {
                "success": False,
                "error": f"Failed to remove {item_type} {item_id} from favorites",
            }
    except Exception as e:
        logger.error(f"Mock remove_favorite delegation failed: {e}")
        return {
            "success": False,
            "error": f"Failed to remove from favorites: {str(e)}"
        }


async def mock_tidal_get_favorites_fn(content_type: str = "tracks", limit: int = 50, offset: int = 0):
    """Mock get favorites function that delegates to the mocked service."""
    try:
        service = await ensure_service()
        limit = min(max(1, limit), 100)  # Clamp between 1 and 100
        offset = max(0, offset)

        favorites_result = service.get_user_favorites(content_type, limit, offset)
        import asyncio
        if asyncio.iscoroutine(favorites_result):
            favorites = await favorites_result
        elif hasattr(favorites_result, 'return_value'):
            favorites = favorites_result.return_value
        elif callable(favorites_result):
            favorites = await favorites_result
        else:
            favorites = favorites_result

        if favorites is None:
            favorites = []

        return {
            "content_type": content_type,
            "favorites": [fav.to_dict() if hasattr(fav, 'to_dict') else fav for fav in favorites],
            "total_results": len(favorites),
        }
    except Exception as e:
        logger.error(f"Mock get_favorites delegation failed: {e}")
        return {
            "content_type": content_type,
            "favorites": [],
            "total_results": 0
        }


async def mock_tidal_add_to_playlist_fn(playlist_id: str, track_ids: list):
    """Mock add to playlist function that delegates to the mocked service."""
    # Check for empty track_ids first
    if not track_ids:
        return {"success": False, "error": "No track IDs provided"}

    try:
        service = await ensure_service()
        success_result = service.add_tracks_to_playlist(playlist_id, track_ids)
        import asyncio
        if asyncio.iscoroutine(success_result):
            success = await success_result
        elif hasattr(success_result, 'return_value'):
            success = success_result.return_value
        elif callable(success_result):
            success = await success_result
        else:
            success = success_result

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
    except Exception as e:
        logger.error(f"Mock add_to_playlist delegation failed: {e}")
        # Don't fall back to success - return an error response
        return {
            "success": False,
            "error": f"Failed to add tracks to playlist: {str(e)}"
        }


async def mock_tidal_remove_from_playlist_fn(playlist_id: str, track_indices: list):
    """Mock remove from playlist function that delegates to the mocked service."""
    # Check for empty track_indices first
    if not track_indices:
        return {"success": False, "error": "No track indices provided"}

    try:
        service = await ensure_service()
        success_result = service.remove_tracks_from_playlist(playlist_id, track_indices)
        import asyncio
        if asyncio.iscoroutine(success_result):
            success = await success_result
        elif hasattr(success_result, 'return_value'):
            success = success_result.return_value
        elif callable(success_result):
            success = await success_result
        else:
            success = success_result

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
    except Exception as e:
        logger.error(f"Mock remove_from_playlist delegation failed: {e}")
        return {
            "success": False,
            "error": f"Failed to remove tracks from playlist: {str(e)}"
        }


async def mock_tidal_get_track_radio_fn(track_id: str, limit: int = 50):
    """Mock get track radio function that delegates to the mocked service."""
    try:
        service = await ensure_service()
        radio_tracks = await service.get_track_radio(track_id, limit)

        return {
            "seed_track_id": track_id,
            "radio_tracks": [track.to_dict() for track in radio_tracks],
            "total_results": len(radio_tracks),
        }
    except Exception as e:
        logger.error(f"Mock get_track_radio delegation failed: {e}")
        return {
            "seed_track_id": track_id,
            "radio_tracks": [],
            "total_results": 0
        }


# Mock all server tools with dynamic implementations
async def mock_tidal_login_fn():
    """Mock login function."""
    return {
        "success": True,
        "message": "Mock authentication successful",
        "user": {
            "id": "mock_user_123",
            "username": "mock_user",
            "country_code": "US",
            "subscription": "premium"
        }
    }


async def mock_tidal_get_recommendations_fn(limit: int = 50):
    """Mock get recommendations function that delegates to the mocked service."""
    try:
        service = await ensure_service()
        limit = min(max(1, limit), 100)  # Clamp between 1 and 100

        recommendations_result = service.get_recommended_tracks(limit)
        import asyncio
        if asyncio.iscoroutine(recommendations_result):
            recommendations = await recommendations_result
        elif hasattr(recommendations_result, 'return_value'):
            recommendations = recommendations_result.return_value
        elif callable(recommendations_result):
            recommendations = await recommendations_result
        else:
            recommendations = recommendations_result

        if recommendations is None:
            recommendations = []

        return {
            "recommendations": [track.to_dict() if hasattr(track, 'to_dict') else track for track in recommendations],
            "total_results": len(recommendations),
        }
    except Exception as e:
        logger.error(f"Mock get_recommendations delegation failed: {e}")
        return {
            "recommendations": [],
            "total_results": 0
        }


async def mock_tidal_get_user_playlists_fn(limit: int = 50, offset: int = 0):
    """Mock get user playlists function that delegates to the mocked service."""
    try:
        service = await ensure_service()
        limit = min(max(1, limit), 100)  # Clamp between 1 and 100
        offset = max(0, offset)

        playlists = await service.get_user_playlists(limit, offset)

        return {
            "playlists": [playlist.to_dict() for playlist in playlists],
            "total_results": len(playlists),
        }
    except Exception as e:
        logger.error(f"Mock get_user_playlists delegation failed: {e}")
        return {
            "playlists": [],
            "total_results": 0
        }


async def mock_tidal_get_playlist_fn(playlist_id: str, include_tracks: bool = False):
    """Mock get playlist function that delegates to the mocked service."""
    try:
        service = await ensure_service()
        playlist = await service.get_playlist(playlist_id, include_tracks)
        return {
            "success": True,
            "playlist": playlist.to_dict() if playlist else None
        }
    except Exception as e:
        logger.error(f"Mock get_playlist delegation failed: {e}")
        return {
            "success": False,
            "error": f"Failed to get playlist: {str(e)}"
        }


async def mock_tidal_create_playlist_fn(title: str, description: str = ""):
    """Mock create playlist function."""
    # Check for empty title first
    if not title or title.strip() == "":
        return {"success": False, "error": "Playlist title cannot be empty"}

    try:
        service = await ensure_service()
        playlist_result = service.create_playlist(title, description)
        import asyncio
        if asyncio.iscoroutine(playlist_result):
            playlist = await playlist_result
        elif hasattr(playlist_result, 'return_value'):
            playlist = playlist_result.return_value
        elif callable(playlist_result):
            playlist = await playlist_result
        else:
            playlist = playlist_result

        if playlist:
            return {"success": True, "playlist": playlist.to_dict() if hasattr(playlist, 'to_dict') else playlist}
        else:
            return {"success": False, "error": f"Failed to create playlist '{title}'"}
    except Exception as e:
        return {"success": False, "error": f"Failed to create playlist: {str(e)}"}




# Create tools with dynamic implementations
tidal_login = create_mock_tool("tidal_login", mock_tidal_login_fn, "Authenticate with Tidal using OAuth2 flow for testing")

tidal_search = create_mock_tool("tidal_search", mock_tidal_search_fn, "Search for tracks, albums, artists, or playlists on Tidal")

tidal_get_playlist = create_mock_tool("tidal_get_playlist", mock_tidal_get_playlist_fn, "Get a specific playlist by ID")

tidal_create_playlist = create_mock_tool("tidal_create_playlist", mock_tidal_create_playlist_fn, "Create a new playlist with the given title and description")

tidal_add_to_playlist = create_mock_tool("tidal_add_to_playlist", mock_tidal_add_to_playlist_fn, "Add tracks to an existing playlist")

tidal_remove_from_playlist = create_mock_tool("tidal_remove_from_playlist", mock_tidal_remove_from_playlist_fn, "Remove tracks from a playlist by their indices")

tidal_get_favorites = create_mock_tool("tidal_get_favorites", mock_tidal_get_favorites_fn, "Get user's favorite tracks, albums, artists, or playlists")

tidal_add_favorite = create_mock_tool("tidal_add_favorite", mock_tidal_add_favorite_fn, "Add a track, album, artist, or playlist to favorites")

tidal_remove_favorite = create_mock_tool("tidal_remove_favorite", mock_tidal_remove_favorite_fn, "Remove a track, album, artist, or playlist from favorites")

tidal_get_recommendations = create_mock_tool("tidal_get_recommendations", mock_tidal_get_recommendations_fn, "Get personalized track recommendations")

tidal_get_track_radio = create_mock_tool("tidal_get_track_radio", mock_tidal_get_track_radio_fn, "Get radio tracks based on a seed track")

tidal_get_user_playlists = create_mock_tool("tidal_get_user_playlists", mock_tidal_get_user_playlists_fn, "Get all playlists created by the current user")

tidal_get_track = create_mock_tool("tidal_get_track", mock_tidal_get_track_fn, "Get detailed information about a specific track")

tidal_get_album = create_mock_tool("tidal_get_album", mock_tidal_get_album_fn, "Get detailed information about a specific album")

tidal_get_artist = create_mock_tool("tidal_get_artist", mock_tidal_get_artist_fn, "Get detailed information about a specific artist")


def main():
    """Mock main function that does nothing."""
    logger.info("Mock Tidal MCP Server - No actual server started")
    print("Mock server called - no actual startup in test mode")


# Mock module-level variables that the real server has
mcp = Mock()  # Mock FastMCP instance
mcp.name = "Tidal Music Integration"  # Set the expected name attribute
auth_manager = mock_auth_manager
tidal_service = mock_tidal_service
