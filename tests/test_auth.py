"""

Comprehensive tests for Tidal Authentication Module

Tests OAuth2 flows, session management, token handling, and security features.
Focuses on achieving high coverage while maintaining security standards.
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tidal_mcp.auth import TidalAuth, TidalAuthError


class TestTidalAuthInitialization:
    """Test TidalAuth initialization and configuration."""

    def test_init_with_client_id(self):
        """Test initialization with client ID parameter."""
        auth = TidalAuth(client_id="test_client_id")
        assert auth.client_id == "test_client_id"
        assert auth.client_secret is None

    def test_init_with_both_credentials(self):
        """Test initialization with both client ID and secret."""
        auth = TidalAuth(client_id="test_id", client_secret="test_secret")
        assert auth.client_id == "test_id"
        assert auth.client_secret == "test_secret"  # pragma: allowlist secret

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "env_client_id"})
    def test_init_from_environment(self):
        """Test initialization loading from environment variables."""
        auth = TidalAuth()
        assert auth.client_id == "env_client_id"

    def test_init_without_client_id_raises_error(self):
        """Test that missing client ID raises TidalAuthError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(TidalAuthError) as exc_info:
                TidalAuth()
            assert "client ID is required" in str(exc_info.value)

    def test_default_configuration_values(self):
        """Test default configuration values are set correctly."""
        auth = TidalAuth(client_id="test_id")
        assert auth.callback_port == 8080
        assert auth.country_code == "US"
        assert "localhost:8080/callback" in auth.redirect_uri

    @patch.dict(
        os.environ,
        {
            "TIDAL_CLIENT_ID": "test_id",
            "TIDAL_CALLBACK_PORT": "9090",
            "TIDAL_CALLBACK_URL": "http://custom.host/callback",
            "TIDAL_SESSION_PATH": "/custom/path/session.json",
            "TIDAL_CACHE_DIR": "/custom/cache",
        },
    )
    def test_custom_environment_configuration(self):
        """Test custom configuration from environment variables."""
        auth = TidalAuth()
        assert auth.callback_port == 9090
        assert auth.redirect_uri == "http://custom.host/callback"
        assert "/custom/path/session.json" in str(auth.session_file)
        assert "/custom/cache" in str(auth.cache_dir)

    def test_session_directory_creation(self):
        """Test that session directory is created with proper permissions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            session_path = Path(temp_dir) / "test_session" / "session.json"
            auth = TidalAuth(client_id="test_id")
            auth.session_file = session_path
            auth.session_file.parent.mkdir(parents=True, exist_ok=True)
            auth._secure_session_directory()

            # Check directory exists and has proper permissions
            assert session_path.parent.exists()
            dir_stat = session_path.parent.stat()
            # Check that only owner has permissions (0o700)
            assert (dir_stat.st_mode & 0o777) == 0o700


class TestSessionManagement:
    """Test session loading, saving, and validation."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.session_file = Path(self.temp_dir) / "session.json"

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_valid_session(self):
        """Test loading a valid session file."""
        # Create valid session data
        session_data = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "session_id": "test_session_id",
            "user_id": "test_user_id",
            "country_code": "US",
            "expires_at": (datetime.now() + timedelta(hours=1)).isoformat(),
            "saved_at": datetime.now().isoformat(),
        }

        # Write session file with secure permissions
        fd = os.open(self.session_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(session_data, f)

        auth = TidalAuth(client_id="test_id")
        auth.session_file = self.session_file
        auth._load_session()

        assert auth.access_token == "test_access_token"
        assert auth.refresh_token == "test_refresh_token"
        assert auth.session_id == "test_session_id"
        assert auth.user_id == "test_user_id"
        assert auth.country_code == "US"
        assert auth.token_expires_at is not None

    def test_load_expired_session(self):
        """Test that expired sessions are rejected and cleared."""
        # Create expired session data
        session_data = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_at": (datetime.now() - timedelta(hours=1)).isoformat(),
            "saved_at": datetime.now().isoformat(),
        }

        fd = os.open(self.session_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(session_data, f)

        auth = TidalAuth(client_id="test_id")
        auth.session_file = self.session_file
        auth._load_session()

        # Session should be cleared
        assert auth.access_token is None
        assert auth.refresh_token is None
        assert not self.session_file.exists()

    def test_load_session_with_insecure_permissions(self):
        """Test that sessions with insecure permissions are rejected."""
        session_data = {
            "access_token": "test_access_token",
            "expires_at": (datetime.now() + timedelta(hours=1)).isoformat(),
        }

        # Create file with insecure permissions (readable by others)
        with open(self.session_file, "w") as f:
            json.dump(session_data, f)
        self.session_file.chmod(0o644)  # Insecure permissions

        auth = TidalAuth(client_id="test_id")
        auth.session_file = self.session_file
        auth._load_session()

        # Session should be rejected and file cleared
        assert auth.access_token is None
        assert not self.session_file.exists()

    def test_load_corrupted_session(self):
        """Test handling of corrupted session files."""
        # Write invalid JSON
        with open(self.session_file, "w") as f:
            f.write("invalid json content")
        self.session_file.chmod(0o600)

        auth = TidalAuth(client_id="test_id")
        auth.session_file = self.session_file
        auth._load_session()

        # Session should be cleared
        assert auth.access_token is None
        assert not self.session_file.exists()

    def test_save_session(self):
        """Test saving session data with secure permissions."""
        auth = TidalAuth(client_id="test_id")
        auth.session_file = self.session_file
        auth.access_token = "test_access_token"
        auth.refresh_token = "test_refresh_token"
        auth.session_id = "test_session_id"
        auth.user_id = "test_user_id"
        auth.country_code = "US"
        auth.token_expires_at = datetime.now() + timedelta(hours=1)

        auth._save_session()

        # Check file exists with secure permissions
        assert self.session_file.exists()
        file_stat = self.session_file.stat()
        assert (file_stat.st_mode & 0o777) == 0o600

        # Check content
        with open(self.session_file, "r") as f:
            saved_data = json.load(f)
        assert saved_data["access_token"] == "test_access_token"
        assert saved_data["user_id"] == "test_user_id"

    def test_clear_session_file(self):
        """Test clearing session file."""
        # Create session file
        with open(self.session_file, "w") as f:
            f.write("test content")

        auth = TidalAuth(client_id="test_id")
        auth.session_file = self.session_file
        auth._clear_session_file()

        assert not self.session_file.exists()

    def test_session_invalidation(self):
        """Test session invalidation clears all data."""
        auth = TidalAuth(client_id="test_id")
        auth.session_file = self.session_file
        auth.access_token = "test_token"
        auth.refresh_token = "test_refresh"
        auth.session_id = "test_session"
        auth.user_id = "test_user"
        auth.tidal_session = MagicMock()

        auth._invalidate_session("test_reason")

        assert auth.access_token is None
        assert auth.refresh_token is None
        assert auth.session_id is None
        assert auth.user_id is None
        assert auth.tidal_session is None


class TestPKCEGeneration:
    """Test PKCE parameter generation for OAuth2."""

    def test_pkce_generation(self):
        """Test PKCE code verifier and challenge generation."""
        auth = TidalAuth(client_id="test_id")
        verifier, challenge = auth._generate_pkce_params()

        # Verifier should be base64url encoded
        assert len(verifier) >= 43  # Minimum length
        assert len(verifier) <= 128  # Maximum length
        assert all(
            c
            in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"  # pragma: allowlist secret
            for c in verifier
        )

        # Challenge should be base64url encoded SHA256 hash
        assert len(challenge) >= 43
        assert all(
            c
            in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"  # pragma: allowlist secret
            for c in challenge
        )

    def test_pkce_uniqueness(self):
        """Test that PKCE parameters are unique across calls."""
        auth = TidalAuth(client_id="test_id")
        verifier1, challenge1 = auth._generate_pkce_params()
        verifier2, challenge2 = auth._generate_pkce_params()

        assert verifier1 != verifier2
        assert challenge1 != challenge2


class TestAuthenticationFlow:
    """Test OAuth2 authentication flows."""

    def test_is_authenticated_with_valid_token(self):
        """Test is_authenticated with valid token and session."""
        auth = TidalAuth(client_id="test_id")
        auth.access_token = "valid_token"
        auth.token_expires_at = datetime.now() + timedelta(hours=1)

        # Mock valid tidal session
        mock_session = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "123"
        mock_session.user = mock_user
        auth.tidal_session = mock_session

        assert auth.is_authenticated()

    def test_is_authenticated_with_expired_token(self):
        """Test is_authenticated with expired token."""
        auth = TidalAuth(client_id="test_id")
        auth.access_token = "expired_token"
        auth.token_expires_at = datetime.now() - timedelta(hours=1)

        assert not auth.is_authenticated()
        # Token should be cleared
        assert auth.access_token is None

    def test_is_authenticated_without_token(self):
        """Test is_authenticated without access token."""
        auth = TidalAuth(client_id="test_id")
        assert not auth.is_authenticated()

    def test_get_auth_headers(self):
        """Test getting authentication headers."""
        auth = TidalAuth(client_id="test_id")
        auth.access_token = "test_token"

        headers = auth.get_auth_headers()
        assert headers["Authorization"] == "Bearer test_token"
        assert headers["X-Tidal-Token"] == "test_token"

    def test_get_auth_headers_without_token(self):
        """Test getting auth headers without token raises error."""
        auth = TidalAuth(client_id="test_id")

        with pytest.raises(ValueError, match="No access token available"):
            auth.get_auth_headers()

    def test_get_tidal_session_when_authenticated(self):
        """Test getting tidal session when authenticated."""
        auth = TidalAuth(client_id="test_id")
        auth.access_token = "test_token"
        auth.token_expires_at = datetime.now() + timedelta(hours=1)

        mock_session = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "123"
        mock_session.user = mock_user
        auth.tidal_session = mock_session

        session = auth.get_tidal_session()
        assert session == mock_session

    def test_get_tidal_session_when_not_authenticated(self):
        """Test getting tidal session when not authenticated raises error."""
        auth = TidalAuth(client_id="test_id")

        with pytest.raises(TidalAuthError, match="Not authenticated"):
            auth.get_tidal_session()


@pytest.mark.asyncio
class TestAsyncAuthenticationOperations:
    """Test async authentication operations."""

    @patch("aiohttp.ClientSession.post")
    async def test_refresh_access_token_success(self, mock_post):
        """Test successful token refresh."""
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "access_token": "new_access_token",
                "refresh_token": "new_refresh_token",
                "expires_in": 3600,
            }
        )
        mock_post.return_value.__aenter__.return_value = mock_response

        auth = TidalAuth(client_id="test_id")
        auth.refresh_token = "valid_refresh_token"

        success = await auth.refresh_access_token()

        assert success
        assert auth.access_token == "new_access_token"
        assert auth.refresh_token == "new_refresh_token"
        assert auth.token_expires_at is not None

    @patch("aiohttp.ClientSession.post")
    async def test_refresh_access_token_failure(self, mock_post):
        """Test token refresh failure."""
        # Mock error response
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value="invalid_grant")
        mock_post.return_value.__aenter__.return_value = mock_response

        auth = TidalAuth(client_id="test_id")
        auth.refresh_token = "invalid_refresh_token"
        auth.access_token = "old_token"

        success = await auth.refresh_access_token()

        assert not success
        # Session should be invalidated on failure
        assert auth.access_token is None
        assert auth.refresh_token is None

    async def test_refresh_access_token_without_refresh_token(self):
        """Test token refresh without refresh token."""
        auth = TidalAuth(client_id="test_id")

        success = await auth.refresh_access_token()
        assert not success

    @patch("src.tidal_mcp.auth.TidalAuth._try_existing_session")
    async def test_authenticate_with_existing_session(self, mock_try_existing):
        """Test authentication using existing session."""
        mock_try_existing.return_value = True

        auth = TidalAuth(client_id="test_id")
        success = await auth.authenticate()

        assert success
        mock_try_existing.assert_called_once()

    @patch("src.tidal_mcp.auth.TidalAuth._try_existing_session")
    @patch("src.tidal_mcp.auth.TidalAuth._oauth2_flow")
    async def test_authenticate_with_oauth_flow(self, mock_oauth2, mock_try_existing):
        """Test authentication using OAuth2 flow."""
        mock_try_existing.return_value = False
        mock_oauth2.return_value = True

        auth = TidalAuth(client_id="test_id")
        success = await auth.authenticate()

        assert success
        mock_try_existing.assert_called_once()
        mock_oauth2.assert_called_once()

    async def test_ensure_valid_token_when_authenticated(self):
        """Test ensure_valid_token when already authenticated."""
        auth = TidalAuth(client_id="test_id")
        auth.access_token = "valid_token"
        auth.token_expires_at = datetime.now() + timedelta(hours=1)

        # Mock valid session
        mock_session = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "123"
        mock_session.user = mock_user
        auth.tidal_session = mock_session

        result = await auth.ensure_valid_token()
        assert result

    @patch("src.tidal_mcp.auth.TidalAuth.refresh_access_token")
    async def test_ensure_valid_token_with_refresh(self, mock_refresh):
        """Test ensure_valid_token with token refresh."""
        mock_refresh.return_value = True

        auth = TidalAuth(client_id="test_id")
        auth.refresh_token = "valid_refresh"
        auth.access_token = "expired_token"
        auth.token_expires_at = datetime.now() - timedelta(hours=1)

        result = await auth.ensure_valid_token()
        assert result
        mock_refresh.assert_called_once()

    async def test_logout(self):
        """Test logout clears all session data."""
        auth = TidalAuth(client_id="test_id")
        auth.access_token = "test_token"
        auth.refresh_token = "test_refresh"
        auth.user_id = "test_user"
        auth.tidal_session = MagicMock()

        await auth.logout()

        assert auth.access_token is None
        assert auth.refresh_token is None
        assert auth.user_id is None
        assert auth.tidal_session is None

    async def test_try_existing_session_with_valid_session(self):
        """Test trying existing session with valid tidalapi session."""
        auth = TidalAuth(client_id="test_id")
        auth.access_token = "valid_token"
        auth.token_expires_at = datetime.now() + timedelta(hours=1)

        # Mock tidalapi session with valid user
        with patch("tidalapi.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_user = MagicMock()
            mock_user.id = "123"
            mock_user.country_code = "US"
            mock_session.user = mock_user
            mock_session_class.return_value = mock_session

            result = await auth._try_existing_session()

            assert result
            assert auth.user_id == "123"
            assert auth.country_code == "US"
            assert auth.tidal_session == mock_session

    async def test_try_existing_session_with_expired_token(self):
        """Test trying existing session with expired token."""
        auth = TidalAuth(client_id="test_id")
        auth.access_token = "expired_token"
        auth.token_expires_at = datetime.now() - timedelta(hours=1)

        result = await auth._try_existing_session()

        assert not result
        assert auth.access_token is None  # Should be invalidated

    async def test_try_existing_session_with_invalid_session(self):
        """Test trying existing session with invalid tidalapi session."""
        auth = TidalAuth(client_id="test_id")
        auth.access_token = "invalid_token"
        auth.token_expires_at = datetime.now() + timedelta(hours=1)

        # Mock tidalapi session that raises exception
        with patch("tidalapi.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session.user = None  # Invalid session
            mock_session_class.return_value = mock_session

            result = await auth._try_existing_session()

            assert not result
            assert auth.access_token is None  # Should be invalidated


class TestUserInfo:
    """Test user information retrieval."""

    def test_get_user_info_when_authenticated(self):
        """Test getting user info when authenticated."""
        auth = TidalAuth(client_id="test_id")
        auth.access_token = "valid_token"
        auth.token_expires_at = datetime.now() + timedelta(hours=1)

        # Mock tidal session with user
        mock_session = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "123"
        mock_user.username = "testuser"
        mock_user.country_code = "US"
        mock_user.subscription = {"type": "premium", "valid": True}
        mock_session.user = mock_user
        auth.tidal_session = mock_session

        user_info = auth.get_user_info()

        assert user_info is not None
        assert user_info["id"] == "123"
        assert user_info["username"] == "testuser"
        assert user_info["country_code"] == "US"
        assert user_info["subscription"]["type"] == "premium"

    def test_get_user_info_when_not_authenticated(self):
        """Test getting user info when not authenticated."""
        auth = TidalAuth(client_id="test_id")

        user_info = auth.get_user_info()
        assert user_info is None

    def test_get_user_info_with_exception(self):
        """Test getting user info when exception occurs."""
        auth = TidalAuth(client_id="test_id")
        auth.access_token = "valid_token"
        auth.token_expires_at = datetime.now() + timedelta(hours=1)

        # Mock session that raises exception
        mock_session = MagicMock()
        mock_session.user.side_effect = Exception("API Error")
        auth.tidal_session = mock_session

        user_info = auth.get_user_info()
        assert user_info is None


class TestOAuth2CallbackCapture:
    """Test OAuth2 callback server functionality."""

    @pytest.mark.asyncio
    async def test_capture_auth_code_timeout(self):
        """Test auth code capture with timeout."""
        auth = TidalAuth(client_id="test_id")

        # Mock the callback capture to timeout quickly
        with patch.object(auth, "_capture_auth_code") as mock_capture:
            mock_capture.return_value = None  # Timeout

            result = await auth._capture_auth_code()
            assert result is None

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_exchange_code_for_tokens_success(self, mock_post):
        """Test successful code-to-token exchange."""
        # Mock successful token response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "access_token": "new_access_token",
                "refresh_token": "new_refresh_token",
                "expires_in": 3600,
            }
        )
        mock_post.return_value.__aenter__.return_value = mock_response

        # Mock tidalapi session
        with patch("tidalapi.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_user = MagicMock()
            mock_user.id = "123"
            mock_user.country_code = "US"
            mock_session.user = mock_user
            mock_session_class.return_value = mock_session

            auth = TidalAuth(client_id="test_id")
            success = await auth._exchange_code_for_tokens("auth_code", "code_verifier")

            assert success
            assert auth.access_token == "new_access_token"
            assert auth.refresh_token == "new_refresh_token"

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_exchange_code_for_tokens_failure(self, mock_post):
        """Test failed code-to-token exchange."""
        # Mock error response
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value="invalid_grant")
        mock_post.return_value.__aenter__.return_value = mock_response

        auth = TidalAuth(client_id="test_id")
        success = await auth._exchange_code_for_tokens("invalid_code", "code_verifier")

        assert not success


class TestSecurityLogging:
    """Test security event logging functionality."""

    def test_log_security_event(self):
        """Test security event logging."""
        auth = TidalAuth(client_id="test_id")
        auth.user_id = "test_user"

        with patch("src.tidal_mcp.auth.security_logger") as mock_logger:
            auth._log_security_event("TEST_EVENT", {"detail": "test_detail"})

            # Verify logging was called
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "TEST_EVENT" in call_args
            assert "test_user" in call_args

    def test_secure_session_directory_success(self):
        """Test successful session directory securing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            session_file = Path(temp_dir) / "session.json"

            auth = TidalAuth(client_id="test_id")
            auth.session_file = session_file

            # Should not raise exception
            auth._secure_session_directory()

            # Directory should have secure permissions
            dir_stat = session_file.parent.stat()
            assert (dir_stat.st_mode & 0o777) == 0o700

    def test_secure_session_directory_failure(self):
        """Test session directory securing failure handling."""
        auth = TidalAuth(client_id="test_id")
        auth.session_file = Path("/nonexistent/path/session.json")

        with patch("src.tidal_mcp.auth.security_logger") as mock_logger:
            # Should not raise exception, just log warning
            auth._secure_session_directory()

            # Should log warning
            mock_logger.warning.assert_called_once()
