"""
ArXiv Cache Manager Module

This module handles caching of arXiv API responses to reduce API calls
and improve performance.
"""

import os
import json
import time
import hashlib
import logging
from typing import Dict, Any, Optional, Union

# Set up logging
logger = logging.getLogger(__name__)

class ArxivCacheManager:
    """
    Manager for caching arXiv API responses.
    
    This class handles:
    1. Storing and retrieving cached API responses
    2. Managing cache expiration
    3. Creating hash keys for queries
    """
    
    # Default cache settings
    DEFAULT_CACHE_DIR = "storage/arxiv_cache"
    CACHE_EXPIRY_DAYS = 30  # Consider results fresh for 30 days
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the ArXiv cache manager.
        
        Args:
            cache_dir: Directory to store cached results. Defaults to 'storage/arxiv_cache'.
        """
        self.cache_dir = cache_dir or self.DEFAULT_CACHE_DIR
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self) -> None:
        """Ensure the cache directory exists."""
        os.makedirs(self.cache_dir, exist_ok=True)
        logger.debug(f"ArXiv cache directory ensured at: {self.cache_dir}")
    
    def _get_cache_path(self, query_hash: str) -> str:
        """
        Get the file path for a cached result.
        
        Args:
            query_hash: Hash string of query parameters
            
        Returns:
            Path to the cache file
        """
        return os.path.join(self.cache_dir, f"{query_hash}.json")
    
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
    
    def is_cache_valid(self, cache_path: str) -> bool:
        """
        Check if a cached result is still valid (not expired).
        
        Args:
            cache_path: Path to the cache file
            
        Returns:
            True if cache is valid, False otherwise
        """
        if not os.path.exists(cache_path):
            return False
        
        file_time = os.path.getmtime(cache_path)
        file_age = time.time() - file_time
        max_age = self.CACHE_EXPIRY_DAYS * 24 * 60 * 60  # Convert days to seconds
        
        return file_age < max_age
    
    def get_cached_response(self, query_params: Dict[str, Any]) -> Optional[Any]:
        """
        Get cached response for the given query parameters.
        
        Args:
            query_params: Dictionary of query parameters
            
        Returns:
            Cached response if available and valid, None otherwise
        """
        query_hash = self.hash_query(query_params)
        cache_path = self._get_cache_path(query_hash)
        
        if not self.is_cache_valid(cache_path):
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                logger.debug(f"Using cached results from {cache_path}")
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cached results: {e}")
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
        cache_path = self._get_cache_path(query_hash)
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2)
            logger.debug(f"Saved results to cache at {cache_path}")
            return True
        except Exception as e:
            logger.warning(f"Failed to cache results: {e}")
            return False
    
    def clear_cache(self, older_than_days: Optional[int] = None) -> int:
        """
        Clear cache files.
        
        Args:
            older_than_days: If provided, only clear files older than this many days
            
        Returns:
            Number of files cleared
        """
        if not os.path.exists(self.cache_dir):
            return 0
            
        files = os.listdir(self.cache_dir)
        count = 0
        
        for file in files:
            if not file.endswith('.json'):
                continue
                
            file_path = os.path.join(self.cache_dir, file)
            
            # If older_than_days is specified, check file age
            if older_than_days is not None:
                file_time = os.path.getmtime(file_path)
                file_age_days = (time.time() - file_time) / (24 * 60 * 60)
                
                if file_age_days < older_than_days:
                    continue
            
            try:
                os.remove(file_path)
                count += 1
            except Exception as e:
                logger.warning(f"Failed to remove cache file {file_path}: {e}")
        
        logger.info(f"Cleared {count} cache files")
        return count
