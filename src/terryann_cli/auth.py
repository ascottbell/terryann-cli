"""Authentication management for TerryAnn CLI.

Uses Supabase Auth for user authentication.
Tokens are stored in ~/.terryann/credentials.json
"""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Config paths
CONFIG_DIR = Path.home() / ".terryann"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"

# Supabase configuration - same as web UI
# These are public (publishable) keys, safe to embed
SUPABASE_URL = os.environ.get(
    "TERRYANN_SUPABASE_URL",
    "https://fstlpkeycotygqvhqmud.supabase.co"
)
SUPABASE_ANON_KEY = os.environ.get(
    "TERRYANN_SUPABASE_ANON_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZzdGxwa2V5Y290eWdxdmhxbXVkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYyNjM4MTEsImV4cCI6MjA4MTgzOTgxMX0.Oo7xpirlQeEygPy-g-WJSIOtFfBbJlbI3G1WftliXt8"
)


@dataclass
class AuthCredentials:
    """Stored authentication credentials."""
    access_token: str
    refresh_token: str
    user_id: str
    email: str
    first_name: Optional[str]
    expires_at: datetime


@dataclass
class AuthUser:
    """Current authenticated user."""
    user_id: str
    email: str
    access_token: str
    first_name: Optional[str] = None
    is_authenticated: bool = True


def _ensure_config_dir() -> None:
    """Ensure config directory exists with proper permissions."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    # Set directory permissions to user-only (700)
    os.chmod(CONFIG_DIR, 0o700)


def _get_supabase_client() -> Client:
    """Create Supabase client for auth operations."""
    # Note: We handle token persistence ourselves in ~/.terryann/credentials.json
    # Don't use ClientOptions due to bug in supabase-py 2.24.0+
    # See: https://github.com/supabase/supabase-py/issues/1306
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def save_credentials(creds: AuthCredentials) -> None:
    """Save credentials to file with secure permissions."""
    _ensure_config_dir()

    data = {
        "access_token": creds.access_token,
        "refresh_token": creds.refresh_token,
        "user_id": creds.user_id,
        "email": creds.email,
        "first_name": creds.first_name,
        "expires_at": creds.expires_at.isoformat(),
    }

    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(data, f, indent=2)

    # Set file permissions to user-only (600)
    os.chmod(CREDENTIALS_FILE, 0o600)
    logger.debug(f"Credentials saved to {CREDENTIALS_FILE}")


def load_credentials() -> Optional[AuthCredentials]:
    """Load credentials from file if they exist and are valid."""
    if not CREDENTIALS_FILE.exists():
        return None

    try:
        with open(CREDENTIALS_FILE, "r") as f:
            data = json.load(f)

        expires_at = datetime.fromisoformat(data["expires_at"])

        return AuthCredentials(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            user_id=data["user_id"],
            email=data["email"],
            first_name=data.get("first_name"),
            expires_at=expires_at,
        )
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning(f"Failed to load credentials: {e}")
        return None


def clear_credentials() -> bool:
    """Remove stored credentials."""
    if CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.unlink()
        logger.debug("Credentials cleared")
        return True
    return False


def login(email: str, password: str) -> AuthUser:
    """
    Authenticate user with email and password.

    Args:
        email: User email
        password: User password

    Returns:
        AuthUser with user info and access token

    Raises:
        Exception: If authentication fails
    """
    client = _get_supabase_client()

    response = client.auth.sign_in_with_password({
        "email": email,
        "password": password,
    })

    if not response.user or not response.session:
        raise Exception("Authentication failed: No user or session returned")

    user = response.user
    session = response.session

    # Calculate expiration time
    expires_at = datetime.fromtimestamp(session.expires_at, tz=timezone.utc)

    # Fetch user profile to get first_name
    first_name = None
    try:
        profile_response = client.table("profiles").select("first_name").eq("id", user.id).single().execute()
        if profile_response.data:
            first_name = profile_response.data.get("first_name")
    except Exception as e:
        logger.debug(f"Could not fetch profile for first_name: {e}")

    # Save credentials for future sessions
    creds = AuthCredentials(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        user_id=user.id,
        email=user.email or email,
        first_name=first_name,
        expires_at=expires_at,
    )
    save_credentials(creds)

    return AuthUser(
        user_id=user.id,
        email=user.email or email,
        access_token=session.access_token,
        first_name=first_name,
    )


def logout() -> bool:
    """
    Log out current user and clear stored credentials.

    Returns:
        True if credentials were cleared, False if not logged in
    """
    creds = load_credentials()
    if creds:
        try:
            # Try to sign out from Supabase (invalidate token)
            client = _get_supabase_client()
            client.auth.sign_out()
        except Exception as e:
            logger.debug(f"Supabase sign out failed (token may be expired): {e}")

    return clear_credentials()


def get_current_user() -> Optional[AuthUser]:
    """
    Get the current authenticated user.

    Loads credentials from storage and refreshes token if needed.

    Returns:
        AuthUser if logged in, None otherwise
    """
    creds = load_credentials()
    if not creds:
        return None

    # Check if token is expired or about to expire (within 5 minutes)
    now = datetime.now(timezone.utc)
    expires_soon = creds.expires_at <= now or (creds.expires_at - now).total_seconds() < 300

    if expires_soon:
        # Try to refresh the token
        try:
            client = _get_supabase_client()
            response = client.auth.refresh_session(creds.refresh_token)

            if response.session:
                session = response.session
                user = response.user

                # Update stored credentials (keep first_name from original creds)
                new_creds = AuthCredentials(
                    access_token=session.access_token,
                    refresh_token=session.refresh_token,
                    user_id=user.id if user else creds.user_id,
                    email=user.email if user else creds.email,
                    first_name=creds.first_name,
                    expires_at=datetime.fromtimestamp(session.expires_at, tz=timezone.utc),
                )
                save_credentials(new_creds)

                return AuthUser(
                    user_id=new_creds.user_id,
                    email=new_creds.email,
                    access_token=new_creds.access_token,
                    first_name=new_creds.first_name,
                )
        except Exception as e:
            logger.warning(f"Token refresh failed: {e}")
            # Token refresh failed, credentials are invalid
            clear_credentials()
            return None

    # Token is still valid
    return AuthUser(
        user_id=creds.user_id,
        email=creds.email,
        access_token=creds.access_token,
        first_name=creds.first_name,
    )


def require_auth() -> AuthUser:
    """
    Get current user or raise exception if not logged in.

    Returns:
        AuthUser

    Raises:
        Exception: If not logged in
    """
    user = get_current_user()
    if not user:
        raise Exception("Not logged in. Run 'terryann login' first.")
    return user
