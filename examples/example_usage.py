"""
Tidal MCP Server Usage Examples

Example scripts demonstrating how to use the Tidal MCP server
for various music streaming operations.
"""

import asyncio
import logging
from typing import List, Dict, Any

# TODO: Update imports when MCP dependencies are added
# from mcp import ClientSession, StdioServerParameters
# from mcp.client.stdio import stdio_client

from tidal_mcp.server import TidalMCPServer
from tidal_mcp.auth import TidalAuth
from tidal_mcp.service import TidalService
from tidal_mcp.models import Track, Album, Artist, Playlist

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_direct_api_usage():
    """
    Example of using the Tidal service directly (without MCP).
    This demonstrates the core functionality before MCP integration.
    """
    logger.info("=== Direct API Usage Example ===")
    
    # Initialize authentication
    auth = TidalAuth()
    
    # Note: In real usage, you would need valid Tidal API credentials
    # auth = TidalAuth(client_id="your_client_id", client_secret="your_secret")
    
    try:
        # Authenticate with Tidal
        logger.info("Authenticating with Tidal...")
        authenticated = await auth.authenticate()
        
        if not authenticated:
            logger.error("Authentication failed. Please check your credentials.")
            return
        
        logger.info("Authentication successful!")
        
        # Create service instance
        async with TidalService(auth) as service:
            
            # Search for tracks
            logger.info("Searching for tracks...")
            tracks = await service.search_tracks("Bohemian Rhapsody", limit=5)
            logger.info(f"Found {len(tracks)} tracks")
            
            for track in tracks[:3]:  # Show first 3 results
                logger.info(f"  - {track.title} by {track.artist_names} ({track.formatted_duration})")
            
            # Search for albums
            logger.info("Searching for albums...")
            albums = await service.search_albums("Dark Side of the Moon", limit=3)
            logger.info(f"Found {len(albums)} albums")
            
            for album in albums:
                artists = ", ".join(artist.name for artist in album.artists)
                logger.info(f"  - {album.title} by {artists} ({album.number_of_tracks} tracks)")
            
            # Search for artists
            logger.info("Searching for artists...")
            artists = await service.search_artists("Pink Floyd", limit=3)
            logger.info(f"Found {len(artists)} artists")
            
            for artist in artists:
                logger.info(f"  - {artist.name} (popularity: {artist.popularity})")
            
            # Get user favorites (if authenticated)
            logger.info("Getting user favorites...")
            favorite_tracks = await service.get_user_favorites("tracks", limit=5)
            logger.info(f"Found {len(favorite_tracks)} favorite tracks")
            
            # Create a new playlist
            logger.info("Creating a new playlist...")
            new_playlist = await service.create_playlist(
                "My MCP Test Playlist",
                "Created via Tidal MCP server example"
            )
            
            if new_playlist:
                logger.info(f"Created playlist: {new_playlist.title}")
                
                # Add tracks to the playlist
                if tracks:
                    track_ids = [track.id for track in tracks[:3]]
                    success = await service.add_tracks_to_playlist(new_playlist.id, track_ids)
                    if success:
                        logger.info(f"Added {len(track_ids)} tracks to playlist")
            
    except Exception as e:
        logger.error(f"Error in direct API usage: {e}")


async def example_mcp_server_usage():
    """
    Example of running the Tidal MCP server.
    This demonstrates the MCP server functionality.
    """
    logger.info("=== MCP Server Usage Example ===")
    
    try:
        # Create and configure MCP server
        server = TidalMCPServer()
        
        # Setup tools (this will register MCP tools)
        await server.setup_tools()
        logger.info("MCP tools registered successfully")
        
        # Example of calling server methods directly
        # In real usage, these would be called via MCP protocol
        
        # Search for tracks
        logger.info("Testing track search via server...")
        track_results = await server.handle_search_tracks("Imagine", limit=3)
        logger.info(f"Server returned {len(track_results)} track results")
        
        # Search for albums
        logger.info("Testing album search via server...")
        album_results = await server.handle_search_albums("Abbey Road", limit=2)
        logger.info(f"Server returned {len(album_results)} album results")
        
        # Get playlist
        logger.info("Testing playlist retrieval via server...")
        playlist_result = await server.handle_get_playlist("example_playlist_id")
        if playlist_result:
            logger.info(f"Retrieved playlist: {playlist_result}")
        else:
            logger.info("No playlist found (expected for example)")
        
        logger.info("MCP server methods tested successfully")
        
        # TODO: Start actual MCP server when MCP dependency is added
        # logger.info("Starting MCP server...")
        # await server.run()
        
    except Exception as e:
        logger.error(f"Error in MCP server usage: {e}")


async def example_mcp_client_usage():
    """
    Example of connecting to the Tidal MCP server as a client.
    This demonstrates how external applications would use the server.
    """
    logger.info("=== MCP Client Usage Example ===")
    
    # TODO: Implement when MCP dependencies are added
    # This will show how to connect to the server and call tools
    
    try:
        # Example client connection (pseudo-code)
        # server_params = StdioServerParameters(
        #     command="python",
        #     args=["-m", "tidal_mcp.server"]
        # )
        
        # async with stdio_client(server_params) as (read, write):
        #     async with ClientSession(read, write) as session:
        #         # List available tools
        #         tools = await session.list_tools()
        #         logger.info(f"Available tools: {[tool.name for tool in tools]}")
        #         
        #         # Call search_tracks tool
        #         result = await session.call_tool("search_tracks", {
        #             "query": "Hotel California",
        #             "limit": 5
        #         })
        #         logger.info(f"Search results: {result}")
        #         
        #         # Call get_playlist tool
        #         playlist = await session.call_tool("get_playlist", {
        #             "playlist_id": "example_id"
        #         })
        #         logger.info(f"Playlist: {playlist}")
        
        logger.info("MCP client example completed (placeholder)")
        
    except Exception as e:
        logger.error(f"Error in MCP client usage: {e}")


async def example_batch_operations():
    """
    Example of performing batch operations with the Tidal service.
    """
    logger.info("=== Batch Operations Example ===")
    
    auth = TidalAuth()
    
    try:
        # Mock authentication for example
        auth.access_token = "mock_token"
        
        async with TidalService(auth) as service:
            
            # Batch search for multiple queries
            search_queries = [
                "The Beatles",
                "Pink Floyd", 
                "Led Zeppelin",
                "Queen",
                "The Rolling Stones"
            ]
            
            logger.info("Performing batch artist searches...")
            batch_results = []
            
            for query in search_queries:
                logger.info(f"Searching for: {query}")
                artists = await service.search_artists(query, limit=1)
                batch_results.append({
                    'query': query,
                    'results': artists
                })
                
                # Add small delay to be respectful to API
                await asyncio.sleep(0.1)
            
            # Process batch results
            logger.info("Batch search results:")
            for result in batch_results:
                query = result['query']
                artists = result['results']
                if artists:
                    artist = artists[0]
                    logger.info(f"  {query}: Found {artist.name} (ID: {artist.id})")
                else:
                    logger.info(f"  {query}: No results found")
            
            logger.info("Batch operations completed")
            
    except Exception as e:
        logger.error(f"Error in batch operations: {e}")


async def example_playlist_management():
    """
    Example of comprehensive playlist management operations.
    """
    logger.info("=== Playlist Management Example ===")
    
    auth = TidalAuth()
    auth.access_token = "mock_token"  # Mock for example
    
    try:
        async with TidalService(auth) as service:
            
            # Create a new playlist
            playlist_title = "My Coding Playlist"
            playlist_description = "Perfect music for coding sessions"
            
            logger.info(f"Creating playlist: {playlist_title}")
            new_playlist = await service.create_playlist(playlist_title, playlist_description)
            
            if new_playlist:
                logger.info(f"Created playlist: {new_playlist.title} (ID: {new_playlist.id})")
                
                # Search for tracks to add
                coding_music_queries = [
                    "Tycho Awake",
                    "Boards of Canada Roygbiv", 
                    "Carbon Based Lifeforms Photosynthesis",
                    "Emancipator Soon It Will Be Cold Enough"
                ]
                
                track_ids_to_add = []
                
                for query in coding_music_queries:
                    logger.info(f"Searching for: {query}")
                    tracks = await service.search_tracks(query, limit=1)
                    
                    if tracks:
                        track = tracks[0]
                        track_ids_to_add.append(track.id)
                        logger.info(f"  Found: {track.title} by {track.artist_names}")
                    
                    await asyncio.sleep(0.1)  # Rate limiting
                
                # Add tracks to playlist
                if track_ids_to_add:
                    logger.info(f"Adding {len(track_ids_to_add)} tracks to playlist...")
                    success = await service.add_tracks_to_playlist(new_playlist.id, track_ids_to_add)
                    
                    if success:
                        logger.info("Tracks added successfully!")
                        
                        # Get updated playlist
                        updated_playlist = await service.get_playlist(new_playlist.id)
                        if updated_playlist:
                            logger.info(f"Playlist now has {updated_playlist.number_of_tracks} tracks")
                            logger.info(f"Total duration: {updated_playlist.formatted_duration}")
            
            else:
                logger.info("Playlist creation failed (expected in mock mode)")
            
    except Exception as e:
        logger.error(f"Error in playlist management: {e}")


async def main():
    """
    Main function to run all examples.
    """
    logger.info("Starting Tidal MCP Server Examples")
    logger.info("=" * 50)
    
    # Run examples in sequence
    examples = [
        ("Direct API Usage", example_direct_api_usage),
        ("MCP Server Usage", example_mcp_server_usage),
        ("MCP Client Usage", example_mcp_client_usage),
        ("Batch Operations", example_batch_operations),
        ("Playlist Management", example_playlist_management)
    ]
    
    for name, example_func in examples:
        try:
            logger.info(f"\nRunning example: {name}")
            await example_func()
            logger.info(f"Completed example: {name}")
        except Exception as e:
            logger.error(f"Error in {name}: {e}")
        
        logger.info("-" * 30)
    
    logger.info("\nAll examples completed!")


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())