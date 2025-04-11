"""
ArXiv Reference Service for the Critique Council.

This module provides a facade to the modular ArXiv reference service implementation.
It exposes functionality to search, fetch, and cache arXiv paper references,
which can then be used by different reasoning agents to support their critiques.
"""

import logging
from typing import Dict, List, Any, Optional, Set, Tuple

# Import the modular implementation
from .arxiv.arxiv_reference_service import ArxivReferenceService

# Set up logging
logger = logging.getLogger(__name__)

# Re-export the main class for backward compatibility
__all__ = ['ArxivReferenceService']
