"""
Content assessor module for objective point extraction.

This module provides a ContentAssessor class that analyzes input content
and extracts a list of objective points or claims made in the content
without any philosophical bias or critique.
"""

import logging
import json
from typing import Dict, List, Any, Optional

from .providers import call_with_retry

logger = logging.getLogger(__name__)

class ContentAssessor:
    """
    Content assessor that extracts objective points from content.
    
    This class analyzes content and identifies key points or claims made
    without applying any philosophical framework or bias. It serves as an
    unbiased first step in the critique process to identify points that
    can be distributed among philosophical critics.
    """
    
    def __init__(self):
        """Initialize the content assessor."""
        self.style = "ContentAssessor"
    
    def set_logger(self, logger: logging.Logger):
        """Set the logger for this assessor."""
        self.logger = logger
    
    def extract_points(self, content: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract a list of objective points from the content.
        
        Args:
            content: The content to analyze.
            config: Configuration settings.
            
        Returns:
            A list of extracted points, each as a dictionary with at least
            'id' and 'point' keys.
        """
        self.logger.info("Extracting objective points from content")
        
        # Create a prompt to identify key points without bias
        prompt = self._create_extraction_prompt(content)
        
        try:
            # Call the provider to extract points
            result, model_used = call_with_retry(
                prompt_template=prompt,
                context={},
                config=config,
                is_structured=True
            )
            
            self.logger.info(f"Successfully extracted points using {model_used}")
            
            # Ensure the result is a list of points
            points = self._validate_and_format_points(result)
            
            self.logger.info(f"Extracted {len(points)} points from content")
            return points
            
        except Exception as e:
            self.logger.error(f"Error extracting points: {e}", exc_info=True)
            # Return an empty list if extraction fails
            return []
    
    def _create_extraction_prompt(self, content: str) -> str:
        """
        Create a prompt for extracting objective points.
        
        Args:
            content: The content to analyze.
            
        Returns:
            A prompt string.
        """
        return f"""
        You are an objective content assessor. Your task is to extract a comprehensive list of distinct factual claims, 
        statements, or points made in the provided content. Do NOT provide any analysis, critique, or evaluation of these points.
        Simply extract and list them objectively.

        Guidelines:
        1. Identify ALL distinct points, claims, or statements in the content
        2. Focus on extracting the substance of each claim without adding interpretation
        3. Extract points at a medium level of granularity (not too broad, not too specific)
        4. Include ALL significant claims, not just the main ones
        5. Do NOT provide any evaluation or judgment of the points
        6. Do NOT skip any significant claims
        7. Each point should be distinct and non-overlapping with others
        8. Number the points starting from 1
        9. Points must accurately reflect what's in the content, not what you think should be there

        CONTENT TO ANALYZE:
        {content}

        Your response must be a JSON object with the following structure:
        {{
            "points": [
                {{
                    "id": "point-1",
                    "point": "The first objective point extracted from the content"
                }},
                {{
                    "id": "point-2",
                    "point": "The second objective point extracted from the content"
                }},
                ...
            ]
        }}

        Extract at least 10 points (or as many as the content contains if fewer than 10).
        """
    
    def _validate_and_format_points(self, result: Any) -> List[Dict[str, Any]]:
        """
        Validate and format the extracted points.
        
        Args:
            result: The result from the provider call.
            
        Returns:
            A list of formatted points.
        """
        points = []
        
        try:
            # Handle different possible formats from the provider
            if isinstance(result, dict) and "points" in result:
                raw_points = result["points"]
            elif isinstance(result, list):
                raw_points = result
            else:
                self.logger.warning(f"Unexpected result format: {type(result)}")
                raw_points = []
            
            # Process each point to ensure it has the required fields
            for i, point in enumerate(raw_points):
                if isinstance(point, dict):
                    # Ensure each point has an id
                    if "id" not in point:
                        point["id"] = f"point-{i+1}"
                    points.append(point)
                else:
                    # Convert simple strings to dictionaries
                    points.append({
                        "id": f"point-{i+1}",
                        "point": str(point)
                    })
            
        except Exception as e:
            self.logger.error(f"Error validating points: {e}", exc_info=True)
        
        return points
