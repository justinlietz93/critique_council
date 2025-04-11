"""
ArXiv Vector Database Module

This module provides vector-based semantic search capabilities for ArXiv papers
using embeddings for more accurate relevance matching.
"""

import os
import time
import json
import logging
import sqlite3
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import threading

# Set up logging
logger = logging.getLogger(__name__)

class ArxivVectorStore:
    """
    Vector-based storage and retrieval for ArXiv papers.
    
    This class implements:
    1. Storage of paper embeddings in SQLite
    2. Semantic similarity search using vector operations
    3. Hybrid search combining keywords and vector similarity
    4. TTL-based expiration of cached embeddings
    """
    
    # Default settings
    DEFAULT_DB_PATH = "storage/arxiv_cache/arxiv_vectors.db"
    DEFAULT_CACHE_TTL_DAYS = 30
    DEFAULT_EMBEDDING_DIMENSION = 1536  # Default for OpenAI embeddings
    DEFAULT_CLEANUP_INTERVAL_HOURS = 24
    
    # SQL statements
    CREATE_PAPERS_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS papers (
        id TEXT PRIMARY KEY,
        metadata BLOB,
        embedding BLOB,
        timestamp TEXT,
        expiration TEXT
    );
    """
    
    CREATE_INDICES_SQL = [
        "CREATE INDEX IF NOT EXISTS idx_papers_expiration ON papers(expiration);",
        "CREATE INDEX IF NOT EXISTS idx_papers_timestamp ON papers(timestamp);"
    ]
    
    INSERT_PAPER_SQL = """
    INSERT OR REPLACE INTO papers (id, metadata, embedding, timestamp, expiration)
    VALUES (?, ?, ?, ?, ?);
    """
    
    SELECT_PAPER_SQL = """
    SELECT metadata, embedding FROM papers
    WHERE id = ? AND expiration > ?;
    """
    
    SELECT_ALL_PAPERS_SQL = """
    SELECT id, metadata, embedding FROM papers
    WHERE expiration > ?;
    """
    
    DELETE_EXPIRED_SQL = """
    DELETE FROM papers WHERE expiration <= ?;
    """
    
    def __init__(self, 
                 db_path: Optional[str] = None, 
                 ttl_days: int = DEFAULT_CACHE_TTL_DAYS,
                 embedding_dim: int = DEFAULT_EMBEDDING_DIMENSION,
                 cleanup_interval_hours: int = DEFAULT_CLEANUP_INTERVAL_HOURS,
                 auto_cleanup: bool = True):
        """
        Initialize the ArXiv vector store.
        
        Args:
            db_path: Path to the SQLite database file.
            ttl_days: Number of days before cached entries expire.
            embedding_dim: Dimension of embedding vectors.
            cleanup_interval_hours: Hours between automatic cleanup runs.
            auto_cleanup: Whether to automatically clean up expired entries.
        """
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self.ttl_days = ttl_days
        self.embedding_dim = embedding_dim
        self.cleanup_interval_hours = cleanup_interval_hours
        self.auto_cleanup = auto_cleanup
        self._lock = threading.RLock()  # For thread safety
        
        # Initialize the database
        self._ensure_db_path()
        self._init_db()
        
        # Start cleanup scheduler if enabled
        if self.auto_cleanup:
            self._start_cleanup_scheduler()
    
    def _ensure_db_path(self) -> None:
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        os.makedirs(db_dir, exist_ok=True)
        logger.debug(f"ArXiv vector database directory ensured at: {db_dir}")
    
    def _init_db(self) -> None:
        """Initialize the database with required schema."""
        with self._get_connection() as conn:
            # Create papers table
            conn.execute(self.CREATE_PAPERS_TABLE_SQL)
            
            # Create indices
            for index_sql in self.CREATE_INDICES_SQL:
                conn.execute(index_sql)
            
            conn.commit()
        logger.debug("ArXiv vector database initialized")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a SQLite database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dictionary access for rows
        return conn
    
    def _start_cleanup_scheduler(self) -> None:
        """Start a background thread for periodic cleanup."""
        cleanup_thread = threading.Thread(target=self._cleanup_scheduler, daemon=True)
        cleanup_thread.start()
        logger.debug(f"Cleanup scheduler started with interval of {self.cleanup_interval_hours} hours")
    
    def _cleanup_scheduler(self) -> None:
        """Background thread function for periodic cleanup."""
        while True:
            time.sleep(self.cleanup_interval_hours * 3600)  # Convert hours to seconds
            try:
                self.cleanup_expired()
            except Exception as e:
                logger.error(f"Error during scheduled cleanup: {e}")
    
    def _serialize_numpy(self, arr: np.ndarray) -> bytes:
        """Serialize a numpy array to bytes."""
        return np.ndarray.tobytes(arr)
    
    def _deserialize_numpy(self, data: bytes, dtype: np.dtype = np.float32) -> np.ndarray:
        """Deserialize bytes to a numpy array."""
        arr = np.frombuffer(data, dtype=dtype)
        # Reshape if it's a vector
        if arr.shape[0] == self.embedding_dim:
            arr = arr.reshape(1, -1)
        return arr
    
    def _serialize_metadata(self, metadata: Dict[str, Any]) -> bytes:
        """Serialize metadata to bytes."""
        return json.dumps(metadata).encode('utf-8')
    
    def _deserialize_metadata(self, data: bytes) -> Dict[str, Any]:
        """Deserialize bytes to metadata."""
        return json.loads(data.decode('utf-8'))
    
    def add_paper(self, 
                  paper_id: str, 
                  metadata: Dict[str, Any], 
                  embedding: Optional[np.ndarray] = None) -> bool:
        """
        Add a paper with its embedding to the store.
        
        Args:
            paper_id: Unique identifier for the paper (e.g., ArXiv ID)
            metadata: Paper metadata dictionary
            embedding: Paper embedding vector (optional)
            
        Returns:
            True if added successfully, False otherwise
        """
        # If no embedding is provided, use zeros
        if embedding is None:
            embedding = np.zeros((1, self.embedding_dim), dtype=np.float32)
        
        # Ensure embedding has the right shape
        if embedding.shape[-1] != self.embedding_dim:
            logger.warning(f"Embedding dimension mismatch: expected {self.embedding_dim}, got {embedding.shape[-1]}")
            return False
        
        # Flatten if needed
        if len(embedding.shape) > 1 and embedding.shape[0] == 1:
            embedding = embedding.flatten()
        
        # Prepare data
        current_time = datetime.now()
        expiration_time = current_time + timedelta(days=self.ttl_days)
        serialized_metadata = self._serialize_metadata(metadata)
        serialized_embedding = self._serialize_numpy(embedding)
        
        with self._lock:
            try:
                with self._get_connection() as conn:
                    conn.execute(
                        self.INSERT_PAPER_SQL,
                        (
                            paper_id,
                            serialized_metadata,
                            serialized_embedding,
                            current_time.isoformat(),
                            expiration_time.isoformat()
                        )
                    )
                    conn.commit()
                
                logger.debug(f"Added paper to vector store: {paper_id}")
                return True
            except Exception as e:
                logger.warning(f"Failed to add paper to vector store: {e}")
                return False
    
    def get_paper(self, paper_id: str) -> Optional[Tuple[Dict[str, Any], np.ndarray]]:
        """
        Get a paper and its embedding from the store.
        
        Args:
            paper_id: Unique identifier for the paper
            
        Returns:
            Tuple of (metadata, embedding) if found, None otherwise
        """
        current_time = datetime.now().isoformat()
        
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.execute(self.SELECT_PAPER_SQL, (paper_id, current_time))
                    row = cursor.fetchone()
                    
                    if row:
                        metadata = self._deserialize_metadata(row['metadata'])
                        embedding = self._deserialize_numpy(row['embedding'])
                        return metadata, embedding
                    
                    return None
            except Exception as e:
                logger.warning(f"Error retrieving paper from vector store: {e}")
                return None
    
    def get_all_papers(self) -> List[Tuple[str, Dict[str, Any], np.ndarray]]:
        """
        Get all papers and their embeddings from the store.
        
        Returns:
            List of (paper_id, metadata, embedding) tuples
        """
        current_time = datetime.now().isoformat()
        results = []
        
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.execute(self.SELECT_ALL_PAPERS_SQL, (current_time,))
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        paper_id = row['id']
                        metadata = self._deserialize_metadata(row['metadata'])
                        embedding = self._deserialize_numpy(row['embedding'])
                        results.append((paper_id, metadata, embedding))
                    
                    return results
            except Exception as e:
                logger.warning(f"Error retrieving all papers from vector store: {e}")
                return []
    
    def search_by_embedding(self, 
                            query_embedding: np.ndarray, 
                            top_k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search for similar papers using vector similarity.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of top results to return
            
        Returns:
            List of (metadata, similarity_score) tuples, sorted by descending score
        """
        # Ensure query embedding has the right shape
        if query_embedding.shape[-1] != self.embedding_dim:
            logger.warning(f"Query embedding dimension mismatch: expected {self.embedding_dim}, got {query_embedding.shape[-1]}")
            return []
        
        # Normalize query embedding for cosine similarity
        query_norm = np.linalg.norm(query_embedding)
        if query_norm > 0:
            query_embedding = query_embedding / query_norm
        
        # Get all papers
        all_papers = self.get_all_papers()
        if not all_papers:
            return []
        
        # Calculate similarities
        results = []
        for paper_id, metadata, embedding in all_papers:
            # Normalize paper embedding
            paper_norm = np.linalg.norm(embedding)
            if paper_norm > 0:
                embedding = embedding / paper_norm
            
            # Calculate cosine similarity
            similarity = float(np.dot(query_embedding, embedding.T)[0][0])
            
            results.append((metadata, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k results
        return results[:top_k]
    
    def search_hybrid(self, 
                     query_embedding: np.ndarray,
                     query_keywords: List[str],
                     top_k: int = 10,
                     vector_weight: float = 0.7) -> List[Tuple[Dict[str, Any], float]]:
        """
        Perform hybrid search using both vector similarity and keyword matching.
        
        Args:
            query_embedding: Query embedding vector
            query_keywords: List of query keywords
            top_k: Number of top results to return
            vector_weight: Weight for vector similarity vs keyword matching (0.0-1.0)
                          Higher value gives more importance to vector similarity
            
        Returns:
            List of (metadata, combined_score) tuples, sorted by descending score
        """
        # Get all papers
        all_papers = self.get_all_papers()
        if not all_papers:
            return []
        
        # Ensure query embedding has the right shape
        if query_embedding.shape[-1] != self.embedding_dim:
            logger.warning(f"Query embedding dimension mismatch: expected {self.embedding_dim}, got {query_embedding.shape[-1]}")
            # Fall back to keyword search only
            vector_weight = 0.0
        
        # Normalize query embedding for cosine similarity
        if vector_weight > 0:
            query_norm = np.linalg.norm(query_embedding)
            if query_norm > 0:
                query_embedding = query_embedding / query_norm
        
        # Calculate combined scores
        results = []
        for paper_id, metadata, embedding in all_papers:
            # Calculate vector similarity if weight > 0
            vector_score = 0.0
            if vector_weight > 0:
                # Normalize paper embedding
                paper_norm = np.linalg.norm(embedding)
                if paper_norm > 0:
                    embedding = embedding / paper_norm
                
                # Calculate cosine similarity
                vector_score = float(np.dot(query_embedding, embedding.T)[0][0])
            
            # Calculate keyword score if weight < 1
            keyword_score = 0.0
            if vector_weight < 1.0:
                paper_text = f"{metadata.get('title', '')} {metadata.get('summary', '')}"
                paper_text = paper_text.lower()
                
                # Count matching keywords
                matches = sum(1 for keyword in query_keywords if keyword.lower() in paper_text)
                keyword_score = matches / max(1, len(query_keywords))
            
            # Calculate combined score
            combined_score = (vector_score * vector_weight) + (keyword_score * (1 - vector_weight))
            
            results.append((metadata, combined_score))
        
        # Sort by combined score (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k results
        return results[:top_k]
    
    def cleanup_expired(self) -> int:
        """
        Clean up expired papers.
        
        Returns:
            Number of papers removed
        """
        current_time = datetime.now().isoformat()
        
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.execute(self.DELETE_EXPIRED_SQL, (current_time,))
                    deleted_count = cursor.rowcount
                    conn.commit()
                
                logger.info(f"Cleaned up {deleted_count} expired papers from vector store")
                return deleted_count
            except Exception as e:
                logger.error(f"Error cleaning up expired papers from vector store: {e}")
                return 0
