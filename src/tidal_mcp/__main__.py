"""
Main entry point for the Tidal MCP server.

This module allows the package to be run as a module:
    python -m tidal_mcp

Or via uvx:
    uvx --from . tidal-mcp
"""

from .server import main

if __name__ == "__main__":
    main()
