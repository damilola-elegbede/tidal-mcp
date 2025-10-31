"""Focused tests for auth module to increase coverage."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

from tidal_mcp.auth import TidalAuth, TidalAuthError


class TestTidalAuthFocused:
    """Focused tests for TidalAuth class to maximize coverage."""

    @pytest.fixture
    def temp_session_file(self):
        """Create a temporary session file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            session_data = {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "expires_at": 9999999999,  # Far future
                "user_id": "test_user",
            }
            json.dump(session_data, f)
            temp_path = f.name

        yield temp_path

        # Cleanup
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def test_auth_error_creation(self):
        """Test TidalAuthError creation and inheritance."""
        error = TidalAuthError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_auth_error_with_cause(self):
        """Test TidalAuthError with cause."""
        original_error = ValueError("Original error")
        try:
            raise TidalAuthError("Wrapped error") from original_error
        except TidalAuthError as error:
            assert str(error) == "Wrapped error"
            assert error.__cause__ == original_error

    @patch.dict(
        os.environ,
        {
            "TIDAL_CLIENT_ID": "test_client_id",
            "TIDAL_SESSION_PATH": "/tmp/test_session.json",
            "TIDAL_CACHE_DIR": "/tmp/test_cache",
        },
    )
    @patch("tidal_mcp.auth.load_dotenv")
    def test_auth_init_with_env_vars(self, mock_load_dotenv):
        """Test TidalAuth initialization with environment variables."""
        with patch("tidal_mcp.auth.Path.expanduser") as mock_expanduser:
            mock_expanduser.return_value = Path("/tmp/test_session.json")

            auth = TidalAuth()

            assert auth.client_id == "test_client_id"
            mock_load_dotenv.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)
    @patch("tidal_mcp.auth.load_dotenv")
    def test_auth_init_missing_client_id(self, mock_load_dotenv):
        """Test TidalAuth initialization with missing client ID."""
        with pytest.raises(
            TidalAuthError,
            match="TIDAL_CLIENT_ID environment variable is required",
        ):
            TidalAuth()

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    @patch("tidal_mcp.auth.load_dotenv")
    def test_auth_init_default_paths(self, mock_load_dotenv):
        """Test TidalAuth initialization with default paths."""
        with patch("tidal_mcp.auth.Path.expanduser") as mock_expanduser:
            mock_expanduser.return_value = Path("/home/user/.tidal-mcp/session.json")

            auth = TidalAuth()

            assert auth.client_id == "test_client_id"
            # Should use default paths
            mock_expanduser.assert_called()

    def test_load_session_valid_file(self, temp_session_file):
        """Test loading valid session file."""
        with patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"}):
            with patch("tidal_mcp.auth.Path.expanduser") as mock_expanduser:
                mock_expanduser.return_value = Path(temp_session_file)

                auth = TidalAuth()
                session_data = auth._load_session()

                assert session_data is not None
                assert session_data["access_token"] == "test_access_token"

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    def test_load_session_missing_file(self):
        """Test loading missing session file."""
        with patch("tidal_mcp.auth.Path.expanduser") as mock_expanduser:
            mock_expanduser.return_value = Path("/nonexistent/session.json")

            auth = TidalAuth()
            session_data = auth._load_session()

            assert session_data is None

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    def test_load_session_invalid_json(self):
        """Test loading session with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            f.write("invalid json content")
            temp_path = f.name

        try:
            with patch("tidal_mcp.auth.Path.expanduser") as mock_expanduser:
                mock_expanduser.return_value = Path(temp_path)

                auth = TidalAuth()
                session_data = auth._load_session()

                assert session_data is None
        finally:
            os.unlink(temp_path)

    def test_save_session_success(self, temp_cache_dir):
        """Test successful session saving."""
        session_file = os.path.join(temp_cache_dir, "session.json")

        with patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"}):
            with patch("tidal_mcp.auth.Path.expanduser") as mock_expanduser:
                mock_expanduser.return_value = Path(session_file)

                auth = TidalAuth()
                session_data = {
                    "access_token": "new_token",
                    "refresh_token": "new_refresh",
                    "expires_at": 1234567890,
                }

                auth._save_session(session_data)

                # Verify file was created and contains correct data
                assert os.path.exists(session_file)
                with open(session_file, "r") as f:
                    saved_data = json.load(f)
                assert saved_data == session_data

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    def test_save_session_permission_error(self):
        """Test session saving with permission error."""
        with patch("tidal_mcp.auth.Path.expanduser") as mock_expanduser:
            mock_expanduser.return_value = Path("/root/readonly/session.json")

            auth = TidalAuth()
            session_data = {"test": "data"}

            # Should not raise exception, just log error
            auth._save_session(session_data)

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    def test_is_session_expired_no_session(self):
        """Test session expiry check with no session."""
        with patch("tidal_mcp.auth.Path.expanduser") as mock_expanduser:
            mock_expanduser.return_value = Path("/nonexistent/session.json")

            auth = TidalAuth()
            assert auth._is_session_expired() is True

    def test_is_session_expired_valid_session(self, temp_session_file):
        """Test session expiry check with valid session."""
        with patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"}):
            with patch("tidal_mcp.auth.Path.expanduser") as mock_expanduser:
                mock_expanduser.return_value = Path(temp_session_file)

                auth = TidalAuth()
                assert auth._is_session_expired() is False

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    def test_is_session_expired_missing_expires_at(self):
        """Test session expiry check with missing expires_at."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            session_data = {
                "access_token": "test_token",
                "refresh_token": "test_refresh",
                # Missing expires_at
            }
            json.dump(session_data, f)
            temp_path = f.name

        try:
            with patch("tidal_mcp.auth.Path.expanduser") as mock_expanduser:
                mock_expanduser.return_value = Path(temp_path)

                auth = TidalAuth()
                assert auth._is_session_expired() is True
        finally:
            os.unlink(temp_path)

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    def test_is_session_expired_expired_session(self):
        """Test session expiry check with expired session."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            session_data = {
                "access_token": "test_token",
                "refresh_token": "test_refresh",
                "expires_at": 1000000000,  # Past timestamp
            }
            json.dump(session_data, f)
            temp_path = f.name

        try:
            with patch("tidal_mcp.auth.Path.expanduser") as mock_expanduser:
                mock_expanduser.return_value = Path(temp_path)

                auth = TidalAuth()
                assert auth._is_session_expired() is True
        finally:
            os.unlink(temp_path)

    @patch("tidal_mcp.auth.tidalapi.Session")
    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    def test_get_tidal_session_no_existing_session(self, mock_session_class):
        """Test getting Tidal session when none exists."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        with patch("tidal_mcp.auth.Path.expanduser") as mock_expanduser:
            mock_expanduser.return_value = Path("/nonexistent/session.json")

            auth = TidalAuth()
            session = auth.get_tidal_session()

            assert session == mock_session
            mock_session_class.assert_called_once()

    @patch("tidal_mcp.auth.tidalapi.Session")
    def test_get_tidal_session_with_existing_session(
        self, mock_session_class, temp_session_file
    ):
        """Test getting Tidal session when one exists."""
        mock_session = Mock()
        mock_session.load_oauth_session.return_value = True
        mock_session_class.return_value = mock_session

        with patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"}):
            with patch("tidal_mcp.auth.Path.expanduser") as mock_expanduser:
                mock_expanduser.return_value = Path(temp_session_file)

                auth = TidalAuth()
                session = auth.get_tidal_session()

                assert session == mock_session
                mock_session.load_oauth_session.assert_called_once()

    @patch("tidal_mcp.auth.webbrowser.open")
    @patch("tidal_mcp.auth.tidalapi.Session")
    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    def test_authenticate_user_success(self, mock_session_class, mock_webbrowser):
        """Test successful user authentication."""
        mock_session = Mock()
        mock_session.login_oauth.return_value = True
        mock_session.check_login.return_value = True
        mock_session.access_token = "new_access_token"
        mock_session.refresh_token = "new_refresh_token"
        mock_session.expires_at = 9999999999
        mock_session_class.return_value = mock_session

        with patch("tidal_mcp.auth.Path.expanduser") as mock_expanduser:
            mock_expanduser.return_value = Path("/tmp/test_session.json")

            with patch.object(TidalAuth, "_save_session") as mock_save:
                auth = TidalAuth()
                result = auth.authenticate_user()

                assert result is True
                mock_session.login_oauth.assert_called_once()
                mock_save.assert_called_once()

    @patch("tidal_mcp.auth.tidalapi.Session")
    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    def test_authenticate_user_failure(self, mock_session_class):
        """Test failed user authentication."""
        mock_session = Mock()
        mock_session.login_oauth.return_value = False
        mock_session_class.return_value = mock_session

        with patch("tidal_mcp.auth.Path.expanduser") as mock_expanduser:
            mock_expanduser.return_value = Path("/tmp/test_session.json")

            auth = TidalAuth()
            result = auth.authenticate_user()

            assert result is False

    @patch("tidal_mcp.auth.tidalapi.Session")
    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    def test_authenticate_user_exception(self, mock_session_class):
        """Test authentication with exception."""
        mock_session = Mock()
        mock_session.login_oauth.side_effect = Exception("OAuth error")
        mock_session_class.return_value = mock_session

        with patch("tidal_mcp.auth.Path.expanduser") as mock_expanduser:
            mock_expanduser.return_value = Path("/tmp/test_session.json")

            auth = TidalAuth()

            with pytest.raises(TidalAuthError, match="Authentication failed"):
                auth.authenticate_user()

    @pytest.mark.asyncio
    async def test_ensure_valid_token_no_session(self):
        """Test ensure_valid_token with no session."""
        with patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"}):
            with patch("tidal_mcp.auth.Path.expanduser") as mock_expanduser:
                mock_expanduser.return_value = Path("/nonexistent/session.json")

                auth = TidalAuth()
                result = await auth.ensure_valid_token()

                assert result is False

    @pytest.mark.asyncio
    async def test_ensure_valid_token_valid_session(self, temp_session_file):
        """Test ensure_valid_token with valid session."""
        with patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"}):
            with patch("tidal_mcp.auth.Path.expanduser") as mock_expanduser:
                mock_expanduser.return_value = Path(temp_session_file)

                auth = TidalAuth()
                result = await auth.ensure_valid_token()

                assert result is True

    @pytest.mark.asyncio
    async def test_ensure_valid_token_expired_session(self):
        """Test ensure_valid_token with expired session."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            session_data = {
                "access_token": "expired_token",
                "refresh_token": "refresh_token",
                "expires_at": 1000000000,  # Past timestamp
            }
            json.dump(session_data, f)
            temp_path = f.name

        try:
            with patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"}):
                with patch("tidal_mcp.auth.Path.expanduser") as mock_expanduser:
                    mock_expanduser.return_value = Path(temp_path)

                    auth = TidalAuth()
                    result = await auth.ensure_valid_token()

                    assert result is False
        finally:
            os.unlink(temp_path)

    def test_clear_session_success(self, temp_session_file):
        """Test successful session clearing."""
        with patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"}):
            with patch("tidal_mcp.auth.Path.expanduser") as mock_expanduser:
                mock_expanduser.return_value = Path(temp_session_file)

                auth = TidalAuth()

                # Verify file exists before clearing
                assert os.path.exists(temp_session_file)

                auth.clear_session()

                # Verify file is deleted
                assert not os.path.exists(temp_session_file)

    @patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"})
    def test_clear_session_missing_file(self):
        """Test clearing session when file doesn't exist."""
        with patch("tidal_mcp.auth.Path.expanduser") as mock_expanduser:
            mock_expanduser.return_value = Path("/nonexistent/session.json")

            auth = TidalAuth()

            # Should not raise exception
            auth.clear_session()

    def test_repr_string(self):
        """Test string representation of TidalAuth."""
        with patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"}):
            with patch("tidal_mcp.auth.Path.expanduser") as mock_expanduser:
                mock_expanduser.return_value = Path("/tmp/test_session.json")

                auth = TidalAuth()
                repr_str = repr(auth)

                assert "TidalAuth" in repr_str
                assert "test_client_id" in repr_str

    def test_str_method(self):
        """Test __str__ method of TidalAuth."""
        with patch.dict(os.environ, {"TIDAL_CLIENT_ID": "test_client_id"}):
            with patch("tidal_mcp.auth.Path.expanduser") as mock_expanduser:
                mock_expanduser.return_value = Path("/tmp/test_session.json")

                auth = TidalAuth()
                str_repr = str(auth)

                assert "TidalAuth" in str_repr
