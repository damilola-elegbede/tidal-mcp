"""
Tidal MCP Server

A Model Context Protocol (MCP) server for interacting with Tidal music
streaming service. Provides tools for searching music, managing playlists,
and controlling playback.
"""

__version__ = "0.1.0"
__author__ = "Tidal MCP Team"
__description__ = "MCP server for Tidal music streaming service"

from .auth import TidalAuth
from .models import Album, Artist, Playlist, SearchResults, Track
from .server import main, mcp
from .service import TidalService

__all__ = [
    "main",
    "mcp",
    "TidalService",
    "TidalAuth",
    "Track",
    "Album",
    "Artist",
    "Playlist",
    "SearchResults",
]
