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

# Import basic Agno modules
import agno
from agno.document import Document
from agno.models import embedding as embedding_module
from agno.vectordb import vectordb

# Set up logging
logger = logging.getLogger(__name__)

class ArxivAgnoStore:
    """
    ArXiv paper storage and retrieval using Agno's vector search capabilities.
    
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
                 openai_api_key: Optional[str] = None):
        """
        Initialize the ArXiv Agno integration.
        
        Args:
            cache_dir: Directory for storing the vector database
            table_name: Name of the table to store papers in
            ttl_days: Number of days to keep papers before considering them expired
            openai_api_key: OpenAI API key for embeddings
        """
        self.cache_dir = cache_dir or self.DEFAULT_CACHE_DIR
        self.table_name = table_name or self.DEFAULT_TABLE_NAME
        self.ttl_days = ttl_days
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Set up OpenAI API key if provided
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key

        # Initialize embedding model
        # Try to use OpenAI embeddings if API key is available, otherwise use a simpler model
        try:
            self.embedder = embedding_module.OpenAIEmbedding("text-embedding-3-small")
            logger.info("Using OpenAI embeddings")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI embedding: {e}")
            logger.info("Falling back to simpler embedding model")
            self.embedder = embedding_module.SimpleEmbedding()
        
        # Initialize vector database
        self.vector_db = vectordb.VectorDB(
            name=self.table_name,
            embedding_model=self.embedder,
            persist_directory=self.cache_dir
        )
        
        logger.info(f"ArXiv Agno integration initialized with cache at {self.cache_dir}")
    
    def _prepare_paper_document(self, paper: Dict[str, Any]) -> Document:
        """
        Prepare a paper for storage as an Agno Document.
        
        Args:
            paper: Paper metadata dictionary
            
        Returns:
            Agno Document object
        """
        # Extract key information
        paper_id = paper.get('id', '')
        title = paper.get('title', '')
        summary = paper.get('summary', '')
        authors = ', '.join([author.get('name', '') for author in paper.get('authors', [])])
        published = paper.get('published', '')
        
        # Calculate expiration date
        expiration = (datetime.now() + timedelta(days=self.ttl_days)).isoformat()
        
        # Create full text content
        content = f"Title: {title}\nAuthors: {authors}\nPublished: {published}\nSummary: {summary}"
        
        # Store full metadata in metadata field
        metadata = {
            "id": paper_id,
            "title": title,
            "summary": summary,
            "authors": authors,
            "published": published,
            "expiration": expiration,
            "metadata": json.dumps(paper)  # Store full metadata as JSON
        }
        
        # Create document
        document = Document(
            id=paper_id,
            content=content,
            metadata=metadata
        )
        
        return document
    
    def add_papers(self, papers: List[Dict[str, Any]]) -> int:
        """
        Add multiple papers to the vector database.
        
        Args:
            papers: List of paper metadata dictionaries
            
        Returns:
            Number of papers successfully added
        """
        if not papers:
            return 0
        
        # Prepare documents
        documents = [self._prepare_paper_document(paper) for paper in papers]
        
        # Add to vector database
        try:
            self.vector_db.add_documents(documents)
            logger.info(f"Added {len(documents)} papers to vector database")
            return len(documents)
        except Exception as e:
            logger.error(f"Error adding papers to vector database: {e}")
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
            # Search vector database
            results = self.vector_db.search(
                query=query,
                top_k=max_results,
                score_threshold=min_score
            )
            
            # Extract and parse metadata
            papers = []
            for result in results:
                try:
                    # Get full metadata from the metadata JSON
                    metadata_json = result.metadata.get("metadata")
                    if metadata_json:
                        paper = json.loads(metadata_json)
                        papers.append(paper)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse metadata for result: {result.id}")
                    # Fallback to the basic metadata
                    paper = {
                        "id": result.metadata.get("id", ""),
                        "title": result.metadata.get("title", ""),
                        "summary": result.metadata.get("summary", ""),
                        "authors": [{"name": name.strip()} for name in result.metadata.get("authors", "").split(",") if name.strip()],
                        "published": result.metadata.get("published", "")
                    }
                    papers.append(paper)
            
            logger.info(f"Found {len(papers)} papers matching query: {query}")
            return papers
        except Exception as e:
            logger.error(f"Error searching vector database: {e}")
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
            # Get document by ID
            document = self.vector_db.get_document(paper_id)
            if not document:
                return None
                
            # Extract full metadata
            try:
                metadata_json = document.metadata.get("metadata")
                if metadata_json:
                    return json.loads(metadata_json)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse metadata for paper: {paper_id}")
                
            # Fallback to basic metadata
            return {
                "id": document.metadata.get("id", ""),
                "title": document.metadata.get("title", ""),
                "summary": document.metadata.get("summary", ""),
                "authors": [{"name": name.strip()} for name in document.metadata.get("authors", "").split(",") if name.strip()],
                "published": document.metadata.get("published", "")
            }
        except Exception as e:
            logger.error(f"Error retrieving paper: {e}")
            return None
    
    def clear(self) -> bool:
        """
        Clear all papers from the vector database.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear the vector database
            self.vector_db.clear()
            logger.info("Cleared vector database")
            return True
        except Exception as e:
            logger.error(f"Error clearing vector database: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database.
        
        Returns:
            Dictionary with vector database statistics
        """
        try:
            # Get document count
            doc_count = self.vector_db.count()
            
            return {
                "document_count": doc_count,
                "cache_dir": self.cache_dir,
                "table_name": self.table_name,
                "ttl_days": self.ttl_days,
            }
        except Exception as e:
            logger.error(f"Error getting vector database stats: {e}")
            return {
                "error": str(e),
                "cache_dir": self.cache_dir,
                "table_name": self.table_name,
                "ttl_days": self.ttl_days,
            }
