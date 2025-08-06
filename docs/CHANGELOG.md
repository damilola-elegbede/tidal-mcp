# Changelog

All notable changes to the Tidal MCP project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-05

### Added
- Initial release of Tidal MCP server
- OAuth2 authentication with PKCE flow for secure Tidal login
- Comprehensive search functionality across tracks, albums, artists, and playlists
- Full playlist management (create, modify, delete)
- Favorites/library management for all content types
- Personalized recommendations and radio stations
- Detailed content retrieval for tracks, albums, and artists
- User profile access and management
- Token persistence with automatic refresh
- FastMCP integration for Claude Desktop compatibility
- Comprehensive test suite with >80% coverage
- Complete documentation and examples
- PyPI package configuration for easy installation

### Security
- Secure OAuth2 PKCE implementation
- Token storage with appropriate file permissions
- No credential logging or exposure in error messages

### Technical Details
- Single-process architecture for simplicity
- Async/await patterns throughout for performance
- Direct tidalapi library integration
- Minimal dependencies for easier maintenance
- Cross-platform compatibility (Windows, macOS, Linux)

## [Unreleased]

### Planned Features
- Playback control integration (play, pause, skip)
- Offline cache for frequently accessed data
- Advanced search filters and sorting
- Collaborative playlist support
- Export playlists to other formats
- Batch operations for efficiency
- Enhanced error recovery mechanisms

---

For detailed release notes and migration guides, see the [GitHub Releases](https://github.com/tidal-mcp/tidal-mcp/releases) page.