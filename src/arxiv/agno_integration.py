"""
ArXiv Integration with Agno

This module provides integration between the ArXiv reference service and Agno,
enabling vector search and efficient retrieval of academic papers.
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

import agno
from agno.knowledge import KnowledgeBase
from agno.vectordb import lancedb 
from agno.embedder import openai
from agno.embedder import base as embedder_base

# Set up logging
logger = logging.getLogger(__name__)

class ArxivAgnoStore:
    """
    ArXiv paper storage and retrieval using Agno's knowledge base and vector search capabilities.
    
    This class integrates with Agno to provide:
    1. Efficient storage of ArXiv papers with embeddings
    2. Vector-based semantic search
    3. Hybrid search combining keywords and vector similarity
    4. TTL-based expiration of cached papers
    """
    
    # Default settings
    DEFAULT_CACHE_DIR = "storage/arxiv_cache"
    DEFAULT_CACHE_TTL_DAYS = 30
    DEFAULT_TABLE_NAME = "arxiv_papers"
    
    def __init__(self,
                 cache_dir: Optional[str] = None,
                 table_name: Optional[str] = None,
                 ttl_days: int = DEFAULT_CACHE_TTL_DAYS,
                 embedder: Optional[embedder_base.Embedder] = None,
                 openai_api_key: Optional[str] = None):
        """
        Initialize the ArXiv Agno integration.
        
        Args:
            cache_dir: Directory for storing the vector database
            table_name: Name of the table to store papers in
            ttl_days: Number of days to keep papers before considering them expired
            embedder: Custom embedder to use (if None, will use OpenAI's embedder)
            openai_api_key: OpenAI API key for the default embedder
        """
        self.cache_dir = cache_dir or self.DEFAULT_CACHE_DIR
        self.table_name = table_name or self.DEFAULT_TABLE_NAME
        self.ttl_days = ttl_days
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Set up embedder
        if embedder is None:
            # If no key is provided, it will look for the OPENAI_API_KEY environment variable
            if openai_api_key:
                os.environ["OPENAI_API_KEY"] = openai_api_key
            self.embedder = openai.OpenAIEmbedder(id="text-embedding-3-small")
        else:
            self.embedder = embedder
        
        # Set up vector database
        self.vector_db = lancedb.LanceDb(
            uri=self.cache_dir,
            table_name=self.table_name,
            search_type=lancedb.SearchType.hybrid,  # Use hybrid search by default for better results
            embedder=self.embedder,
        )
        
        # Create knowledge base
        self.knowledge_base = KnowledgeBase(
            vector_db=self.vector_db,
        )
        
        logger.info(f"ArXiv Agno integration initialized with cache at {self.cache_dir}")
    
    def _prepare_paper_document(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare a paper for storage in the knowledge base.
        
        Args:
            paper: Paper metadata dictionary
            
        Returns:
            Document dictionary for the knowledge base
        """
        # Extract key information
        paper_id = paper.get('id', '')
        title = paper.get('title', '')
        summary = paper.get('summary', '')
        authors = ', '.join([author.get('name', '') for author in paper.get('authors', [])])
        published = paper.get('published', '')
        
        # Create document
        document = {
            "id": paper_id,
            "title": title,
            "summary": summary,
            "authors": authors,
            "published": published,
            "metadata": json.dumps(paper),  # Store full metadata as JSON
            "expiration": (datetime.now() + timedelta(days=self.ttl_days)).isoformat(),
            "text": f"Title: {title}\nAuthors: {authors}\nPublished: {published}\nSummary: {summary}",
        }
        
        return document
    
    def add_papers(self, papers: List[Dict[str, Any]]) -> int:
        """
        Add multiple papers to the knowledge base.
        
        Args:
            papers: List of paper metadata dictionaries
            
        Returns:
            Number of papers successfully added
        """
        if not papers:
            return 0
        
        # Prepare documents
        documents = [self._prepare_paper_document(paper) for paper in papers]
        
        # Add to knowledge base
        try:
            self.knowledge_base.add_documents(documents)
            logger.info(f"Added {len(documents)} papers to knowledge base")
            return len(documents)
        except Exception as e:
            logger.error(f"Error adding papers to knowledge base: {e}")
            return 0
    
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
        try:
            # Search knowledge base
            results = self.knowledge_base.search(
                query=query,
                limit=max_results,
                min_score=min_score,
            )
            
            # Extract and parse metadata
            papers = []
            for result in results:
                if "metadata" in result:
                    try:
                        metadata = json.loads(result["metadata"])
                        papers.append(metadata)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse metadata for result: {result.get('id', 'unknown')}")
            
            logger.info(f"Found {len(papers)} papers matching query: {query}")
            return papers
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
    
    def get_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific paper by ID.
        
        Args:
            paper_id: Unique identifier for the paper
            
        Returns:
            Paper metadata dictionary if found, None otherwise
        """
        try:
            # Query by ID
            results = self.knowledge_base.search(
                query=f"id:{paper_id}",
                limit=1,
            )
            
            # Extract and parse metadata
            if results and "metadata" in results[0]:
                try:
                    return json.loads(results[0]["metadata"])
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse metadata for paper: {paper_id}")
            
            return None
        except Exception as e:
            logger.error(f"Error retrieving paper: {e}")
            return None
    
    def clear(self) -> bool:
        """
        Clear all papers from the knowledge base.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove and recreate the knowledge base
            self.knowledge_base.clear()
            logger.info("Cleared knowledge base")
            return True
        except Exception as e:
            logger.error(f"Error clearing knowledge base: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge base.
        
        Returns:
            Dictionary with knowledge base statistics
        """
        try:
            # Get document count
            doc_count = self.knowledge_base.count()
            
            return {
                "document_count": doc_count,
                "cache_dir": self.cache_dir,
                "table_name": self.table_name,
                "ttl_days": self.ttl_days,
            }
        except Exception as e:
            logger.error(f"Error getting knowledge base stats: {e}")
            return {
                "error": str(e),
                "cache_dir": self.cache_dir,
                "table_name": self.table_name,
                "ttl_days": self.ttl_days,
            }
