"""
Tidal MCP Search Functionality Examples

This script demonstrates advanced search capabilities using Tidal MCP.
"""

import asyncio
import logging

from tidal_mcp import tidal_login, tidal_search

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def search_tracks_example():
    """
    Demonstrate track search with various parameters.
    Shows how to search, filter, and paginate results.
    """
    logger.info("=== Track Search Example ===")

    # Authenticate first
    await tidal_login()

    # Basic track search
    basic_results = await tidal_search(
        query="Daft Punk", content_type="tracks", limit=5
    )
    logger.info(
        f"Basic Search Results: {len(basic_results.get('results', {}).get('tracks', []))} tracks"
    )

    # Paginated search
    paginated_results = await tidal_search(
        query="Daft Punk", content_type="tracks", limit=3, offset=5
    )
    logger.info(
        f"Paginated Search Results: {len(paginated_results.get('results', {}).get('tracks', []))} tracks"
    )


async def search_albums_example():
    """
    Demonstrate album search capabilities with comprehensive filtering.
    """
    logger.info("=== Album Search Example ===")

    # Authenticate first
    await tidal_login()

    # Search for albums by genre or artist
    album_results = await tidal_search(
        query="Electronic", content_type="albums", limit=10
    )
    logger.info(
        f"Album Search Results: {len(album_results.get('results', {}).get('albums', []))} albums"
    )


async def search_artists_example():
    """
    Demonstrate advanced artist search techniques.
    """
    logger.info("=== Artist Search Example ===")

    # Authenticate first
    await tidal_login()

    # Global artist search
    artist_results = await tidal_search(
        query="French House", content_type="artists", limit=5
    )
    logger.info(
        f"Artist Search Results: {len(artist_results.get('results', {}).get('artists', []))} artists"
    )


async def comprehensive_search_example():
    """
    Perform a comprehensive search across all content types.
    """
    logger.info("=== Comprehensive Search Example ===")

    # Authenticate first
    await tidal_login()

    # Perform global search
    global_results = await tidal_search(query="Radiohead")

    # Display results by type
    results = global_results.get("results", {})
    for content_type, items in results.items():
        logger.info(f"{content_type.capitalize()} Results: {len(items)}")
        for item in items[:3]:  # Show first 3 items of each type
            logger.info(f"  - {item.get('title', item.get('name', 'Unknown'))}")


async def main():
    """
    Run all search examples sequentially.
    """
    await search_tracks_example()
    await search_albums_example()
    await search_artists_example()
    await comprehensive_search_example()


if __name__ == "__main__":
    asyncio.run(main())
