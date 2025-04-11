"""
ArXiv Reference Service with Agno Integration

This module provides a version of the ArXiv reference service that uses
Agno for efficient vector search and storage of ArXiv papers.
"""

import os
import logging
import json
import time
from typing import Dict, List, Any, Optional, Union, Tuple

from src.arxiv.api_client import ArxivApiClient
from src.arxiv.agno_integration import ArxivAgnoStore
from src.arxiv.bibtex_converter import convert_to_bibtex

# Set up logging
logger = logging.getLogger(__name__)

class ArxivAgnoReferenceService:
    """
    ArXiv reference service using Agno for efficient vector search.
    
    This service combines the ArXiv API client with Agno vector storage
    to provide relevant academic paper references with semantic search.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the ArXiv Agno reference service.
        
        Args:
            config: Configuration dictionary with settings for the service
        """
        self.config = config or {}
        
        # Extract configuration
        arxiv_config = self.config.get('arxiv', {})
        self.use_cache = arxiv_config.get('use_cache', True)
        self.cache_dir = arxiv_config.get('cache_dir', 'storage/arxiv_cache')
        self.cache_ttl_days = arxiv_config.get('cache_ttl_days', 30)
        self.max_references = arxiv_config.get('max_references_per_point', 3)
        self.default_sort_by = arxiv_config.get('default_sort_by', 'relevance')
        self.default_sort_order = arxiv_config.get('default_sort_order', 'descending')
        self.update_bibliography = arxiv_config.get('update_bibliography', True)
        
        # Initialize API client
        self.api_client = ArxivApiClient()
        
        # Initialize Agno store if caching is enabled
        if self.use_cache:
            openai_api_key = os.environ.get("OPENAI_API_KEY")
            self.agno_store = ArxivAgnoStore(
                cache_dir=self.cache_dir,
                table_name="arxiv_papers",
                ttl_days=self.cache_ttl_days,
                openai_api_key=openai_api_key
            )
            logger.info(f"ArXiv service using Agno store at {self.cache_dir}")
        else:
            self.agno_store = None
            logger.info("ArXiv service running without cache")
        
        logger.info("ArXiv reference service initialized")
    
    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from text for search queries.
        
        Args:
            text: Text to extract keywords from
            max_keywords: Maximum number of keywords to extract
            
        Returns:
            List of extracted keywords
        """
        # Split into words and filter out short words
        words = [word.lower() for word in text.split() if len(word) > 3]
        
        # Get unique words
        unique_words = list(set(words))
        
        # Limit to max_keywords
        keywords = unique_words[:max_keywords]
        
        return keywords
    
    def _build_search_query(self, text: str) -> str:
        """
        Build an ArXiv search query from text.
        
        Args:
            text: Text to build query from
            
        Returns:
            ArXiv search query string
        """
        # Extract keywords
        keywords = self._extract_keywords(text, max_keywords=10)
        
        # Build query
        keyword_parts = [f"all:{keyword}" for keyword in keywords]
        
        # Add phrase parts for better matching
        phrases = []
        for i in range(len(keywords) - 1):
            if i + 1 < len(keywords):
                phrase = f"{keywords[i]} {keywords[i+1]}"
                phrases.append(f'all:"{phrase}"')
        
        # Combine keyword and phrase parts
        query_parts = keyword_parts + phrases
        
        # Join with OR
        query = " OR ".join(query_parts)
        
        return query
    
    def search_arxiv(self, 
                     search_query: str, 
                     max_results: int = 10, 
                     sort_by: str = None, 
                     sort_order: str = None,
                     use_cache: bool = None) -> List[Dict[str, Any]]:
        """
        Search ArXiv for papers matching the query.
        
        Args:
            search_query: Search query string
            max_results: Maximum number of results to return
            sort_by: Field to sort results by
            sort_order: Order to sort results in
            use_cache: Whether to use the cache (overrides service setting)
            
        Returns:
            List of paper metadata dictionaries
        """
        # Set default values
        sort_by = sort_by or self.default_sort_by
        sort_order = sort_order or self.default_sort_order
        if use_cache is None:
            use_cache = self.use_cache
        
        # Check if we should use cache
        if use_cache and self.agno_store:
            # Try to search in Agno store
            logger.info(f"Searching Agno store for query: {search_query}")
            cached_results = self.agno_store.search(
                query=search_query,
                max_results=max_results
            )
            
            if cached_results:
                logger.info(f"Using cached results for query: {search_query}")
                return cached_results
            
            logger.info(f"No cached results for query: {search_query}")
        
        # If we get here, either caching is disabled or there was a cache miss
        logger.info(f"Fetching arXiv results for query: {search_query}")
        
        # Perform API search
        try:
            results = self.api_client.search(
                query=search_query,
                max_results=max_results,
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            # Cache results if enabled
            if use_cache and self.agno_store and results:
                self.agno_store.add_papers(results)
            
            return results
        except Exception as e:
            logger.error(f"Error searching ArXiv: {e}")
            return []
    
    def get_references_for_point(self, 
                                point: str, 
                                max_references: int = None) -> List[Dict[str, Any]]:
        """
        Get references for a content point.
        
        Args:
            point: Content point to get references for
            max_references: Maximum number of references to return
            
        Returns:
            List of reference dictionaries
        """
        max_references = max_references or self.max_references
        
        # Build search query from point
        search_query = self._build_search_query(point)
        
        # Search ArXiv
        papers = self.search_arxiv(
            search_query=search_query,
            max_results=max_references,
            sort_by=self.default_sort_by,
            sort_order=self.default_sort_order
        )
        
        return papers
    
    def attach_references_to_points(self, 
                                   points: List[str]) -> List[Tuple[str, List[Dict[str, Any]]]]:
        """
        Attach ArXiv references to content points.
        
        Args:
            points: List of content points
            
        Returns:
            List of (point, references) tuples
        """
        results = []
        
        for point in points:
            # Get references for point
            refs = self.get_references_for_point(point)
            
            # Add to results
            results.append((point, refs))
        
        return results
    
    def update_bibliography_file(self, 
                                references: List[Dict[str, Any]], 
                                output_path: str) -> bool:
        """
        Update bibliography file with ArXiv references.
        
        Args:
            references: List of reference dictionaries
            output_path: Path to write bibliography file to
            
        Returns:
            True if successful, False otherwise
        """
        if not self.update_bibliography:
            logger.info("Bibliography updates disabled")
            return False
        
        try:
            # Create output directory if needed
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Convert references to BibTeX
            bibtex_entries = []
            for ref in references:
                entry = convert_to_bibtex(ref)
                if entry:
                    bibtex_entries.append(entry)
            
            # Create header
            header = "% ArXiv references generated for Critique Council\n\n"
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(header)
                f.write('\n\n'.join(bibtex_entries))
            
            logger.info(f"Updated LaTeX bibliography at {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error updating bibliography: {e}")
            return False
    
    def clear_cache(self) -> bool:
        """
        Clear the cache.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.agno_store:
            logger.warning("Cache is not enabled")
            return False
        
        return self.agno_store.clear()
    
    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics or None if cache is disabled
        """
        if not self.agno_store:
            logger.warning("Cache is not enabled")
            return None
        
        return self.agno_store.get_stats()
