"""
Database connection and utilities.

This module provides database connection management.
Individual repositories will handle data operations.
"""
import sqlite3
import logging
from contextlib import contextmanager
from typing import Generator, Optional
from pathlib import Path

from .exceptions import DatabaseError, DatabaseConnectionError


logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and provides connection pool."""

    def __init__(self, db_path: str = "backend/simulator_v3.db"):
        """Initialize database manager."""
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self) -> None:
        """Ensure database file exists."""
        db_file = Path(self.db_path)
        if not db_file.exists():
            logger.warning(f"Database file {self.db_path} does not exist")
            # Don't create automatically - let migrations handle this

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Get a database connection as context manager.

        Usage:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(...)
                conn.commit()
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise DatabaseConnectionError(f"Failed to connect to database: {e}")
        finally:
            if conn:
                conn.close()

    def execute_query(
        self,
        query: str,
        params: tuple = (),
        fetch_one: bool = False,
        fetch_all: bool = False
    ):
        """
        Execute a query and optionally fetch results.

        Args:
            query: SQL query to execute
            params: Query parameters
            fetch_one: Return single row
            fetch_all: Return all rows

        Returns:
            None, single row, or list of rows based on fetch parameters
        """
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)

                if fetch_one:
                    result = cursor.fetchone()
                    return dict(result) if result else None
                elif fetch_all:
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
                else:
                    conn.commit()
                    return cursor.lastrowid

            except sqlite3.Error as e:
                logger.error(f"Query execution error: {e}\nQuery: {query}")
                raise DatabaseError(f"Query execution failed: {e}")

    def execute_many(self, query: str, params_list: list[tuple]):
        """
        Execute a query multiple times with different parameters.

        Args:
            query: SQL query to execute
            params_list: List of parameter tuples
        """
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
            except sqlite3.Error as e:
                logger.error(f"Batch query execution error: {e}\nQuery: {query}")
                raise DatabaseError(f"Batch query execution failed: {e}")


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager(db_path: str = "backend/simulator_v3.db") -> DatabaseManager:
    """Get or create the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
    return _db_manager


def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    FastAPI dependency for getting database connection.

    Usage:
        @router.get("/example")
        def example(conn = Depends(get_db_connection)):
            cursor = conn.cursor()
            ...
    """
    db = get_db_manager()
    with db.get_connection() as conn:
        yield conn
