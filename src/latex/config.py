"""
Configuration settings for the LaTeX document formatter.

This module provides default configurations and utilities for customizing the
LaTeX document generation process.
"""

import os
from typing import Dict, Any, Optional, List, Union

# Default configuration values
DEFAULT_CONFIG = {
    # Document settings
    "document_class": "article",
    "document_options": ["12pt", "a4paper"],
    "title": "Critique Council Report",
    "use_hyperref": True,
    
    # Template settings
    "template_dir": os.path.join(os.path.dirname(__file__), "templates"),
    # Use specialized templates based on mode
    "main_template": "academic_paper.tex",  # Default, but will be overridden in formatter
    "scientific_template": "scientific_paper.tex",
    "philosophical_template": "philosophical_paper.tex",
    "preamble_template": "preamble.tex",
    "bibliography_template": "bibliography.bib",
    
    # Content processing settings
    "replace_philosophical_jargon": True,
    "scientific_objectivity_level": "high",  # Options: low, medium, high
    "scientific_mode": False,  # Whether to use scientific methodology mode
    "include_bibliography": True,
    
    # Math settings
    "detect_math": True,
    "math_environments": ["equation", "align", "gather"],
    "inline_math_delimiters": ["$", "$"],
    "display_math_delimiters": ["$$", "$$"],
    
    # Output settings
    "output_dir": "latex_output",
    "output_filename": "critique_report",
    "compile_pdf": False,  # Set to True to compile PDF if LaTeX is installed
    "keep_tex": True,      # Keep .tex files after PDF compilation
    
    # LaTeX compilation settings (if compile_pdf is True)
    "latex_engine": "pdflatex",
    "latex_args": ["-interaction=nonstopmode", "-halt-on-error"],
    "bibtex_run": True,
    "latex_runs": 2,  # Number of LaTeX compilation passes
    
    # MiKTeX configuration (Windows-specific)
    "miktex": {
        "custom_path": "",  # Custom path to MiKTeX installation
        "additional_search_paths": []  # Additional paths to search for LaTeX executables
    }
}


class LatexConfig:
    """
    Configuration class for LaTeX document generation.
    
    This class manages configuration settings for the LaTeX formatter,
    allowing for customization while providing sensible defaults.
    """
    
    def __init__(self, user_config: Optional[Dict[str, Any]] = None):
        """
        Initialize configuration with default values, optionally overridden
        by user-provided configuration.
        
        Args:
            user_config: Optional dictionary of user configuration settings
                        that will override the defaults.
        """
        self.config = DEFAULT_CONFIG.copy()
        
        if user_config:
            self._update_config(user_config)
            
    def _update_config(self, user_config: Dict[str, Any]) -> None:
        """
        Update configuration with user-provided values.
        
        Args:
            user_config: Dictionary of user configuration settings.
        """
        for key, value in user_config.items():
            if key in self.config:
                self.config[key] = value
            else:
                raise ValueError(f"Unknown configuration key: {key}")
                
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Configuration key to retrieve.
            default: Default value to return if key is not found.
            
        Returns:
            The configuration value, or default if not found.
        """
        return self.config.get(key, default)
        
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key to set.
            value: Value to set for the key.
            
        Raises:
            ValueError: If key is not a valid configuration option.
        """
        if key in self.config:
            self.config[key] = value
        else:
            raise ValueError(f"Unknown configuration key: {key}")
            
    def get_template_path(self, template_name: str) -> str:
        """
        Get the full path to a template file.
        
        Args:
            template_name: Name of the template file.
            
        Returns:
            Full path to the template file.
        """
        return os.path.join(self.config["template_dir"], template_name)
        
    @property
    def output_tex_path(self) -> str:
        """
        Get the full path to the output .tex file.
        
        Returns:
            Full path to the output .tex file.
        """
        os.makedirs(self.config["output_dir"], exist_ok=True)
        return os.path.join(
            self.config["output_dir"],
            f"{self.config['output_filename']}.tex"
        )
        
    @property
    def output_pdf_path(self) -> str:
        """
        Get the full path to the output .pdf file.
        
        Returns:
            Full path to the output .pdf file.
        """
        return os.path.join(
            self.config["output_dir"],
            f"{self.config['output_filename']}.pdf"
        )
