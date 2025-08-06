"""
Tests for Tidal Authentication Module

Comprehensive unit tests for the TidalAuth class covering OAuth2 PKCE flow,
token management, session handling, and error scenarios.
"""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock, mock_open, PropertyMock
from datetime import datetime, timedelta
from aiohttp import web
import aiohttp
import tidalapi

from tidal_mcp.auth import TidalAuth, TidalAuthError


@pytest.fixture
def temp_session_file():
    """Create a temporary session file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    yield temp_path
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def mock_tidal_session():
    """Create a mock tidalapi session."""
    session = Mock(spec=tidalapi.Session)
    user = Mock()
    user.id = 12345
    user.country_code = 'US'
    user.username = 'testuser'
    user.subscription = {'type': 'HiFi', 'valid': True}
    session.user = user
    session.load_oauth_session.return_value = True
    return session


class TestTidalAuth:
    """Test cases for TidalAuth class."""
    
    @pytest.fixture
    def auth(self, temp_session_file):
        """Create TidalAuth instance for testing."""
        with patch.object(Path, 'home') as mock_home:
            mock_home.return_value = temp_session_file.parent
            auth = TidalAuth(client_id="test_client", client_secret="test_secret")
            auth.session_file = temp_session_file
            return auth
    
    def test_init_default_client_id(self):
        """Test TidalAuth initialization with default client ID."""
        with patch.object(Path, 'home'):
            auth = TidalAuth()
            assert auth.client_id == TidalAuth.CLIENT_ID
            assert auth.client_secret is None
    
    def test_init_custom_credentials(self, temp_session_file):
        """Test TidalAuth initialization with custom credentials."""
        with patch.object(Path, 'home') as mock_home:
            mock_home.return_value = temp_session_file.parent
            auth = TidalAuth(client_id="custom_client", client_secret="custom_secret")
            assert auth.client_id == "custom_client"
            assert auth.client_secret == "custom_secret"
            assert auth.access_token is None
            assert auth.refresh_token is None
            assert auth.token_expires_at is None
            assert auth.country_code == "US"
    
    def test_is_authenticated_no_token(self, auth):
        """Test is_authenticated returns False when no token."""
        assert not auth.is_authenticated()
    
    def test_is_authenticated_expired_token(self, auth):
        """Test is_authenticated returns False for expired token."""
        auth.access_token = "test_token"
        auth.token_expires_at = datetime.now() - timedelta(minutes=1)
        assert not auth.is_authenticated()
    
    def test_is_authenticated_valid_token_no_session(self, auth):
        """Test is_authenticated returns False for valid token but no session."""
        auth.access_token = "test_token"
        auth.token_expires_at = datetime.now() + timedelta(hours=1)
        auth.tidal_session = None
        assert not auth.is_authenticated()
    
    def test_is_authenticated_valid_token_with_session(self, auth, mock_tidal_session):
        """Test is_authenticated returns True for valid token with session."""
        auth.access_token = "test_token"
        auth.token_expires_at = datetime.now() + timedelta(hours=1)
        auth.tidal_session = mock_tidal_session
        assert auth.is_authenticated()
    
    def test_is_authenticated_session_error(self, auth, mock_tidal_session):
        """Test is_authenticated handles session errors gracefully."""
        auth.access_token = "test_token"
        auth.token_expires_at = datetime.now() + timedelta(hours=1)
        auth.tidal_session = mock_tidal_session
        mock_tidal_session.user = None  # Simulate session error
        
        assert not auth.is_authenticated()
    
    def test_generate_pkce_params(self, auth):
        """Test PKCE parameter generation."""
        code_verifier, code_challenge = auth._generate_pkce_params()
        
        # Verify code verifier format (base64url without padding)
        assert len(code_verifier) == 43  # 32 bytes base64url encoded
        assert all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_' for c in code_verifier)
        
        # Verify code challenge format
        assert len(code_challenge) == 43  # SHA256 hash base64url encoded
        assert all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_' for c in code_challenge)
        
        # Generate again to ensure randomness
        code_verifier2, code_challenge2 = auth._generate_pkce_params()
        assert code_verifier != code_verifier2
        assert code_challenge != code_challenge2
    
    @pytest.mark.asyncio
    async def test_authenticate_existing_session(self, auth, mock_tidal_session):
        """Test authentication with existing valid session."""
        auth.access_token = "existing_token"
        auth.refresh_token = "existing_refresh"
        
        with patch.object(auth, '_try_existing_session', new_callable=AsyncMock, return_value=True) as mock_existing:
            result = await auth.authenticate()
            assert result is True
            mock_existing.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticate_oauth_flow(self, auth):
        """Test authentication with OAuth2 flow."""
        with patch.object(auth, '_try_existing_session', new_callable=AsyncMock, return_value=False), \
             patch.object(auth, '_oauth2_flow', new_callable=AsyncMock, return_value=True) as mock_oauth:
            
            result = await auth.authenticate()
            assert result is True
            mock_oauth.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticate_failure(self, auth):
        """Test authentication failure handling."""
        with patch.object(auth, '_try_existing_session', new_callable=AsyncMock, side_effect=Exception("Auth failed")):
            result = await auth.authenticate()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_try_existing_session_no_token(self, auth):
        """Test trying existing session without token."""
        result = await auth._try_existing_session()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_try_existing_session_success(self, auth, mock_tidal_session):
        """Test successful existing session load."""
        auth.access_token = "valid_token"
        auth.refresh_token = "valid_refresh"
        
        with patch('tidalapi.Session', return_value=mock_tidal_session):
            result = await auth._try_existing_session()
            assert result is True
            assert auth.tidal_session == mock_tidal_session
            assert auth.user_id == "12345"
            assert auth.country_code == "US"
    
    @pytest.mark.asyncio
    async def test_try_existing_session_invalid_token(self, auth):
        """Test existing session with invalid token."""
        auth.access_token = "invalid_token"
        auth.refresh_token = "invalid_refresh"
        
        mock_session = Mock(spec=tidalapi.Session)
        mock_session.load_oauth_session.return_value = False
        
        with patch('tidalapi.Session', return_value=mock_session):
            result = await auth._try_existing_session()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_success(self, auth, mock_tidal_session):
        """Test successful token exchange."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token',
            'expires_in': 3600
        })
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session), \
             patch('tidalapi.Session', return_value=mock_tidal_session), \
             patch.object(auth, '_save_session') as mock_save:
            
            result = await auth._exchange_code_for_tokens('auth_code', 'code_verifier')
            assert result is True
            assert auth.access_token == 'new_access_token'
            assert auth.refresh_token == 'new_refresh_token'
            assert auth.user_id == "12345"
            mock_save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_failure(self, auth):
        """Test token exchange failure."""
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value='Invalid grant')
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await auth._exchange_code_for_tokens('invalid_code', 'code_verifier')
            assert result is False
    
    @pytest.mark.asyncio
    async def test_refresh_access_token_no_refresh_token(self, auth):
        """Test token refresh without refresh token."""
        result = await auth.refresh_access_token()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, auth, mock_tidal_session):
        """Test successful token refresh."""
        auth.refresh_token = "refresh_token"
        auth.tidal_session = mock_tidal_session
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token',
            'expires_in': 3600
        })
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session), \
             patch.object(auth, '_save_session') as mock_save:
            
            result = await auth.refresh_access_token()
            assert result is True
            assert auth.access_token == 'new_access_token'
            assert auth.refresh_token == 'new_refresh_token'
            mock_tidal_session.load_oauth_session.assert_called_with(
                token_type='Bearer',
                access_token='new_access_token',
                refresh_token='new_refresh_token'
            )
            mock_save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_refresh_access_token_failure(self, auth):
        """Test token refresh failure."""
        auth.refresh_token = "invalid_refresh_token"
        
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value='Invalid refresh token')
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await auth.refresh_access_token()
            assert result is False
    
    def test_get_auth_headers_no_token(self, auth):
        """Test get_auth_headers raises error without token."""
        with pytest.raises(ValueError, match="No access token available"):
            auth.get_auth_headers()
    
    def test_get_auth_headers_with_token(self, auth):
        """Test get_auth_headers returns proper headers."""
        auth.access_token = "test_token"
        headers = auth.get_auth_headers()
        
        assert headers["Authorization"] == "Bearer test_token"
        assert headers["X-Tidal-Token"] == "test_token"
    
    def test_get_tidal_session_not_authenticated(self, auth):
        """Test get_tidal_session raises error when not authenticated."""
        with pytest.raises(TidalAuthError, match="Not authenticated"):
            auth.get_tidal_session()
    
    def test_get_tidal_session_success(self, auth, mock_tidal_session):
        """Test get_tidal_session returns session when authenticated."""
        auth.access_token = "test_token"
        auth.token_expires_at = datetime.now() + timedelta(hours=1)
        auth.tidal_session = mock_tidal_session
        
        session = auth.get_tidal_session()
        assert session == mock_tidal_session
    
    @pytest.mark.asyncio
    async def test_ensure_valid_token_authenticated(self, auth, mock_tidal_session):
        """Test ensure_valid_token when already authenticated."""
        auth.access_token = "test_token"
        auth.token_expires_at = datetime.now() + timedelta(hours=1)
        auth.tidal_session = mock_tidal_session
        
        result = await auth.ensure_valid_token()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_ensure_valid_token_refresh_needed(self, auth):
        """Test ensure_valid_token triggers refresh when needed."""
        auth.refresh_token = "refresh_token"
        
        with patch.object(auth, 'refresh_access_token', new_callable=AsyncMock) as mock_refresh:
            mock_refresh.return_value = True
            
            result = await auth.ensure_valid_token()
            assert result is True
            mock_refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ensure_valid_token_reauth_needed(self, auth):
        """Test ensure_valid_token triggers re-authentication when needed."""
        with patch.object(auth, 'authenticate', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = True
            
            result = await auth.ensure_valid_token()
            assert result is True
            mock_auth.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ensure_valid_token_refresh_failure(self, auth):
        """Test ensure_valid_token when refresh fails."""
        auth.refresh_token = "refresh_token"
        
        with patch.object(auth, 'refresh_access_token', new_callable=AsyncMock, return_value=False), \
             patch.object(auth, 'authenticate', new_callable=AsyncMock, return_value=True) as mock_auth:
            
            result = await auth.ensure_valid_token()
            assert result is True
            mock_auth.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_logout(self, auth):
        """Test logout clears all tokens and session data."""
        auth.access_token = "test_token"
        auth.refresh_token = "refresh_token"
        auth.session_id = "session_id"
        auth.user_id = "12345"
        
        with patch.object(auth, '_revoke_tokens', new_callable=AsyncMock), \
             patch.object(auth, '_clear_session_file') as mock_clear:
            
            await auth.logout()
            
            assert auth.access_token is None
            assert auth.refresh_token is None
            assert auth.session_id is None
            assert auth.user_id is None
            assert auth.tidal_session is None
            mock_clear.assert_called_once()
    
    def test_get_user_info_not_authenticated(self, auth):
        """Test get_user_info when not authenticated."""
        result = auth.get_user_info()
        assert result is None
    
    def test_get_user_info_success(self, auth, mock_tidal_session):
        """Test get_user_info returns user data."""
        auth.access_token = "test_token"
        auth.token_expires_at = datetime.now() + timedelta(hours=1)
        auth.tidal_session = mock_tidal_session
        
        result = auth.get_user_info()
        assert result is not None
        assert result['id'] == 12345
        assert result['country_code'] == 'US'
        assert result['subscription']['type'] == 'HiFi'
        assert result['subscription']['valid'] is True


class TestSessionManagement:
    """Test session file management."""
    
    @pytest.fixture
    def auth_with_session(self, temp_session_file):
        """Create auth instance with session file."""
        with patch.object(Path, 'home') as mock_home:
            mock_home.return_value = temp_session_file.parent
            auth = TidalAuth()
            auth.session_file = temp_session_file
            return auth
    
    def test_save_session(self, auth_with_session):
        """Test saving session to file."""
        auth_with_session.access_token = "test_token"
        auth_with_session.refresh_token = "refresh_token"
        auth_with_session.user_id = "12345"
        auth_with_session.country_code = "US"
        auth_with_session.token_expires_at = datetime.now() + timedelta(hours=1)
        
        with patch('os.chmod') as mock_chmod:
            auth_with_session._save_session()
            
            # Verify file was created and contains expected data
            assert auth_with_session.session_file.exists()
            with open(auth_with_session.session_file, 'r') as f:
                data = json.load(f)
                assert data['access_token'] == "test_token"
                assert data['refresh_token'] == "refresh_token"
                assert data['user_id'] == "12345"
                assert data['country_code'] == "US"
            
            # Verify permissions were set
            mock_chmod.assert_called_once_with(auth_with_session.session_file, 0o600)
    
    def test_load_session_success(self, auth_with_session):
        """Test loading session from file."""
        session_data = {
            'access_token': 'saved_token',
            'refresh_token': 'saved_refresh',
            'user_id': '12345',
            'country_code': 'US',
            'expires_at': (datetime.now() + timedelta(hours=1)).isoformat()
        }
        
        with open(auth_with_session.session_file, 'w') as f:
            json.dump(session_data, f)
        
        auth_with_session._load_session()
        
        assert auth_with_session.access_token == 'saved_token'
        assert auth_with_session.refresh_token == 'saved_refresh'
        assert auth_with_session.user_id == '12345'
        assert auth_with_session.country_code == 'US'
    
    def test_load_session_missing_file(self, auth_with_session):
        """Test loading session when file doesn't exist."""
        # Ensure file doesn't exist
        if auth_with_session.session_file.exists():
            auth_with_session.session_file.unlink()
        
        auth_with_session._load_session()
        
        # Should not crash, tokens should remain None
        assert auth_with_session.access_token is None
        assert auth_with_session.refresh_token is None
    
    def test_load_session_corrupted(self, auth_with_session):
        """Test loading corrupted session file."""
        with open(auth_with_session.session_file, 'w') as f:
            f.write("invalid json")
        
        with patch.object(auth_with_session, '_clear_session_file') as mock_clear:
            auth_with_session._load_session()
            mock_clear.assert_called_once()
    
    def test_clear_session_file(self, auth_with_session):
        """Test clearing session file."""
        # Create a session file
        with open(auth_with_session.session_file, 'w') as f:
            f.write("{}")
        
        assert auth_with_session.session_file.exists()
        auth_with_session._clear_session_file()
        assert not auth_with_session.session_file.exists()
    
    def test_clear_session_file_not_exists(self, auth_with_session):
        """Test clearing session file that doesn't exist."""
        # Ensure file doesn't exist
        if auth_with_session.session_file.exists():
            auth_with_session.session_file.unlink()
        
        # Should not raise exception
        auth_with_session._clear_session_file()


class TestOAuth2Flow:
    """Test OAuth2 PKCE flow components."""
    
    @pytest.fixture
    def auth(self, temp_session_file):
        """Create auth instance for OAuth2 testing."""
        with patch.object(Path, 'home') as mock_home:
            mock_home.return_value = temp_session_file.parent
            auth = TidalAuth()
            auth.session_file = temp_session_file
            return auth
    
    @pytest.mark.asyncio
    async def test_oauth2_flow_success(self, auth, mock_tidal_session):
        """Test complete OAuth2 flow success."""
        with patch.object(auth, '_capture_auth_code', new_callable=AsyncMock, return_value='auth_code'), \
             patch.object(auth, '_exchange_code_for_tokens', new_callable=AsyncMock, return_value=True), \
             patch('webbrowser.open') as mock_browser:
            
            result = await auth._oauth2_flow()
            assert result is True
            mock_browser.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_oauth2_flow_no_auth_code(self, auth):
        """Test OAuth2 flow when no auth code is captured."""
        with patch.object(auth, '_capture_auth_code', new_callable=AsyncMock, return_value=None), \
             patch('webbrowser.open'):
            
            result = await auth._oauth2_flow()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_oauth2_flow_token_exchange_fails(self, auth):
        """Test OAuth2 flow when token exchange fails."""
        with patch.object(auth, '_capture_auth_code', new_callable=AsyncMock, return_value='auth_code'), \
             patch.object(auth, '_exchange_code_for_tokens', new_callable=AsyncMock, return_value=False), \
             patch('webbrowser.open'):
            
            result = await auth._oauth2_flow()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_capture_auth_code_timeout(self, auth):
        """Test auth code capture timeout."""
        # Mock the web server components
        mock_app = Mock()
        mock_runner = AsyncMock()
        mock_site = AsyncMock()
        
        with patch('aiohttp.web.Application', return_value=mock_app), \
             patch('aiohttp.web.AppRunner', return_value=mock_runner), \
             patch('aiohttp.web.TCPSite', return_value=mock_site), \
             patch('asyncio.sleep', side_effect=[None] * 301):  # Simulate timeout
            
            # Set a very short timeout for testing
            auth_code = await auth._capture_auth_code()
            assert auth_code is None


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.fixture
    def auth(self, temp_session_file):
        """Create auth instance for error testing."""
        with patch.object(Path, 'home') as mock_home:
            mock_home.return_value = temp_session_file.parent
            auth = TidalAuth()
            auth.session_file = temp_session_file
            return auth
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, auth):
        """Test handling of network errors during token operations."""
        auth.refresh_token = "refresh_token"
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            mock_session.post.side_effect = aiohttp.ClientError("Network error")
            
            result = await auth.refresh_access_token()
            assert result is False
    
    def test_invalid_session_file_permissions(self, auth):
        """Test handling of session file permission errors."""
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            auth._load_session()
            # Should not raise exception, just log warning
    
    def test_save_session_permission_error(self, auth):
        """Test handling of permission errors when saving session."""
        auth.access_token = "test_token"
        
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            auth._save_session()
            # Should not raise exception, just log error
    
    def test_tidal_auth_error_custom_exception(self):
        """Test TidalAuthError custom exception."""
        error = TidalAuthError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    @pytest.mark.asyncio
    async def test_authenticate_exception_handling(self, auth):
        """Test exception handling in authenticate method."""
        with patch.object(auth, '_try_existing_session', side_effect=Exception("Unexpected error")):
            result = await auth.authenticate()
            assert result is False
    
    def test_get_user_info_exception_handling(self, auth, mock_tidal_session):
        """Test exception handling in get_user_info."""
        auth.access_token = "test_token"
        auth.token_expires_at = datetime.now() + timedelta(hours=1)
        auth.tidal_session = mock_tidal_session
        
        # Make user property raise an exception
        type(mock_tidal_session).user = PropertyMock(side_effect=Exception("User fetch failed"))
        
        result = auth.get_user_info()
        assert result is None


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.fixture
    def auth(self, temp_session_file):
        """Create auth instance for edge case testing."""
        with patch.object(Path, 'home') as mock_home:
            mock_home.return_value = temp_session_file.parent
            auth = TidalAuth()
            auth.session_file = temp_session_file
            return auth
    
    def test_token_expiry_boundary(self, auth, mock_tidal_session):
        """Test token expiry at exact boundary."""
        auth.access_token = "test_token"
        auth.token_expires_at = datetime.now()  # Expires exactly now
        auth.tidal_session = mock_tidal_session
        
        # Should return False as token is expired/expiring
        assert not auth.is_authenticated()
    
    @pytest.mark.asyncio
    async def test_refresh_token_rotation(self, auth, mock_tidal_session):
        """Test refresh token rotation handling."""
        auth.refresh_token = "old_refresh_token"
        auth.tidal_session = mock_tidal_session
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token',  # New refresh token
            'expires_in': 3600
        })
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session), \
             patch.object(auth, '_save_session'):
            
            result = await auth.refresh_access_token()
            assert result is True
            assert auth.refresh_token == 'new_refresh_token'
    
    @pytest.mark.asyncio
    async def test_refresh_no_new_refresh_token(self, auth, mock_tidal_session):
        """Test refresh when no new refresh token is provided."""
        old_refresh = "old_refresh_token"
        auth.refresh_token = old_refresh
        auth.tidal_session = mock_tidal_session
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'access_token': 'new_access_token',
            # No refresh_token in response
            'expires_in': 3600
        })
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session), \
             patch.object(auth, '_save_session'):
            
            result = await auth.refresh_access_token()
            assert result is True
            assert auth.refresh_token == old_refresh  # Should keep old refresh token


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])