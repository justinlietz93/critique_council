# ArXiv Reference Integration

This document explains the ArXiv reference integration feature, which automatically finds and attaches relevant academic papers from ArXiv to content points during analysis.

## Overview

The ArXiv integration enhances the content assessment process by automatically searching for and attaching relevant academic papers from [arXiv.org](https://arxiv.org/) to each extracted point. This provides scientific context and supporting references for claims and concepts identified in the content.

## How It Works

1. During the content assessment phase, the system extracts key points from the content
2. For each point, the system:
   - Analyzes the text to identify relevant search terms
   - Queries the ArXiv API for related academic papers
   - Retrieves and attaches the most relevant papers as references
3. References are attached directly to point objects and made available to agents
4. A comprehensive bibliography is generated in BibTeX format for LaTeX output

## Configuration

ArXiv integration can be configured in the `config.yaml` file:

```yaml
# ArXiv Configuration
arxiv:
  # Whether to enable ArXiv reference lookups during content assessment
  enabled: true
  
  # Maximum number of references to attach per content point
  max_references_per_point: 3
  
  # Cache settings
  cache_dir: "storage/arxiv_cache"
  use_cache: true
  use_db_cache: true          # Whether to use database (SQLite) cache instead of file-based cache
  cache_ttl_days: 30          # Number of days before cached entries expire
  cache_cleanup_interval_hours: 24  # How often to run cleanup jobs (in hours)
  
  # Search settings
  search_sort_by: "relevance"    # Options: relevance, lastUpdatedDate, submittedDate
  search_sort_order: "descending" # Options: ascending, descending
  
  # Bibliography settings
  update_bibliography: true  # Whether to update LaTeX bibliography with ArXiv references
```

## Reference Format

Each reference attached to a point includes:

- `id`: ArXiv paper ID
- `title`: Paper title
- `authors`: List of author names
- `summary`: Brief summary of the paper (truncated)
- `url`: Link to the paper on ArXiv
- `published`: Publication date

## LaTeX Bibliography Integration

When LaTeX output is enabled, the system automatically generates a BibTeX file containing all referenced papers. This file is placed in the configured output directory and named according to the output filename pattern:

```
{output_dir}/{output_filename}_bibliography.bib
```

The BibTeX entries use standard academic citation formatting and can be referenced in LaTeX documents.

## Example Usage

To see ArXiv references in action, run the demonstration script:

```bash
python test_arxiv_integration_demo.py
```

This will process sample content, attach ArXiv references to each point, and display the results.

## Cache Management

The system includes a database-backed caching system to reduce API calls and improve performance. By default, ArXiv query results are cached in a SQLite database and automatically expire after the configured TTL period.

You can manage the cache using the included utility script:

```bash
# Show cache statistics
python manage_arxiv_cache.py stats

# Show cache configuration
python manage_arxiv_cache.py info

# Clear the entire cache
python manage_arxiv_cache.py clear

# Clear entries older than 60 days
python manage_arxiv_cache.py clear --days=60

# Manually run cleanup to remove expired entries
python manage_arxiv_cache.py cleanup
```

### Cache Implementation

The system supports two caching implementations:

1. **File-based Cache**: The original implementation that stores each query result in a separate JSON file.
2. **Database Cache**: The new SQLite-based implementation that offers better performance, automatic TTL enforcement, and more detailed statistics.

You can configure which implementation to use with the `use_db_cache` setting in the configuration file.

## Benefits

- Provides scientific context for extracted points
- Enhances critique quality with academic references
- Enables citation-backed LaTeX output
- Improves the credibility of analyses with peer-reviewed sources

## Error Handling

The ArXiv integration is designed to be non-blocking. If reference lookup fails for any reason:

- The error is logged but does not halt the assessment process
- Points are still processed without references
- The system continues with the next steps of the analysis

This ensures robustness while providing enhanced functionality when available.
