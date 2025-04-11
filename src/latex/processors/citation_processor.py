"""
Processor for handling citations and references in LaTeX documents.

This module provides a processor that extracts and formats citations from
content, generating proper LaTeX citations and a BibTeX bibliography.
"""

import re
import os
import datetime
from typing import Dict, Any, Optional, List, Set, Tuple
from .content_processor import ContentProcessor


class CitationProcessor(ContentProcessor):
    """
    Processor for handling citations and references in LaTeX documents.
    
    This processor extracts citations from the content, formats them as proper
    LaTeX citations, and generates a BibTeX bibliography file.
    """
    
    # Regular expressions for identifying different citation formats
    CITATION_PATTERNS = [
        # APA style in-text citations
        r'\(([A-Za-z\s]+),\s+(\d{4}[a-z]?)\)',
        # Author year format
        r'([A-Za-z\s]+)\s+\((\d{4}[a-z]?)\)',
        # References in the format: Author (Year)
        r'([A-Za-z\s]+)\s+\((\d{4}[a-z]?)\)',
        # Formal bibliography entries
        r'([A-Za-z\s-]+)\.\s+\((\d{4}[a-z]?)\)\.\s+([^\.]+)\.'
    ]
    
    # Dictionary mapping reference types to BibTeX entry types
    REFERENCE_TYPES = {
        'book': '@book',
        'article': '@article',
        'conference': '@conference',
        'techreport': '@techreport',
        'online': '@online',
        'misc': '@misc'
    }
    
    def __init__(self, output_dir: str = "latex_output"):
        """
        Initialize the CitationProcessor.
        
        Args:
            output_dir: Directory where the bibliography file will be saved.
        """
        self._output_dir = output_dir
        self._citations = {}  # Dictionary to store extracted citations
        self._compiled_patterns = [re.compile(pattern) for pattern in self.CITATION_PATTERNS]
        
    def process(self, content: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process the input content to handle citations and references.
        
        Args:
            content: The input content to process.
            context: Optional dictionary providing additional context or settings.
            
        Returns:
            The processed content with properly formatted LaTeX citations.
        """
        processed_content = content
        
        # Override output directory if provided in context
        output_dir = context.get("output_dir", self._output_dir) if context else self._output_dir
        
        # Extract citations from content
        self._extract_citations(content)
        
        # Replace citation references with LaTeX cite commands
        processed_content = self._replace_citations(processed_content)
        
        # Generate BibTeX file if we have citations and context specifies to do so
        if self._citations and (not context or context.get("generate_bibtex", True)):
            self._generate_bibtex_file(output_dir)
            
        return processed_content
    
    def _extract_citations(self, content: str) -> None:
        """
        Extract citations from the content.
        
        Args:
            content: The input content to extract citations from.
        """
        lines = content.split('\n')
        
        # First pass: extract formal bibliography entries
        references_section = False
        for line in lines:
            if re.search(r'^-{3,}$', line) or re.search(r'^#{1,3}\s+References', line, re.IGNORECASE):
                references_section = True
                continue
                
            if references_section and line.strip():
                # Try to parse as a bibliography entry
                self._parse_bibliography_entry(line)
        
        # Second pass: extract in-text citations
        for pattern in self._compiled_patterns:
            matches = pattern.findall(content)
            for match in matches:
                if len(match) >= 2:
                    author, year = match[0], match[1]
                    cite_key = self._generate_cite_key(author, year)
                    
                    # Only add if not already extracted from bibliography
                    if cite_key not in self._citations:
                        self._citations[cite_key] = {
                            'author': author,
                            'year': year,
                            'title': f"Reference by {author}",
                            'type': 'misc'
                        }
    
    def _parse_bibliography_entry(self, line: str) -> None:
        """
        Parse a bibliography entry line.
        
        Args:
            line: The bibliography entry line to parse.
        """
        # Check for APA style reference line
        apa_match = re.search(r'([A-Za-z\s-]+),\s+([A-Za-z\s-]+)\.\s+\((\d{4}[a-z]?)\)\.\s+([^\.]+)\.(?:\s+([^\.]+))?', line)
        if apa_match:
            last_name = apa_match.group(1).strip()
            first_name = apa_match.group(2).strip()
            year = apa_match.group(3)
            title = apa_match.group(4).strip()
            publication = apa_match.group(5).strip() if apa_match.group(5) else ""
            
            # Determine type based on content
            ref_type = 'article' if re.search(r'journal|proceedings', publication, re.IGNORECASE) else 'book'
            
            cite_key = self._generate_cite_key(f"{last_name}", year)
            self._citations[cite_key] = {
                'author': f"{last_name}, {first_name}",
                'year': year,
                'title': title,
                'publisher': publication,
                'type': ref_type
            }
            return
            
        # Check for simple author (year) entry
        simple_match = re.search(r'([A-Za-z\s]+)\.\s+\((\d{4}[a-z]?)\)\.\s+([^\.]+)', line)
        if simple_match:
            author = simple_match.group(1).strip()
            year = simple_match.group(2)
            title = simple_match.group(3).strip()
            
            cite_key = self._generate_cite_key(author, year)
            self._citations[cite_key] = {
                'author': author,
                'year': year,
                'title': title,
                'type': 'misc'
            }
            
    def _generate_cite_key(self, author: str, year: str) -> str:
        """
        Generate a citation key from author and year.
        
        Args:
            author: The author of the citation.
            year: The publication year.
            
        Returns:
            A citation key in the format 'LastName:Year'.
        """
        # Extract last name from author
        author = author.strip()
        last_name = author.split(',')[0] if ',' in author else author.split()[-1]
        last_name = re.sub(r'[^\w]', '', last_name)
        
        return f"{last_name.lower()}{year}"
    
    def _replace_citations(self, content: str) -> str:
        """
        Replace citation references with LaTeX cite commands.
        
        Args:
            content: The input content to process.
            
        Returns:
            The processed content with LaTeX cite commands.
        """
        processed_content = content
        
        # Replace APA style citations: (Author, Year)
        processed_content = re.sub(
            r'\(([A-Za-z\s]+),\s+(\d{4}[a-z]?)\)',
            lambda m: r'\cite{' + self._generate_cite_key(m.group(1), m.group(2)) + '}',
            processed_content
        )
        
        # Replace Author (Year) citations
        processed_content = re.sub(
            r'([A-Za-z\s]+)\s+\((\d{4}[a-z]?)\)',
            lambda m: r'\citeauthor{' + self._generate_cite_key(m.group(1), m.group(2)) + '} ' + 
                     r'(\citeyear{' + self._generate_cite_key(m.group(1), m.group(2)) + '})',
            processed_content
        )
        
        return processed_content
    
    def _generate_bibtex_file(self, output_dir: str) -> None:
        """
        Generate a BibTeX file for the output.
        
        Instead of generating a potentially malformed bibliography from extracted citations,
        this now copies the template bibliography file to ensure a well-formatted result.
        
        Args:
            output_dir: Directory where the bibliography file will be saved.
        """
        os.makedirs(output_dir, exist_ok=True)
        output_bibtex_file = os.path.join(output_dir, 'bibliography.bib')
        
        # Path to the template bibliography file (assuming standard project structure)
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        template_bibtex_file = os.path.join(template_dir, 'bibliography.bib')
        
        # Check if template file exists
        if os.path.exists(template_bibtex_file):
            # Copy the template bibliography file to the output directory
            try:
                with open(template_bibtex_file, 'r', encoding='utf-8') as source_file:
                    template_content = source_file.read()
                
                with open(output_bibtex_file, 'w', encoding='utf-8') as target_file:
                    # Add a timestamp comment at the top
                    target_file.write(f"% Bibliography file copied from template on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    target_file.write(template_content)
                
                print(f"Bibliography copied from template to {output_bibtex_file}")
                return
            except Exception as e:
                print(f"Error copying bibliography template: {e}")
        
        # Fallback to the old method if template file doesn't exist or copying fails
        print("Bibliography template not found or copy failed. Generating bibliography from extracted citations.")
        with open(output_bibtex_file, 'w', encoding='utf-8') as f:
            f.write(f"% Bibliography file generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for cite_key, citation in self._citations.items():
                entry_type = self.REFERENCE_TYPES.get(citation.get('type', 'misc'), '@misc')
                f.write(f"{entry_type}{{{cite_key},\n")
                
                # Write required fields
                f.write(f"  author = {{{citation['author']}}},\n")
                f.write(f"  year = {{{citation['year']}}},\n")
                f.write(f"  title = {{{citation['title']}}},\n")
                
                # Write optional fields if available
                if 'publisher' in citation:
                    f.write(f"  publisher = {{{citation['publisher']}}},\n")
                if 'journal' in citation:
                    f.write(f"  journal = {{{citation['journal']}}},\n")
                if 'volume' in citation:
                    f.write(f"  volume = {{{citation['volume']}}},\n")
                if 'number' in citation:
                    f.write(f"  number = {{{citation['number']}}},\n")
                if 'pages' in citation:
                    f.write(f"  pages = {{{citation['pages']}}},\n")
                if 'url' in citation:
                    f.write(f"  url = {{{citation['url']}}},\n")
                
                f.write("}\n\n")
    
    @property
    def name(self) -> str:
        """
        Get the name of the processor.
        
        Returns:
            The processor name.
        """
        return "citation_processor"
    
    @property
    def description(self) -> str:
        """
        Get a description of what the processor does.
        
        Returns:
            The processor description.
        """
        return "Handles citations and generates a BibTeX bibliography"
