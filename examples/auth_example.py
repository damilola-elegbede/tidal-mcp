#!/usr/bin/env python3
"""
Tidal Authentication Example

Simple example demonstrating how to use the TidalAuth class
for OAuth2 authentication with PKCE flow.
"""

import asyncio
import logging
from tidal_mcp.auth import TidalAuth, TidalAuthError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_authentication():
    """Test the complete authentication flow."""
    logger.info("Testing Tidal Authentication")
    logger.info("=" * 40)
    
    try:
        # Initialize authentication manager
        auth = TidalAuth()
        
        # Check if already authenticated
        if auth.is_authenticated():
            logger.info("Already authenticated!")
            user_info = auth.get_user_info()
            if user_info:
                logger.info(f"User: {user_info['id']} ({user_info['country_code']})")
            return auth
        
        # Perform authentication
        logger.info("Starting authentication flow...")
        success = await auth.authenticate()
        
        if success:
            logger.info("Authentication successful!")
            
            # Get user information
            user_info = auth.get_user_info()
            if user_info:
                logger.info(f"User ID: {user_info['id']}")
                logger.info(f"Username: {user_info.get('username', 'N/A')}")
                logger.info(f"Country: {user_info['country_code']}")
                logger.info(f"Subscription Type: {user_info['subscription']['type']}")
                logger.info(f"Subscription Valid: {user_info['subscription']['valid']}")
            
            # Test getting Tidal session
            try:
                tidal_session = auth.get_tidal_session()
                logger.info("Tidal session obtained successfully")
                
                # Test session with a simple request
                user = tidal_session.user
                logger.info(f"Session verified - User: {user.id}")
                
            except TidalAuthError as e:
                logger.error(f"Failed to get Tidal session: {e}")
            
            return auth
            
        else:
            logger.error("Authentication failed")
            return None
            
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return None


async def test_token_refresh():
    """Test token refresh functionality."""
    logger.info("\nTesting Token Refresh")
    logger.info("=" * 40)
    
    try:
        auth = TidalAuth()
        
        if not auth.refresh_token:
            logger.info("No refresh token available - authenticate first")
            return
        
        # Force token refresh
        logger.info("Attempting to refresh token...")
        success = await auth.refresh_access_token()
        
        if success:
            logger.info("Token refresh successful!")
            logger.info(f"New token expires at: {auth.token_expires_at}")
        else:
            logger.error("Token refresh failed")
            
    except Exception as e:
        logger.error(f"Token refresh error: {e}")


async def test_session_persistence():
    """Test session file persistence."""
    logger.info("\nTesting Session Persistence")
    logger.info("=" * 40)
    
    try:
        # Create first auth instance
        auth1 = TidalAuth()
        
        if auth1.is_authenticated():
            logger.info("Session loaded from file successfully")
            logger.info(f"Access token (first 20 chars): {auth1.access_token[:20]}...")
            logger.info(f"Session file: {auth1.session_file}")
            
            # Create second auth instance (should load same session)
            auth2 = TidalAuth()
            
            if auth2.is_authenticated():
                logger.info("Second instance also loaded session successfully")
                
                # Verify tokens match
                if auth1.access_token == auth2.access_token:
                    logger.info("Session persistence verified - tokens match")
                else:
                    logger.warning("Session persistence issue - tokens don't match")
            else:
                logger.error("Second instance failed to load session")
        else:
            logger.info("No existing session found - authenticate first")
            
    except Exception as e:
        logger.error(f"Session persistence error: {e}")


async def test_logout():
    """Test logout functionality."""
    logger.info("\nTesting Logout")
    logger.info("=" * 40)
    
    try:
        auth = TidalAuth()
        
        if auth.is_authenticated():
            logger.info("Currently authenticated - logging out...")
            await auth.logout()
            
            # Verify logout
            if not auth.is_authenticated():
                logger.info("Logout successful - no longer authenticated")
                
                # Verify session file is cleared
                if not auth.session_file.exists():
                    logger.info("Session file cleared successfully")
                else:
                    logger.warning("Session file still exists after logout")
            else:
                logger.warning("Still authenticated after logout")
        else:
            logger.info("Not currently authenticated - nothing to logout")
            
    except Exception as e:
        logger.error(f"Logout error: {e}")


async def main():
    """Run all authentication tests."""
    logger.info("Tidal MCP Authentication Example")
    logger.info("=" * 50)
    
    # Test complete flow
    auth = await test_authentication()
    
    if auth:
        # Test additional functionality
        await test_token_refresh()
        await test_session_persistence()
        
        # Ask user if they want to logout
        print("\nWould you like to logout and clear the session? (y/N): ", end="")
        try:
            response = input().strip().lower()
            if response in ['y', 'yes']:
                await test_logout()
            else:
                logger.info("Keeping session active")
        except (EOFError, KeyboardInterrupt):
            logger.info("\nKeeping session active")
    
    logger.info("\nAuthentication example completed!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nExample interrupted by user")
    except Exception as e:
        logger.error(f"Example failed: {e}")