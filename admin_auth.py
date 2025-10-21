"""Admin authentication module for securing admin endpoints."""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict
import os


class AdminAuth:
    """Simple session-based authentication for admin users."""

    def __init__(self, username: str, password: str):
        """Initialize admin auth with credentials."""
        self.admin_username = username
        self.admin_password_hash = self._hash_password(password)
        self.sessions: Dict[str, Dict] = {}  # token -> session data
        self.session_duration = timedelta(hours=24)

    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_credentials(self, username: str, password: str) -> bool:
        """Verify username and password."""
        return (
            username == self.admin_username and
            self._hash_password(password) == self.admin_password_hash
        )

    def create_session(self, username: str) -> str:
        """Create a new session and return the session token."""
        token = secrets.token_urlsafe(32)
        self.sessions[token] = {
            'username': username,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + self.session_duration
        }
        return token

    def verify_session(self, token: Optional[str]) -> bool:
        """Verify if a session token is valid."""
        if not token:
            return False

        session = self.sessions.get(token)
        if not session:
            return False

        # Check if session has expired
        if datetime.utcnow() > session['expires_at']:
            del self.sessions[token]
            return False

        return True

    def get_session_info(self, token: str) -> Optional[Dict]:
        """Get session information."""
        return self.sessions.get(token)

    def delete_session(self, token: str):
        """Delete a session (logout)."""
        if token in self.sessions:
            del self.sessions[token]

    def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        now = datetime.utcnow()
        expired_tokens = [
            token for token, session in self.sessions.items()
            if now > session['expires_at']
        ]
        for token in expired_tokens:
            del self.sessions[token]


# Global admin auth instance (will be initialized in proxy_server.py)
admin_auth: Optional[AdminAuth] = None


def init_admin_auth():
    """Initialize admin auth from environment variables."""
    global admin_auth

    username = os.getenv('ADMIN_USERNAME', 'admin')
    password = os.getenv('ADMIN_PASSWORD', 'changeme')

    if password == 'changeme':
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            "⚠️  WARNING: Using default admin password! "
            "Please set ADMIN_PASSWORD in .env file for security."
        )

    admin_auth = AdminAuth(username, password)
    return admin_auth
