"""Backend API service management."""

import sqlite3
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BackendManager:
    """Manages multiple OpenAI-compatible backend API services."""

    def __init__(self, db_path: str = "data/proxy_users.db"):
        """
        Initialize backend manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        """Create backend_services table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create backend_services table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backend_services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                short_name TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                base_url TEXT NOT NULL,
                api_key TEXT NOT NULL,
                default_model TEXT,
                is_active INTEGER DEFAULT 1,
                is_default INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Add backend_id column to api_keys table if it doesn't exist
        try:
            cursor.execute("ALTER TABLE api_keys ADD COLUMN backend_id INTEGER REFERENCES backend_services(id)")
            logger.info("Added backend_id column to api_keys table")
        except sqlite3.OperationalError:
            # Column already exists
            pass

        conn.commit()
        conn.close()
        logger.info(f"Backend manager initialized with database at {self.db_path}")

    def create_backend(
        self,
        short_name: str,
        name: str,
        base_url: str,
        api_key: str,
        default_model: Optional[str] = None,
        is_default: bool = False
    ) -> int:
        """
        Create a new backend service.

        Args:
            short_name: Short identifier (e.g., "inf", "zhipu", "sf")
            name: Display name
            base_url: API base URL
            api_key: API key for the backend
            default_model: Default model for this backend
            is_default: Whether this is the default backend

        Returns:
            Backend ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # If setting as default, unset other defaults
            if is_default:
                cursor.execute("UPDATE backend_services SET is_default = 0")

            cursor.execute("""
                INSERT INTO backend_services
                (short_name, name, base_url, api_key, default_model, is_default)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (short_name, name, base_url, api_key, default_model, 1 if is_default else 0))

            backend_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Created backend service: {short_name} (ID: {backend_id})")
            return backend_id

        except sqlite3.IntegrityError as e:
            logger.error(f"Failed to create backend {short_name}: {e}")
            raise ValueError(f"Backend with short_name '{short_name}' already exists")
        finally:
            conn.close()

    def list_backends(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """
        List all backend services.

        Args:
            active_only: If True, only return active backends

        Returns:
            List of backend service dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM backend_services"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY is_default DESC, short_name ASC"

        cursor.execute(query)
        backends = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Don't expose full API key, only show last 4 characters
        for backend in backends:
            if backend['api_key']:
                backend['api_key_masked'] = backend['api_key'][-4:] if len(backend['api_key']) > 4 else '****'

        return backends

    def get_backend(self, backend_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific backend by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM backend_services WHERE id = ?", (backend_id,))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def get_backend_by_short_name(self, short_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific backend by short name."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM backend_services WHERE short_name = ? AND is_active = 1", (short_name,))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def get_default_backend(self) -> Optional[Dict[str, Any]]:
        """Get the default backend service."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Try to get backend marked as default
        cursor.execute("SELECT * FROM backend_services WHERE is_default = 1 AND is_active = 1")
        row = cursor.fetchone()

        # If no default, get first active backend
        if not row:
            cursor.execute("SELECT * FROM backend_services WHERE is_active = 1 ORDER BY id ASC LIMIT 1")
            row = cursor.fetchone()

        conn.close()
        return dict(row) if row else None

    def update_backend(
        self,
        backend_id: int,
        short_name: Optional[str] = None,
        name: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_default: Optional[bool] = None
    ) -> bool:
        """
        Update a backend service.

        Returns:
            True if update successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Build update query dynamically
            updates = []
            params = []

            if short_name is not None:
                updates.append("short_name = ?")
                params.append(short_name)
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if base_url is not None:
                updates.append("base_url = ?")
                params.append(base_url)
            if api_key is not None:
                updates.append("api_key = ?")
                params.append(api_key)
            if default_model is not None:
                updates.append("default_model = ?")
                params.append(default_model)
            if is_active is not None:
                updates.append("is_active = ?")
                params.append(1 if is_active else 0)
            if is_default is not None:
                # If setting as default, unset other defaults first
                if is_default:
                    cursor.execute("UPDATE backend_services SET is_default = 0")
                updates.append("is_default = ?")
                params.append(1 if is_default else 0)

            if not updates:
                return False

            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(backend_id)

            query = f"UPDATE backend_services SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)

            success = cursor.rowcount > 0
            conn.commit()

            if success:
                logger.info(f"Updated backend service ID: {backend_id}")
            return success

        except sqlite3.IntegrityError as e:
            logger.error(f"Failed to update backend {backend_id}: {e}")
            raise ValueError(f"Update failed: {str(e)}")
        finally:
            conn.close()

    def delete_backend(self, backend_id: int) -> bool:
        """
        Delete a backend service.

        Note: This will fail if any API keys are using this backend.
        Consider setting is_active=False instead.

        Returns:
            True if deletion successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Check if any API keys are using this backend
            cursor.execute("SELECT COUNT(*) FROM api_keys WHERE backend_id = ?", (backend_id,))
            count = cursor.fetchone()[0]

            if count > 0:
                raise ValueError(
                    f"Cannot delete backend: {count} API key(s) are using this backend. "
                    "Please reassign or delete those API keys first, or set is_active=False instead."
                )

            cursor.execute("DELETE FROM backend_services WHERE id = ?", (backend_id,))
            success = cursor.rowcount > 0
            conn.commit()

            if success:
                logger.info(f"Deleted backend service ID: {backend_id}")
            return success

        except ValueError:
            raise
        finally:
            conn.close()

    def set_user_backend(self, api_key_id: int, backend_id: Optional[int]) -> bool:
        """
        Set the preferred backend for an API key.

        Args:
            api_key_id: API key ID
            backend_id: Backend ID (None to use default)

        Returns:
            True if successful
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "UPDATE api_keys SET backend_id = ? WHERE id = ?",
                (backend_id, api_key_id)
            )
            success = cursor.rowcount > 0
            conn.commit()

            if success:
                logger.info(f"Set backend {backend_id} for API key ID {api_key_id}")
            return success

        finally:
            conn.close()

    def get_user_backend(self, api_key_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the backend configured for an API key.

        Returns:
            Backend dict if user has one set, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT bs.* FROM backend_services bs
            JOIN api_keys ak ON ak.backend_id = bs.id
            WHERE ak.id = ? AND bs.is_active = 1
        """, (api_key_id,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None
