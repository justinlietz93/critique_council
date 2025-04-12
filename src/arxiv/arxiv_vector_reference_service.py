"""
ArXiv Vector Reference Service

This module extends the ArXiv reference service with vector-based semantic search capabilities,
using the smart vector store for improved relevance matching.
"""

import os
import logging
from typing import Dict, List, Any, Optional

from .arxiv_reference_service import ArxivReferenceService
from .smart_vector_store import ArxivSmartStore
from .utils import TextProcessor

# Set up logging
logger = logging.getLogger(__name__)

class ArxivVectorReferenceService(ArxivReferenceService):
    """
    Enhanced ArXiv reference service using vector search.
    
    This extends the standard reference service with vector-based semantic 
    search capabilities for better relevance matching.
    """
    
    def __init__(self, 
                 cache_dir: Optional[str] = None, 
                 use_db_cache: bool = True,
                 cache_ttl_days: int = 30,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize the ArXiv vector reference service.
        
        Args:
            cache_dir: Directory to store cached results. Defaults to 'storage/arxiv_cache'.
            use_db_cache: Whether to use the database cache manager. Defaults to True.
            cache_ttl_days: Number of days before cached entries expire. Defaults to 30.
            config: Additional configuration settings.
        """
        # Initialize the parent reference service
        super().__init__(
            cache_dir=cache_dir,
            use_db_cache=use_db_cache,
            cache_ttl_days=cache_ttl_days,
            config=config
        )
        
        # Extract vector store config
        self.force_fallback = False
        self.openai_api_key = None
        self.vector_table_name = "arxiv_papers"
        self.vector_cache_dir = cache_dir
        
        if config:
            arxiv_config = config.get('arxiv', {})
            self.force_fallback = arxiv_config.get('force_vector_fallback', False)
            self.openai_api_key = arxiv_config.get('openai_api_key')
            self.vector_table_name = arxiv_config.get('vector_table_name', self.vector_table_name)
            self.vector_cache_dir = arxiv_config.get('vector_cache_dir', cache_dir)
        
        # Initialize vector store
        self.vector_store = ArxivSmartStore(
            cache_dir=self.vector_cache_dir,
            table_name=self.vector_table_name,
            ttl_days=cache_ttl_days,
            openai_api_key=self.openai_api_key,
            force_fallback=self.force_fallback
        )
        
        logger.info(f"ArXiv vector reference service initialized with {self.vector_store._store.__class__.__name__}")
    
    def _ensure_paper_in_vector_store(self, paper: Dict[str, Any]) -> None:
        """
        Ensure the paper is added to the vector store.
        
        Args:
            paper: Paper metadata dictionary
        """
        if not paper:
            return
            
        # Check if this paper already exists in the vector store
        paper_id = paper.get('id')
        if not paper_id:
            return
            
        # Search for existing paper
        existing_paper = self.vector_store.get_paper(paper_id)
        if existing_paper:
            return
            
        # Add to vector store
        self.vector_store.add_papers([paper])
    
    def _ensure_papers_in_vector_store(self, papers: List[Dict[str, Any]]) -> None:
        """
        Ensure multiple papers are added to the vector store.
        
        Args:
            papers: List of paper metadata dictionaries
        """
        if not papers:
            return
            
        # Get existing paper IDs
        paper_ids = [p.get('id') for p in papers if p.get('id')]
        
        # Filter to only add papers not already in the vector store
        papers_to_add = []
        for paper in papers:
            paper_id = paper.get('id')
            if not paper_id:
                continue
                
            # Check if we need to add this paper
            existing_paper = self.vector_store.get_paper(paper_id)
            if not existing_paper:
                papers_to_add.append(paper)
        
        # Add all papers that need adding
        if papers_to_add:
            self.vector_store.add_papers(papers_to_add)
    
    def search_arxiv(
        self, 
        search_query: str, 
        max_results: int = 10, 
        sort_by: str = "relevance",
        sort_order: str = "descending",
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search arXiv for papers matching the given query.
        
        This method overrides the base method to ensure all retrieved papers
        are also added to the vector store for future semantic search.
        
        Args:
            search_query: The search query string
            max_results: Maximum number of results to return
            sort_by: Sort field ("relevance", "lastUpdatedDate", "submittedDate")
            sort_order: Sort direction ("ascending" or "descending")
            use_cache: Whether to use cached results when available
            
        Returns:
            List of paper metadata
        """
        # First, use the original search method
        results = super().search_arxiv(
            search_query=search_query,
            max_results=max_results,
            sort_by=sort_by,
            sort_order=sort_order,
            use_cache=use_cache
        )
        
        # Then, ensure all results are added to the vector store
        self._ensure_papers_in_vector_store(results)
        
        return results
    
    def fetch_by_id(self, arxiv_id: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Fetch metadata for a specific arXiv paper by ID.
        
        This method overrides the base method to ensure retrieved papers
        are also added to the vector store for future semantic search.
        
        Args:
            arxiv_id: The arXiv ID of the paper
            use_cache: Whether to use cached results
            
        Returns:
            Paper metadata or None if not found
        """
        # First, check if we can get this directly from the vector store
        paper = self.vector_store.get_paper(arxiv_id)
        if paper:
            # Also update the global references
            self.global_references[arxiv_id] = paper
            return paper
        
        # If not found, use the original method
        paper = super().fetch_by_id(arxiv_id, use_cache)
        
        # Add to vector store if found
        if paper:
            self._ensure_paper_in_vector_store(paper)
        
        return paper
    
    def get_references_for_content(
        self, 
        content: str, 
        max_results: int = 10,
        domains: Optional[List[str]] = None 
    ) -> List[Dict[str, Any]]:
        """
        Find relevant references for the given content using vector search.
        
        This method overrides the base method to use vector search for semantic matching.
        
        Args:
            content: The content to find references for
            max_results: Maximum number of results to return
            domains: Optional list of domains to prioritize
            
        Returns:
            List of paper metadata for relevant papers
        """
        # Try vector search first
        vector_results = self.vector_store.search(
            query=content,
            max_results=max_results,
            min_score=0.25  # Higher threshold for better quality
        )
        
        # If we have a good number of vector results, use them
        if len(vector_results) >= max_results // 2:
            logger.info(f"Using vector search results for content (found {len(vector_results)} papers)")
            # Add to global references
            for paper in vector_results:
                paper_id = paper.get('id')
                if paper_id:
                    self.global_references[paper_id] = paper
            return vector_results[:max_results]
        
        # Otherwise, fall back to keyword search
        logger.info(f"Vector search insufficient ({len(vector_results)} papers), falling back to keyword search")
        keyword_results = super().get_references_for_content(
            content, max_results=max_results, domains=domains
        )
        
        # Ensure keyword results are added to vector store for future searches
        self._ensure_papers_in_vector_store(keyword_results)
        
        # Combine results, removing duplicates
        combined_results = vector_results.copy()
        seen_ids = {paper.get('id') for paper in vector_results if paper.get('id')}
        
        for paper in keyword_results:
            paper_id = paper.get('id')
            if paper_id and paper_id not in seen_ids:
                combined_results.append(paper)
                seen_ids.add(paper_id)
                
                if len(combined_results) >= max_results:
                    break
        
        return combined_results[:max_results]
    
    def suggest_references_for_agent(
        self, 
        agent_name: str, 
        content: str, 
        agent_perspective: Optional[str] = None,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Suggest relevant references for an agent based on content and agent's perspective.
        
        This method overrides the base method to use vector search for semantic matching.
        
        Args:
            agent_name: Name of the agent
            content: Content to find references for
            agent_perspective: Optional description of agent's perspective 
                               (e.g., "Kantian philosophy", "Systems analysis")
            max_results: Maximum number of results to return
            
        Returns:
            List of paper metadata
        """
        # Combine content and agent perspective for a more targeted search
        search_content = content
        if agent_perspective:
            search_content = f"{content}\n\nPerspective: {agent_perspective}"
        
        # Use vector search
        papers = self.vector_store.search(
            query=search_content,
            max_results=max_results,
            min_score=0.2
        )
        
        # If results are limited, fall back to keyword search
        if len(papers) < max_results // 2:
            # Use the original method for keyword search
            keyword_papers = super().suggest_references_for_agent(
                agent_name, content, agent_perspective, max_results
            )
            
            # Combine results, removing duplicates
            seen_ids = {paper.get('id') for paper in papers if paper.get('id')}
            for paper in keyword_papers:
                paper_id = paper.get('id')
                if paper_id and paper_id not in seen_ids:
                    papers.append(paper)
                    seen_ids.add(paper_id)
                    
                    if len(papers) >= max_results:
                        break
        
        # Register for agent with diminishing relevance
        for i, paper in enumerate(papers):
            paper_id = paper.get('id')
            if paper_id:
                # Register with diminishing relevance (top result gets 1.0, last gets 0.5)
                score = 1.0 - (i / (2 * max_results))
                self.register_reference_for_agent(agent_name, paper_id, score)
        
        return papers[:max_results]
    
    def clear_cache(self, older_than_days: Optional[int] = None) -> int:
        """
        Clear both the regular cache and the vector store cache.
        
        Args:
            older_than_days: If provided, only clear files or entries older than this many days
            
        Returns:
            Number of cache files or entries cleared
        """
        # Clear regular cache
        count = super().clear_cache(older_than_days)
        
        # Clear vector store
        if self.vector_store.clear():
            count += 1
        
        return count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get combined statistics about both the regular cache and vector store cache.
        
        Returns:
            Dictionary with cache statistics from both sources
        """
        # Get original cache stats
        stats = super().get_cache_stats()
        
        # Get vector store stats
        vector_stats = self.vector_store.get_stats()
        
        # Merge stats with vector store stats
        stats.update({
            "vector_store_implementation": vector_stats.get("implementation", "Unknown"),
            "vector_store_document_count": vector_stats.get("document_count", 0),
            "vector_store_cache_dir": vector_stats.get("cache_dir", ""),
        })
        
        return stats
