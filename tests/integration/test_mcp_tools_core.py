"""
Integration tests for core MCP tools.

Tests the complete request/response cycle for all basic MCP tools including
authentication, search, playlist management, and favorites.

Note: These tests are skipped and need refactoring for proper MCP integration.
"""

import pytest

# Skip entire module - tests need refactoring for proper MCP integration
pytestmark = pytest.mark.skip(reason="MCP tool integration tests need refactoring")


class TestAuthenticationTools:
    """Test authentication-related MCP tools."""

    @pytest.mark.asyncio
    @pytest.mark.auth
    async def test_tidal_login_success(self):
        """Test successful Tidal login flow - needs refactoring."""
        pytest.skip("Needs refactoring for MCP tool integration")


class TestSearchTools:
    """Test search-related MCP tools."""

    @pytest.mark.asyncio
    @pytest.mark.search
    async def test_tidal_search_tracks(self):
        """Test track search functionality - needs refactoring."""
        pytest.skip("Needs refactoring for MCP tool integration")


class TestPlaylistTools:
    """Test playlist management MCP tools."""

    @pytest.mark.asyncio
    @pytest.mark.playlist
    async def test_tidal_get_playlist_success(self):
        """Test successful playlist retrieval - needs refactoring."""
        pytest.skip("Needs refactoring for MCP tool integration")


class TestFavoriteTools:
    """Test favorites management MCP tools."""

    @pytest.mark.asyncio
    @pytest.mark.favorites
    async def test_tidal_get_favorites_tracks(self):
        """Test getting favorite tracks - needs refactoring."""
        pytest.skip("Needs refactoring for MCP tool integration")


class TestDetailedRetrievalTools:
    """Test detailed item retrieval MCP tools."""

    @pytest.mark.asyncio
    async def test_tidal_get_track_success(self):
        """Test successful track retrieval - needs refactoring."""
        pytest.skip("Needs refactoring for MCP tool integration")


class TestRecommendationTools:
    """Test recommendation and radio MCP tools."""

    @pytest.mark.asyncio
    async def test_tidal_get_recommendations(self):
        """Test getting personalized recommendations - needs refactoring."""
        pytest.skip("Needs refactoring for MCP tool integration")