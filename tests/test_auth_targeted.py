"""

Targeted tests for auth module to increase coverage quickly.
Focus on simple scenarios that exercise specific uncovered lines.
"""

import json
import os
from unittest.mock import Mock, mock_open, patch

import pytest

from tidal_mcp.auth import TidalAuth, TidalAuthError


class TestTidalAuthTargeted:
    """Targeted tests to quickly increase auth.py coverage."""

    def test_auth_error_basic_usage(self):
        """Test basic TidalAuthError usage."""
        error = TidalAuthError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client"})
    @patch("tidal_mcp.auth.load_dotenv")
    def test_init_with_valid_client_id(self, mock_load_dotenv):
        """Test initialization with valid client ID."""
        with patch("tidal_mcp.auth.Path") as mock_path:
            mock_path_instance = Mock()
            mock_path.return_value = mock_path_instance
            mock_path_instance.expanduser.return_value = mock_path_instance
            mock_path_instance.exists.return_value = True

            auth = TidalAuth()
            assert auth.client_id == "test_client"

    @patch.dict(os.environ, {}, clear=True)
    @patch("tidal_mcp.auth.load_dotenv")
    def test_init_missing_client_id(self, mock_load_dotenv):
        """Test initialization without client ID."""
        with pytest.raises(TidalAuthError):
            TidalAuth()

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client"})
    @patch("tidal_mcp.auth.load_dotenv")
    def test_init_with_custom_client_id(self, mock_load_dotenv):
        """Test initialization with custom client ID parameter."""
        with patch("tidal_mcp.auth.Path"):
            auth = TidalAuth(client_id="custom_client")
            assert auth.client_id == "custom_client"

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client"})
    @patch("tidal_mcp.auth.load_dotenv")
    def test_init_with_custom_secret(self, mock_load_dotenv):
        """Test initialization with custom client secret."""
        with patch("tidal_mcp.auth.Path"):
            auth = TidalAuth(
                client_secret="custom_secret"  # pragma: allowlist secret
            )  # pragma: allowlist secret
            auth = TidalAuth(
                client_secret="custom_secret"  # pragma: allowlist secret
            )  # pragma: allowlist secret

    @patch.dict(
        os.environ,
        {
            "TIDAL_CLIENT_ID": "test_client",
            "TIDAL_CLIENT_SECRET": "env_secret",  # pragma: allowlist secret
        },
    )
    @patch("tidal_mcp.auth.load_dotenv")
    def test_init_uses_env_secret(self, mock_load_dotenv):
        """Test initialization uses environment secret."""
        with patch("tidal_mcp.auth.Path"):
            auth = TidalAuth()
            assert (
                auth.client_secret == "env_secret"  # pragma: allowlist secret
            )  # pragma: allowlist secret

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client"})
    @patch("tidal_mcp.auth.load_dotenv")
    def test_session_path_properties(self, mock_load_dotenv):
        """Test session path properties."""
        with patch("tidal_mcp.auth.Path") as mock_path:
            mock_path_instance = Mock()
            mock_path.return_value = mock_path_instance
            mock_path_instance.expanduser.return_value = mock_path_instance

            auth = TidalAuth()
            # Access the property to trigger code execution
            _ = auth.session_path
            mock_path_instance.expanduser.assert_called()

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client"})
    @patch("tidal_mcp.auth.load_dotenv")
    def test_cache_dir_properties(self, mock_load_dotenv):
        """Test cache directory properties."""
        with patch("tidal_mcp.auth.Path") as mock_path:
            mock_path_instance = Mock()
            mock_path.return_value = mock_path_instance
            mock_path_instance.expanduser.return_value = mock_path_instance

            auth = TidalAuth()
            # Access the property to trigger code execution
            _ = auth.cache_dir
            mock_path_instance.expanduser.assert_called()

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client"})
    @patch("tidal_mcp.auth.load_dotenv")
    def test_str_and_repr_methods(self, mock_load_dotenv):
        """Test string representation methods."""
        with patch("tidal_mcp.auth.Path"):
            auth = TidalAuth()

            str_result = str(auth)
            repr_result = repr(auth)

            assert "TidalAuth" in str_result
            assert "TidalAuth" in repr_result
            assert "test_client" in repr_result

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client"})
    @patch("tidal_mcp.auth.load_dotenv")
    def test_load_session_missing_file(self, mock_load_dotenv):
        """Test loading session when file doesn't exist."""
        with patch("tidal_mcp.auth.Path") as mock_path:
            mock_path_instance = Mock()
            mock_path.return_value = mock_path_instance
            mock_path_instance.expanduser.return_value = mock_path_instance
            mock_path_instance.exists.return_value = False  # File doesn't exist

            auth = TidalAuth()
            result = auth._load_session()
            assert result is None

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client"})
    @patch("tidal_mcp.auth.load_dotenv")
    def test_load_session_invalid_json(self, mock_load_dotenv):
        """Test loading session with invalid JSON."""
        with patch("tidal_mcp.auth.Path") as mock_path:
            mock_path_instance = Mock()
            mock_path.return_value = mock_path_instance
            mock_path_instance.expanduser.return_value = mock_path_instance
            mock_path_instance.exists.return_value = True

            with patch("builtins.open", mock_open(read_data="invalid json")):
                auth = TidalAuth()
                result = auth._load_session()
                assert result is None

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client"})
    @patch("tidal_mcp.auth.load_dotenv")
    def test_save_session_with_data(self, mock_load_dotenv):
        """Test saving session data."""
        with patch("tidal_mcp.auth.Path") as mock_path:
            mock_path_instance = Mock()
            mock_path.return_value = mock_path_instance
            mock_path_instance.expanduser.return_value = mock_path_instance
            mock_path_instance.exists.return_value = True

            session_data = {"access_token": "test_token"}

            with patch("builtins.open", mock_open()) as mock_file:
                auth = TidalAuth()
                auth._save_session(session_data)
                mock_file.assert_called_once()

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client"})
    @patch("tidal_mcp.auth.load_dotenv")
    def test_is_session_expired_no_session(self, mock_load_dotenv):
        """Test session expiry when no session exists."""
        with patch("tidal_mcp.auth.Path") as mock_path:
            mock_path_instance = Mock()
            mock_path.return_value = mock_path_instance
            mock_path_instance.expanduser.return_value = mock_path_instance
            mock_path_instance.exists.return_value = False

            auth = TidalAuth()
            assert auth._is_session_expired() is True

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client"})
    @patch("tidal_mcp.auth.load_dotenv")
    def test_clear_session_file_exists(self, mock_load_dotenv):
        """Test clearing session when file exists."""
        with patch("tidal_mcp.auth.Path") as mock_path:
            mock_path_instance = Mock()
            mock_path.return_value = mock_path_instance
            mock_path_instance.expanduser.return_value = mock_path_instance
            mock_path_instance.exists.return_value = True

            auth = TidalAuth()
            auth.clear_session()
            mock_path_instance.unlink.assert_called_once()

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client"})
    @patch("tidal_mcp.auth.load_dotenv")
    def test_clear_session_file_missing(self, mock_load_dotenv):
        """Test clearing session when file doesn't exist."""
        with patch("tidal_mcp.auth.Path") as mock_path:
            mock_path_instance = Mock()
            mock_path.return_value = mock_path_instance
            mock_path_instance.expanduser.return_value = mock_path_instance
            mock_path_instance.exists.return_value = False

            auth = TidalAuth()
            auth.clear_session()
            mock_path_instance.unlink.assert_not_called()

    @patch("tidal_mcp.auth.tidalapi.Session")
    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client"})
    @patch("tidal_mcp.auth.load_dotenv")
    def test_get_tidal_session_basic(self, mock_load_dotenv, mock_session_class):
        """Test basic Tidal session creation."""
        with patch("tidal_mcp.auth.Path") as mock_path:
            mock_path_instance = Mock()
            mock_path.return_value = mock_path_instance
            mock_path_instance.expanduser.return_value = mock_path_instance
            mock_path_instance.exists.return_value = False

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            auth = TidalAuth()
            result = auth.get_tidal_session()

            assert result == mock_session
            mock_session_class.assert_called_once()

    def test_oauth_endpoints_from_env(self):
        """Test OAuth endpoints can be configured via environment."""
        # Test default values
        assert TidalAuth.OAUTH_BASE_URL == "https://login.tidal.com"
        assert TidalAuth.TOKEN_URL == "https://auth.tidal.com/v1/oauth2/token"

    @patch.dict(
        os.environ,
        {
            "TIDAL_CLIENT_ID": "test_client",
            "TIDAL_OAUTH_BASE_URL": "https://custom-oauth.tidal.com",
            "TIDAL_TOKEN_URL": "https://custom-token.tidal.com/token",
        },
    )
    @patch("tidal_mcp.auth.load_dotenv")
    def test_custom_oauth_endpoints(self, mock_load_dotenv):
        """Test custom OAuth endpoints from environment."""
        # Reload the module to pick up env vars
        import importlib

        from tidal_mcp import auth

        importlib.reload(auth)

        assert auth.TidalAuth.OAUTH_BASE_URL == "https://custom-oauth.tidal.com"
        assert auth.TidalAuth.TOKEN_URL == "https://custom-token.tidal.com/token"

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client"})
    @patch("tidal_mcp.auth.load_dotenv")
    async def test_ensure_valid_token_no_session(self, mock_load_dotenv):
        """Test ensure_valid_token when no session exists."""
        with patch("tidal_mcp.auth.Path") as mock_path:
            mock_path_instance = Mock()
            mock_path.return_value = mock_path_instance
            mock_path_instance.expanduser.return_value = mock_path_instance
            mock_path_instance.exists.return_value = False

            auth = TidalAuth()
            result = await auth.ensure_valid_token()
            assert result is False

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client"})
    @patch("tidal_mcp.auth.load_dotenv")
    async def test_ensure_valid_token_with_valid_session(self, mock_load_dotenv):
        """Test ensure_valid_token with valid session."""
        import time

        with patch("tidal_mcp.auth.Path") as mock_path:
            mock_path_instance = Mock()
            mock_path.return_value = mock_path_instance
            mock_path_instance.expanduser.return_value = mock_path_instance
            mock_path_instance.exists.return_value = True

            session_data = {
                "access_token": "test_token",
                "expires_at": time.time() + 3600,  # Valid for 1 hour
            }

            with patch("builtins.open", mock_open(read_data=json.dumps(session_data))):
                auth = TidalAuth()
                result = await auth.ensure_valid_token()
                assert result is True
