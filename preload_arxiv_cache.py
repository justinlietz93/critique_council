#!/usr/bin/env python
"""
ArXiv Cache Preloader

This script preloads the ArXiv cache database with references from common academic 
topics to improve cold-start performance and provide a foundation of relevant papers.

Usage:
    python preload_arxiv_cache.py
"""

import os
import sys
import logging
import argparse
import yaml
from typing import Dict, List, Any, Optional
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("arxiv_preloader")

# Ensure proper import paths
sys.path.insert(0, os.path.abspath('.'))
from src.arxiv.arxiv_reference_service import ArxivReferenceService

# Define common academic topics by domain
COMMON_TOPICS = {
    "computer_science": [
        "quantum computing", "machine learning", "neural networks", "deep learning", 
        "reinforcement learning", "computer vision", "natural language processing",
        "graph theory", "algorithms", "data structures", "artificial intelligence",
        "cryptography", "computer security", "distributed systems", "parallel computing"
    ],
    "physics": [
        "quantum mechanics", "string theory", "condensed matter", "particle physics",
        "astrophysics", "relativity", "quantum field theory", "statistical mechanics",
        "plasma physics", "nuclear physics", "optics", "thermodynamics"
    ],
    "mathematics": [
        "graph theory", "number theory", "topology", "algebra", "analysis", 
        "differential equations", "geometry", "probability theory", "statistics",
        "mathematical logic", "discrete mathematics", "numerical analysis"
    ],
    "biology": [
        "molecular biology", "genetics", "genomics", "proteomics", "cell biology",
        "evolutionary biology", "ecology", "microbiology", "neuroscience", 
        "biotechnology", "bioinformatics"
    ],
    "economics": [
        "macroeconomics", "microeconomics", "game theory", "behavioral economics",
        "financial economics", "economic development", "international economics"
    ],
    "philosophy": [
        "epistemology", "metaphysics", "ethics", "philosophy of mind", 
        "philosophy of science", "philosophy of language", "logic", "aesthetics",
        "political philosophy", "existentialism", "phenomenology"
    ]
}

def load_config() -> Dict[str, Any]:
    """Load application configuration."""
    config_path = 'config.yaml'
    try:
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
                'use_cache': True
            }
        }

def preload_topics(topics: Dict[str, List[str]], max_per_topic: int = 5, domains: Optional[List[str]] = None) -> None:
    """
    Preload the ArXiv cache with references from common academic topics.
    
    Args:
        topics: Dictionary mapping domains to lists of topics
        max_per_topic: Maximum number of papers to cache per topic
        domains: Optional list of domains to preload. If None, preload all domains.
    """
    # Load configuration
    config = load_config()
    
    # Override cache settings
    config['arxiv']['use_cache'] = False  # Don't use cache while preloading
    
    # Create ArXiv service
    arxiv_service = ArxivReferenceService(config=config)
    logger.info(f"ArXiv service initialized")
    
    # Track statistics
    total_topics = 0
    total_cached = 0
    
    # Process each domain
    for domain, topic_list in topics.items():
        if domains and domain not in domains:
            continue
            
        logger.info(f"Preloading topics for domain: {domain}")
        
        # Process each topic in the domain
        for topic in tqdm(topic_list, desc=f"Preloading {domain} topics"):
            # Construct a query for this topic
            query = f"all:\"{topic}\""
            
            # Fetch results
            try:
                logger.debug(f"Fetching papers for topic: {topic}")
                papers = arxiv_service.search_arxiv(
                    search_query=query,
                    max_results=max_per_topic,
                    sort_by="relevance",
                    sort_order="descending",
                    use_cache=False  # Force API call to get fresh data
                )
                
                # Now store in cache by requesting again with cache enabled
                if papers:
                    # Enable cache for this request
                    config_with_cache = config.copy()
                    config_with_cache['arxiv']['use_cache'] = True
                    
                    # Create a new service with cache enabled
                    cache_service = ArxivReferenceService(config=config_with_cache)
                    
                    # This will store in cache
                    _ = cache_service.search_arxiv(
                        search_query=query,
                        max_results=max_per_topic,
                        sort_by="relevance",
                        sort_order="descending"
                    )
                    
                    # Update statistics
                    total_cached += len(papers)
                    logger.debug(f"Cached {len(papers)} papers for topic: {topic}")
                else:
                    logger.warning(f"No papers found for topic: {topic}")
                
                total_topics += 1
                
            except Exception as e:
                logger.error(f"Error fetching papers for topic {topic}: {e}")
    
    logger.info(f"Preloading complete: Processed {total_topics} topics, cached {total_cached} papers")
    
    # Get cache statistics
    try:
        stats = arxiv_service.get_cache_stats()
        if stats:
            logger.info(f"Cache statistics: {stats}")
    except Exception as e:
        logger.error(f"Error getting cache statistics: {e}")

def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description='Preload ArXiv cache with common academic topics')
    parser.add_argument('--max-per-topic', type=int, default=5, 
                      help='Maximum number of papers to cache per topic (default: 5)')
    parser.add_argument('--domains', nargs='+', 
                      help='Domains to preload (e.g., computer_science physics). If not specified, all domains are preloaded.')
    parser.add_argument('--list-domains', action='store_true', 
                      help='List available domains and exit')
    
    args = parser.parse_args()
    
    if args.list_domains:
        print("Available domains for preloading:")
        for domain in COMMON_TOPICS.keys():
            print(f"  - {domain}: {len(COMMON_TOPICS[domain])} topics")
        return
    
    domains = args.domains
    if domains:
        for domain in domains:
            if domain not in COMMON_TOPICS:
                print(f"Error: Unknown domain '{domain}'. Use --list-domains to see available domains.")
                return
    
    max_per_topic = args.max_per_topic
    if max_per_topic < 1 or max_per_topic > 20:
        print("Error: max_per_topic must be between 1 and 20")
        return
    
    preload_topics(COMMON_TOPICS, max_per_topic, domains)

if __name__ == "__main__":
    main()
