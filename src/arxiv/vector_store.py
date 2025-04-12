"""
ArXiv Vector Store Implementation

This module provides a simplified vector storage implementation for ArXiv papers,
which can be used as a fallback if the Agno integration has issues.
"""

import os
import json
import logging
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict

# Set up logging
logger = logging.getLogger(__name__)

class SimpleEmbedder:
    """Simple text embedder using hash-based vectors."""
    
    def __init__(self, dimensions=64):
        """Initialize with embedding dimensions."""
        self.dimensions = dimensions
    
    def embed(self, text: str) -> List[float]:
        """Convert text to a fixed-length embedding vector."""
        # Use hash for deterministic embedding
        text = text.lower()  # Normalize
        hash_obj = hashlib.md5(text.encode("utf-8"))
        hash_bytes = hash_obj.digest()
        
        # Convert hash bytes to floats in range [-1, 1]
        embedding = []
        for i in range(min(self.dimensions, len(hash_bytes))):
            val = (hash_bytes[i] / 127.5) - 1.0
            embedding.append(val)
            
        # Pad if needed
        while len(embedding) < self.dimensions:
            embedding.append(0.0)
            
        return embedding

class Document:
    """Simple document class for storing paper data."""
    
    def __init__(self, id: str, content: str, metadata: Dict[str, Any]):
        """Initialize document with ID, content and metadata."""
        self.id = id
        self.content = content
        self.metadata = metadata
        self._embedding = None
    
    def get_embedding(self, embedder) -> List[float]:
        """Get or compute embedding for this document."""
        if self._embedding is None:
            self._embedding = embedder.embed(self.content)
        return self._embedding

class VectorStore:
    """Simple vector store for text documents."""
    
    def __init__(self, name: str = "default", persist_directory: str = None):
        """Initialize vector store with name and persistence directory."""
        self.name = name
        self.persist_directory = persist_directory
        self.documents = {}  # id -> Document
        self.embedder = SimpleEmbedder()
        
        # Create persistence directory if provided
        if self.persist_directory:
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Load any existing data
            self._load()
    
    def _load(self):
        """Load documents from persistence directory."""
        if not self.persist_directory:
            return
            
        store_file = os.path.join(self.persist_directory, f"{self.name}.json")
        if os.path.exists(store_file):
            try:
                with open(store_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for doc_data in data:
                        doc = Document(
                            id=doc_data["id"],
                            content=doc_data["content"],
                            metadata=doc_data["metadata"]
                        )
                        self.documents[doc.id] = doc
                logger.info(f"Loaded {len(self.documents)} documents from {store_file}")
            except Exception as e:
                logger.error(f"Error loading documents: {e}")
    
    def _save(self):
        """Save documents to persistence directory."""
        if not self.persist_directory:
            return
            
        store_file = os.path.join(self.persist_directory, f"{self.name}.json")
        try:
            data = []
            for doc in self.documents.values():
                data.append({
                    "id": doc.id,
                    "content": doc.content,
                    "metadata": doc.metadata
                })
            with open(store_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(data)} documents to {store_file}")
        except Exception as e:
            logger.error(f"Error saving documents: {e}")
    
    def add_documents(self, documents: List[Document]):
        """Add multiple documents to the store."""
        for doc in documents:
            self.documents[doc.id] = doc
        self._save()
    
    def get_document(self, id: str) -> Optional[Document]:
        """Get document by ID."""
        return self.documents.get(id)
    
    def count(self) -> int:
        """Get document count."""
        return len(self.documents)
    
    def clear(self):
        """Clear all documents."""
        self.documents.clear()
        self._save()
    
    def _compute_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Compute cosine similarity between vectors."""
        v1_array = np.array(v1)
        v2_array = np.array(v2)
        
        # Normalize
        v1_norm = np.linalg.norm(v1_array)
        v2_norm = np.linalg.norm(v2_array)
        
        if v1_norm == 0 or v2_norm == 0:
            return 0.0
            
        # Compute cosine similarity
        similarity = np.dot(v1_array, v2_array) / (v1_norm * v2_norm)
        
        # Convert from [-1, 1] to [0, 1]
        similarity = (similarity + 1) / 2
        
        return float(similarity)
    
    def search(self, query: str, top_k: int = 10, score_threshold: float = 0.0) -> List[Document]:
        """Search for similar documents."""
        if not self.documents:
            return []
            
        # Encode query
        query_embedding = self.embedder.embed(query)
        
        # Score all documents
        scores = []
        for doc in self.documents.values():
            doc_embedding = doc.get_embedding(self.embedder)
            similarity = self._compute_similarity(query_embedding, doc_embedding)
            scores.append((doc, similarity))
        
        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Filter by threshold and limit to top_k
        results = []
        for doc, score in scores[:top_k]:
            if score >= score_threshold:
                results.append(doc)
        
        return results

class ArxivVectorStore:
    """
    ArXiv paper storage and retrieval using vector-based search.
    
    This class provides a simplified vector search implementation for ArXiv papers,
    which can be used as a fallback if the Agno integration has issues.
    """
    
    # Default settings
    DEFAULT_CACHE_DIR = "storage/arxiv_cache"
    DEFAULT_CACHE_TTL_DAYS = 30
    DEFAULT_TABLE_NAME = "arxiv_papers"
    
    def __init__(self,
                 cache_dir: Optional[str] = None,
                 table_name: Optional[str] = None,
                 ttl_days: int = DEFAULT_CACHE_TTL_DAYS):
        """
        Initialize the ArXiv vector store.
        
        Args:
            cache_dir: Directory for storing the vector database
            table_name: Name of the table to store papers in
            ttl_days: Number of days to keep papers before considering them expired
        """
        self.cache_dir = cache_dir or self.DEFAULT_CACHE_DIR
        self.table_name = table_name or self.DEFAULT_TABLE_NAME
        self.ttl_days = ttl_days
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize embedder and vector store
        self.embedder = SimpleEmbedder()
        self.vector_db = VectorStore(
            name=self.table_name,
            persist_directory=self.cache_dir
        )
        
        logger.info(f"ArXiv vector store initialized with cache at {self.cache_dir}")
    
    def _prepare_paper_document(self, paper: Dict[str, Any]) -> Document:
        """
        Prepare a paper for storage as a Document.
        
        Args:
            paper: Paper metadata dictionary
            
        Returns:
            Document object
        """
        # Extract key information
        paper_id = paper.get('id', '')
        title = paper.get('title', '')
        summary = paper.get('summary', '')
        
        # Handle different author formats
        authors_list = paper.get('authors', [])
        author_names = []
        for author in authors_list:
            if isinstance(author, dict):
                # Dictionary format: {"name": "Author Name", ...}
                author_name = author.get('name', '')
                if author_name:
                    author_names.append(author_name)
            elif isinstance(author, str):
                # String format: "Author Name"
                author_names.append(author)
        authors = ', '.join(author_names)
        
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
        Add multiple papers to the vector store.
        
        Args:
            papers: List of paper metadata dictionaries
            
        Returns:
            Number of papers successfully added
        """
        if not papers:
            return 0
        
        # Prepare documents
        documents = [self._prepare_paper_document(paper) for paper in papers]
        
        # Add to vector store
        try:
            self.vector_db.add_documents(documents)
            logger.info(f"Added {len(documents)} papers to vector store")
            return len(documents)
        except Exception as e:
            logger.error(f"Error adding papers to vector store: {e}")
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
            # Search vector store
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
            logger.error(f"Error searching vector store: {e}")
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
        Clear all papers from the vector store.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear the vector store
            self.vector_db.clear()
            logger.info("Cleared vector store")
            return True
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary with vector store statistics
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
            logger.error(f"Error getting vector store stats: {e}")
            return {
                "error": str(e),
                "cache_dir": self.cache_dir,
                "table_name": self.table_name,
                "ttl_days": self.ttl_days,
            }
