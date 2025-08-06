"""
Tidal MCP Favorites and Recommendations Examples

This script demonstrates advanced favorites tracking and recommendation retrieval.
"""

import asyncio
import logging
from tidal_mcp import (
    tidal_login,
    tidal_get_favorites,
    tidal_add_favorite,
    tidal_remove_favorite,
    tidal_get_recommendations,
    tidal_get_track_radio
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_favorites_example():
    """
    Demonstrate retrieving user's favorite content with pagination.
    """
    logger.info("=== Retrieve Favorites Example ===")
    
    # Authenticate first
    await tidal_login()
    
    # Get favorite tracks
    favorite_tracks = await tidal_get_favorites(content_type="tracks", limit=10)
    logger.info(f"Favorite Tracks: {favorite_tracks.get('total_results')} tracks")
    
    # Get favorite albums
    favorite_albums = await tidal_get_favorites(content_type="albums", limit=5)
    logger.info(f"Favorite Albums: {favorite_albums.get('total_results')} albums")
    
    # Get favorite artists
    favorite_artists = await tidal_get_favorites(content_type="artists", limit=3)
    logger.info(f"Favorite Artists: {favorite_artists.get('total_results')} artists")

async def manage_favorites_example():
    """
    Demonstrate adding and removing items from favorites.
    """
    logger.info("=== Manage Favorites Example ===")
    
    # Authenticate first
    await tidal_login()
    
    # Example track ID to add to favorites
    track_id = "123456"  # Replace with a real Tidal track ID
    
    # Add track to favorites
    add_result = await tidal_add_favorite(item_id=track_id, content_type="track")
    logger.info(f"Add to Favorites Result: {add_result}")
    
    # Remove track from favorites
    remove_result = await tidal_remove_favorite(item_id=track_id, content_type="track")
    logger.info(f"Remove from Favorites Result: {remove_result}")

async def get_recommendations_example():
    """
    Demonstrate retrieving personalized music recommendations.
    """
    logger.info("=== Recommendations Example ===")
    
    # Authenticate first
    await tidal_login()
    
    # Get personalized recommendations
    recommendations = await tidal_get_recommendations(limit=20)
    logger.info(f"Recommendations: {recommendations.get('total_results')} tracks")
    
    # Display recommendation details
    for track in recommendations.get('recommendations', [])[:5]:
        logger.info(f"  - {track.get('title')} by {track.get('artist_names')}")

async def track_radio_example():
    """
    Demonstrate generating a radio station based on a seed track.
    """
    logger.info("=== Track Radio Example ===")
    
    # Authenticate first
    await tidal_login()
    
    # Example track ID to generate radio from
    track_id = "789012"  # Replace with a real Tidal track ID
    
    # Generate track radio
    radio_tracks = await tidal_get_track_radio(track_id=track_id, limit=15)
    logger.info(f"Track Radio: {radio_tracks.get('total_results')} tracks")
    
    # Display track radio details
    for track in radio_tracks.get('radio_tracks', [])[:5]:
        logger.info(f"  - {track.get('title')} by {track.get('artist_names')}")

async def main():
    """
    Run all favorites and recommendations examples sequentially.
    """
    await get_favorites_example()
    await manage_favorites_example()
    await get_recommendations_example()
    await track_radio_example()

if __name__ == "__main__":
    asyncio.run(main())