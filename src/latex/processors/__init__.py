"""
Content processors for the LaTeX formatter.

This package provides a set of processors that transform content
into LaTeX-compatible formats, with a focus on scientific objectivity.
"""

from .content_processor import ContentProcessor
from .jargon_processor import JargonProcessor
from .citation_processor import CitationProcessor

__all__ = ['ContentProcessor', 'JargonProcessor', 'CitationProcessor']
