# ArXiv Vector Search

This document describes the vector-based semantic search capabilities for ArXiv papers that have been implemented in the system.

## Overview

The vector search enhancement provides semantic search capabilities for ArXiv papers, allowing for more accurate and relevant search results based on the meaning of content rather than just keyword matching.

### Key Components

1. **ArxivVectorStore** (`src/arxiv/vector_store.py`)
   - Pure Python implementation of vector storage and search
   - Uses hash-based embeddings and cosine similarity
   - Requires only NumPy as a dependency

2. **ArxivAgnoStore** (`src/arxiv/agno_integration.py`)
   - Agno-based implementation for high-quality vector search
   - Uses OpenAI embeddings for state-of-the-art semantic matching
   - Requires Agno package and its dependencies

3. **ArxivSmartStore** (`src/arxiv/smart_vector_store.py`)
   - Smart wrapper that automatically chooses the best implementation
   - Tries to use Agno first, falls back to pure Python implementation
   - Provides consistent API regardless of which backend is active

4. **ArxivVectorReferenceService** (`src/arxiv/arxiv_vector_reference_service.py`)
   - Enhanced reference service that integrates with the vector store
   - Extends the standard reference service with semantic search
   - Combines vector and keyword search for optimal results

## Configuration

The vector search system can be configured through the standard configuration dictionary:

```python
config = {
    'arxiv': {
        # Standard ArXiv configuration
        'cache_dir': 'storage/arxiv_cache',
        'use_db_cache': True,
        'cache_ttl_days': 30,
        
        # Vector search specific configuration
        'vector_cache_dir': 'storage/arxiv_vector_cache',  # Optional separate directory
        'vector_table_name': 'arxiv_papers',               # Name for the vector table
        'force_vector_fallback': False,                    # Force use of pure Python impl
        'openai_api_key': 'your-api-key-here'              # For Agno with OpenAI embeddings
    }
}
```

## Usage

### Basic Usage

Replace the standard ArXiv reference service with the vector-enhanced version:

```python
from src.arxiv.arxiv_vector_reference_service import ArxivVectorReferenceService

# Initialize with configuration
reference_service = ArxivVectorReferenceService(config=config)

# Use just like the standard reference service
papers = reference_service.get_references_for_content(
    content="Quantum computing with topological qubits...",
    max_results=5
)
```

### Enhanced Agent-Based References

The vector service provides improved reference suggestions based on agent perspective:

```python
# Get references tailored to a specific perspective
papers = reference_service.suggest_references_for_agent(
    agent_name="kantian_philosopher",
    content="The nature of consciousness...",
    agent_perspective="Kantian transcendental idealism",
    max_results=3
)
```

### Direct Vector Store Access

For applications that need direct access to the vector store:

```python
from src.arxiv.smart_vector_store import ArxivSmartStore

# Initialize smart vector store
vector_store = ArxivSmartStore(
    cache_dir="storage/arxiv_cache",
    openai_api_key=openai_api_key,
    force_fallback=False  # Set to True to force using pure Python impl
)

# Add papers
vector_store.add_papers(papers)

# Search by content
results = vector_store.search(
    query="Quantum computing superposition",
    max_results=10,
    min_score=0.2  # Minimum similarity threshold
)

# Get paper by ID
paper = vector_store.get_paper("1905.10481v1")
```

## Fallback Mechanism

The system is designed to gracefully degrade if dependencies are unavailable:

1. **First Attempt**: Try to use Agno with OpenAI embeddings (best quality)
2. **If OpenAI API is unavailable**: Fall back to Agno with simpler embeddings
3. **If Agno is unavailable**: Fall back to pure Python implementation

This ensures that the system always provides vector search capabilities, even if the optimal components aren't available.

## Performance Considerations

- **Memory Usage**: The pure Python implementation keeps all embeddings in memory, which may be a concern for very large collections (>100K papers).
- **Speed**: The pure Python implementation is significantly faster for search operations but less accurate than the Agno/OpenAI implementation.
- **Accuracy**: The Agno implementation with OpenAI embeddings provides the highest accuracy but requires API access and has costs associated with it.
- **Persistence**: Both implementations persist embeddings to disk to avoid recomputing them.

## Demo and Testing

Two test scripts are provided to demonstrate the functionality:

1. `test_vector_store.py`: Demonstrates the pure Python vector store
2. `test_smart_vector_store.py`: Demonstrates the smart store with automatic backend selection
3. `test_vector_reference_service.py`: Demonstrates the enhanced reference service

Run these scripts to see the vector search capabilities in action:

```bash
# Test with default settings (tries Agno first)
python test_vector_reference_service.py

# Force use of pure Python implementation
python test_vector_reference_service.py --force-fallback

# Provide OpenAI API key for Agno with OpenAI embeddings
python test_vector_reference_service.py --openai-api-key=your-api-key
