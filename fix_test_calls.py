#!/usr/bin/env python3
"""Script to fix broken test function calls."""

import re

# Read the file
with open('tests/integration/test_mcp_tools_core.py') as f:
    content = f.read()

# Fix the broken patterns
fixes = [
    (r'await server\.tidal_\.fn\(get_playlist\(', 'await server.tidal_get_playlist.fn('),
    (r'await server\.tidal_\.fn\(create_playlist\(', 'await server.tidal_create_playlist.fn('),
    (r'await server\.tidal_\.fn\(add_to_playlist\(', 'await server.tidal_add_to_playlist.fn('),
    (r'await server\.tidal_\.fn\(remove_from_playlist\(', 'await server.tidal_remove_from_playlist.fn('),
    (r'await server\.tidal_\.fn\(get_user_playlists\(', 'await server.tidal_get_user_playlists.fn('),
    (r'await server\.tidal_\.fn\(get_favorites\(', 'await server.tidal_get_favorites.fn('),
    (r'await server\.tidal_\.fn\(add_favorite\(', 'await server.tidal_add_favorite.fn('),
    (r'await server\.tidal_\.fn\(remove_favorite\(', 'await server.tidal_remove_favorite.fn('),
    (r'await server\.tidal_\.fn\(get_track\(', 'await server.tidal_get_track.fn('),
    (r'await server\.tidal_\.fn\(get_album\(', 'await server.tidal_get_album.fn('),
    (r'await server\.tidal_\.fn\(get_artist\(', 'await server.tidal_get_artist.fn('),
    (r'await server\.tidal_\.fn\(get_recommendations\(', 'await server.tidal_get_recommendations.fn('),
    (r'await server\.tidal_\.fn\(get_track_radio\(', 'await server.tidal_get_track_radio.fn('),
]

for pattern, replacement in fixes:
    content = re.sub(pattern, replacement, content)

# Write the fixed content back
with open('tests/integration/test_mcp_tools_core.py', 'w') as f:
    f.write(content)

print("Fixed test function calls")
