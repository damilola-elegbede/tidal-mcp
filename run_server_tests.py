#!/usr/bin/env python3
"""
Simple test runner for server.py tests.

Runs basic functionality tests without requiring pytest installation.
"""

import asyncio
import sys
import traceback
from unittest.mock import AsyncMock, Mock, patch

# Add src to path
sys.path.insert(0, 'src')

from src.tidal_mcp import server
from src.tidal_mcp.auth import TidalAuthError
from src.tidal_mcp.models import Album, Artist, Playlist, Track


class SimpleTestRunner:
    """Simple test runner for server tests."""

    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0

    def run_test(self, test_name, test_func):
        """Run a single test."""
        self.tests_run += 1
        try:
            if asyncio.iscoroutinefunction(test_func):
                asyncio.run(test_func())
            else:
                test_func()
            print(f"✅ {test_name}")
            self.tests_passed += 1
        except Exception as e:
            print(f"❌ {test_name}: {e}")
            self.tests_failed += 1
            if "--verbose" in sys.argv:
                traceback.print_exc()

    def summary(self):
        """Print test summary."""
        print("\n📊 Test Summary:")
        print(f"   Total: {self.tests_run}")
        print(f"   Passed: {self.tests_passed}")
        print(f"   Failed: {self.tests_failed}")

        if self.tests_failed == 0:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"💥 {self.tests_failed} tests failed!")
            return False


def test_mcp_tool_registration():
    """Test that all MCP tools are registered."""
    expected_tools = [
        "tidal_login", "tidal_search", "tidal_get_playlist", "tidal_create_playlist",
        "tidal_add_to_playlist", "tidal_remove_from_playlist", "tidal_get_favorites",
        "tidal_add_favorite", "tidal_remove_favorite", "tidal_get_recommendations",
        "tidal_get_track_radio", "tidal_get_user_playlists", "tidal_get_track",
        "tidal_get_album", "tidal_get_artist"
    ]

    for tool_name in expected_tools:
        tool = getattr(server, tool_name, None)
        assert tool is not None, f"Tool {tool_name} not found"
        assert hasattr(tool, 'name'), f"Tool {tool_name} missing name attribute"
        assert tool.name == tool_name, f"Tool name mismatch: {tool.name} != {tool_name}"

    assert server.mcp.name == "Tidal Music Integration"


async def test_ensure_service_creates_instances():
    """Test ensure_service creates auth and service instances."""
    # Reset global instances
    server.auth_manager = None
    server.tidal_service = None

    with patch('src.tidal_mcp.server.TidalAuth') as mock_auth_class, \
         patch('src.tidal_mcp.server.TidalService') as mock_service_class:

        mock_auth = Mock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_service = Mock()
        mock_service_class.return_value = mock_service

        result = await server.ensure_service()

        assert result == mock_service
        assert server.auth_manager == mock_auth
        assert server.tidal_service == mock_service


async def test_ensure_service_not_authenticated():
    """Test ensure_service raises error when not authenticated."""
    server.auth_manager = None
    server.tidal_service = None

    with patch('src.tidal_mcp.server.TidalAuth') as mock_auth_class:
        mock_auth = Mock()
        mock_auth.is_authenticated.return_value = False
        mock_auth_class.return_value = mock_auth

        try:
            await server.ensure_service()
            raise AssertionError("Expected TidalAuthError")
        except TidalAuthError as e:
            assert "Not authenticated" in str(e)


async def test_tidal_login_success():
    """Test successful Tidal login."""
    with patch('src.tidal_mcp.server.TidalAuth') as mock_auth_class:
        mock_auth = Mock()  # Use regular Mock, not AsyncMock
        mock_auth.authenticate = AsyncMock(return_value=True)  # Only the async method needs AsyncMock
        mock_auth.get_user_info.return_value = {
            "id": "12345",
            "username": "testuser",
            "country_code": "US"
        }
        mock_auth_class.return_value = mock_auth

        with patch('src.tidal_mcp.server.TidalService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            result = await server.tidal_login.fn()

            assert result["success"] is True
            assert "Successfully authenticated" in result["message"]
            assert result["user"]["id"] == "12345"


async def test_tidal_login_failure():
    """Test failed Tidal login."""
    with patch('src.tidal_mcp.server.TidalAuth') as mock_auth_class:
        mock_auth = Mock()
        mock_auth.authenticate = AsyncMock(return_value=False)
        mock_auth_class.return_value = mock_auth

        result = await server.tidal_login.fn()

        assert result["success"] is False
        assert "Authentication failed" in result["message"]
        assert result["user"] is None


async def test_tidal_search_tracks():
    """Test successful track search."""
    # Create a sample track
    sample_track = Track(
        id="12345",
        title="Test Song",
        artists=[Artist(id="67890", name="Test Artist", picture="", popularity=85)],
        album=Album(id="11111", title="Test Album", artists=[], release_date="2023-01-01",
                   duration=2400, number_of_tracks=12, cover="", explicit=False),
        duration=210,
        track_number=1,
        disc_number=1,
        explicit=False,
        quality="LOSSLESS"
    )

    mock_service = AsyncMock()
    mock_service.search_tracks.return_value = [sample_track]

    with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
        result = await server.tidal_search.fn("test query", "tracks", 10, 0)

        assert result["query"] == "test query"
        assert result["content_type"] == "tracks"
        assert len(result["results"]["tracks"]) == 1
        assert result["results"]["tracks"][0]["id"] == "12345"
        assert result["total_results"] == 1


async def test_tidal_search_parameter_clamping():
    """Test search parameter validation and clamping."""
    mock_service = AsyncMock()
    mock_service.search_tracks.return_value = []

    with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
        # Test limit clamping (max 50)
        await server.tidal_search.fn("test", "tracks", 100, 0)
        mock_service.search_tracks.assert_called_with("test", 50, 0)

        # Test negative offset clamping
        await server.tidal_search.fn("test", "tracks", 10, -5)
        mock_service.search_tracks.assert_called_with("test", 10, 0)


async def test_tidal_search_auth_error():
    """Test search with authentication error."""
    with patch('src.tidal_mcp.server.ensure_service', side_effect=TidalAuthError("Not authenticated")):
        result = await server.tidal_search.fn("test", "tracks", 10, 0)

        assert "error" in result
        assert "Authentication required" in result["error"]


async def test_create_playlist_success():
    """Test successful playlist creation."""
    sample_playlist = Playlist(
        id="test-playlist-uuid",
        title="Test Playlist",
        description="A test playlist",
        creator="Test User",
        tracks=[],
        number_of_tracks=0,
        duration=0,
        created_at=None,
        updated_at=None,
        image="",
        public=True
    )

    mock_service = AsyncMock()
    mock_service.create_playlist.return_value = sample_playlist

    with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
        result = await server.tidal_create_playlist.fn("New Playlist", "Description")

        assert result["success"] is True
        assert "Created playlist" in result["message"]
        assert result["playlist"]["title"] == "Test Playlist"


async def test_add_to_playlist_success():
    """Test successful track addition to playlist."""
    mock_service = AsyncMock()
    mock_service.add_tracks_to_playlist.return_value = True
    track_ids = ["track1", "track2", "track3"]

    with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
        result = await server.tidal_add_to_playlist.fn("playlist_123", track_ids)

        assert result["success"] is True
        assert "Added 3 tracks" in result["message"]


async def test_add_to_playlist_empty_list():
    """Test adding empty track list to playlist."""
    mock_service = AsyncMock()

    with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
        result = await server.tidal_add_to_playlist.fn("playlist_123", [])

        assert result["success"] is False
        assert "No track IDs provided" in result["error"]


def test_main_function_exists():
    """Test that main function exists and is callable."""
    assert callable(server.main)


def main():
    """Run all tests."""
    print("🧪 Running Server.py MCP Tools Tests")
    print("=" * 50)

    runner = SimpleTestRunner()

    # Run tests
    runner.run_test("MCP Tool Registration", test_mcp_tool_registration)
    runner.run_test("Ensure Service Creates Instances", test_ensure_service_creates_instances)
    runner.run_test("Ensure Service Not Authenticated", test_ensure_service_not_authenticated)
    runner.run_test("Tidal Login Success", test_tidal_login_success)
    runner.run_test("Tidal Login Failure", test_tidal_login_failure)
    runner.run_test("Tidal Search Tracks", test_tidal_search_tracks)
    runner.run_test("Tidal Search Parameter Clamping", test_tidal_search_parameter_clamping)
    runner.run_test("Tidal Search Auth Error", test_tidal_search_auth_error)
    runner.run_test("Create Playlist Success", test_create_playlist_success)
    runner.run_test("Add to Playlist Success", test_add_to_playlist_success)
    runner.run_test("Add to Playlist Empty List", test_add_to_playlist_empty_list)
    runner.run_test("Main Function Exists", test_main_function_exists)

    # Print summary
    success = runner.summary()

    if success:
        print("\n✅ Server tests validate basic MCP tool functionality!")
        print("🎯 The comprehensive test file should provide good coverage.")
    else:
        print("\n❌ Some tests failed. Check the implementation.")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
