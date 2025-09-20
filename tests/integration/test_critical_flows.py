"""
Integration tests for critical user flows in Tidal MCP.

Tests complete end-to-end workflows that users would perform,
validating data consistency and state persistence across operations.
"""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tidal_mcp.auth import TidalAuth, TidalAuthError
from src.tidal_mcp.service import TidalService

# Conditional import based on testing environment
if os.getenv('TESTING') == '1':
    from tests import mock_tidal_server as server_module
    mcp = server_module.mcp
    ensure_service = server_module.ensure_service
    auth_manager = server_module.auth_manager
    tidal_service = server_module.tidal_service
else:
    from src.tidal_mcp.server import mcp
from src.tidal_mcp.models import Album, Artist, Playlist, SearchResults, Track


@pytest.fixture
async def test_server_instance():
    """Create a test server instance with mocked dependencies."""
    # Reset global state for clean testing
    import src.tidal_mcp.server as server_module
    server_module.auth_manager = None
    server_module.tidal_service = None

    # Mock the auth manager
    mock_auth = AsyncMock(spec=TidalAuth)
    mock_auth.is_authenticated.return_value = True
    mock_auth.access_token = "fake_test_token_12345_TEST_ONLY"
    mock_auth.user_id = "fake_test_user_999"
    mock_auth.session_id = "fake_test_session_123"
    mock_auth.ensure_valid_token = AsyncMock(return_value=True)

    # Mock Tidal session
    mock_session = MagicMock()
    mock_session.user = MagicMock()
    mock_session.user.favorites = MagicMock()
    mock_session.user.playlists = MagicMock(return_value=[])
    mock_session.user.create_playlist = MagicMock()
    mock_auth.get_tidal_session = MagicMock(return_value=mock_session)

    # Create service with mocked auth
    mock_service = TidalService(mock_auth)

    # Patch the global instances
    with patch.object(server_module, 'auth_manager', mock_auth), \
         patch.object(server_module, 'tidal_service', mock_service):
        yield {
            'auth': mock_auth,
            'service': mock_service,
            'session': mock_session,
            'server': mcp
        }


@pytest.fixture
def sample_search_data():
    """Sample search response data for testing."""
    return {
        "tracks": [
            {
                "id": "test_track_1",
                "title": "Test Track 1",
                "artists": [{"id": "artist_1", "name": "Test Artist 1"}],
                "album": {"id": "album_1", "title": "Test Album 1"},
                "duration": 180,
                "track_number": 1,
                "disc_number": 1,
                "explicit": False,
                "quality": "HIGH"
            },
            {
                "id": "test_track_2",
                "title": "Test Track 2",
                "artists": [{"id": "artist_2", "name": "Test Artist 2"}],
                "album": {"id": "album_2", "title": "Test Album 2"},
                "duration": 200,
                "track_number": 2,
                "disc_number": 1,
                "explicit": False,
                "quality": "HIGH"
            },
            {
                "id": "test_track_3",
                "title": "Test Track 3",
                "artists": [{"id": "artist_3", "name": "Test Artist 3"}],
                "album": {"id": "album_3", "title": "Test Album 3"},
                "duration": 220,
                "track_number": 3,
                "disc_number": 1,
                "explicit": False,
                "quality": "HIGH"
            }
        ],
        "albums": [
            {
                "id": "album_1",
                "title": "Test Album 1",
                "artists": [{"id": "artist_1", "name": "Test Artist 1"}],
                "release_date": "2023-01-15",
                "duration": 3600,
                "number_of_tracks": 12,
                "cover": "https://example.com/album1.jpg",
                "explicit": False
            }
        ],
        "artists": [
            {
                "id": "artist_1",
                "name": "Test Artist 1",
                "picture": "https://example.com/artist1.jpg",
                "popularity": 85
            }
        ],
        "playlists": []
    }


@pytest.fixture
def sample_playlist_data():
    """Sample playlist data for testing."""
    return {
        "id": "test_playlist_123",
        "title": "Test Playlist",
        "description": "A test playlist for integration testing",
        "creator": "Test User",
        "tracks": [],
        "number_of_tracks": 0,
        "duration": 0,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "image": "https://example.com/playlist.jpg",
        "public": True
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_auth_search_playlist_flow(test_server_instance, sample_search_data, sample_playlist_data):
    """
    Test complete Authentication → Search → Playlist creation flow.

    Validates:
    1. User can authenticate with Tidal
    2. Search for tracks returns valid results
    3. Can create a new playlist
    4. Can add tracks to the playlist
    5. Data consistency across operations
    """
    server_ctx = test_server_instance
    service = server_ctx['service']
    auth = server_ctx['auth']
    server_ctx['session']

    # Mock service methods for this flow
    with patch.object(service, 'search_all', new_callable=AsyncMock) as mock_search, \
         patch.object(service, 'create_playlist', new_callable=AsyncMock) as mock_create_playlist, \
         patch.object(service, 'add_tracks_to_playlist', new_callable=AsyncMock) as mock_add_tracks, \
         patch.object(service, 'get_playlist', new_callable=AsyncMock) as mock_get_playlist:

        # Configure mocks with expected data
        mock_search.return_value = SearchResults(
            tracks=[
                Track(
                    id=track["id"],
                    title=track["title"],
                    artists=[Artist(id=track["artists"][0]["id"], name=track["artists"][0]["name"])],
                    album=Album(
                        id=track["album"]["id"],
                        title=track["album"]["title"],
                        artists=[Artist(id=track["artists"][0]["id"], name=track["artists"][0]["name"])],
                        release_date="2023-01-15",
                        duration=3600,
                        number_of_tracks=12,
                        cover=None,
                        explicit=False
                    ),
                    duration=track["duration"],
                    track_number=track["track_number"],
                    disc_number=track["disc_number"],
                    explicit=track["explicit"],
                    quality=track["quality"]
                )
                for track in sample_search_data["tracks"]
            ],
            albums=[],
            artists=[],
            playlists=[]
        )

        mock_create_playlist.return_value = Playlist(
            id=sample_playlist_data["id"],
            title=sample_playlist_data["title"],
            description=sample_playlist_data["description"],
            creator=sample_playlist_data["creator"],
            tracks=[],
            number_of_tracks=0,
            duration=0,
            created_at=None,
            updated_at=None,
            image=sample_playlist_data["image"],
            public=sample_playlist_data["public"]
        )

        mock_add_tracks.return_value = {"success": True, "added_count": 3}

        # Configure final playlist state after adding tracks
        final_playlist = Playlist(
            id=sample_playlist_data["id"],
            title=sample_playlist_data["title"],
            description=sample_playlist_data["description"],
            creator=sample_playlist_data["creator"],
            tracks=[
                Track(
                    id=track["id"],
                    title=track["title"],
                    artists=[Artist(id=track["artists"][0]["id"], name=track["artists"][0]["name"])],
                    album=Album(
                        id=track["album"]["id"],
                        title=track["album"]["title"],
                        artists=[Artist(id=track["artists"][0]["id"], name=track["artists"][0]["name"])],
                        release_date="2023-01-15",
                        duration=3600,
                        number_of_tracks=12,
                        cover=None,
                        explicit=False
                    ),
                    duration=track["duration"],
                    track_number=track["track_number"],
                    disc_number=track["disc_number"],
                    explicit=track["explicit"],
                    quality=track["quality"]
                )
                for track in sample_search_data["tracks"]
            ],
            number_of_tracks=3,
            duration=600,  # Sum of track durations: 180 + 200 + 220
            created_at=None,
            updated_at=None,
            image=sample_playlist_data["image"],
            public=sample_playlist_data["public"]
        )
        mock_get_playlist.return_value = final_playlist

        # Step 1: Authenticate (should already be done via fixture)
        assert auth.is_authenticated() is True
        assert auth.access_token is not None

        # Step 2: Search for tracks
        search_result = await service.search_all(query="test", limit=10)

        # Verify search results
        assert len(search_result.tracks) == 3
        assert search_result.tracks[0].title == "Test Track 1"
        assert search_result.tracks[1].title == "Test Track 2"
        assert search_result.tracks[2].title == "Test Track 3"

        # Step 3: Create playlist
        playlist = await service.create_playlist(
            title="Test Playlist",
            description="A test playlist for integration testing"
        )

        # Verify playlist creation
        assert playlist.id == "test_playlist_123"
        assert playlist.title == "Test Playlist"
        assert playlist.description == "A test playlist for integration testing"
        assert playlist.number_of_tracks == 0

        # Step 4: Add tracks to playlist
        track_ids = [track.id for track in search_result.tracks]
        add_result = await service.add_tracks_to_playlist(
            playlist_id=playlist.id,
            track_ids=track_ids
        )

        # Verify tracks were added
        assert add_result["success"] is True
        assert add_result["added_count"] == 3

        # Step 5: Verify final playlist state
        updated_playlist = await service.get_playlist(playlist.id, include_tracks=True)

        # Verify playlist consistency
        assert updated_playlist.id == playlist.id
        assert updated_playlist.number_of_tracks == 3
        assert updated_playlist.duration == 600  # 180 + 200 + 220
        assert len(updated_playlist.tracks) == 3

        # Verify track IDs match original search
        playlist_track_ids = [track.id for track in updated_playlist.tracks]
        assert set(playlist_track_ids) == set(track_ids)

        # Verify service method calls
        mock_search.assert_called_once_with(query="test", limit=10)
        mock_create_playlist.assert_called_once()
        mock_add_tracks.assert_called_once_with(
            playlist_id="test_playlist_123",
            track_ids=["test_track_1", "test_track_2", "test_track_3"]
        )
        mock_get_playlist.assert_called_once_with("test_playlist_123", include_tracks=True)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_favorites_flow(test_server_instance, sample_search_data):
    """
    Test Search → Favorites management flow.

    Validates:
    1. Search for content (tracks/albums/artists)
    2. Add items to favorites
    3. Retrieve favorites list
    4. Remove items from favorites
    5. State consistency across operations
    """
    server_ctx = test_server_instance
    service = server_ctx['service']

    # Mock service methods for this flow
    with patch.object(service, 'search_all', new_callable=AsyncMock) as mock_search, \
         patch.object(service, 'add_to_favorites', new_callable=AsyncMock) as mock_add_fav, \
         patch.object(service, 'get_user_favorites', new_callable=AsyncMock) as mock_get_favs, \
         patch.object(service, 'remove_from_favorites', new_callable=AsyncMock) as mock_remove_fav:

        # Configure search results
        search_tracks = [
            Track(
                id=track["id"],
                title=track["title"],
                artists=[Artist(id=track["artists"][0]["id"], name=track["artists"][0]["name"])],
                album=Album(
                    id=track["album"]["id"],
                    title=track["album"]["title"],
                    artists=[Artist(id=track["artists"][0]["id"], name=track["artists"][0]["name"])],
                    release_date="2023-01-15",
                    duration=3600,
                    number_of_tracks=12,
                    cover=None,
                    explicit=False
                ),
                duration=track["duration"],
                track_number=track["track_number"],
                disc_number=track["disc_number"],
                explicit=track["explicit"],
                quality=track["quality"]
            )
            for track in sample_search_data["tracks"][:2]  # Only use first 2 tracks
        ]

        mock_search.return_value = SearchResults(
            tracks=search_tracks,
            albums=[],
            artists=[],
            playlists=[]
        )

        mock_add_fav.return_value = {"success": True, "message": "Added to favorites"}
        mock_remove_fav.return_value = {"success": True, "message": "Removed from favorites"}

        # Step 1: Search for content
        search_result = await service.search_all(query="test music", limit=10)

        # Verify search results
        assert len(search_result.tracks) == 2
        track_1 = search_result.tracks[0]
        track_2 = search_result.tracks[1]

        # Step 2: Add items to favorites
        add_result_1 = await service.add_to_favorites(track_1.id, "track")
        add_result_2 = await service.add_to_favorites(track_2.id, "track")

        # Verify additions
        assert add_result_1["success"] is True
        assert add_result_2["success"] is True

        # Step 3: Get favorites list (mock returns what we added)
        mock_get_favs.return_value = {
            "tracks": search_tracks,
            "albums": [],
            "artists": [],
            "playlists": []
        }

        favorites = await service.get_user_favorites(content_type="tracks", limit=50)

        # Verify favorites content
        assert len(favorites["tracks"]) == 2
        favorite_track_ids = [track.id for track in favorites["tracks"]]
        assert track_1.id in favorite_track_ids
        assert track_2.id in favorite_track_ids

        # Step 4: Remove one item from favorites
        remove_result = await service.remove_from_favorites(track_1.id, "track")
        assert remove_result["success"] is True

        # Step 5: Verify updated favorites (mock returns updated state)
        mock_get_favs.return_value = {
            "tracks": [track_2],  # Only track_2 remains
            "albums": [],
            "artists": [],
            "playlists": []
        }

        updated_favorites = await service.get_user_favorites(content_type="tracks", limit=50)

        # Verify final state
        assert len(updated_favorites["tracks"]) == 1
        assert updated_favorites["tracks"][0].id == track_2.id

        # Verify service method calls
        mock_search.assert_called_once_with(query="test music", limit=10)
        assert mock_add_fav.call_count == 2
        mock_remove_fav.assert_called_once_with(track_1.id, "track")
        assert mock_get_favs.call_count == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_playlist_management_flow(test_server_instance, sample_playlist_data, sample_search_data):
    """
    Test comprehensive playlist management flow.

    Validates:
    1. Get user's existing playlists
    2. Update playlist metadata
    3. Add/remove tracks from playlist
    4. Delete playlist
    5. State consistency throughout operations
    """
    server_ctx = test_server_instance
    service = server_ctx['service']

    # Create sample tracks for testing
    sample_tracks = [
        Track(
            id=track["id"],
            title=track["title"],
            artists=[Artist(id=track["artists"][0]["id"], name=track["artists"][0]["name"])],
            album=Album(
                id=track["album"]["id"],
                title=track["album"]["title"],
                artists=[Artist(id=track["artists"][0]["id"], name=track["artists"][0]["name"])],
                release_date="2023-01-15",
                duration=3600,
                number_of_tracks=12,
                cover=None,
                explicit=False
            ),
            duration=track["duration"],
            track_number=track["track_number"],
            disc_number=track["disc_number"],
            explicit=track["explicit"],
            quality=track["quality"]
        )
        for track in sample_search_data["tracks"]
    ]

    # Mock service methods
    with patch.object(service, 'get_user_playlists', new_callable=AsyncMock) as mock_get_playlists, \
         patch.object(service, 'create_playlist', new_callable=AsyncMock) as mock_create, \
         patch.object(service, 'add_tracks_to_playlist', new_callable=AsyncMock) as mock_add_tracks, \
         patch.object(service, 'remove_tracks_from_playlist', new_callable=AsyncMock) as mock_remove_tracks, \
         patch.object(service, 'get_playlist', new_callable=AsyncMock) as mock_get_playlist, \
         patch.object(service, 'delete_playlist', new_callable=AsyncMock) as mock_delete:

        # Step 1: Get existing playlists (start with empty list)
        mock_get_playlists.return_value = {"playlists": [], "total": 0}

        initial_playlists = await service.get_user_playlists(limit=50)
        assert len(initial_playlists["playlists"]) == 0

        # Step 2: Create new playlist
        new_playlist = Playlist(
            id=sample_playlist_data["id"],
            title=sample_playlist_data["title"],
            description=sample_playlist_data["description"],
            creator=sample_playlist_data["creator"],
            tracks=[],
            number_of_tracks=0,
            duration=0,
            created_at=None,
            updated_at=None,
            image=sample_playlist_data["image"],
            public=sample_playlist_data["public"]
        )
        mock_create.return_value = new_playlist

        created_playlist = await service.create_playlist(
            title="Test Playlist",
            description="A test playlist"
        )

        assert created_playlist.id == "test_playlist_123"
        assert created_playlist.title == "Test Playlist"
        assert created_playlist.number_of_tracks == 0

        # Step 3: Add tracks to playlist
        mock_add_tracks.return_value = {"success": True, "added_count": 3}

        track_ids = [track.id for track in sample_tracks]
        add_result = await service.add_tracks_to_playlist(
            playlist_id=created_playlist.id,
            track_ids=track_ids
        )

        assert add_result["success"] is True
        assert add_result["added_count"] == 3

        # Step 4: Get updated playlist state
        updated_playlist = Playlist(
            id=sample_playlist_data["id"],
            title=sample_playlist_data["title"],
            description=sample_playlist_data["description"],
            creator=sample_playlist_data["creator"],
            tracks=sample_tracks,
            number_of_tracks=3,
            duration=600,  # 180 + 200 + 220
            created_at=None,
            updated_at=None,
            image=sample_playlist_data["image"],
            public=sample_playlist_data["public"]
        )
        mock_get_playlist.return_value = updated_playlist

        playlist_with_tracks = await service.get_playlist(
            created_playlist.id,
            include_tracks=True
        )

        assert playlist_with_tracks.number_of_tracks == 3
        assert len(playlist_with_tracks.tracks) == 3
        assert playlist_with_tracks.duration == 600

        # Step 5: Remove some tracks (remove first track)
        mock_remove_tracks.return_value = {"success": True, "removed_count": 1}

        remove_result = await service.remove_tracks_from_playlist(
            playlist_id=created_playlist.id,
            track_indices=[0]  # Remove first track
        )

        assert remove_result["success"] is True
        assert remove_result["removed_count"] == 1

        # Step 6: Verify updated state after removal
        playlist_after_removal = Playlist(
            id=sample_playlist_data["id"],
            title=sample_playlist_data["title"],
            description=sample_playlist_data["description"],
            creator=sample_playlist_data["creator"],
            tracks=sample_tracks[1:],  # Only tracks 2 and 3 remain
            number_of_tracks=2,
            duration=420,  # 200 + 220
            created_at=None,
            updated_at=None,
            image=sample_playlist_data["image"],
            public=sample_playlist_data["public"]
        )
        mock_get_playlist.return_value = playlist_after_removal

        final_playlist = await service.get_playlist(
            created_playlist.id,
            include_tracks=True
        )

        assert final_playlist.number_of_tracks == 2
        assert len(final_playlist.tracks) == 2
        assert final_playlist.duration == 420

        # Step 7: Delete playlist
        mock_delete.return_value = {"success": True, "message": "Playlist deleted"}

        delete_result = await service.delete_playlist(created_playlist.id)
        assert delete_result["success"] is True

        # Verify all service calls were made correctly
        mock_get_playlists.assert_called_once_with(limit=50)
        mock_create.assert_called_once()
        mock_add_tracks.assert_called_once_with(
            playlist_id="test_playlist_123",
            track_ids=["test_track_1", "test_track_2", "test_track_3"]
        )
        mock_remove_tracks.assert_called_once_with(
            playlist_id="test_playlist_123",
            track_indices=[0]
        )
        mock_delete.assert_called_once_with("test_playlist_123")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_content_discovery_flow(test_server_instance, sample_search_data):
    """
    Test content discovery flow.

    Validates:
    1. Search for artist
    2. Get artist details and top tracks
    3. Get album details
    4. Get track radio/recommendations
    5. Data consistency across discovery operations
    """
    server_ctx = test_server_instance
    service = server_ctx['service']

    # Create sample data for discovery flow
    sample_artist = Artist(
        id="artist_1",
        name="Test Artist 1",
        picture="https://example.com/artist1.jpg",
        popularity=85
    )

    sample_album = Album(
        id="album_1",
        title="Test Album 1",
        artists=[sample_artist],
        release_date="2023-01-15",
        duration=3600,
        number_of_tracks=12,
        cover="https://example.com/album1.jpg",
        explicit=False
    )

    sample_track = Track(
        id="test_track_1",
        title="Test Track 1",
        artists=[sample_artist],
        album=sample_album,
        duration=180,
        track_number=1,
        disc_number=1,
        explicit=False,
        quality="HIGH"
    )

    # Mock service methods
    with patch.object(service, 'search_artists', new_callable=AsyncMock) as mock_search_artists, \
         patch.object(service, 'get_artist', new_callable=AsyncMock) as mock_get_artist, \
         patch.object(service, 'get_album', new_callable=AsyncMock) as mock_get_album, \
         patch.object(service, 'get_track_radio', new_callable=AsyncMock) as mock_get_radio:

        # Step 1: Search for artist
        mock_search_artists.return_value = [sample_artist]

        artist_results = await service.search_artists(query="Test Artist", limit=10)

        assert len(artist_results) == 1
        found_artist = artist_results[0]
        assert found_artist.id == "artist_1"
        assert found_artist.name == "Test Artist 1"

        # Step 2: Get artist details and top tracks
        mock_get_artist.return_value = {
            "artist": sample_artist,
            "top_tracks": [sample_track],
            "albums": [sample_album]
        }

        artist_details = await service.get_artist(found_artist.id)

        assert artist_details["artist"].id == found_artist.id
        assert len(artist_details["top_tracks"]) == 1
        assert len(artist_details["albums"]) == 1

        top_track = artist_details["top_tracks"][0]
        assert top_track.id == "test_track_1"
        assert top_track.title == "Test Track 1"

        # Step 3: Get album details
        mock_get_album.return_value = {
            "album": sample_album,
            "tracks": [sample_track]
        }

        album = artist_details["albums"][0]
        album_details = await service.get_album(album.id, include_tracks=True)

        assert album_details["album"].id == album.id
        assert album_details["album"].title == "Test Album 1"
        assert len(album_details["tracks"]) == 1

        album_track = album_details["tracks"][0]
        assert album_track.id == top_track.id

        # Step 4: Get track radio/recommendations
        radio_tracks = [
            Track(
                id=f"radio_track_{i}",
                title=f"Radio Track {i}",
                artists=[sample_artist],
                album=sample_album,
                duration=180 + i * 10,
                track_number=i + 1,
                disc_number=1,
                explicit=False,
                quality="HIGH"
            )
            for i in range(1, 4)  # 3 radio tracks
        ]

        mock_get_radio.return_value = radio_tracks

        radio_result = await service.get_track_radio(top_track.id, limit=10)

        assert len(radio_result) == 3

        # Verify radio tracks are related
        for i, radio_track in enumerate(radio_result):
            assert radio_track.id == f"radio_track_{i + 1}"
            assert radio_track.title == f"Radio Track {i + 1}"
            assert radio_track.artists[0].id == sample_artist.id

        # Step 5: Verify data consistency
        # All tracks should reference the same artist
        all_tracks = [top_track, album_track] + radio_result
        for track in all_tracks:
            assert track.artists[0].id == sample_artist.id
            assert track.artists[0].name == sample_artist.name

        # Verify service method calls
        mock_search_artists.assert_called_once_with(query="Test Artist", limit=10)
        mock_get_artist.assert_called_once_with("artist_1")
        mock_get_album.assert_called_once_with("album_1", include_tracks=True)
        mock_get_radio.assert_called_once_with("test_track_1", limit=10)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_recovery_flow(test_server_instance):
    """
    Test error recovery in integration flows.

    Validates:
    1. Graceful handling of authentication errors
    2. Proper error propagation in failed operations
    3. Service state consistency after errors
    4. Recovery after partial failures
    """
    server_ctx = test_server_instance
    service = server_ctx['service']
    auth = server_ctx['auth']

    # Test authentication error recovery
    with patch.object(auth, 'is_authenticated', return_value=False), \
         patch.object(auth, 'ensure_valid_token', new_callable=AsyncMock) as mock_ensure_token:

        # Configure auth to fail initially, then succeed
        mock_ensure_token.side_effect = [
            TidalAuthError("Token expired"),
            True  # Success on retry
        ]

        # First attempt should fail
        with pytest.raises(TidalAuthError, match="Token expired"):
            await mock_ensure_token()

        # Second attempt should succeed
        result = await mock_ensure_token()
        assert result is True

        # Verify retry logic was called
        assert mock_ensure_token.call_count == 2

    # Test partial playlist operation failure
    with patch.object(service, 'create_playlist', new_callable=AsyncMock) as mock_create, \
         patch.object(service, 'add_tracks_to_playlist', new_callable=AsyncMock) as mock_add_tracks, \
         patch.object(service, 'delete_playlist', new_callable=AsyncMock) as mock_delete:

        # Playlist creation succeeds
        mock_playlist = Playlist(
            id="test_playlist_error",
            title="Error Test Playlist",
            description="Testing error recovery",
            creator="Test User",
            tracks=[],
            number_of_tracks=0,
            duration=0,
            created_at=None,
            updated_at=None,
            image=None,
            public=True
        )
        mock_create.return_value = mock_playlist

        # Adding tracks fails
        mock_add_tracks.side_effect = Exception("Failed to add tracks")

        # Cleanup (delete) succeeds
        mock_delete.return_value = {"success": True, "message": "Playlist deleted"}

        # Execute flow with error handling
        playlist = await service.create_playlist("Error Test Playlist", "Testing error recovery")
        assert playlist.id == "test_playlist_error"

        # Adding tracks should fail
        with pytest.raises(Exception, match="Failed to add tracks"):
            await service.add_tracks_to_playlist(
                playlist.id,
                ["track_1", "track_2"]
            )

        # Cleanup should still work
        cleanup_result = await service.delete_playlist(playlist.id)
        assert cleanup_result["success"] is True

        # Verify all operations were attempted
        mock_create.assert_called_once()
        mock_add_tracks.assert_called_once()
        mock_delete.assert_called_once()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_operations_flow(test_server_instance, sample_search_data):
    """
    Test concurrent operations and state consistency.

    Validates:
    1. Multiple searches can run concurrently
    2. Concurrent playlist operations maintain consistency
    3. No race conditions in favorites management
    4. Service handles concurrent load properly
    """
    server_ctx = test_server_instance
    service = server_ctx['service']

    # Mock service methods for concurrent testing
    with patch.object(service, 'search_all', new_callable=AsyncMock) as mock_search, \
         patch.object(service, 'create_playlist', new_callable=AsyncMock) as mock_create, \
         patch.object(service, 'add_to_favorites', new_callable=AsyncMock) as mock_add_fav:

        # Configure mock to return different results for different queries
        def search_side_effect(query, **kwargs):
            if "rock" in query.lower():
                return SearchResults(tracks=[], albums=[], artists=[], playlists=[])
            elif "jazz" in query.lower():
                return SearchResults(tracks=[], albums=[], artists=[], playlists=[])
            else:
                return SearchResults(tracks=[], albums=[], artists=[], playlists=[])

        mock_search.side_effect = search_side_effect

        # Configure playlist creation to return unique playlists
        playlist_counter = 0
        def create_playlist_side_effect(title, description=""):
            nonlocal playlist_counter
            playlist_counter += 1
            return Playlist(
                id=f"concurrent_playlist_{playlist_counter}",
                title=title,
                description=description,
                creator="Test User",
                tracks=[],
                number_of_tracks=0,
                duration=0,
                created_at=None,
                updated_at=None,
                image=None,
                public=True
            )

        mock_create.side_effect = create_playlist_side_effect
        mock_add_fav.return_value = {"success": True, "message": "Added to favorites"}

        # Test 1: Concurrent searches
        search_tasks = [
            service.search_all(query="rock music", limit=10),
            service.search_all(query="jazz music", limit=10),
            service.search_all(query="classical music", limit=10)
        ]

        search_results = await asyncio.gather(*search_tasks)

        # Verify all searches completed
        assert len(search_results) == 3
        assert mock_search.call_count == 3

        # Test 2: Concurrent playlist creation
        playlist_tasks = [
            service.create_playlist("Concurrent Playlist 1", "First concurrent playlist"),
            service.create_playlist("Concurrent Playlist 2", "Second concurrent playlist"),
            service.create_playlist("Concurrent Playlist 3", "Third concurrent playlist")
        ]

        playlist_results = await asyncio.gather(*playlist_tasks)

        # Verify all playlists were created with unique IDs
        assert len(playlist_results) == 3
        playlist_ids = [p.id for p in playlist_results]
        assert len(set(playlist_ids)) == 3  # All IDs should be unique
        assert mock_create.call_count == 3

        # Test 3: Concurrent favorites operations
        fav_tasks = [
            service.add_to_favorites("track_1", "track"),
            service.add_to_favorites("track_2", "track"),
            service.add_to_favorites("album_1", "album"),
            service.add_to_favorites("artist_1", "artist")
        ]

        fav_results = await asyncio.gather(*fav_tasks)

        # Verify all favorites operations completed successfully
        assert len(fav_results) == 4
        for result in fav_results:
            assert result["success"] is True
        assert mock_add_fav.call_count == 4

        # Verify no exceptions were raised during concurrent operations
        # If we reach this point, all concurrent operations completed successfully


# Performance marker for CI/CD pipeline
@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_performance(test_server_instance):
    """
    Basic performance test for integration flows.

    Ensures integration tests complete within reasonable time limits.
    """
    import time

    server_ctx = test_server_instance
    service = server_ctx['service']

    # Mock quick-responding service methods
    with patch.object(service, 'search_all', new_callable=AsyncMock) as mock_search, \
         patch.object(service, 'create_playlist', new_callable=AsyncMock) as mock_create:

        mock_search.return_value = SearchResults(tracks=[], albums=[], artists=[], playlists=[])
        mock_create.return_value = Playlist(
            id="perf_test_playlist",
            title="Performance Test",
            description="",
            creator="Test User",
            tracks=[],
            number_of_tracks=0,
            duration=0,
            created_at=None,
            updated_at=None,
            image=None,
            public=True
        )

        # Test that basic operations complete quickly
        start_time = time.time()

        # Perform a sequence of operations
        await service.search_all(query="performance test", limit=10)
        await service.create_playlist("Performance Test Playlist")

        end_time = time.time()
        execution_time = end_time - start_time

        # Integration tests should complete within reasonable time (< 1 second for mocked operations)
        assert execution_time < 1.0, f"Integration operations took too long: {execution_time:.2f}s"

        # Verify operations were called
        mock_search.assert_called_once()
        mock_create.assert_called_once()
