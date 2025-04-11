"""
LaTeX document formatter for the Critique Council.

This package provides a modular and extensible way to format critique reports and peer reviews
into professional LaTeX documents, with support for mathematical expressions using KaTeX.
"""

from .formatter import format_as_latex, LatexFormatter

__all__ = ['format_as_latex', 'LatexFormatter']
