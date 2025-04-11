"""
ArXiv Database Cache Manager Module

This module provides a SQLite-based caching system for ArXiv API responses
to reduce API calls and improve performance.
"""

import os
import json
import time
import hashlib
import logging
import sqlite3
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
import threading

# Set up logging
logger = logging.getLogger(__name__)

class ArxivDBCacheManager:
    """
    SQLite-based manager for caching arXiv API responses.
    
    This class handles:
    1. Storing and retrieving cached API responses in a SQLite database
    2. Automatic cache expiration based on TTL
    3. Periodic cleanup of expired entries
    4. Thread-safe database operations
    """
    
    # Default cache settings
    DEFAULT_DB_PATH = "storage/arxiv_cache/arxiv_cache.db"
    DEFAULT_CACHE_TTL_DAYS = 30  # Consider results fresh for 30 days
    DEFAULT_CLEANUP_INTERVAL_HOURS = 24  # Run cleanup once a day
    
    # SQL statements for database operations
    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS arxiv_cache (
        query_hash TEXT PRIMARY KEY,
        response_data BLOB,
        timestamp TEXT,
        expiration TEXT
    );
    """
    
    CREATE_INDEX_SQL = """
    CREATE INDEX IF NOT EXISTS idx_expiration ON arxiv_cache(expiration);
    """
    
    INSERT_SQL = """
    INSERT OR REPLACE INTO arxiv_cache (query_hash, response_data, timestamp, expiration)
    VALUES (?, ?, ?, ?);
    """
    
    SELECT_SQL = """
    SELECT response_data FROM arxiv_cache
    WHERE query_hash = ? AND expiration > ?;
    """
    
    DELETE_EXPIRED_SQL = """
    DELETE FROM arxiv_cache WHERE expiration <= ?;
    """
    
    def __init__(self, db_path: Optional[str] = None, ttl_days: int = DEFAULT_CACHE_TTL_DAYS,
                 cleanup_interval_hours: int = DEFAULT_CLEANUP_INTERVAL_HOURS,
                 auto_cleanup: bool = True):
        """
        Initialize the ArXiv database cache manager.
        
        Args:
            db_path: Path to the SQLite database file. Defaults to 'storage/arxiv_cache/arxiv_cache.db'.
            ttl_days: Number of days before cached entries expire. Defaults to 30 days.
            cleanup_interval_hours: Hours between automatic cleanup runs. Defaults to 24 hours.
            auto_cleanup: Whether to automatically clean up expired entries. Defaults to True.
        """
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self.ttl_days = ttl_days
        self.cleanup_interval_hours = cleanup_interval_hours
        self.auto_cleanup = auto_cleanup
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        
        # Initialize the database
        self._ensure_db_path()
        self._init_db()
        
        # Start cleanup scheduler if enabled
        if self.auto_cleanup:
            self._start_cleanup_scheduler()
    
    def _ensure_db_path(self) -> None:
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        os.makedirs(db_dir, exist_ok=True)
        logger.debug(f"ArXiv cache database directory ensured at: {db_dir}")
    
    def _init_db(self) -> None:
        """Initialize the database with required schema."""
        with self._get_connection() as conn:
            conn.execute(self.CREATE_TABLE_SQL)
            conn.execute(self.CREATE_INDEX_SQL)
            conn.commit()
        logger.debug("ArXiv cache database initialized")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a SQLite database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dictionary access for rows
        return conn
    
    def _start_cleanup_scheduler(self) -> None:
        """Start a background thread for periodic cleanup."""
        cleanup_thread = threading.Thread(target=self._cleanup_scheduler, daemon=True)
        cleanup_thread.start()
        logger.debug(f"Cleanup scheduler started with interval of {self.cleanup_interval_hours} hours")
    
    def _cleanup_scheduler(self) -> None:
        """Background thread function for periodic cleanup."""
        while True:
            time.sleep(self.cleanup_interval_hours * 3600)  # Convert hours to seconds
            try:
                self.cleanup_expired()
            except Exception as e:
                logger.error(f"Error during scheduled cleanup: {e}")
    
    def hash_query(self, query_params: Dict[str, Any]) -> str:
        """
        Create a hash of the query parameters for cache keys.
        
        Args:
            query_params: Dictionary of query parameters
            
        Returns:
            MD5 hash of the sorted JSON string of parameters
        """
        # Sort the params to ensure consistent hashing
        query_str = json.dumps(query_params, sort_keys=True)
        return hashlib.md5(query_str.encode()).hexdigest()
    
    def get_cached_response(self, query_params: Dict[str, Any]) -> Optional[Any]:
        """
        Get cached response for the given query parameters.
        
        Args:
            query_params: Dictionary of query parameters
            
        Returns:
            Cached response if available and valid, None otherwise
        """
        query_hash = self.hash_query(query_params)
        current_time = datetime.now().isoformat()
        
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.execute(self.SELECT_SQL, (query_hash, current_time))
                    row = cursor.fetchone()
                    
                    if row:
                        logger.debug(f"Cache hit for query hash: {query_hash}")
                        response_data = row['response_data']
                        return json.loads(response_data)
                    
                    logger.debug(f"Cache miss for query hash: {query_hash}")
                    return None
            except Exception as e:
                logger.warning(f"Error retrieving from cache: {e}")
                return None
    
    def save_to_cache(self, query_params: Dict[str, Any], response_data: Any) -> bool:
        """
        Save response data to cache.
        
        Args:
            query_params: Dictionary of query parameters
            response_data: Data to cache
            
        Returns:
            True if saved successfully, False otherwise
        """
        query_hash = self.hash_query(query_params)
        current_time = datetime.now()
        expiration_time = current_time + timedelta(days=self.ttl_days)
        
        # Serialize the response data to JSON
        try:
            serialized_data = json.dumps(response_data)
        except Exception as e:
            logger.warning(f"Failed to serialize response data: {e}")
            return False
        
        with self._lock:
            try:
                with self._get_connection() as conn:
                    conn.execute(
                        self.INSERT_SQL,
                        (
                            query_hash,
                            serialized_data,
                            current_time.isoformat(),
                            expiration_time.isoformat()
                        )
                    )
                    conn.commit()
                
                logger.debug(f"Saved results to cache with hash: {query_hash}")
                return True
            except Exception as e:
                logger.warning(f"Failed to cache results: {e}")
                return False
    
    def cleanup_expired(self) -> int:
        """
        Clean up expired cache entries.
        
        Returns:
            Number of entries removed
        """
        current_time = datetime.now().isoformat()
        
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.execute(self.DELETE_EXPIRED_SQL, (current_time,))
                    deleted_count = cursor.rowcount
                    conn.commit()
                
                logger.info(f"Cleaned up {deleted_count} expired cache entries")
                return deleted_count
            except Exception as e:
                logger.error(f"Error cleaning up expired cache entries: {e}")
                return 0
    
    def clear_cache(self, older_than_days: Optional[int] = None) -> int:
        """
        Clear cache entries.
        
        Args:
            older_than_days: If provided, only clear entries older than this many days
            
        Returns:
            Number of entries cleared
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    if older_than_days is not None:
                        # Clear entries older than specified days
                        cutoff_date = (datetime.now() - timedelta(days=older_than_days)).isoformat()
                        cursor = conn.execute("DELETE FROM arxiv_cache WHERE timestamp <= ?", (cutoff_date,))
                    else:
                        # Clear all entries
                        cursor = conn.execute("DELETE FROM arxiv_cache")
                    
                    deleted_count = cursor.rowcount
                    conn.commit()
                
                logger.info(f"Cleared {deleted_count} cache entries")
                return deleted_count
            except Exception as e:
                logger.error(f"Error clearing cache: {e}")
                return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    # Total entries
                    cursor = conn.execute("SELECT COUNT(*) as count FROM arxiv_cache")
                    total_count = cursor.fetchone()['count']
                    
                    # Expired entries
                    current_time = datetime.now().isoformat()
                    cursor = conn.execute(
                        "SELECT COUNT(*) as count FROM arxiv_cache WHERE expiration <= ?",
                        (current_time,)
                    )
                    expired_count = cursor.fetchone()['count']
                    
                    # Database size
                    cursor = conn.execute("PRAGMA page_count")
                    page_count = cursor.fetchone()[0]
                    cursor = conn.execute("PRAGMA page_size")
                    page_size = cursor.fetchone()[0]
                    db_size = page_count * page_size
                    
                    return {
                        'total_entries': total_count,
                        'expired_entries': expired_count,
                        'valid_entries': total_count - expired_count,
                        'db_size_bytes': db_size,
                        'db_size_mb': round(db_size / (1024 * 1024), 2),
                        'ttl_days': self.ttl_days,
                        'cleanup_interval_hours': self.cleanup_interval_hours,
                        'path': self.db_path
                    }
            except Exception as e:
                logger.error(f"Error getting cache stats: {e}")
                return {
                    'error': str(e),
                    'ttl_days': self.ttl_days,
                    'cleanup_interval_hours': self.cleanup_interval_hours,
                    'path': self.db_path
                }
