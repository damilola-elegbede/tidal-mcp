"""
Tidal MCP Playlist Management Examples

This script demonstrates comprehensive playlist management capabilities.
"""

import asyncio
import logging

from tidal_mcp import (
    tidal_add_to_playlist,
    tidal_create_playlist,
    tidal_get_user_playlists,
    tidal_login,
    tidal_remove_from_playlist,
    tidal_search,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_playlist_example():
    """
    Demonstrate playlist creation with various configurations.
    """
    logger.info("=== Playlist Creation Example ===")

    # Authenticate first
    await tidal_login()

    # Create playlists with different descriptions
    coding_playlist = await tidal_create_playlist(
        title="Coding Beats",
        description="High-energy electronic music for productive coding sessions",
    )

    workout_playlist = await tidal_create_playlist(
        title="Workout Motivation",
        description="Intense tracks to keep you moving and energized",
    )

    logger.info(f"Created Playlist: {coding_playlist.get('playlist', {}).get('title')}")
    logger.info(
        f"Created Playlist: {workout_playlist.get('playlist', {}).get('title')}"
    )


async def add_tracks_to_playlist_example():
    """
    Demonstrate adding tracks to a newly created playlist.
    """
    logger.info("=== Add Tracks to Playlist Example ===")

    # Authenticate first
    await tidal_login()

    # Create a new playlist
    playlist = await tidal_create_playlist("Morning Vibes")
    playlist_id = playlist.get("playlist", {}).get("id")

    if playlist_id:
        # Search for tracks to add
        track_search = await tidal_search(query="Tycho", content_type="tracks", limit=5)
        tracks = track_search.get("results", {}).get("tracks", [])

        if tracks:
            # Extract track IDs
            track_ids = [track["id"] for track in tracks[:3]]

            # Add tracks to playlist
            result = await tidal_add_to_playlist(
                playlist_id=playlist_id, track_ids=track_ids
            )
            logger.info(f"Added tracks to playlist: {result}")


async def remove_tracks_from_playlist_example():
    """
    Demonstrate removing tracks from a playlist by index.
    """
    logger.info("=== Remove Tracks from Playlist Example ===")

    # Authenticate first
    await tidal_login()

    # Get user's playlists
    user_playlists = await tidal_get_user_playlists(limit=1)
    playlists = user_playlists.get("playlists", [])

    if playlists:
        first_playlist_id = playlists[0]["id"]

        # Remove first two tracks from the playlist
        result = await tidal_remove_from_playlist(
            playlist_id=first_playlist_id, track_indices=[0, 1]
        )
        logger.info(f"Removed tracks from playlist: {result}")


async def list_user_playlists_example():
    """
    Demonstrate retrieving and displaying user's playlists.
    """
    logger.info("=== List User Playlists Example ===")

    # Authenticate first
    await tidal_login()

    # Retrieve user playlists with pagination
    page_1 = await tidal_get_user_playlists(limit=10, offset=0)
    page_2 = await tidal_get_user_playlists(limit=10, offset=10)

    logger.info("First Page of Playlists:")
    for playlist in page_1.get("playlists", []):
        logger.info(f"  - {playlist['title']} (ID: {playlist['id']})")

    logger.info("\nSecond Page of Playlists:")
    for playlist in page_2.get("playlists", []):
        logger.info(f"  - {playlist['title']} (ID: {playlist['id']})")


async def main():
    """
    Run all playlist management examples sequentially.
    """
    await create_playlist_example()
    await add_tracks_to_playlist_example()
    await remove_tracks_from_playlist_example()
    await list_user_playlists_example()


if __name__ == "__main__":
    asyncio.run(main())
