# Tidal MCP (Model Context Protocol) Server

## 🚨 CRITICAL SECURITY WARNINGS

### ⚠️ NEVER COMMIT CREDENTIALS TO VERSION CONTROL

**IMMEDIATE ACTION REQUIRED**: Ensure the following are NEVER committed to your repository:
- Tidal client secrets
- Authentication tokens
- Session data
- Personal access credentials

### 🛡️ Essential Security Setup

1. **Use Environment Variables Only**: Store ALL sensitive data in environment variables
2. **Configure .gitignore**: Ensure `.env`, `*.session`, and token files are excluded
3. **Validate Configuration**: Always verify your environment setup before deployment

**See the [Security Guidelines](#-security-guidelines) section below for complete requirements.**

---

## Overview

Tidal MCP is a high-performance, asynchronous Python library for seamless interaction with the Tidal music streaming service. Built with modern Python async capabilities, it provides a robust, type-safe, and developer-friendly interface for music discovery, playlist management, and personalized music experiences.

## 🎵 Key Features

- **Comprehensive Tidal Integration**
  - Full access to tracks, albums, artists, and playlists
  - Advanced search capabilities across all content types
  - Personalized recommendations and track radio generation

- **Asynchronous Performance**
  - Built with `asyncio` for non-blocking, high-concurrency operations
  - Efficient API interaction with minimal overhead
  - Supports modern Python async/await syntax

- **Advanced Authentication**
  - Secure OAuth2 authentication flow
  - Token management and automatic refresh
  - Support for environment-based configuration

- **Flexible Toolset**
  - Comprehensive playlist management
  - Favorites tracking and manipulation
  - Detailed track, album, and artist information retrieval

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Tidal Premium or HiFi subscription
- `pip` or `uvx` package manager

### Installation

```bash
# Using pip
pip install tidal-mcp

# Using uvx
uvx install tidal-mcp
```

### 🔐 Secure Environment Setup

**CRITICAL**: Complete this security setup before using Tidal MCP:

1. **Create Environment File**:
   ```bash
   cp .env.example .env
   ```

2. **Configure Required Variables**:
   ```bash
   # Edit .env with your secure credentials
   TIDAL_CLIENT_ID=your_client_id_here
   TIDAL_CLIENT_SECRET=your_client_secret_here
   TIDAL_TOKEN_CACHE_PATH=/secure/path/to/tokens
   ```

3. **Verify .gitignore Configuration**:
   Ensure these patterns are in your `.gitignore`:
   ```
   .env
   .env.*
   *.session
   tokens/
   .tidal_cache/
   ```

4. **Set Secure Permissions**:
   ```bash
   chmod 600 .env
   chmod 700 tokens/
   ```

### Basic Authentication

```python
import asyncio
from tidal_mcp import tidal_login

async def main():
    # Authenticate with Tidal
    # This will open a browser window for login
    auth_result = await tidal_login()
    print(auth_result)

asyncio.run(main())
```

## 🔍 Usage Examples

### Search Music

```python
from tidal_mcp import tidal_search

async def search_example():
    # Search for tracks by Daft Punk
    tracks = await tidal_search(query="Daft Punk", content_type="tracks")

    # Global search across all content types
    all_results = await tidal_search(query="Radiohead")
```

### Playlist Management

```python
from tidal_mcp import (
    tidal_create_playlist,
    tidal_add_to_playlist,
    tidal_get_playlist
)

async def playlist_example():
    # Create a new playlist
    playlist = await tidal_create_playlist("My Awesome Playlist")

    # Add tracks to playlist
    await tidal_add_to_playlist(
        playlist_id=playlist['playlist']['id'],
        track_ids=['123456', '789012']
    )

    # Get playlist details
    playlist_details = await tidal_get_playlist(playlist['playlist']['id'])
```

### Recommendations

```python
from tidal_mcp import tidal_get_recommendations

async def recommendations_example():
    # Get personalized track recommendations
    recommendations = await tidal_get_recommendations(limit=25)
```

## 🔧 Configuration

### Environment Variables

Configure Tidal MCP using the following environment variables:

| Variable | Required | Description | Security Notes |
|----------|----------|-------------|----------------|
| `TIDAL_CLIENT_ID` | Yes | Your Tidal API client ID | Store in `.env` only |
| `TIDAL_CLIENT_SECRET` | Yes | Your Tidal API client secret | **NEVER commit to git** |
| `TIDAL_TOKEN_CACHE_PATH` | No | Custom path for storing authentication tokens | Use secure directory with restricted permissions |

### 🛡️ Security Guidelines

#### Credential Management

1. **Environment Variables Only**:
   - Store ALL sensitive data in environment variables
   - Use `.env` files for local development
   - Use secure environment management in production

2. **File Permissions**:
   ```bash
   # Set restrictive permissions
   chmod 600 .env
   chmod 700 $(dirname $TIDAL_TOKEN_CACHE_PATH)
   ```

3. **Version Control Exclusions**:
   Ensure your `.gitignore` includes:
   ```
   .env
   .env.*
   *.session
   tokens/
   .tidal_cache/
   auth_cache/
   ```

#### Session Security

1. **Token Storage**:
   - Tokens are automatically cached in a secure location
   - Never share or commit token files
   - Use custom `TIDAL_TOKEN_CACHE_PATH` for enhanced security

2. **Session Management**:
   - Sessions expire automatically for security
   - Re-authentication may be required periodically
   - Monitor for unusual authentication requests

#### Production Deployment

1. **Environment Management**:
   - Use platform-specific secret management (AWS Secrets Manager, Azure Key Vault, etc.)
   - Never use `.env` files in production
   - Implement credential rotation policies

2. **Access Control**:
   - Limit access to credential storage
   - Use principle of least privilege
   - Monitor authentication logs

3. **Security Monitoring**:
   - Implement logging for authentication events
   - Monitor for failed authentication attempts
   - Set up alerts for credential-related errors

## 📋 Available Tools

### Authentication
- `tidal_login()`: Authenticate with Tidal
- OAuth2 browser-based authentication

### Search
- `tidal_search()`: Search across tracks, albums, artists, playlists
- Supports pagination and content type filtering

### Content Retrieval
- `tidal_get_track()`: Retrieve detailed track information
- `tidal_get_album()`: Get comprehensive album details
- `tidal_get_artist()`: Fetch artist information

### Playlist Management
- `tidal_create_playlist()`: Create new playlists
- `tidal_add_to_playlist()`: Add tracks to playlists
- `tidal_remove_from_playlist()`: Remove tracks from playlists
- `tidal_get_user_playlists()`: List user's playlists

### Favorites
- `tidal_get_favorites()`: Retrieve favorite content
- `tidal_add_favorite()`: Add items to favorites
- `tidal_remove_favorite()`: Remove items from favorites

### Discovery
- `tidal_get_recommendations()`: Get personalized recommendations
- `tidal_get_track_radio()`: Generate radio based on a track

## 🛡 Error Handling

Tidal MCP provides comprehensive error handling:
- Authentication errors
- Rate limit handling
- Detailed error messages
- Type-safe error responses

## 📊 Performance Considerations

- Use `limit` and `offset` for efficient pagination
- Be mindful of API rate limits
- Consider caching frequently accessed data
- Leverage async programming for concurrent operations

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to get started.

**Security Requirements for Contributors**: All contributors must follow our [Security Policy](SECURITY.md) and never commit credentials or sensitive data.

## 📄 License

[Specify your project's license here]

## 🙌 Credits

- Developed by Tidal MCP Team
- Built with ❤️ and Python
- Powered by FastMCP and TidalAPI

## 📞 Support

For issues, feature requests, or support, please file an issue on our [GitHub repository](https://github.com/tidal-mcp/tidal-mcp/issues).

**Security Issues**: Report security vulnerabilities through our [Security Policy](SECURITY.md).

---

**Version**: 0.1.0
**Last Updated**: 2025-09-20
