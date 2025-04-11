# Agno Integration for ArXiv References

This document describes the integration of [Agno](https://github.com/agno-agi/agno) with the ArXiv reference service to provide efficient vector-based semantic search for academic papers.

## Overview

The ArXiv integration with Agno provides significant improvements over the previous SQLite-based implementation:

- **Semantic search**: Papers are matched based on meaning, not just keywords
- **Vector embeddings**: Each paper is represented as a high-dimensional vector for similarity search
- **Hybrid search**: Combines vector similarity with keyword matching for better results
- **Memory efficiency**: Optimized for performance with larger document collections
- **Speed improvements**: Significantly faster retrieval for cached queries

## Setup and Installation

### Prerequisites

- Python 3.9+
- Agno library (`pip install agno`)
- LanceDB for vector storage (`pip install lancedb`)
- OpenAI API key for embeddings (or another supported embedding model)

### Configuration

Add the following to your `config.yaml`:

```yaml
arxiv:
  # Existing configuration
  cache_dir: "storage/arxiv_cache"
  use_cache: true
  cache_ttl_days: 30
  max_references_per_point: 3
  default_sort_by: "relevance"
  default_sort_order: "descending"
  update_bibliography: true
  
  # Agno specific configuration
  use_agno: true  # Set to true to use Agno instead of SQLite
  agno_table: "arxiv_papers"  # Table name for LanceDB
  embedder: "openai"  # Embedding provider (openai, cohere, or sentence-transformers)
```

### Environment Variables

Set the API key for your chosen embedding provider:

```bash
# For OpenAI embeddings (recommended)
export OPENAI_API_KEY=your_api_key_here

# For Cohere embeddings (alternative)
export COHERE_API_KEY=your_api_key_here
```

## Usage

You can use the Agno-powered reference service in the same way as the original service:

```python
from src.arxiv.arxiv_agno_service import ArxivAgnoReferenceService

# Initialize service
config = {...}  # Load config from file
service = ArxivAgnoReferenceService(config=config)

# Get references for a content point
references = service.get_references_for_point(
    "Quantum computing uses qubits instead of classical bits"
)

# Attach references to multiple points
points = ["Point 1", "Point 2", "Point 3"]
results = service.attach_references_to_points(points)

# Update bibliography
all_references = []
for _, refs in results:
    all_references.extend(refs)
service.update_bibliography_file(all_references, "path/to/output.bib")
```

## Demo Scripts

Two demonstration scripts are provided:

1. `test_agno_integration.py`: Tests the core Agno integration with the vector database
2. `test_agno_reference_service.py`: Tests the full reference service with comparison to SQLite

### Running the Demo

```bash
# Simple integration test
python test_agno_integration.py

# Reference service test
python test_agno_reference_service.py

# Performance comparison with SQLite implementation
python test_agno_reference_service.py --compare
```

## Performance Considerations

### Memory Usage

The vector database uses more memory initially when loading embeddings for search but is significantly more memory-efficient as the collection grows. For large collections of papers, this can be a crucial advantage.

### Speed

- **First queries**: Initial queries may be slower as embeddings are computed
- **Cached queries**: Subsequent queries using the same embeddings will be 5-10x faster than the SQLite version
- **Scale efficiency**: The performance advantage increases with the size of the paper collection

### API Costs

Using OpenAI embeddings incurs API costs. To minimize costs:

1. Use the cache effectively (longer TTL for stable content)
2. Pre-populate with common queries using `preload_arxiv_cache.py`
3. Consider alternative embedding providers like `sentence-transformers` which run locally

## Comparison with SQLite Implementation

| Feature | Agno Integration | SQLite Implementation |
|---------|-----------------|----------------------|
| Search quality | High (semantic matching) | Medium (keyword matching) |
| Initial query speed | Medium (embedding computation) | Medium (API calls) |
| Cached query speed | Very Fast | Fast |
| Memory efficiency | High | Medium |
| Scalability | Excellent | Limited |
| Hybrid search | Built-in | Manual implementation |
| Dependencies | Agno, LanceDB, OpenAI | None additional |

## Troubleshooting

### Missing Dependencies

If you encounter ImportError, install the required dependencies:

```bash
pip install agno lancedb
```

### Embedding API Errors

If you see errors related to embedding generation:

1. Check your API key is set correctly in the environment
2. Verify you have API credits/quota available
3. Try using a local embedding model via `sentence-transformers`

### Database Errors

If the vector database encounters issues:

1. Clear the cache using `service.clear_cache()`
2. Check permissions on the cache directory
3. Ensure LanceDB is installed correctly

## Advanced Configuration

### Custom Embedding Models

You can configure alternative embedding models by providing a custom embedder:

```python
from agno.embedder.sentence_transformers import SentenceTransformersEmbedder

# Use a local embedding model
embedder = SentenceTransformersEmbedder(id="all-MiniLM-L6-v2")

# Initialize store with custom embedder
store = ArxivAgnoStore(
    cache_dir="storage/arxiv_cache",
    table_name="arxiv_papers",
    embedder=embedder
)
```

### Search Parameters

You can fine-tune the search behavior:

```python
# Adjust the vector/keyword balance (higher value gives more weight to vector similarity)
results = store.search(
    query="quantum computing",
    max_results=5,
    vector_weight=0.8  # 80% vector similarity, 20% keyword matching
)
```

## Future Improvements

- Support for more embedding providers
- Integration with full Agno agent capabilities
- Customizable relevance scoring algorithms
- Multi-modal paper search (include figures, tables, etc.)
