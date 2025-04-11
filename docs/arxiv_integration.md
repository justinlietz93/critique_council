# ArXiv Reference Service Integration

This document describes the integration of ArXiv reference capabilities into the Critique Council, allowing for scientific references to be automatically retrieved and cited in LaTeX documents.

## Modular Design

The ArXiv Reference Service has been implemented following the Apex Modular Organization Standard (AMOS), with a clean separation of concerns across multiple modules. Each component has been kept under 500 lines of code for maintainability.

### Architecture Overview

```
src/
└── arxiv/
    ├── __init__.py                # Package initialization
    ├── api_client.py              # ArXiv API communication with rate limiting
    ├── arxiv_reference_service.py # Main service facade
    ├── bibtex_converter.py        # Conversion of metadata to BibTeX
    ├── cache_manager.py           # Caching of API responses
    └── utils.py                   # Text processing utilities
```

A backwards-compatible facade is available at `src/arxiv_reference_service.py` to ensure existing code continues to work.

## Key Components

### API Client

Handles direct communication with the ArXiv API, including:
- Rate limiting to avoid overloading the API
- Request formation with appropriate parameters
- XML response parsing

### Cache Manager

Provides efficient caching of API responses:
- Stores responses as JSON files for reuse
- Implements expiration to refresh stale data
- Hashes query parameters for consistent cache keys

### Text Processor

Extracts relevant search terms from content:
- Keyword extraction based on frequency
- Domain-specific term identification
- Query formation for ArXiv search

### BibTeX Converter

Converts ArXiv metadata to BibTeX format:
- Generates consistent citation keys
- Formats author names appropriately
- Handles journal references and DOIs

### Main Service

Acts as a facade to tie all components together:
- Centralizes reference management across agents
- Provides an agent-specific reference registry
- Supports content-based reference suggestions

## Usage Examples

### Basic Search

```python
from src.arxiv_reference_service import ArxivReferenceService

# Initialize the service
arxiv_service = ArxivReferenceService()

# Search for papers
papers = arxiv_service.search_arxiv('quantum mechanics', max_results=5)

# Print the titles
for paper in papers:
    print(paper['title'])
```

### Agent-Specific References

```python
# Suggest references for a specific agent and their perspective
agent_name = "Aristotle"
content = "Analysis of causality in physical systems..."
agent_perspective = "Aristotelian metaphysics"

papers = arxiv_service.suggest_references_for_agent(
    agent_name, 
    content, 
    agent_perspective
)

# Get all references registered for this agent
agent_refs = arxiv_service.get_agent_references(agent_name)
```

### BibTeX Generation

```python
# Generate BibTeX entries for all referenced papers
bibtex = arxiv_service.generate_bibtex_for_all_references()

# Update the LaTeX bibliography file
arxiv_service.update_latex_bibliography('latex_output/bibliography.bib')
```

## Testing

The ArXiv Reference Service includes comprehensive offline tests that verify the functionality without making actual API calls. To run the tests:

```bash
python tests/test_arxiv_integration.py
```

An optional online test is included but skipped by default to avoid unnecessary API calls.

## Configuration

The service uses sensible defaults but can be configured:
- Cache directory: `storage/arxiv_cache`
- Cache expiry: 30 days
- API rate limiting: 3 seconds between requests

## Future Enhancements

1. Integration with NLP libraries for better keyword extraction
2. Support for additional citation formats beyond BibTeX
3. Integration with other scientific databases (e.g., PubMed, IEEE Xplore)
