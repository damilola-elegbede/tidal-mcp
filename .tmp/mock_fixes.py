# Critical fixes for conftest.py mocking issues

# Fix 1: Replace TidalAuth() with AsyncMock
mock_auth_fix = '''
@pytest.fixture
def mock_auth(mock_env_vars, mock_tidal_session):
    """Create mock TidalAuth instance with secure fake credentials."""
    import uuid
    fake_uuid = uuid.uuid4().hex

    # Create a proper AsyncMock instead of real object
    mock_auth = AsyncMock(spec=TidalAuth)
    mock_auth.tidal_session = mock_tidal_session
    mock_auth.access_token = f"fake_auth_token_{fake_uuid[:16]}_TEST_ONLY"
    mock_auth.refresh_token = f"fake_refresh_token_{fake_uuid[16:32]}_TEST_ONLY"
    mock_auth.token_expires_at = datetime.now() + timedelta(hours=1)
    mock_auth.user_id = "999999999"  # Obviously fake user ID
    mock_auth.session_id = f"fake_auth_session_{fake_uuid[:8]}_TEST"

    # Mock common auth methods with proper AsyncMock
    mock_auth.ensure_valid_token = AsyncMock()
    mock_auth.get_tidal_session = AsyncMock(return_value=mock_tidal_session)
    mock_auth.get_user_info = AsyncMock()

    return mock_auth
'''

# Fix 2: Replace TidalService(mock_auth) with AsyncMock
mock_service_fix = '''
@pytest.fixture
def mock_service(mock_auth):
    """Create mock TidalService instance."""
    # Create a proper AsyncMock instead of real object
    mock_service = AsyncMock(spec=TidalService)
    mock_service.auth = mock_auth
    mock_service._cache = {}
    mock_service._cache_ttl = 300

    # Mock common service methods as AsyncMock
    mock_service.ensure_authenticated = AsyncMock()
    mock_service.get_session = Mock(return_value=mock_auth.get_tidal_session.return_value)
    mock_service.search_tracks = AsyncMock()
    mock_service.search_albums = AsyncMock()
    mock_service.search_artists = AsyncMock()
    mock_service.search_playlists = AsyncMock()
    mock_service.search_all = AsyncMock()
    mock_service.get_track = AsyncMock()
    mock_service.get_album = AsyncMock()
    mock_service.get_artist = AsyncMock()
    mock_service.get_playlist = AsyncMock()
    mock_service.create_playlist = AsyncMock()
    mock_service.add_tracks_to_playlist = AsyncMock()
    mock_service.remove_tracks_from_playlist = AsyncMock()
    mock_service.delete_playlist = AsyncMock()
    mock_service.get_user_favorites = AsyncMock()
    mock_service.add_to_favorites = AsyncMock()
    mock_service.remove_from_favorites = AsyncMock()
    mock_service.get_track_radio = AsyncMock()
    mock_service.get_artist_radio = AsyncMock()
    mock_service.get_recommended_tracks = AsyncMock()
    mock_service.get_user_profile = AsyncMock()
    mock_service._convert_tidal_track = AsyncMock()
    mock_service._convert_tidal_album = AsyncMock()
    mock_service._convert_tidal_artist = AsyncMock()
    mock_service._convert_tidal_playlist = AsyncMock()
    mock_service._is_uuid = Mock()

    return mock_service
'''

print("Mocking fixes documented for manual application")
