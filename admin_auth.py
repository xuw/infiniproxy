"""Admin authentication module for securing admin endpoints."""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict
import os
import sqlite3
import json
from contextlib import contextmanager


class AdminAuth:
    """Session-based authentication for admin users with database-backed sessions."""

    def __init__(self, username: str, password: str, db_path: str = "proxy_users.db"):
        """Initialize admin auth with credentials and database path."""
        self.admin_username = username
        self.admin_password_hash = self._hash_password(password)
        self.db_path = db_path
        self.session_duration = timedelta(hours=24)
        self._init_sessions_table()

    @contextmanager
    def _get_db(self):
        """Get database connection context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_sessions_table(self):
        """Initialize the sessions table in the database."""
        with self._get_db() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS admin_sessions (
                    token TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
            ''')
            # Create index for faster expiration cleanup
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_admin_sessions_expires
                ON admin_sessions(expires_at)
            ''')
            conn.commit()

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
        created_at = datetime.utcnow()
        expires_at = created_at + self.session_duration

        with self._get_db() as conn:
            conn.execute('''
                INSERT INTO admin_sessions (token, username, created_at, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (token, username, created_at.isoformat(), expires_at.isoformat()))
            conn.commit()

        return token

    def verify_session(self, token: Optional[str]) -> bool:
        """Verify if a session token is valid."""
        if not token:
            return False

        with self._get_db() as conn:
            cursor = conn.execute('''
                SELECT expires_at FROM admin_sessions
                WHERE token = ?
            ''', (token,))
            row = cursor.fetchone()

            if not row:
                return False

            # Check if session has expired
            expires_at = datetime.fromisoformat(row['expires_at'])
            if datetime.utcnow() > expires_at:
                # Delete expired session
                conn.execute('DELETE FROM admin_sessions WHERE token = ?', (token,))
                conn.commit()
                return False

            return True

    def get_session_info(self, token: str) -> Optional[Dict]:
        """Get session information."""
        with self._get_db() as conn:
            cursor = conn.execute('''
                SELECT username, created_at, expires_at
                FROM admin_sessions
                WHERE token = ?
            ''', (token,))
            row = cursor.fetchone()

            if not row:
                return None

            return {
                'username': row['username'],
                'created_at': datetime.fromisoformat(row['created_at']),
                'expires_at': datetime.fromisoformat(row['expires_at'])
            }

    def delete_session(self, token: str):
        """Delete a session (logout)."""
        with self._get_db() as conn:
            conn.execute('DELETE FROM admin_sessions WHERE token = ?', (token,))
            conn.commit()

    def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        with self._get_db() as conn:
            now = datetime.utcnow()
            conn.execute('''
                DELETE FROM admin_sessions
                WHERE expires_at < ?
            ''', (now.isoformat(),))
            conn.commit()


# Global admin auth instance (will be initialized in proxy_server.py)
admin_auth: Optional[AdminAuth] = None


def init_admin_auth(db_path: str = "proxy_users.db"):
    """Initialize admin auth from environment variables with database-backed sessions."""
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

    admin_auth = AdminAuth(username, password, db_path)
    return admin_auth
