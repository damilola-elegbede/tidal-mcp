"""Tidal Authentication Manager.

Handles authentication and authorization for Tidal API access.
Supports OAuth2 flow with PKCE and token management for secure API
interactions.
"""

import base64
import hashlib
import json
import logging
import os
import secrets
import stat
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import aiohttp
import tidalapi
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Security-focused logger for authentication events
security_logger = logging.getLogger(f"{__name__}.security")
security_logger.setLevel(logging.INFO)

# Ensure security events are logged even if main logger is disabled
if not security_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - SECURITY - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    security_logger.addHandler(handler)


class TidalAuthError(Exception):
    """Custom exception for Tidal authentication errors."""

    pass


class TidalAuth:
    """
    Manages authentication and authorization for Tidal API.

    Handles OAuth2 flow with PKCE, token refresh, and session managemen
    to ensure secure and persistent access to Tidal services.
    """

    # OAuth2 endpoints for Tidal (configurable via environment variables)
    OAUTH_BASE_URL = os.getenv("TIDAL_OAUTH_BASE_URL", "https://login.tidal.com")
    TOKEN_URL = os.getenv("TIDAL_TOKEN_URL", "https://auth.tidal.com/v1/oauth2/token")

    def __init__(self, client_id: str | None = None, client_secret: str | None = None):
        """
        Initialize Tidal authentication manager.

        Args:
            client_id: Tidal API client ID (optional, loads from environment)
            client_secret: Tidal API client secret (optional, loads from environment)
        """
        # Load credentials from environment variables with fallbacks
        self.client_id = client_id or os.getenv("TIDAL_CLIENT_ID")
        if not self.client_id:
            raise TidalAuthError(
                "Tidal client ID is required. Set TIDAL_CLIENT_ID environment variable "
                "or pass client_id parameter."
            )

        self.client_secret = client_secret or os.getenv("TIDAL_CLIENT_SECRET")
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.token_expires_at: datetime | None = None
        self.session_id: str | None = None
        self.country_code: str = "US"  # Default country code
        self.user_id: str | None = None

        # Configure callback port and URI from environment
        self.callback_port = int(os.getenv("TIDAL_CALLBACK_PORT", "8080"))
        self.redirect_uri = os.getenv(
            "TIDAL_CALLBACK_URL", f"http://localhost:{self.callback_port}/callback"
        )

        # Configure session file path from environment
        session_path = os.getenv("TIDAL_SESSION_PATH", "~/.tidal-mcp/session.json")
        self.session_file = Path(session_path).expanduser()
        self.session_file.parent.mkdir(parents=True, exist_ok=True)

        # Secure the session directory with restrictive permissions (0700)
        self._secure_session_directory()

        # Configure cache directory from environment
        cache_dir = os.getenv("TIDAL_CACHE_DIR", "~/.tidal-mcp/cache")
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Tidal API clien
        self.tidal_session: tidalapi.Session | None = None

        # Load existing session if available
        self._load_session()

    def _secure_session_directory(self) -> None:
        """Secure the session directory with restrictive permissions."""
        try:
            session_dir = self.session_file.parent
            # Set directory permissions to 0700 (user read/write/execute only)
            session_dir.chmod(0o700)
            security_logger.info(f"Secured session directory: {session_dir}")
        except Exception as e:
            security_logger.warning(f"Failed to secure session directory: {e}")

    def _is_session_expired(self, session_data: dict) -> bool:
        """Check if session data represents an expired session."""
        try:
            expires_str = session_data.get("expires_at")
            if not expires_str:
                return True

            expires_at = datetime.fromisoformat(expires_str)
            if datetime.now() >= expires_at:
                security_logger.warning("Session expired, rejecting")
                return True

            return False
        except (ValueError, TypeError) as e:
            security_logger.warning(f"Invalid session expiry format: {e}")
            return True

    def _log_security_event(self, event: str, details: dict | None = None) -> None:
        """Log security-related events with structured data."""
        log_data = {
            "event": event,
            "timestamp": datetime.now().isoformat(),
            "user_id": self.user_id,
            "session_file": str(self.session_file),
        }
        if details:
            log_data.update(details)

        security_logger.info(f"{event}: {log_data}")

    def _invalidate_session(self, reason: str) -> None:
        """Invalidate current session and clear session data."""
        self._log_security_event("SESSION_INVALIDATED", {"reason": reason})

        # Clear in-memory session data
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.session_id = None
        self.user_id = None
        self.tidal_session = None

        # Clear session file
        self._clear_session_file()

    def _load_session(self) -> None:
        """Load saved session from file if it exists with security validation."""
        try:
            if not self.session_file.exists():
                return

            # Verify session file permissions before loading
            try:
                file_stat = self.session_file.stat()
                file_mode = stat.filemode(file_stat.st_mode)
                if (
                    file_stat.st_mode & 0o077
                ):  # Check if group/other have any permissions
                    security_logger.warning(
                        f"Session file has insecure permissions: {file_mode}"
                    )
                    self._clear_session_file()
                    return
            except Exception as e:
                security_logger.warning(
                    f"Failed to check session file permissions: {e}"
                )
                return

            # Use secure file opening with proper error handling
            with open(self.session_file, encoding="utf-8") as f:
                session_data = json.load(f)

            # Validate session expiry before loading
            if self._is_session_expired(session_data):
                self._clear_session_file()
                self._log_security_event("SESSION_EXPIRED_ON_LOAD")
                return

            self.access_token = session_data.get("access_token")
            self.refresh_token = session_data.get("refresh_token")
            self.session_id = session_data.get("session_id")
            self.user_id = session_data.get("user_id")
            self.country_code = session_data.get("country_code", "US")

            # Parse expiration time
            expires_str = session_data.get("expires_at")
            if expires_str:
                self.token_expires_at = datetime.fromisoformat(expires_str)

            self._log_security_event(
                "SESSION_LOADED", {"user_id": self.user_id, "expires_at": expires_str}
            )
            logger.info("Loaded existing session from file")

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            security_logger.warning(f"Session file corrupted or invalid: {e}")
            self._clear_session_file()
            self._log_security_event("SESSION_LOAD_FAILED", {"error": str(e)})
        except (OSError, PermissionError) as e:
            security_logger.error(f"Permission error loading session file: {e}")
            self._log_security_event("SESSION_PERMISSION_ERROR", {"error": str(e)})

    def _save_session(self) -> None:
        """Save current session to file with secure permissions and logging."""
        try:
            session_data = {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "session_id": self.session_id,
                "user_id": self.user_id,
                "country_code": self.country_code,
                "expires_at": (
                    self.token_expires_at.isoformat() if self.token_expires_at else None
                ),
                "saved_at": datetime.now().isoformat(),
            }

            # Create session file with secure permissions from the start
            # Use os.open with secure flags, then write with json
            fd = os.open(
                self.session_file,
                os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                0o600,  # User read/write only
            )

            try:
                with os.fdopen(fd, "w") as f:
                    json.dump(session_data, f, indent=2)
            except Exception:
                os.close(fd)  # Ensure fd is closed on error
                raise

            # Verify permissions were set correctly
            file_stat = self.session_file.stat()
            if file_stat.st_mode & 0o077:
                security_logger.error(
                    "Failed to set secure permissions on session file"
                )
                self._clear_session_file()
                return

            self._log_security_event(
                "SESSION_SAVED",
                {
                    "user_id": self.user_id,
                    "expires_at": session_data.get("expires_at"),
                    "file_permissions": oct(file_stat.st_mode)[-3:],
                },
            )
            logger.info("Session saved to file with secure permissions")

        except Exception as e:
            security_logger.error(f"Failed to save session securely: {e}")
            self._log_security_event("SESSION_SAVE_FAILED", {"error": str(e)})
            # Clean up any potentially insecure file
            try:
                if self.session_file.exists():
                    self.session_file.unlink()
            except Exception:
                pass

    def _clear_session_file(self) -> None:
        """Clear the session file with security logging."""
        try:
            if self.session_file.exists():
                self.session_file.unlink()
                self._log_security_event("SESSION_FILE_CLEARED")
                logger.info("Session file cleared")
        except Exception as e:
            security_logger.error(f"Failed to clear session file: {e}")
            self._log_security_event("SESSION_CLEAR_FAILED", {"error": str(e)})

    def _generate_pkce_params(self) -> tuple[str, str]:
        """
        Generate PKCE code verifier and challenge.

        Returns:
            Tuple of (code_verifier, code_challenge)
        """
        # Generate code verifier (43-128 characters, URL-safe)
        code_verifier = (
            base64.urlsafe_b64encode(secrets.token_bytes(32))
            .decode("utf-8")
            .rstrip("=")
        )

        # Generate code challenge (SHA256 hash of verifier, base64 encoded)
        code_challenge = (
            base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode("utf-8")).digest()
            )
            .decode("utf-8")
            .rstrip("=")
        )

        return code_verifier, code_challenge

    async def authenticate(self) -> bool:
        """
        Perform initial authentication with Tidal using OAuth2 PKCE flow.

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            self._log_security_event("AUTH_ATTEMPT_STARTED")
            logger.info("Starting Tidal OAuth2 authentication...")

            # Try to use existing session first
            if await self._try_existing_session():
                self._log_security_event(
                    "AUTH_SUCCESS_EXISTING_SESSION", {"user_id": self.user_id}
                )
                return True

            # If no valid session, start OAuth2 flow
            result = await self._oauth2_flow()
            if result:
                self._log_security_event(
                    "AUTH_SUCCESS_NEW_SESSION", {"user_id": self.user_id}
                )
            else:
                self._log_security_event("AUTH_FAILED_OAUTH_FLOW")

            return result

        except Exception as e:
            self._log_security_event("AUTH_FAILED_EXCEPTION", {"error": str(e)})
            logger.error(f"Authentication failed: {e}")
            # Invalidate any partial session on authentication failure
            self._invalidate_session("authentication_exception")
            return False

    async def _try_existing_session(self) -> bool:
        """Try to use existing tidalapi session with enhanced error handling."""
        try:
            if not self.access_token:
                return False

            # Check if token is expired before attempting to use it
            if self.token_expires_at and datetime.now() >= self.token_expires_at:
                self._log_security_event("SESSION_TOKEN_EXPIRED")
                self._invalidate_session("token_expired")
                return False

            # Initialize tidalapi session
            self.tidal_session = tidalapi.Session()

            # Directly set the OAuth tokens instead of using load_oauth_session
            # which tries to call /sessions endpoint that returns 403
            self.tidal_session.access_token = self.access_token
            self.tidal_session.refresh_token = self.refresh_token
            self.tidal_session.token_type = "Bearer"
            self.tidal_session.session_id = self.session_id

            # Set expiry time if available
            if self.token_expires_at:
                # Convert datetime to seconds since epoch
                import time

                self.tidal_session.expiry_time = time.mktime(
                    self.token_expires_at.timetuple()
                )

            # Verify session is valid by making a test request
            try:
                user = self.tidal_session.user
                if user and user.id:
                    self.user_id = str(user.id)
                    self.country_code = user.country_code or "US"
                    self._log_security_event(
                        "SESSION_VALIDATION_SUCCESS", {"user_id": self.user_id}
                    )
                    logger.info(
                        f"Successfully loaded existing session for user {self.user_id}"
                    )
                    return True
                else:
                    self._log_security_event(
                        "SESSION_VALIDATION_FAILED", {"reason": "no_user_data"}
                    )
                    self._invalidate_session("session_validation_failed")
            except Exception as e:
                self._log_security_event("SESSION_VALIDATION_ERROR", {"error": str(e)})
                logger.warning(f"Existing session token is invalid: {e}")
                self._invalidate_session("session_validation_error")

            return False

        except Exception as e:
            self._log_security_event("SESSION_LOAD_ERROR", {"error": str(e)})
            logger.warning(f"Failed to load existing session: {e}")
            self._invalidate_session("session_load_error")
            return False

    async def _oauth2_flow(self) -> bool:
        """Perform OAuth2 PKCE authentication flow."""
        try:
            # Generate PKCE parameters
            code_verifier, code_challenge = self._generate_pkce_params()

            # Generate authorization URL - minimal params for compatibility
            auth_params = {
                "response_type": "code",
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
                "state": secrets.token_urlsafe(32),
            }

            auth_url = f"{self.OAUTH_BASE_URL}/authorize?{urlencode(auth_params)}"

            print("\nOpening browser for Tidal authentication...")
            print("If the browser doesn't open automatically, visit:")
            print(f"{auth_url}\n")

            # Open browser
            webbrowser.open(auth_url)

            # Start local server to capture callback
            auth_code = await self._capture_auth_code()
            if not auth_code:
                raise TidalAuthError("Failed to capture authorization code")

            # Exchange code for tokens
            success = await self._exchange_code_for_tokens(auth_code, code_verifier)
            return success

        except Exception as e:
            logger.error(f"OAuth2 flow failed: {e}")
            return False

    async def _capture_auth_code(self) -> str | None:
        """Start local server to capture OAuth2 callback."""
        import asyncio

        from aiohttp import web

        auth_code = None

        async def callback_handler(request):
            nonlocal auth_code

            # Extract authorization code from callback
            code = request.query.get("code")
            error = request.query.get("error")

            if error:
                logger.error(f"OAuth2 error: {error}")
                return web.Response(text=f"Authentication failed: {error}", status=400)

            if code:
                auth_code = code
                logger.info("Authorization code received")
                return web.Response(
                    text=("Authentication successful! You can close this window."),
                    content_type="text/html",
                )

            return web.Response(text="No authorization code received", status=400)

        try:
            app = web.Application()
            app.router.add_get("/callback", callback_handler)

            # Start server
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, "localhost", self.callback_port)
            await site.start()

            logger.info(
                f"Local callback server started on http://localhost:{self.callback_port}"
            )

            # Wait for callback (with timeout)
            timeout = 300  # 5 minutes
            start_time = asyncio.get_event_loop().time()

            while (
                auth_code is None
                and (asyncio.get_event_loop().time() - start_time) < timeout
            ):
                await asyncio.sleep(1)

            # Cleanup
            await runner.cleanup()

            if auth_code is None:
                logger.error("Timed out waiting for authorization")

            return auth_code

        except Exception as e:
            logger.error(f"Failed to capture auth code: {e}")
            return None

    async def _exchange_code_for_tokens(
        self, auth_code: str, code_verifier: str
    ) -> bool:
        """Exchange authorization code for access and refresh tokens."""
        try:
            token_data = {
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "code": auth_code,
                "redirect_uri": self.redirect_uri,
                "code_verifier": code_verifier,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.TOKEN_URL,
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise TidalAuthError(f"Token exchange failed: {error_text}")

                    token_response = await response.json()

            # Extract token information
            self.access_token = token_response.get("access_token")
            self.refresh_token = token_response.get("refresh_token")

            expires_in = token_response.get("expires_in", 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

            if not self.access_token:
                raise TidalAuthError("No access token received")

            # Initialize Tidal session with new tokens
            self.tidal_session = tidalapi.Session()

            # Directly set the OAuth tokens instead of using load_oauth_session
            self.tidal_session.access_token = self.access_token
            self.tidal_session.refresh_token = self.refresh_token
            self.tidal_session.token_type = "Bearer"

            # Set expiry time if available
            if self.token_expires_at:
                import time

                self.tidal_session.expiry_time = time.mktime(
                    self.token_expires_at.timetuple()
                )

            # Verify and get user information
            try:
                user = self.tidal_session.user
                if user:
                    self.user_id = str(user.id)
                    self.country_code = user.country_code or "US"

                    # Save session
                    self._save_session()

                    logger.info(f"Authentication successful for user {self.user_id}")
                    return True
                else:
                    error_msg = "Failed to get user information with new tokens"
                    raise TidalAuthError(error_msg)
            except Exception as e:
                error_msg = f"Failed to initialize Tidal session: {e}"
                raise TidalAuthError(error_msg) from e

        except Exception as e:
            logger.error(f"Token exchange failed: {e}")
            return False

    def is_authenticated(self) -> bool:
        """
        Check if current session is authenticated with enhanced security validation.

        Returns:
            True if authenticated and token is valid
        """
        if not self.access_token:
            return False

        # Check token expiration
        if self.token_expires_at and datetime.now() >= self.token_expires_at:
            self._log_security_event("AUTH_CHECK_TOKEN_EXPIRED")
            self._invalidate_session("token_expired_on_check")
            return False

        # Check if tidalapi session is valid
        if self.tidal_session:
            try:
                # Try to access user info to verify session
                user = self.tidal_session.user
                is_valid = user is not None

                if not is_valid:
                    self._log_security_event("AUTH_CHECK_INVALID_SESSION")
                    self._invalidate_session("session_invalid_on_check")

                return is_valid
            except Exception as e:
                self._log_security_event("AUTH_CHECK_SESSION_ERROR", {"error": str(e)})
                self._invalidate_session("session_error_on_check")
                return False

        # Without a working session, we're not fully authenticated
        return False

    async def refresh_access_token(self) -> bool:
        """
        Refresh the access token using refresh token with enhanced security.

        Returns:
            True if refresh successful, False otherwise
        """
        if not self.refresh_token:
            self._log_security_event("TOKEN_REFRESH_NO_REFRESH_TOKEN")
            logger.error("No refresh token available")
            return False

        try:
            self._log_security_event("TOKEN_REFRESH_STARTED")
            logger.info("Refreshing access token...")

            token_data = {
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "refresh_token": self.refresh_token,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.TOKEN_URL,
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self._log_security_event(
                            "TOKEN_REFRESH_FAILED",
                            {"status_code": response.status, "error": error_text},
                        )
                        logger.error(f"Token refresh failed: {error_text}")
                        # Invalidate session on refresh failure
                        self._invalidate_session("token_refresh_failed")
                        return False

                    token_response = await response.json()

            # Update tokens
            self.access_token = token_response.get("access_token")

            # Refresh token might be rotated
            new_refresh_token = token_response.get("refresh_token")
            if new_refresh_token:
                self.refresh_token = new_refresh_token

            expires_in = token_response.get("expires_in", 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

            # Update tidalapi session
            if self.tidal_session:
                self.tidal_session.access_token = self.access_token
                self.tidal_session.refresh_token = self.refresh_token
                self.tidal_session.token_type = "Bearer"

                if self.token_expires_at:
                    import time

                    self.tidal_session.expiry_time = time.mktime(
                        self.token_expires_at.timetuple()
                    )

            # Save updated session
            self._save_session()

            self._log_security_event(
                "TOKEN_REFRESH_SUCCESS",
                {
                    "new_expires_at": (
                        self.token_expires_at.isoformat()
                        if self.token_expires_at
                        else None
                    )
                },
            )
            logger.info("Access token refreshed successfully")
            return True

        except Exception as e:
            self._log_security_event("TOKEN_REFRESH_EXCEPTION", {"error": str(e)})
            logger.error(f"Token refresh failed: {e}")
            # Invalidate session on refresh exception
            self._invalidate_session("token_refresh_exception")
            return False

    async def ensure_valid_token(self) -> bool:
        """
        Ensure we have a valid access token, refreshing if necessary.

        Returns:
            True if valid token is available
        """
        if self.is_authenticated():
            return True

        # Try to refresh token firs
        if self.refresh_token:
            if await self.refresh_access_token():
                return True

        # If refresh failed, need to re-authenticate
        logger.info("Token refresh failed, re-authenticating...")
        return await self.authenticate()

    def get_auth_headers(self) -> dict[str, str]:
        """
        Get authentication headers for API requests.

        Returns:
            Dictionary of HTTP headers for authenticated requests
        """
        if not self.access_token:
            raise ValueError("No access token available")

        return {
            "Authorization": f"Bearer {self.access_token}",
            "X-Tidal-Token": self.access_token,
        }

    def get_tidal_session(self) -> tidalapi.Session:
        """
        Get the tidalapi Session object.

        Returns:
            tidalapi Session objec

        Raises:
            TidalAuthError: If not authenticated
        """
        if not self.tidal_session or not self.is_authenticated():
            raise TidalAuthError("Not authenticated. Call authenticate() first.")

        return self.tidal_session

    async def logout(self) -> None:
        """Clear authentication tokens and session data with security logging."""
        try:
            self._log_security_event("LOGOUT_STARTED", {"user_id": self.user_id})

            # Revoke tokens if possible
            if self.access_token:
                await self._revoke_tokens()
        except Exception as e:
            self._log_security_event("LOGOUT_TOKEN_REVOKE_FAILED", {"error": str(e)})
            logger.warning(f"Failed to revoke tokens: {e}")

        # Clear all tokens and session data
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.session_id = None
        old_user_id = self.user_id  # Store for logging
        self.user_id = None
        self.tidal_session = None

        # Clear session file
        self._clear_session_file()

        self._log_security_event("LOGOUT_COMPLETED", {"user_id": old_user_id})
        logger.info("Logged out from Tidal")

    async def _revoke_tokens(self) -> None:
        """Revoke access and refresh tokens with Tidal."""
        try:
            # Tidal doesn't have a public revoke endpoint,
            # so we just invalidate locally
            logger.info("Tokens cleared locally")
        except Exception as e:
            logger.warning(f"Token revocation failed: {e}")

    def get_user_info(self) -> dict[str, Any] | None:
        """
        Get current user information.

        Returns:
            Dictionary with user info or None if not authenticated
        """
        try:
            if not self.is_authenticated() or not self.tidal_session:
                return None

            user = self.tidal_session.user
            if not user:
                return None

            return {
                "id": user.id,
                "username": getattr(user, "username", None),
                "country_code": user.country_code,
                "subscription": {
                    "type": getattr(user, "subscription", {}).get("type"),
                    "valid": getattr(user, "subscription", {}).get("valid", False),
                },
            }

        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None
