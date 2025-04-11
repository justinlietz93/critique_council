"""
ArXiv Reference Service (Main Module)

This module provides the main interface for the ArXiv reference service,
acting as a facade for the various submodules that handle specific functions.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Set, Tuple

from .api_client import ArxivApiClient
from .cache_manager import ArxivCacheManager
from .utils import TextProcessor
from .bibtex_converter import BibTexConverter

# Set up logging
logger = logging.getLogger(__name__)

class ArxivReferenceService:
    """
    Main service for fetching and managing arXiv references.
    
    This service provides methods to:
    1. Search for papers on arXiv
    2. Fetch metadata for specific papers
    3. Convert arXiv metadata to BibTeX entries
    4. Manage references for different agents
    5. Cache results to avoid redundant API calls
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the ArXiv reference service.
        
        Args:
            cache_dir: Directory to store cached results. Defaults to 'storage/arxiv_cache'.
        """
        # Initialize component services
        self.api_client = ArxivApiClient()
        self.cache_manager = ArxivCacheManager(cache_dir)
        
        # Reference pools - shared across all agents
        self.global_references: Dict[str, Dict[str, Any]] = {}  # id -> full metadata
        self.agent_references: Dict[str, Dict[str, float]] = {}  # agent_name -> {id -> relevance_score}
        
        logger.info("ArXiv reference service initialized")
    
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
        
        Args:
            search_query: The search query string
            max_results: Maximum number of results to return
            sort_by: Sort field ("relevance", "lastUpdatedDate", "submittedDate")
            sort_order: Sort direction ("ascending" or "descending")
            use_cache: Whether to use cached results when available
            
        Returns:
            List of paper metadata
        """
        # Prepare query parameters
        params = {
            'search_query': search_query,
            'max_results': min(max_results, 100),  # Limit to 100 for reasonable responses
            'sortBy': sort_by,
            'sortOrder': sort_order
        }
        
        # Check cache if enabled
        if use_cache:
            cached_results = self.cache_manager.get_cached_response(params)
            if cached_results:
                logger.info(f"Using cached arXiv results for query: {search_query}")
                
                # Update global references with cached results
                for paper in cached_results:
                    paper_id = paper.get('id')
                    if paper_id:
                        self.global_references[paper_id] = paper
                
                return cached_results
        
        # Fetch from API
        logger.info(f"Fetching arXiv results for query: {search_query}")
        results = self.api_client.search(
            search_query=search_query,
            max_results=max_results,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Cache the results
        if use_cache:
            self.cache_manager.save_to_cache(params, results)
        
        # Update global references
        for paper in results:
            paper_id = paper.get('id')
            if paper_id:
                self.global_references[paper_id] = paper
        
        return results
    
    def fetch_by_id(self, arxiv_id: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Fetch metadata for a specific arXiv paper by ID.
        
        Args:
            arxiv_id: The arXiv ID of the paper
            use_cache: Whether to use cached results
            
        Returns:
            Paper metadata or None if not found
        """
        # Check if we already have this paper in global references
        if arxiv_id in self.global_references:
            return self.global_references[arxiv_id]
        
        # Prepare query parameters
        params = {
            'id_list': arxiv_id
        }
        
        # Check cache if enabled
        if use_cache:
            cached_results = self.cache_manager.get_cached_response(params)
            if cached_results and cached_results:
                paper = cached_results[0]
                paper_id = paper.get('id')
                if paper_id:
                    self.global_references[paper_id] = paper
                return paper
        
        # Fetch from API
        logger.info(f"Fetching arXiv metadata for paper: {arxiv_id}")
        paper = self.api_client.fetch_by_id(arxiv_id)
        
        # Cache the result
        if use_cache and paper:
            self.cache_manager.save_to_cache(params, [paper])
        
        # Update global references
        if paper:
            paper_id = paper.get('id')
            if paper_id:
                self.global_references[paper_id] = paper
        
        return paper
    
    def get_references_for_content(
        self, 
        content: str, 
        max_results: int = 10,
        domains: Optional[List[str]] = None 
    ) -> List[Dict[str, Any]]:
        """
        Find relevant references for the given content.
        
        Args:
            content: The content to find references for
            max_results: Maximum number of results to return
            domains: Optional list of domains to prioritize
            
        Returns:
            List of paper metadata for relevant papers
        """
        # Extract key terms from content using either keywords or domain-specific terms
        if domains:
            search_terms = TextProcessor.extract_domain_specific_terms(content, domains)
            # Supplement with general keywords if we have few domain terms
            if len(search_terms) < 3:
                search_terms.extend(TextProcessor.extract_keywords(content, max_keywords=5))
        else:
            search_terms = TextProcessor.extract_keywords(content, max_keywords=10)
        
        # Create search query
        search_query = TextProcessor.create_arxiv_search_query(search_terms)
        
        if not search_query:
            logger.warning("Could not generate search query from content")
            return []
        
        # Search arXiv
        papers = self.search_arxiv(search_query, max_results=max_results)
        
        return papers
    
    def paper_to_bibtex(self, paper: Dict[str, Any]) -> str:
        """
        Convert arXiv paper metadata to BibTeX entry.
        
        Args:
            paper: arXiv paper metadata
            
        Returns:
            BibTeX entry as a string
        """
        return BibTexConverter.paper_to_bibtex(paper)
    
    def register_reference_for_agent(self, agent_name: str, paper_id: str, relevance_score: float = 1.0) -> None:
        """
        Register a reference as being used by a specific agent.
        
        Args:
            agent_name: Name of the agent using the reference
            paper_id: arXiv ID of the paper
            relevance_score: How relevant this paper is (0.0-1.0)
        """
        if agent_name not in self.agent_references:
            self.agent_references[agent_name] = {}
        
        self.agent_references[agent_name][paper_id] = relevance_score
        logger.debug(f"Registered reference {paper_id} for agent {agent_name} with score {relevance_score}")
    
    def get_agent_references(self, agent_name: str) -> List[Dict[str, Any]]:
        """
        Get all references registered for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            List of paper metadata for references used by the agent
        """
        if agent_name not in self.agent_references:
            return []
        
        results = []
        for paper_id, score in self.agent_references[agent_name].items():
            if paper_id in self.global_references:
                paper = self.global_references[paper_id].copy()
                paper['relevance_score'] = score
                results.append(paper)
        
        # Sort by relevance score descending
        results.sort(key=lambda x: x.get('relevance_score', 0.0), reverse=True)
        return results
    
    def suggest_references_for_agent(
        self, 
        agent_name: str, 
        content: str, 
        agent_perspective: Optional[str] = None,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Suggest relevant references for an agent based on content and agent's perspective.
        
        Args:
            agent_name: Name of the agent
            content: Content to find references for
            agent_perspective: Optional description of agent's perspective 
                               (e.g., "Kantian philosophy", "Systems analysis")
            max_results: Maximum number of results to return
            
        Returns:
            List of paper metadata
        """
        # Generate search terms from content
        content_terms = TextProcessor.extract_keywords(content, max_keywords=8)
        
        # If agent perspective is provided, include it in search
        if agent_perspective:
            # Extract terms from the agent perspective
            perspective_terms = [term.strip() for term in agent_perspective.split() 
                               if len(term.strip()) > 3 and term.lower() not in TextProcessor.STOPWORDS]
            
            # Create a search query that combines content and perspective
            combined_terms = content_terms + perspective_terms
            search_query = TextProcessor.create_arxiv_search_query(combined_terms, operator="OR")
        else:
            # Just use content terms
            search_query = TextProcessor.create_arxiv_search_query(content_terms)
        
        # If no search query could be generated, return empty list
        if not search_query:
            logger.warning(f"Could not generate search query for agent {agent_name}")
            return []
            
        # Search ArXiv
        papers = self.search_arxiv(search_query, max_results=max_results)
        
        # Register for agent with diminishing relevance
        for i, paper in enumerate(papers):
            paper_id = paper.get('id')
            if paper_id:
                # Register with diminishing relevance (top result gets 1.0, last gets 0.5)
                score = 1.0 - (i / (2 * max_results))
                self.register_reference_for_agent(agent_name, paper_id, score)
        
        return papers
    
    def generate_bibtex_for_all_references(self) -> str:
        """
        Generate BibTeX entries for all referenced papers across all agents.
        
        Returns:
            BibTeX string containing all references
        """
        # Collect all paper IDs from all agents
        all_paper_ids = set()
        for agent_refs in self.agent_references.values():
            all_paper_ids.update(agent_refs.keys())
        
        # Generate BibTeX for each paper
        papers = []
        for paper_id in all_paper_ids:
            if paper_id in self.global_references:
                papers.append(self.global_references[paper_id])
        
        # Format BibTeX file
        current_date = "ArXiv references generated for Critique Council"
        return BibTexConverter.format_bib_file(papers, header_comment=current_date)
    
    def update_latex_bibliography(self, output_path: str) -> bool:
        """
        Update the LaTeX bibliography file with all referenced papers.
        
        Args:
            output_path: Path to write the bibliography file
            
        Returns:
            True if successful, False otherwise
        """
        bibtex_content = self.generate_bibtex_for_all_references()
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(bibtex_content)
            
            logger.info(f"Updated LaTeX bibliography at {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to update LaTeX bibliography: {e}")
            return False
    
    def clear_cache(self, older_than_days: Optional[int] = None) -> int:
        """
        Clear the cache.
        
        Args:
            older_than_days: If provided, only clear files older than this many days
            
        Returns:
            Number of cache files cleared
        """
        return self.cache_manager.clear_cache(older_than_days)
