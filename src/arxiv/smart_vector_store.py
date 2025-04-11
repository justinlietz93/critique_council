"""
Smart Vector Store for ArXiv

This module provides a unified interface for vector search of ArXiv papers,
automatically choosing between available implementations.
"""

import os
import logging
import importlib.util
from typing import Dict, List, Any, Optional

# Set up logging
logger = logging.getLogger(__name__)

class ArxivSmartStore:
    """
    Smart vector store for ArXiv papers.
    
    This class automatically chooses the best available vector store implementation:
    1. Agno-based vector store (if available)
    2. Pure Python vector store (fallback)
    """
    
    def __init__(self,
                 cache_dir: Optional[str] = None,
                 table_name: Optional[str] = None,
                 ttl_days: int = 30,
                 openai_api_key: Optional[str] = None,
                 force_fallback: bool = False):
        """
        Initialize the smart vector store.
        
        Args:
            cache_dir: Directory for storing vector data
            table_name: Name of the table to store data in
            ttl_days: Number of days to keep papers before considering them expired
            openai_api_key: OpenAI API key for embeddings
            force_fallback: Force use of the fallback implementation
        """
        self.cache_dir = cache_dir or "storage/arxiv_cache"
        self.table_name = table_name or "arxiv_papers"
        self.ttl_days = ttl_days
        
        # Try to initialize the best available implementation
        self._store = None
        
        if not force_fallback:
            # Try to use Agno if available
            try:
                logger.info("Trying to initialize with Agno...")
                # Import the required modules
                from src.arxiv.agno_integration import ArxivAgnoStore
                
                # Initialize the Agno-based store
                self._store = ArxivAgnoStore(
                    cache_dir=self.cache_dir,
                    table_name=self.table_name,
                    ttl_days=self.ttl_days,
                    openai_api_key=openai_api_key
                )
                
                logger.info("Successfully initialized with Agno")
            except ImportError as e:
                logger.warning(f"Failed to import Agno: {e}")
                self._store = None
            except Exception as e:
                logger.warning(f"Failed to initialize Agno: {e}")
                self._store = None
                
        # Fall back to our pure Python implementation if needed
        if self._store is None:
            logger.info("Falling back to pure Python vector store")
            from src.arxiv.vector_store import ArxivVectorStore
            
            self._store = ArxivVectorStore(
                cache_dir=self.cache_dir,
                table_name=self.table_name,
                ttl_days=self.ttl_days
            )
        
        logger.info(f"ArXiv smart vector store initialized using: {self._store.__class__.__name__}")
    
    def add_papers(self, papers: List[Dict[str, Any]]) -> int:
        """
        Add multiple papers to the vector store.
        
        Args:
            papers: List of paper metadata dictionaries
            
        Returns:
            Number of papers successfully added
        """
        return self._store.add_papers(papers)
    
    def search(self, 
               query: str, 
               max_results: int = 10, 
               min_score: float = 0.1) -> List[Dict[str, Any]]:
        """
        Search for papers matching the query.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            min_score: Minimum relevance score threshold
            
        Returns:
            List of relevant paper metadata dictionaries
        """
        return self._store.search(query, max_results, min_score)
    
    def get_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific paper by ID.
        
        Args:
            paper_id: Unique identifier for the paper
            
        Returns:
            Paper metadata dictionary if found, None otherwise
        """
        return self._store.get_paper(paper_id)
    
    def clear(self) -> bool:
        """
        Clear all papers from the vector store.
        
        Returns:
            True if successful, False otherwise
        """
        return self._store.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary with vector store statistics
        """
        stats = self._store.get_stats()
        
        # Add information about what backend is being used
        stats["implementation"] = self._store.__class__.__name__
        
        return stats
