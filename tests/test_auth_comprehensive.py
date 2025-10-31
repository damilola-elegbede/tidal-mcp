"""
Comprehensive tests for auth module to reach 80% coverage.
Targets specific uncovered lines identified in coverage report.
"""

import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, mock_open, patch

import pytest

from tidal_mcp.auth import TidalAuth, TidalAuthError


class TestTidalAuthComprehensive:
    """Comprehensive tests targeting specific uncovered lines in auth.py."""

    def test_tidal_auth_error_inheritance(self):
        """Test TidalAuthError inheritance and properties."""
        error = TidalAuthError("Test message")
        assert isinstance(error, Exception)
        assert str(error) == "Test message"

        # Test with chaining
        try:
            raise ValueError("Original")
        except ValueError as e:
            try:
                raise TidalAuthError("Wrapped") from e
            except TidalAuthError as error_with_cause:
                assert error_with_cause.__cause__ == e

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    def test_init_with_custom_paths(self, mock_path, mock_load_dotenv):
        """Test initialization with custom session and cache paths."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.mkdir.return_value = None
        mock_path_instance.exists.return_value = True

        auth = TidalAuth()

        assert auth.client_id == "test_client_id"
        mock_load_dotenv.assert_called_once()
        mock_path_instance.mkdir.assert_called_with(parents=True, exist_ok=True)

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    def test_mkdir_creation_on_init(self, mock_path, mock_load_dotenv):
        """Test directory creation during initialization."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = False  # Force mkdir call

        auth = TidalAuth()

        # Verify mkdir was called with correct parameters
        mock_path_instance.mkdir.assert_called_with(parents=True, exist_ok=True)

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    def test_load_session_file_not_found(self, mock_path, mock_load_dotenv):
        """Test _load_session when session file doesn't exist."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = False

        auth = TidalAuth()
        session_data = auth._load_session()

        assert session_data is None

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    def test_load_session_file_read_error(self, mock_path, mock_load_dotenv):
        """Test _load_session when file exists but can't be read."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True

        # Mock file read to raise exception
        with patch("builtins.open", mock_open()) as mock_file:
            mock_file.side_effect = IOError("Cannot read file")

            auth = TidalAuth()
            session_data = auth._load_session()

            assert session_data is None

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    def test_load_session_invalid_json(self, mock_path, mock_load_dotenv):
        """Test _load_session with invalid JSON content."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True

        # Mock file with invalid JSON
        with patch("builtins.open", mock_open(read_data="invalid json content")):
            auth = TidalAuth()
            session_data = auth._load_session()

            assert session_data is None

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    def test_save_session_success(self, mock_path, mock_load_dotenv):
        """Test successful session saving."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True

        session_data = {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "expires_at": time.time() + 3600,
        }

        with patch("builtins.open", mock_open()) as mock_file:
            auth = TidalAuth()
            auth._save_session(session_data)

            # Verify file was opened for writing
            mock_file.assert_called_once()
            handle = mock_file.return_value
            # Verify JSON was written
            written_content = "".join(
                call[0][0] for call in handle.write.call_args_list
            )
            assert "access_token" in written_content

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    def test_save_session_permission_error(self, mock_path, mock_load_dotenv):
        """Test session saving with permission error."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True

        session_data = {"test": "data"}

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            auth = TidalAuth()
            # Should not raise exception, just log error
            auth._save_session(session_data)

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    def test_save_session_io_error(self, mock_path, mock_load_dotenv):
        """Test session saving with IO error."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True

        session_data = {"test": "data"}

        with patch("builtins.open", side_effect=IOError("IO error")):
            auth = TidalAuth()
            # Should not raise exception, just log error
            auth._save_session(session_data)

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    def test_is_session_expired_no_session(self, mock_path, mock_load_dotenv):
        """Test session expiry check when no session exists."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = False

        auth = TidalAuth()
        assert auth._is_session_expired() is True

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    def test_is_session_expired_missing_expires_at(self, mock_path, mock_load_dotenv):
        """Test session expiry check when expires_at is missing."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True

        session_data = {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            # Missing expires_at
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(session_data))):
            auth = TidalAuth()
            assert auth._is_session_expired() is True

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    def test_is_session_expired_expired_time(self, mock_path, mock_load_dotenv):
        """Test session expiry check with expired timestamp."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True

        session_data = {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "expires_at": time.time() - 3600,  # Expired 1 hour ago
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(session_data))):
            auth = TidalAuth()
            assert auth._is_session_expired() is True

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    def test_is_session_expired_valid_time(self, mock_path, mock_load_dotenv):
        """Test session expiry check with valid timestamp."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True

        session_data = {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "expires_at": time.time() + 3600,  # Valid for 1 hour
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(session_data))):
            auth = TidalAuth()
            assert auth._is_session_expired() is False

    @patch("tidal_mcp.auth.tidalapi.Session")
    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    def test_get_tidal_session_new_session(
        self, mock_path, mock_load_dotenv, mock_session_class
    ):
        """Test getting new Tidal session when none exists."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = False

        mock_session = Mock()
        mock_session_class.return_value = mock_session

        auth = TidalAuth()
        session = auth.get_tidal_session()

        assert session == mock_session
        mock_session_class.assert_called_once()

    @patch("tidal_mcp.auth.tidalapi.Session")
    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    def test_get_tidal_session_load_existing(
        self, mock_path, mock_load_dotenv, mock_session_class
    ):
        """Test loading existing Tidal session."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True

        session_data = {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "expires_at": time.time() + 3600,
        }

        mock_session = Mock()
        mock_session.load_oauth_session.return_value = True
        mock_session_class.return_value = mock_session

        with patch("builtins.open", mock_open(read_data=json.dumps(session_data))):
            auth = TidalAuth()
            session = auth.get_tidal_session()

            assert session == mock_session
            mock_session.load_oauth_session.assert_called_once()

    @patch("tidal_mcp.auth.tidalapi.Session")
    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    def test_get_tidal_session_load_fails(
        self, mock_path, mock_load_dotenv, mock_session_class
    ):
        """Test when loading existing session fails."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True

        session_data = {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "expires_at": time.time() + 3600,
        }

        mock_session = Mock()
        mock_session.load_oauth_session.return_value = False  # Load fails
        mock_session_class.return_value = mock_session

        with patch("builtins.open", mock_open(read_data=json.dumps(session_data))):
            auth = TidalAuth()
            session = auth.get_tidal_session()

            assert session == mock_session
            mock_session.load_oauth_session.assert_called_once()

    @patch("tidal_mcp.auth.webbrowser.open")
    @patch("tidal_mcp.auth.tidalapi.Session")
    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    def test_authenticate_user_success(
        self, mock_path, mock_load_dotenv, mock_session_class, mock_webbrowser
    ):
        """Test successful user authentication."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True

        mock_session = Mock()
        mock_session.login_oauth.return_value = True
        mock_session.check_login.return_value = True
        mock_session.access_token = "new_access_token"
        mock_session.refresh_token = "new_refresh_token"
        mock_session.expires_at = time.time() + 3600
        mock_session_class.return_value = mock_session

        with patch.object(TidalAuth, "_save_session") as mock_save:
            auth = TidalAuth()
            result = auth.authenticate_user()

            assert result is True
            mock_session.login_oauth.assert_called_once()
            mock_save.assert_called_once()

    @patch("tidal_mcp.auth.tidalapi.Session")
    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    def test_authenticate_user_oauth_failure(
        self, mock_path, mock_load_dotenv, mock_session_class
    ):
        """Test user authentication when OAuth fails."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True

        mock_session = Mock()
        mock_session.login_oauth.return_value = False  # OAuth fails
        mock_session_class.return_value = mock_session

        auth = TidalAuth()
        result = auth.authenticate_user()

        assert result is False

    @patch("tidal_mcp.auth.tidalapi.Session")
    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    def test_authenticate_user_login_check_failure(
        self, mock_path, mock_load_dotenv, mock_session_class
    ):
        """Test user authentication when login check fails."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True

        mock_session = Mock()
        mock_session.login_oauth.return_value = True
        mock_session.check_login.return_value = False  # Login check fails
        mock_session_class.return_value = mock_session

        auth = TidalAuth()
        result = auth.authenticate_user()

        assert result is False

    @patch("tidal_mcp.auth.tidalapi.Session")
    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    def test_authenticate_user_exception(
        self, mock_path, mock_load_dotenv, mock_session_class
    ):
        """Test authentication with exception."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True

        mock_session = Mock()
        mock_session.login_oauth.side_effect = Exception("OAuth error")
        mock_session_class.return_value = mock_session

        auth = TidalAuth()

        with pytest.raises(TidalAuthError, match="Authentication failed"):
            auth.authenticate_user()

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    async def test_ensure_valid_token_no_session(self, mock_path, mock_load_dotenv):
        """Test ensure_valid_token when no session exists."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = False

        auth = TidalAuth()
        result = await auth.ensure_valid_token()

        assert result is False

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    async def test_ensure_valid_token_valid_session(self, mock_path, mock_load_dotenv):
        """Test ensure_valid_token with valid session."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True

        session_data = {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "expires_at": time.time() + 3600,
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(session_data))):
            auth = TidalAuth()
            result = await auth.ensure_valid_token()

            assert result is True

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    async def test_ensure_valid_token_expired_session(
        self, mock_path, mock_load_dotenv
    ):
        """Test ensure_valid_token with expired session."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True

        session_data = {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "expires_at": time.time() - 3600,  # Expired
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(session_data))):
            auth = TidalAuth()
            result = await auth.ensure_valid_token()

            assert result is False

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    def test_clear_session_file_exists(self, mock_path, mock_load_dotenv):
        """Test clearing session when file exists."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True
        mock_path_instance.unlink.return_value = None

        auth = TidalAuth()
        auth.clear_session()

        mock_path_instance.unlink.assert_called_once()

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    def test_clear_session_file_not_exists(self, mock_path, mock_load_dotenv):
        """Test clearing session when file doesn't exist."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = False

        auth = TidalAuth()
        auth.clear_session()

        mock_path_instance.unlink.assert_not_called()

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    def test_clear_session_permission_error(self, mock_path, mock_load_dotenv):
        """Test clearing session with permission error."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True
        mock_path_instance.unlink.side_effect = PermissionError("Permission denied")

        auth = TidalAuth()
        # Should not raise exception
        auth.clear_session()

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    @patch("tidal_mcp.auth.Path")
    def test_str_and_repr_methods(self, mock_path, mock_load_dotenv):
        """Test string representation methods."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.expanduser.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True

        auth = TidalAuth()

        str_repr = str(auth)
        repr_str = repr(auth)

        assert "TidalAuth" in str_repr
        assert "TidalAuth" in repr_str
        assert "test_client_id" in repr_str
