"""
Tidal Authentication Manager

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
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import aiohttp
import tidalapi

logger = logging.getLogger(__name__)


class TidalAuthError(Exception):
    """Custom exception for Tidal authentication errors."""

    pass


class TidalAuth:
    """
    Manages authentication and authorization for Tidal API.

    Handles OAuth2 flow with PKCE, token refresh, and session managemen
    to ensure secure and persistent access to Tidal services.
    """

    # OAuth2 endpoints for Tidal
    OAUTH_BASE_URL = "https://login.tidal.com/oauth2"
    TOKEN_URL = "https://auth.tidal.com/v1/oauth2/token"
    CLIENT_ID = "zU4XHVVkc2tDPo4t"  # Tidal's public client ID
    REDIRECT_URI = "http://localhost:8080/callback"

    def __init__(
        self, client_id: str | None = None, client_secret: str | None = None
    ):
        """
        Initialize Tidal authentication manager.

        Args:
            client_id: Tidal API client ID (optional, uses default if no
                      provided)
            client_secret: Tidal API client secret (not needed for PKCE flow)
        """
        self.client_id = client_id or self.CLIENT_ID
        self.client_secret = client_secret
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.token_expires_at: datetime | None = None
        self.session_id: str | None = None
        self.country_code: str = "US"  # Default country code
        self.user_id: str | None = None

        # Session file path
        self.session_file = Path.home() / ".tidal-mcp" / "session.json"
        self.session_file.parent.mkdir(parents=True, exist_ok=True)

        # Tidal API clien
        self.tidal_session: tidalapi.Session | None = None

        # Load existing session if available
        self._load_session()

    def _load_session(self) -> None:
        """Load saved session from file if it exists."""
        try:
            if self.session_file.exists():
                with open(self.session_file) as f:
                    session_data = json.load(f)

                self.access_token = session_data.get("access_token")
                self.refresh_token = session_data.get("refresh_token")
                self.session_id = session_data.get("session_id")
                self.user_id = session_data.get("user_id")
                self.country_code = session_data.get("country_code", "US")

                # Parse expiration time
                expires_str = session_data.get("expires_at")
                if expires_str:
                    self.token_expires_at = datetime.fromisoformat(expires_str)

                logger.info("Loaded existing session from file")

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to load session file: {e}")
            self._clear_session_file()
        except (OSError, PermissionError) as e:
            logger.warning(f"Permission error loading session file: {e}")

    def _save_session(self) -> None:
        """Save current session to file."""
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

            with open(self.session_file, "w") as f:
                json.dump(session_data, f, indent=2)

            # Set restrictive permissions (readable only by owner)
            os.chmod(self.session_file, 0o600)
            logger.info("Session saved to file")

        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    def _clear_session_file(self) -> None:
        """Clear the session file."""
        try:
            if self.session_file.exists():
                self.session_file.unlink()
                logger.info("Session file cleared")
        except Exception as e:
            logger.error(f"Failed to clear session file: {e}")

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
            logger.info("Starting Tidal OAuth2 authentication...")

            # Try to use existing session firs
            if await self._try_existing_session():
                return True

            # If no valid session, start OAuth2 flow
            return await self._oauth2_flow()

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    async def _try_existing_session(self) -> bool:
        """Try to use existing tidalapi session."""
        try:
            if not self.access_token:
                return False

            # Initialize tidalapi session
            self.tidal_session = tidalapi.Session()

            # Try to load session using access token
            if self.tidal_session.load_oauth_session(
                token_type="Bearer",
                access_token=self.access_token,
                refresh_token=self.refresh_token,
            ):
                # Verify session is valid by making a test reques
                try:
                    user = self.tidal_session.user
                    if user and user.id:
                        self.user_id = str(user.id)
                        self.country_code = user.country_code or "US"
                        logger.info(
                            "Successfully loaded existing session for user "
                            f"{self.user_id}"
                        )
                        return True
                except Exception:
                    logger.warning("Existing session token is invalid")

            return False

        except Exception as e:
            logger.warning(f"Failed to load existing session: {e}")
            return False

    async def _oauth2_flow(self) -> bool:
        """Perform OAuth2 PKCE authentication flow."""
        try:
            # Generate PKCE parameters
            code_verifier, code_challenge = self._generate_pkce_params()

            # Generate authorization URL
            auth_params = {
                "response_type": "code",
                "client_id": self.client_id,
                "redirect_uri": self.REDIRECT_URI,
                "scope": "r_usr w_usr w_sub",
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
                "state": secrets.token_urlsafe(32),
            }

            auth_url = f"{self.OAUTH_BASE_URL}/auth?{urlencode(auth_params)}"

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
            site = web.TCPSite(runner, "localhost", 8080)
            await site.start()

            logger.info("Local callback server started on http://localhost:8080")

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
                "redirect_uri": self.REDIRECT_URI,
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

            if self.tidal_session.load_oauth_session(
                token_type="Bearer",
                access_token=self.access_token,
                refresh_token=self.refresh_token,
            ):
                # Get user information
                user = self.tidal_session.user
                if user:
                    self.user_id = str(user.id)
                    self.country_code = user.country_code or "US"

                # Save session
                self._save_session()

                logger.info(f"Authentication successful for user {self.user_id}")
                return True
            else:
                error_msg = "Failed to initialize Tidal session with tokens"
                raise TidalAuthError(error_msg)

        except Exception as e:
            logger.error(f"Token exchange failed: {e}")
            return False

    def is_authenticated(self) -> bool:
        """
        Check if current session is authenticated.

        Returns:
            True if authenticated and token is valid
        """
        if not self.access_token:
            return False

        if self.token_expires_at and datetime.now() >= self.token_expires_at:
            return False

        # Check if tidalapi session is valid
        if self.tidal_session:
            try:
                # Try to access user info to verify session
                user = self.tidal_session.user
                return user is not None
            except Exception:
                return False

        # Without a working session, we're not fully authenticated
        return False

    async def refresh_access_token(self) -> bool:
        """
        Refresh the access token using refresh token.

        Returns:
            True if refresh successful, False otherwise
        """
        if not self.refresh_token:
            logger.error("No refresh token available")
            return False

        try:
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
                        logger.error(f"Token refresh failed: {error_text}")
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
                self.tidal_session.load_oauth_session(
                    token_type="Bearer",
                    access_token=self.access_token,
                    refresh_token=self.refresh_token,
                )

            # Save updated session
            self._save_session()

            logger.info("Access token refreshed successfully")
            return True

        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
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
        """Clear authentication tokens and session data."""
        try:
            # Revoke tokens if possible
            if self.access_token:
                await self._revoke_tokens()
        except Exception as e:
            logger.warning(f"Failed to revoke tokens: {e}")

        # Clear all tokens and session data
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.session_id = None
        self.user_id = None
        self.tidal_session = None

        # Clear session file
        self._clear_session_file()

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
