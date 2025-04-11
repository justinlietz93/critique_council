"""
Main formatter for generating LaTeX documents from critique reports.

This module provides the main formatter class for generating LaTeX documents
from critique reports and peer reviews.
"""

import os
import re
import logging
import datetime
from typing import Dict, Any, Optional, List, Union, Tuple

from .config import LatexConfig
from .converters import MarkdownToLatexConverter, MathFormatter
from .processors import ContentProcessor, JargonProcessor, CitationProcessor
from .utils import FileManager, LatexCompiler

logger = logging.getLogger(__name__)


class LatexFormatter:
    """
    Main formatter for generating LaTeX documents from critique reports.
    
    This class uses the converters, processors, and utilities to generate
    comprehensive LaTeX documents from critique reports and peer reviews.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LaTeX formatter.
        
        Args:
            config: Optional configuration dictionary containing formatter options.
        """
        # Initialize configuration
        self.config = LatexConfig(config)
        
        # Select the appropriate template based on mode
        if self.config.get('scientific_mode', False):
            self.config.set('main_template', self.config.get('scientific_template'))
            print(f"Using scientific methodology mode for LaTeX generation")
        else:
            self.config.set('main_template', self.config.get('philosophical_template', 'academic_paper.tex'))
        
        # Initialize file manager
        self.file_manager = FileManager({
            'template_dir': self.config.get('template_dir'),
            'output_dir': self.config.get('output_dir')
        })
        
        # Initialize converters
        self.markdown_converter = MarkdownToLatexConverter({
            'katex_compatibility': self.config.get('katex_compatibility', True)
        })
        
        self.math_formatter = MathFormatter({
            'katex_compatibility': self.config.get('katex_compatibility', True)
        })
        
        # Initialize processors
        self.jargon_processor = JargonProcessor(
            objectivity_level=self.config.get('scientific_objectivity_level', 'high')
        )
        
        self.citation_processor = CitationProcessor(
            output_dir=self.config.get('output_dir')
        )
        
        # Initialize LaTeX compiler if needed
        if self.config.get('compile_pdf', False):
            self.latex_compiler = LatexCompiler({
                'latex_engine': self.config.get('latex_engine'),
                'bibtex_run': self.config.get('bibtex_run'),
                'latex_runs': self.config.get('latex_runs'),
                'keep_intermediates': self.config.get('keep_intermediates')
            })
        else:
            self.latex_compiler = None
    
    def format_document(
        self, 
        original_content: str, 
        critique_report: str, 
        peer_review: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Format critique report and optional peer review into a LaTeX document.
        
        Args:
            original_content: The original content that was critiqued.
            critique_report: The generated critique report.
            peer_review: Optional peer review document.
            
        Returns:
            A tuple of (tex_file_path, pdf_file_path), where pdf_file_path
            is None if compilation is not enabled or fails.
        """
        logger.info("Formatting critique report into LaTeX document")
        
        # Prepare content context
        context = self._prepare_context(original_content, critique_report, peer_review)
        
        # Process each content field through processors
        if 'analysis_content' in context:
            context['analysis_content'] = self._process_content(context['analysis_content'])
        
        if 'review_content' in context:
            context['review_content'] = self._process_content(context['review_content'])
        
        # Read main template
        template_content = self.file_manager.read_template(self.config.get('main_template'))
        
        # Render template with context
        rendered_content = self.file_manager.render_template(template_content, context)
        
        # Generate timestamp for filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Write the output file
        output_filename = f"{self.config.get('output_filename')}_{timestamp}.tex"
        tex_file_path = self.file_manager.write_output_file(output_filename, rendered_content)
        
        # Copy required template files to output directory
        required_templates = ['preamble.tex']
        if self.config.get('include_bibliography', True):
            required_templates.append('bibliography.bib')
        
        self.file_manager.copy_templates_to_output(required_templates)
        
        # Compile to PDF if enabled
        pdf_file_path = None
        if self.latex_compiler is not None and self.config.get('compile_pdf', False):
            logger.info("Compiling LaTeX document to PDF")
            success, result = self.latex_compiler.compile_document(tex_file_path)
            if success:
                pdf_file_path = result
                logger.info(f"PDF compilation successful: {pdf_file_path}")
            else:
                logger.error(f"PDF compilation failed: {result}")
        
        return tex_file_path, pdf_file_path
    
    def _prepare_context(
        self,
        original_content: str,
        critique_report: str,
        peer_review: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Prepare the context for rendering the LaTeX template.
        
        Args:
            original_content: The original content that was critiqued.
            critique_report: The generated critique report.
            peer_review: Optional peer review document.
            
        Returns:
            Dictionary with context variables for template rendering.
        """
        # Check if we're in scientific mode
        scientific_mode = self.config.get('scientific_mode', False)
        
        # Extract metadata from critique report
        title = "Scientific Methodology Analysis" if scientific_mode else "Philosophical Critique"
        author = "Scientific Methodology Council" if scientific_mode else "Critique Council"
        date = datetime.datetime.now().strftime("%B %d, %Y")
        
        # Try to extract a better title and author if available
        title_match = re.search(r'#\s+([^\n]+)', critique_report)
        if title_match:
            title = title_match.group(1)
        
        author_match = re.search(r'##\s+Author:\s+([^\n]+)', critique_report)
        if author_match:
            author = author_match.group(1)
        
        # Extract possible abstract from critique report
        abstract = self._extract_abstract(critique_report)
        
        # Set keywords based on mode
        if scientific_mode:
            keywords = 'scientific methodology, empirical analysis, systems analysis, validation, logical analysis'
        else:
            keywords = 'philosophical critique, analysis, peer review'
        
        # Process original content
        processed_original = self._escape_latex_chars(original_content)
        if len(processed_original) > 1000:
            processed_original = processed_original[:997] + '...'
        
        # Create context dictionary with template variables
        context = {
            'title': title,
            'author': author,
            'date': date,
            'abstract': abstract,
            'original_content': processed_original,
            'analysis_content': critique_report,
            'review_content': peer_review or "No peer review available for this analysis.",
            'include_bibliography': self.config.get('include_bibliography', True),
            'keywords': keywords
        }
        
        return context
    
    def _extract_abstract(self, content: str) -> str:
        """
        Extract an abstract from the content.
        
        This method attempts to extract an abstract from the content,
        looking for explicit abstract sections or using the first paragraph.
        
        Args:
            content: The content to extract an abstract from.
            
        Returns:
            The extracted abstract.
        """
        # Try to find an explicit abstract section
        abstract_match = re.search(r'(?:##?\s+Abstract|Executive Summary[^\n]*\n)(.*?)(?:\n##?|$)', 
                                  content, re.DOTALL)
        
        if abstract_match:
            return abstract_match.group(1).strip()
        
        # If no explicit abstract, use the first paragraph (up to 500 chars)
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        if paragraphs:
            first_para = paragraphs[0].strip()
            # Remove any headings
            first_para = re.sub(r'^#+ .*\n', '', first_para)
            # Truncate if too long
            if len(first_para) > 500:
                return first_para[:497] + '...'
            return first_para
        
        # Default abstract if nothing else works
        return "This document presents a scientific critique and analysis of the provided content."
    
    def _prepare_original_content_summary(self, original_content: str) -> str:
        """
        Prepare a summary of the original content.
        
        Args:
            original_content: The original content to summarize.
            
        Returns:
            A summary of the original content suitable for inclusion in the LaTeX document.
        """
        # Truncate original content if too long
        if len(original_content) > 1000:
            summary = original_content[:997] + '...'
        else:
            summary = original_content
            
        # Escape any LaTeX special characters
        summary = self._escape_latex_chars(summary)
        
        return f"""
The analysis in this document is based on the following original content:

\\begin{{quote}}
{summary}
\\end{{quote}}

The critique and peer review sections provide a comprehensive analysis of this content
from multiple methodological perspectives.
"""
    
    def _process_content(self, content: str) -> str:
        """
        Process the content through all processors and converters.
        
        Args:
            content: The content to process.
            
        Returns:
            The processed content.
        """
        # Apply jargon processor to make content more scientific
        content = self.jargon_processor.process(content)
        
        # Apply citation processor to handle citations and bibliography
        content = self.citation_processor.process(content)
        
        # Apply math formatter to format mathematical expressions
        content = self.math_formatter.format(content)
        
        # Convert markdown to LaTeX
        content = self.markdown_converter.convert(content)
        
        return content
    
    def _escape_latex_chars(self, text: str) -> str:
        """
        Escape LaTeX special characters in text.
        
        Args:
            text: The text to escape.
            
        Returns:
            The escaped text.
        """
        print(f"Escaping LaTeX chars, text begins with: {repr(text[:50])}")
        
        # Define LaTeX special characters and their escaped versions
        latex_special_chars = [
            ('\\', '\\textbackslash{}'),
            ('&', '\\&'),
            ('%', '\\%'),
            ('$', '\\$'),
            ('#', '\\#'),
            ('_', '\\_'),
            ('{', '\\{'),
            ('}', '\\}'),
            ('~', '\\textasciitilde{}'),
            ('^', '\\textasciicircum{}'),
        ]
        
        # Escape LaTeX special characters
        result = text
        for char, escaped in latex_special_chars:
            result = result.replace(char, escaped)
        
        print(f"After escaping, text begins with: {repr(result[:50])}")
        return result


# Function for direct use
def format_as_latex(
    original_content: str,
    critique_report: str,
    peer_review: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> Tuple[str, Optional[str]]:
    """
    Format critique report and optional peer review into a LaTeX document.
    
    This function provides a simple interface for formatting critique reports
    and peer reviews into LaTeX documents without directly instantiating the
    LatexFormatter class.
    
    Args:
        original_content: The original content that was critiqued.
        critique_report: The generated critique report.
        peer_review: Optional peer review document.
        config: Optional configuration dictionary.
        
    Returns:
        A tuple of (tex_file_path, pdf_file_path), where pdf_file_path
        is None if compilation is not enabled or fails.
    """
    formatter = LatexFormatter(config)
    return formatter.format_document(original_content, critique_report, peer_review)
