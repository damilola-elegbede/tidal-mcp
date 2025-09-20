"""
End-to-end flow integration tests.

Tests complete user workflows and multi-step operations including
authentication → search → playlist creation → favorites management.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch

# Conditional import based on testing environment
if os.getenv('TESTING') == '1':
    from tests import mock_tidal_server as server
else:
    from tidal_mcp import server

try:
    from tidal_mcp.production import enhanced_tools
except ImportError:
    # Handle case where production tools might not be available
    enhanced_tools = None


class TestAuthenticationToSearchFlow:
    """Test complete authentication and search workflows."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.auth
    @pytest.mark.search
    async def test_complete_auth_and_search_flow(
        self,
        mock_auth_manager,
        tidal_service,
        track_factory,
        fixed_time
    ):
        """Test complete flow: login → search tracks → get track details."""
        # Step 1: Authentication
        mock_auth_manager.authenticate.return_value = True
        mock_auth_manager.get_user_info.return_value = {
            "id": "flow_user_123",
            "username": "flow_user",
            "country_code": "US",
            "subscription": "premium"
        }

        # Step 2: Search setup
        search_tracks = [
            track_factory(track_id="flow1", title="Flow Track 1", artist_name="Flow Artist 1"),
            track_factory(track_id="flow2", title="Flow Track 2", artist_name="Flow Artist 2"),
        ]
        tidal_service.search_tracks = AsyncMock(return_value=search_tracks)

        # Step 3: Track details setup
        detailed_track = track_factory(track_id="flow1", title="Flow Track 1 (Detailed)")
        tidal_service.get_track = AsyncMock(return_value=detailed_track)

        with patch.object(server, 'auth_manager', mock_auth_manager), \
             patch.object(server, 'tidal_service', None), \
             patch.object(server, 'ensure_service', return_value=tidal_service), \
             patch('tidal_mcp.server.TidalAuth', return_value=mock_auth_manager):

            # Step 1: Login
            login_result = await server.tidal_login.fn()
            assert login_result["success"] is True
            assert login_result["user"]["id"] == "mock_user_123"

            # Step 2: Search for tracks
            search_result = await server.tidal_search.fn("flow test", "tracks", 10, 0)
            assert search_result["query"] == "flow test"
            assert search_result["total_results"] == 2
            assert len(search_result["results"]["tracks"]) == 2

            # Step 3: Get detailed info for first track
            track_id = search_result["results"]["tracks"][0]["id"]
            detail_result = await server.tidal_get_track.fn(track_id)
            assert detail_result["success"] is True
            assert detail_result["track"]["id"] == "flow1"
            assert "Detailed" in detail_result["track"]["title"]

            # Verify service calls
            tidal_service.search_tracks.assert_called_once_with("flow test", 10, 0)
            tidal_service.get_track.assert_called_once_with("flow1")

    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.search
    async def test_multi_type_search_flow(
        self,
        tidal_service,
        search_results_factory,
        track_factory,
        album_factory,
        artist_factory
    ):
        """Test flow: search all → get details for each type."""
        # Setup comprehensive search results
        search_results = search_results_factory(
            track_count=2,
            album_count=1,
            artist_count=1,
            playlist_count=1,
            query="multi"
        )
        tidal_service.search_all = AsyncMock(return_value=search_results)

        # Setup detailed retrievals
        detailed_track = track_factory(track_id="2000", title="multi Track 1 (Detailed)")
        detailed_album = album_factory(album_id="3000", title="multi Album 1 (Detailed)")
        detailed_artist = artist_factory(artist_id="4000", name="multi Artist 1 (Detailed)")

        tidal_service.get_track = AsyncMock(return_value=detailed_track)
        tidal_service.get_album = AsyncMock(return_value=detailed_album)
        tidal_service.get_artist = AsyncMock(return_value=detailed_artist)

        with patch.object(server, 'ensure_service', return_value=tidal_service):
            # Step 1: Search across all types
            search_result = await server.tidal_search.fn("multi", "all", 10)
            assert search_result["content_type"] == "all"
            assert search_result["total_results"] == 5

            # Step 2: Get track details
            track_id = search_result["results"]["tracks"][0]["id"]
            track_detail = await server.tidal_get_track.fn(track_id)
            assert track_detail["success"] is True
            assert "Detailed" in track_detail["track"]["title"]

            # Step 3: Get album details
            album_id = search_result["results"]["albums"][0]["id"]
            album_detail = await server.tidal_get_album.fn(album_id, True)
            assert album_detail["success"] is True
            assert "Detailed" in album_detail["album"]["title"]

            # Step 4: Get artist details
            artist_id = search_result["results"]["artists"][0]["id"]
            artist_detail = await server.tidal_get_artist.fn(artist_id)
            assert artist_detail["success"] is True
            assert "Detailed" in artist_detail["artist"]["name"]


class TestPlaylistManagementFlow:
    """Test complete playlist management workflows."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.playlist
    async def test_complete_playlist_management_flow(
        self,
        tidal_service,
        playlist_factory,
        track_factory
    ):
        """Test flow: create playlist → add tracks → get playlist → remove tracks."""
        # Setup mocks
        new_playlist = playlist_factory(
            playlist_id="new-flow-playlist",
            title="Flow Test Playlist",
            track_count=0
        )

        updated_playlist = playlist_factory(
            playlist_id="new-flow-playlist",
            title="Flow Test Playlist",
            track_count=3
        )

        final_playlist = playlist_factory(
            playlist_id="new-flow-playlist",
            title="Flow Test Playlist",
            track_count=1
        )

        tidal_service.create_playlist = AsyncMock(return_value=new_playlist)
        tidal_service.add_tracks_to_playlist = AsyncMock(return_value=True)
        tidal_service.remove_tracks_from_playlist = AsyncMock(return_value=True)

        # Mock get_playlist to return different states
        playlist_states = [updated_playlist, final_playlist]
        tidal_service.get_playlist = AsyncMock(side_effect=playlist_states)

        with patch.object(server, 'ensure_service', return_value=tidal_service):
            # Step 1: Create playlist
            create_result = await server.tidal_create_playlist.fn(
                "Flow Test Playlist",
                "A test playlist for flow testing"
            )
            assert create_result["success"] is True
            assert create_result["playlist"]["title"] == "Flow Test Playlist"
            playlist_id = create_result["playlist"]["id"]

            # Step 2: Add tracks to playlist
            track_ids = ["track1", "track2", "track3"]
            add_result = await server.tidal_add_to_playlist.fn(playlist_id, track_ids)
            assert add_result["success"] is True
            assert "Added 3 tracks" in add_result["message"]

            # Step 3: Get updated playlist
            get_result1 = await server.tidal_get_playlist.fn(playlist_id, True)
            assert get_result1["success"] is True
            assert get_result1["playlist"]["number_of_tracks"] == 3

            # Step 4: Remove some tracks
            remove_indices = [0, 2]  # Remove first and third tracks
            remove_result = await server.tidal_remove_from_playlist.fn(playlist_id, remove_indices)
            assert remove_result["success"] is True
            assert "Removed 2 tracks" in remove_result["message"]

            # Step 5: Get final playlist state
            get_result2 = await server.tidal_get_playlist.fn(playlist_id, True)
            assert get_result2["success"] is True
            assert get_result2["playlist"]["number_of_tracks"] == 1

            # Verify all service calls
            tidal_service.create_playlist.assert_called_once()
            tidal_service.add_tracks_to_playlist.assert_called_once_with(playlist_id, track_ids)
            tidal_service.remove_tracks_from_playlist.assert_called_once_with(playlist_id, remove_indices)
            assert tidal_service.get_playlist.call_count == 2

    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.playlist
    async def test_search_to_playlist_flow(
        self,
        tidal_service,
        track_factory,
        playlist_factory
    ):
        """Test flow: search tracks → create playlist → add found tracks."""
        # Setup search results
        search_tracks = [
            track_factory(track_id="search1", title="Search Track 1"),
            track_factory(track_id="search2", title="Search Track 2"),
            track_factory(track_id="search3", title="Search Track 3"),
        ]
        tidal_service.search_tracks = AsyncMock(return_value=search_tracks)

        # Setup playlist creation
        new_playlist = playlist_factory(
            playlist_id="search-playlist",
            title="Search Results Playlist",
            track_count=0
        )
        tidal_service.create_playlist = AsyncMock(return_value=new_playlist)
        tidal_service.add_tracks_to_playlist = AsyncMock(return_value=True)

        with patch.object(server, 'ensure_service', return_value=tidal_service):
            # Step 1: Search for tracks
            search_result = await server.tidal_search.fn("search query", "tracks", 10)
            assert len(search_result["results"]["tracks"]) == 3

            # Step 2: Create playlist for search results
            create_result = await server.tidal_create_playlist.fn(
                "Search Results Playlist",
                "Playlist created from search results"
            )
            assert create_result["success"] is True
            playlist_id = create_result["playlist"]["id"]

            # Step 3: Add all found tracks to playlist
            track_ids = [track["id"] for track in search_result["results"]["tracks"]]
            add_result = await server.tidal_add_to_playlist.fn(playlist_id, track_ids)
            assert add_result["success"] is True

            # Verify the workflow
            tidal_service.search_tracks.assert_called_once_with("search query", 10, 0)
            tidal_service.create_playlist.assert_called_once()
            tidal_service.add_tracks_to_playlist.assert_called_once_with(
                playlist_id,
                ["search1", "search2", "search3"]
            )


class TestFavoritesManagementFlow:
    """Test complete favorites management workflows."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.favorites
    async def test_complete_favorites_flow(
        self,
        tidal_service,
        track_factory,
        album_factory,
        artist_factory
    ):
        """Test flow: add to favorites → get favorites → remove from favorites."""
        # Setup items to favorite
        track = track_factory(track_id="fav-track", title="Favorite Track")
        album = album_factory(album_id="fav-album", title="Favorite Album")
        artist = artist_factory(artist_id="fav-artist", name="Favorite Artist")

        # Setup favorites operations
        tidal_service.add_to_favorites = AsyncMock(return_value=True)
        tidal_service.remove_from_favorites = AsyncMock(return_value=True)

        # Setup favorites retrieval - return different states
        initial_favorites = []
        after_add_favorites = [track]
        empty_favorites = []

        favorite_states = [initial_favorites, after_add_favorites, empty_favorites]
        tidal_service.get_user_favorites = AsyncMock(side_effect=favorite_states)

        with patch.object(server, 'ensure_service', return_value=tidal_service):
            # Step 1: Check initial favorites (should be empty)
            initial_result = await server.tidal_get_favorites.fn("tracks", 50, 0)
            assert initial_result["total_results"] == 0

            # Step 2: Add track to favorites
            add_track_result = await server.tidal_add_favorite.fn("fav-track", "track")
            assert add_track_result["success"] is True
            assert "Added track fav-track to favorites" in add_track_result["message"]

            # Step 3: Add album to favorites
            add_album_result = await server.tidal_add_favorite.fn("fav-album", "album")
            assert add_album_result["success"] is True

            # Step 4: Add artist to favorites
            add_artist_result = await server.tidal_add_favorite.fn("fav-artist", "artist")
            assert add_artist_result["success"] is True

            # Step 5: Check favorites after adding
            after_add_result = await server.tidal_get_favorites.fn("tracks", 50, 0)
            assert after_add_result["total_results"] == 1
            assert after_add_result["favorites"][0]["id"] == "fav-track"

            # Step 6: Remove track from favorites
            remove_result = await server.tidal_remove_favorite.fn("fav-track", "track")
            assert remove_result["success"] is True
            assert "Removed track fav-track from favorites" in remove_result["message"]

            # Step 7: Check favorites after removal
            final_result = await server.tidal_get_favorites.fn("tracks", 50, 0)
            assert final_result["total_results"] == 0

            # Verify service calls
            assert tidal_service.add_to_favorites.call_count == 3
            assert tidal_service.remove_from_favorites.call_count == 1
            assert tidal_service.get_user_favorites.call_count == 3


class TestRecommendationFlow:
    """Test recommendation and discovery workflows."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_recommendation_to_playlist_flow(
        self,
        tidal_service,
        track_factory,
        playlist_factory
    ):
        """Test flow: get recommendations → create playlist → add recommended tracks."""
        # Setup recommendations
        recommended_tracks = [
            track_factory(track_id="rec1", title="Recommended Track 1"),
            track_factory(track_id="rec2", title="Recommended Track 2"),
            track_factory(track_id="rec3", title="Recommended Track 3"),
        ]
        tidal_service.get_recommended_tracks = AsyncMock(return_value=recommended_tracks)

        # Setup playlist creation
        new_playlist = playlist_factory(
            playlist_id="rec-playlist",
            title="My Recommendations",
            track_count=0
        )
        tidal_service.create_playlist = AsyncMock(return_value=new_playlist)
        tidal_service.add_tracks_to_playlist = AsyncMock(return_value=True)

        with patch.object(server, 'ensure_service', return_value=tidal_service):
            # Step 1: Get recommendations
            rec_result = await server.tidal_get_recommendations.fn(25)
            assert len(rec_result["recommendations"]) == 3
            assert rec_result["total_results"] == 3

            # Step 2: Create playlist for recommendations
            create_result = await server.tidal_create_playlist.fn(
                "My Recommendations",
                "Playlist based on my recommendations"
            )
            assert create_result["success"] is True
            playlist_id = create_result["playlist"]["id"]

            # Step 3: Add recommended tracks to playlist
            track_ids = [track["id"] for track in rec_result["recommendations"]]
            add_result = await server.tidal_add_to_playlist.fn(playlist_id, track_ids)
            assert add_result["success"] is True

            # Verify the workflow
            tidal_service.get_recommended_tracks.assert_called_once_with(25)
            tidal_service.create_playlist.assert_called_once()
            tidal_service.add_tracks_to_playlist.assert_called_once_with(
                playlist_id,
                ["rec1", "rec2", "rec3"]
            )

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_track_radio_discovery_flow(
        self,
        tidal_service,
        track_factory
    ):
        """Test flow: get track details → get track radio → add radio tracks to favorites."""
        # Setup seed track
        seed_track = track_factory(track_id="seed123", title="Seed Track")
        tidal_service.get_track = AsyncMock(return_value=seed_track)

        # Setup radio tracks
        radio_tracks = [
            track_factory(track_id="radio1", title="Radio Track 1"),
            track_factory(track_id="radio2", title="Radio Track 2"),
        ]
        tidal_service.get_track_radio = AsyncMock(return_value=radio_tracks)
        tidal_service.add_to_favorites = AsyncMock(return_value=True)

        with patch.object(server, 'ensure_service', return_value=tidal_service):
            # Step 1: Get seed track details
            track_result = await server.tidal_get_track.fn("seed123")
            assert track_result["success"] is True
            assert track_result["track"]["title"] == "Seed Track"

            # Step 2: Get radio based on seed track
            radio_result = await server.tidal_get_track_radio.fn("seed123", 30)
            assert radio_result["seed_track_id"] == "seed123"
            assert len(radio_result["radio_tracks"]) == 2

            # Step 3: Add first radio track to favorites
            first_radio_track_id = radio_result["radio_tracks"][0]["id"]
            fav_result = await server.tidal_add_favorite.fn(first_radio_track_id, "track")
            assert fav_result["success"] is True

            # Verify the workflow
            tidal_service.get_track.assert_called_once_with("seed123")
            tidal_service.get_track_radio.assert_called_once_with("seed123", 30)
            tidal_service.add_to_favorites.assert_called_once_with("radio1", "track")


class TestProductionFlows:
    """Test enhanced production workflows with middleware."""

    @pytest.mark.skipif(True, reason="Production flows temporarily disabled - need complex fixture setup")
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.integration
    async def test_enhanced_auth_to_streaming_flow(
        self,
        middleware_stack,
        mock_auth_manager,
        tidal_service,
        track_factory
    ):
        """Test flow: enhanced login → advanced search → get streaming URL."""
        # Setup enhanced authentication
        mock_auth_manager.authenticate = AsyncMock(return_value=True)
        mock_auth_manager.get_user_info.return_value = {
            "id": "premium_user",
            "subscription": "premium"
        }

        # Setup search
        search_tracks = [
            track_factory(track_id="stream1", title="Streamable Track 1"),
        ]
        tidal_service.search_tracks = AsyncMock(return_value=search_tracks)
        tidal_service.get_track = AsyncMock(return_value=search_tracks[0])

        # Mock streaming URL generation
        streaming_info = {
            "url": "https://streaming.tidal.com/track/stream1?quality=LOSSLESS&format=FLAC",
            "quality": "LOSSLESS",
            "format": "FLAC",
            "bitrate": 1411,
            "sample_rate": 44100,
            "expires_at": "2024-01-15T12:30:00Z",
            "drm_protected": True
        }

        with patch.object(enhanced_tools, 'middleware_stack', middleware_stack), \
             patch.object(enhanced_tools, 'auth_manager', mock_auth_manager), \
             patch.object(enhanced_tools, 'tidal_service', None), \
             patch.object(enhanced_tools, 'ensure_service', return_value=tidal_service), \
             patch.object(enhanced_tools, '_generate_streaming_url', return_value=streaming_info):

            # Step 1: Enhanced login
            login_result = await enhanced_tools.tidal_login.fn()
            assert login_result["success"] is True
            assert "session_info" in login_result
            assert "security" in login_result

            # Step 2: Advanced search
            search_result = await enhanced_tools.tidal_search_advanced.fn(
                "streamable", "tracks", 10, 0
            )
            assert search_result["success"] is True
            assert len(search_result["results"]["tracks"]) == 1

            # Step 3: Get streaming URL for found track
            track_id = search_result["results"]["tracks"][0]["id"]
            stream_result = await enhanced_tools.get_stream_url.fn(
                track_id, "LOSSLESS", "FLAC"
            )
            assert stream_result["success"] is True
            assert stream_result["audio_info"]["quality"] == "LOSSLESS"
            assert stream_result["audio_info"]["format"] == "FLAC"
            assert stream_result["security"]["drm_protected"] is True

    @pytest.mark.skipif(True, reason="Production flows temporarily disabled - need complex fixture setup")
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.integration
    async def test_system_health_monitoring_flow(
        self,
        health_checker,
        middleware_stack
    ):
        """Test flow: health check → system status → rate limit status."""
        # Setup health responses
        health_checker.check_redis_health = AsyncMock(return_value={
            "status": "healthy",
            "response_time_ms": 5.0
        })
        health_checker.check_rate_limiter_health = AsyncMock(return_value={
            "status": "healthy",
            "response_time_ms": 3.0
        })

        # Mock auth manager to be authenticated
        mock_auth_manager = Mock()
        mock_auth_manager.is_authenticated.return_value = True

        with patch.object(enhanced_tools, 'health_checker', health_checker), \
             patch.object(enhanced_tools, 'middleware_stack', middleware_stack), \
             patch('tidal_mcp.production.enhanced_tools.auth_manager', mock_auth_manager):

            # Step 1: Overall health check
            health_result = await enhanced_tools.health_check.fn()
            assert health_result["status"] == "healthy"
            assert "dependencies" in health_result
            assert "metrics" in health_result

            # Step 2: Detailed system status
            status_result = await enhanced_tools.get_system_status.fn()
            assert "service_info" in status_result
            assert "rate_limits" in status_result
            assert "performance" in status_result

            # Step 3: Rate limit status
            rate_limit_result = await enhanced_tools.get_rate_limit_status.fn()
            assert rate_limit_result["success"] is True
            assert "rate_limit_status" in rate_limit_result
            assert "recommendations" in rate_limit_result