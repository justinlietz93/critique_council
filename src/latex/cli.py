"""
CLI integration for LaTeX document generation.

This module provides CLI integration for the LaTeX document formatter,
allowing it to be used from the command line via run_critique.py.
"""

import argparse
import logging
import os
from typing import Dict, Any, Optional, List, Union, Tuple

from .formatter import format_as_latex

logger = logging.getLogger(__name__)


def add_latex_arguments(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """
    Add LaTeX-related command line arguments to an existing ArgumentParser.
    
    Args:
        parser: The ArgumentParser to add arguments to.
        
    Returns:
        The modified ArgumentParser.
    """
    # Create a LaTeX argument group
    latex_group = parser.add_argument_group('LaTeX Options')
    
    # Add LaTeX-specific arguments
    latex_group.add_argument(
        '--latex', 
        action='store_true',
        help='Generate LaTeX document from critique report and peer review'
    )
    
    latex_group.add_argument(
        '--latex-compile', 
        action='store_true',
        help='Compile LaTeX document to PDF (requires LaTeX installation)'
    )
    
    latex_group.add_argument(
        '--latex-output-dir', 
        type=str,
        default='latex_output',
        help='Directory for LaTeX output files'
    )
    
    latex_group.add_argument(
        '--latex-scientific-level', 
        type=str,
        choices=['low', 'medium', 'high'],
        default='high',
        help='Level of scientific objectivity (removes philosophical jargon)'
    )
    
    return parser


def handle_latex_output(
    args: argparse.Namespace,
    original_content: str,
    critique_report: str,
    peer_review: Optional[str] = None,
    scientific_mode: bool = False
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Handle LaTeX document generation based on command line arguments.
    
    Args:
        args: Command line arguments.
        original_content: The original content that was critiqued.
        critique_report: The generated critique report.
        peer_review: Optional peer review document.
        scientific_mode: Whether scientific methodology was used (default: False).
        
    Returns:
        A tuple of (success, tex_file_path, pdf_file_path), where success is a boolean
        indicating whether LaTeX generation was successful, and tex_file_path and
        pdf_file_path are the paths to the generated files (or None if not generated).
    """
    if not args.latex:
        # LaTeX generation not requested
        return False, None, None
    
    logger.info("Generating LaTeX document from critique report")
    
    # Set up the LaTeX configuration
    config = {
        'output_dir': args.latex_output_dir,
        'compile_pdf': args.latex_compile,
        'scientific_objectivity_level': args.latex_scientific_level,
        'include_bibliography': True,
        'output_filename': 'critique_report',
        'scientific_mode': scientific_mode  # Add the scientific_mode flag
    }
    
    try:
        # Make sure the output directory exists
        os.makedirs(args.latex_output_dir, exist_ok=True)
        
        # Generate the LaTeX document
        tex_path, pdf_path = format_as_latex(
            original_content,
            critique_report,
            peer_review,
            config
        )
        
        # Log the result
        if tex_path:
            logger.info(f"LaTeX document generated: {tex_path}")
        if pdf_path:
            logger.info(f"PDF document generated: {pdf_path}")
            
        return True, tex_path, pdf_path
    except Exception as e:
        logger.error(f"Failed to generate LaTeX document: {e}", exc_info=True)
        return False, None, None
