"""User and API key management system."""

import sqlite3
import secrets
import hashlib
from datetime import datetime
from typing import Optional, Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class UserManager:
    """Manages users, API keys, and usage tracking."""

    def __init__(self, db_path: str = "proxy_users.db"):
        """Initialize the user manager with a database path."""
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                created_at TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        """)

        # Create API keys table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                key_hash TEXT UNIQUE NOT NULL,
                key_prefix TEXT NOT NULL,
                name TEXT,
                model_name TEXT,
                created_at TEXT NOT NULL,
                last_used_at TEXT,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        # Create usage tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key_id INTEGER NOT NULL,
                endpoint TEXT NOT NULL,
                model TEXT,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                request_id TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (api_key_id) REFERENCES api_keys (id)
            )
        """)

        # Create indices for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_api_keys_hash
            ON api_keys(key_hash)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_usage_api_key
            ON usage_records(api_key_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_usage_timestamp
            ON usage_records(timestamp)
        """)

        # Migration: Add model_name column if it doesn't exist
        cursor.execute("PRAGMA table_info(api_keys)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'model_name' not in columns:
            logger.info("Migrating database: adding model_name column to api_keys")
            cursor.execute("ALTER TABLE api_keys ADD COLUMN model_name TEXT")

        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")

    @staticmethod
    def _hash_key(api_key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()

    @staticmethod
    def _generate_api_key() -> str:
        """Generate a new API key."""
        # Format: sk-{32 random hex characters}
        return f"sk-{secrets.token_hex(32)}"

    def create_user(self, username: str, email: Optional[str] = None) -> int:
        """
        Create a new user.

        Returns:
            User ID of the created user
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, email, created_at) VALUES (?, ?, ?)",
                (username, email, datetime.utcnow().isoformat())
            )
            conn.commit()
            user_id = cursor.lastrowid
            logger.info(f"Created user: {username} (ID: {user_id})")
            return user_id
        except sqlite3.IntegrityError:
            logger.error(f"User {username} already exists")
            raise ValueError(f"User {username} already exists")
        finally:
            conn.close()

    def create_api_key(self, user_id: int, name: Optional[str] = None) -> str:
        """
        Create a new API key for a user.

        Returns:
            The generated API key (only shown once)
        """
        api_key = self._generate_api_key()
        key_hash = self._hash_key(api_key)
        key_prefix = api_key[:12]  # Store prefix for identification

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """INSERT INTO api_keys
                   (user_id, key_hash, key_prefix, name, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, key_hash, key_prefix, name, datetime.utcnow().isoformat())
            )
            conn.commit()
            api_key_id = cursor.lastrowid
            logger.info(f"Created API key for user_id {user_id} (key_id: {api_key_id})")
            return api_key
        finally:
            conn.close()

    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Validate an API key and return user information.

        Returns:
            Dict with user and api_key info if valid, None otherwise
        """
        key_hash = self._hash_key(api_key)

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    u.id as user_id,
                    u.username,
                    u.email,
                    u.is_active as user_active,
                    a.id as api_key_id,
                    a.name as api_key_name,
                    a.model_name as model_name,
                    a.is_active as key_active
                FROM api_keys a
                JOIN users u ON a.user_id = u.id
                WHERE a.key_hash = ?
            """, (key_hash,))

            row = cursor.fetchone()

            if row is None:
                return None

            if not row['user_active'] or not row['key_active']:
                logger.warning(f"Inactive API key or user attempted access")
                return None

            # Update last_used_at
            cursor.execute(
                "UPDATE api_keys SET last_used_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), row['api_key_id'])
            )
            conn.commit()

            return dict(row)

        finally:
            conn.close()

    def track_usage(
        self,
        api_key_id: int,
        endpoint: str,
        input_tokens: int,
        output_tokens: int,
        model: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        """Track token usage for an API key."""
        total_tokens = input_tokens + output_tokens

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO usage_records
                (api_key_id, endpoint, model, input_tokens, output_tokens,
                 total_tokens, request_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                api_key_id, endpoint, model, input_tokens, output_tokens,
                total_tokens, request_id, datetime.utcnow().isoformat()
            ))
            conn.commit()
        finally:
            conn.close()

    def get_user_usage(
        self,
        user_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get usage statistics for a user.

        Returns:
            Dict with usage statistics
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Build query with optional date filters
            query = """
                SELECT
                    COUNT(*) as total_requests,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens,
                    SUM(total_tokens) as total_tokens,
                    endpoint,
                    model
                FROM usage_records ur
                JOIN api_keys ak ON ur.api_key_id = ak.id
                WHERE ak.user_id = ?
            """
            params = [user_id]

            if start_date:
                query += " AND ur.timestamp >= ?"
                params.append(start_date)

            if end_date:
                query += " AND ur.timestamp <= ?"
                params.append(end_date)

            query += " GROUP BY endpoint, model"

            cursor.execute(query, params)

            usage_by_endpoint = []
            total_input = 0
            total_output = 0
            total_requests = 0

            for row in cursor.fetchall():
                usage_by_endpoint.append(dict(row))
                total_input += row['total_input_tokens'] or 0
                total_output += row['total_output_tokens'] or 0
                total_requests += row['total_requests'] or 0

            return {
                'user_id': user_id,
                'total_requests': total_requests,
                'total_input_tokens': total_input,
                'total_output_tokens': total_output,
                'total_tokens': total_input + total_output,
                'usage_by_endpoint': usage_by_endpoint,
                'start_date': start_date,
                'end_date': end_date
            }

        finally:
            conn.close()

    def get_api_key_usage(self, api_key_id: int) -> Dict[str, Any]:
        """Get usage statistics for a specific API key."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    COUNT(*) as total_requests,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens,
                    SUM(total_tokens) as total_tokens
                FROM usage_records
                WHERE api_key_id = ?
            """, (api_key_id,))

            row = cursor.fetchone()

            return {
                'api_key_id': api_key_id,
                'total_requests': row['total_requests'] or 0,
                'total_input_tokens': row['total_input_tokens'] or 0,
                'total_output_tokens': row['total_output_tokens'] or 0,
                'total_tokens': row['total_tokens'] or 0
            }

        finally:
            conn.close()

    def list_users(self) -> List[Dict[str, Any]]:
        """List all users."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def list_api_keys(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """List API keys, optionally filtered by user."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            if user_id:
                cursor.execute("""
                    SELECT id, user_id, key_prefix, name, model_name, created_at,
                           last_used_at, is_active
                    FROM api_keys
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT id, user_id, key_prefix, name, model_name, created_at,
                           last_used_at, is_active
                    FROM api_keys
                    ORDER BY created_at DESC
                """)

            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def deactivate_api_key(self, api_key_id: int):
        """Deactivate an API key."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "UPDATE api_keys SET is_active = 0 WHERE id = ?",
                (api_key_id,)
            )
            conn.commit()
            logger.info(f"Deactivated API key {api_key_id}")
        finally:
            conn.close()

    def get_model_setting(self, api_key_id: int) -> Optional[str]:
        """
        Get the model name setting for an API key.

        Returns:
            Model name if set, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT model_name FROM api_keys WHERE id = ?",
                (api_key_id,)
            )
            row = cursor.fetchone()
            return row['model_name'] if row else None
        finally:
            conn.close()

    def set_model_setting(self, api_key_id: int, model_name: Optional[str]):
        """
        Set the model name for an API key.

        Args:
            api_key_id: API key ID
            model_name: Model name to set (None to unset)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "UPDATE api_keys SET model_name = ? WHERE id = ?",
                (model_name, api_key_id)
            )
            conn.commit()
            logger.info(f"Set model for API key {api_key_id} to {model_name}")
        finally:
            conn.close()
