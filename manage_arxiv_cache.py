#!/usr/bin/env python
"""
ArXiv Cache Management Utility

This script provides command-line utilities for managing the ArXiv reference cache
in the Critique Council application.

Usage:
    python manage_arxiv_cache.py stats               - Show cache statistics
    python manage_arxiv_cache.py clear               - Clear entire cache
    python manage_arxiv_cache.py clear --days=30     - Clear entries older than 30 days
    python manage_arxiv_cache.py cleanup             - Remove expired entries
    python manage_arxiv_cache.py info                - Show cache configuration
"""

import os
import sys
import json
import argparse
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("arxiv_cache_manager")

# Ensure proper import paths
sys.path.insert(0, os.path.abspath('.'))
from src.arxiv.arxiv_reference_service import ArxivReferenceService
from src.arxiv.db_cache_manager import ArxivDBCacheManager

def load_config() -> Dict[str, Any]:
    """Load application configuration."""
    config_path = 'config.yaml'
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.warning(f"Failed to load config from {config_path}: {e}")
        return {
            'arxiv': {
                'cache_dir': 'storage/arxiv_cache',
                'use_db_cache': True,
                'cache_ttl_days': 30,
                'cache_cleanup_interval_hours': 24
            }
        }

def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def show_stats(cache_manager: Any) -> None:
    """Show cache statistics."""
    if not hasattr(cache_manager, 'get_stats'):
        print("Statistics are only available for the database cache manager.")
        return
    
    stats = cache_manager.get_stats()
    
    print("\n=== ArXiv Cache Statistics ===\n")
    print(f"Total entries:     {stats.get('total_entries', 'N/A')}")
    print(f"Valid entries:     {stats.get('valid_entries', 'N/A')}")
    print(f"Expired entries:   {stats.get('expired_entries', 'N/A')}")
    
    if 'db_size_bytes' in stats:
        print(f"Database size:     {format_size(stats['db_size_bytes'])}")
    
    print(f"Cache TTL:         {stats.get('ttl_days', 'N/A')} days")
    print(f"Cleanup interval:  {stats.get('cleanup_interval_hours', 'N/A')} hours")
    print(f"Cache path:        {stats.get('path', 'N/A')}")
    
    if 'error' in stats:
        print(f"\nError getting complete stats: {stats['error']}")

def clear_cache(cache_manager: Any, older_than_days: Optional[int] = None) -> None:
    """Clear the cache."""
    days_str = f"older than {older_than_days} days " if older_than_days else ""
    print(f"\nClearing cache entries {days_str}...")
    
    cleared = cache_manager.clear_cache(older_than_days)
    
    print(f"Cleared {cleared} cache entries.")

def cleanup_expired(cache_manager: Any) -> None:
    """Clean up expired cache entries."""
    if not hasattr(cache_manager, 'cleanup_expired'):
        print("Explicit cleanup is only available for the database cache manager.")
        print("The file-based cache performs cleanup automatically on each access.")
        return
    
    print("\nCleaning up expired cache entries...")
    
    removed = cache_manager.cleanup_expired()
    
    print(f"Removed {removed} expired cache entries.")

def show_info(config: Dict[str, Any]) -> None:
    """Show cache configuration information."""
    arxiv_config = config.get('arxiv', {})
    
    print("\n=== ArXiv Cache Configuration ===\n")
    print(f"Cache directory:    {arxiv_config.get('cache_dir', 'storage/arxiv_cache')}")
    print(f"Cache type:         {'Database (SQLite)' if arxiv_config.get('use_db_cache', True) else 'File-based'}")
    print(f"Cache enabled:      {arxiv_config.get('use_cache', True)}")
    print(f"Cache TTL:          {arxiv_config.get('cache_ttl_days', 30)} days")
    
    if arxiv_config.get('use_db_cache', True):
        print(f"Cleanup interval:   {arxiv_config.get('cache_cleanup_interval_hours', 24)} hours")
    
    print("\nSearch settings:")
    print(f"  Max references:   {arxiv_config.get('max_references_per_point', 3)} per point")
    print(f"  Sort by:          {arxiv_config.get('search_sort_by', 'relevance')}")
    print(f"  Sort order:       {arxiv_config.get('search_sort_order', 'descending')}")
    
    print(f"\nBibliography updates: {arxiv_config.get('update_bibliography', True)}")

def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description='Manage ArXiv reference cache')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Stats command
    subparsers.add_parser('stats', help='Show cache statistics')
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear the cache')
    clear_parser.add_argument('--days', type=int, help='Clear entries older than specified days')
    
    # Cleanup command
    subparsers.add_parser('cleanup', help='Clean up expired cache entries')
    
    # Info command
    subparsers.add_parser('info', help='Show cache configuration information')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Load configuration
    config = load_config()
    
    # Get the appropriate cache manager
    arxiv_config = config.get('arxiv', {})
    use_db_cache = arxiv_config.get('use_db_cache', True)
    cache_dir = arxiv_config.get('cache_dir', 'storage/arxiv_cache')
    
    if args.command == 'info':
        show_info(config)
        return
    
    # Initialize the appropriate cache manager directly
    if use_db_cache:
        db_path = os.path.join(cache_dir, "arxiv_cache.db")
        ttl_days = arxiv_config.get('cache_ttl_days', 30)
        cleanup_interval = arxiv_config.get('cache_cleanup_interval_hours', 24)
        
        cache_manager = ArxivDBCacheManager(
            db_path=db_path,
            ttl_days=ttl_days,
            cleanup_interval_hours=cleanup_interval,
            auto_cleanup=False  # Disable auto cleanup for this utility
        )
        
        print(f"Using database cache at {db_path}")
    else:
        from src.arxiv.cache_manager import ArxivCacheManager
        cache_manager = ArxivCacheManager(cache_dir=cache_dir)
        print(f"Using file-based cache at {cache_dir}")
    
    # Execute the appropriate command
    if args.command == 'stats':
        show_stats(cache_manager)
    elif args.command == 'clear':
        clear_cache(cache_manager, args.days)
    elif args.command == 'cleanup':
        cleanup_expired(cache_manager)

if __name__ == "__main__":
    main()
