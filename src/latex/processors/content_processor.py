"""
Base interface for content processors.

This module defines the ContentProcessor abstract base class,
which all content processors must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class ContentProcessor(ABC):
    """
    Abstract base class for content processors.
    
    Content processors transform input content into LaTeX-compatible
    formats with specific processing rules.
    """
    
    @abstractmethod
    def process(self, content: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process the input content according to processor-specific rules.
        
        Args:
            content: The input content to process.
            context: Optional dictionary providing additional context or settings
                    for the processing operation.
            
        Returns:
            The processed content.
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the name of the processor.
        
        Returns:
            The processor name.
        """
        pass
    
    @property
    def description(self) -> str:
        """
        Get a description of what the processor does.
        
        Returns:
            The processor description.
        """
        return "Base content processor"
    
    def supports_content_type(self, content_type: str) -> bool:
        """
        Check if this processor supports the given content type.
        
        Args:
            content_type: The content type to check.
            
        Returns:
            True if this processor supports the content type, False otherwise.
        """
        return True  # Default implementation supports all content types
