"""
ArXiv BibTeX Converter Module

This module provides functionality to convert arXiv metadata to BibTeX format,
suitable for inclusion in LaTeX documents.
"""

import re
from typing import Dict, Any, List, Optional

class BibTexConverter:
    """
    Converter for arXiv paper metadata to BibTeX entries.
    
    This class handles:
    1. Converting paper metadata to BibTeX format
    2. Generating citation keys
    3. Formatting author names and other fields
    """
    
    @classmethod
    def paper_to_bibtex(cls, paper: Dict[str, Any], cite_key: Optional[str] = None) -> str:
        """
        Convert arXiv paper metadata to BibTeX entry.
        
        Args:
            paper: arXiv paper metadata
            cite_key: Optional custom citation key
            
        Returns:
            BibTeX entry as a string
        """
        # Extract key info
        arxiv_id = paper.get('id', '').replace('/', '_')
        title = paper.get('title', 'Unknown Title').replace('{', '\\{').replace('}', '\\}')
        
        # Format authors for BibTeX
        authors = paper.get('authors', [])
        author_string = " and ".join([author.replace('{', '\\{').replace('}', '\\}') for author in authors])
        
        # Extract year from published date
        published = paper.get('published', '')
        year_match = re.search(r'(\d{4})', published)
        year = year_match.group(1) if year_match else "YYYY"
        
        # Extract month if available
        month_match = re.search(r'(\d{4})-(\d{2})', published)
        month = month_match.group(2) if month_match else ""
        
        # Determine entry type
        entry_type = "article"
        if paper.get('journal_ref'):
            entry_type = "article"
        else:
            entry_type = "misc"  # For preprints without journal reference
        
        # Generate citation key if not provided
        if not cite_key:
            cite_key = cls.generate_cite_key(paper)
        
        # Build the BibTeX entry
        bibtex = [f"@{entry_type}{{{cite_key},"]
        bibtex.append(f"  author = {{{author_string}}},")
        bibtex.append(f"  title = {{{title}}},")
        bibtex.append(f"  year = {{{year}}},")
        
        if month:
            bibtex.append(f"  month = {month},")
        
        # Add journal reference if available
        if paper.get('journal_ref'):
            bibtex.append(f"  journal = {{{paper.get('journal_ref')}}},")
        
        # Add DOI if available
        if paper.get('doi'):
            bibtex.append(f"  doi = {{{paper.get('doi')}}},")
        
        # Add arXiv identifiers
        bibtex.append(f"  eprint = {{{paper.get('id', '')}}},")
        bibtex.append(f"  archivePrefix = {{arXiv}},")
        
        # Add primary category if available
        if paper.get('primary_category'):
            bibtex.append(f"  primaryClass = {{{paper.get('primary_category')}}},")
        
        # Add URL to abstract page
        abstract_url = paper.get('links', {}).get('abstract_page', f"https://arxiv.org/abs/{paper.get('id', '')}")
        bibtex.append(f"  url = {{{abstract_url}}},")
        
        # Close the entry
        bibtex.append("}")
        
        return "\n".join(bibtex)
    
    @classmethod
    def generate_cite_key(cls, paper: Dict[str, Any]) -> str:
        """
        Generate a citation key for a paper.
        
        Args:
            paper: arXiv paper metadata
            
        Returns:
            Citation key string
        """
        # Extract paper ID and sanitize
        arxiv_id = paper.get('id', '').replace('/', '_').replace('.', '_')
        
        # Extract first author's last name (if available)
        authors = paper.get('authors', [])
        author_part = "unknown"
        if authors:
            first_author = authors[0]
            # Try to extract last name
            parts = first_author.split()
            if len(parts) > 0:
                author_part = parts[-1].lower()
                # Remove any non-alphanumeric characters
                author_part = re.sub(r'[^a-z0-9]', '', author_part)
        
        # Extract year
        published = paper.get('published', '')
        year_match = re.search(r'(\d{4})', published)
        year_part = year_match.group(1) if year_match else ""
        
        # If we have both author and year, use them
        if author_part and year_part:
            return f"arxiv_{author_part}{year_part}"
        
        # Otherwise, use the arXiv ID
        return f"arxiv_{arxiv_id}"
    
    @classmethod
    def format_bib_file(cls, papers: List[Dict[str, Any]], header_comment: Optional[str] = None) -> str:
        """
        Format a complete BibTeX file from a list of papers.
        
        Args:
            papers: List of arXiv paper metadata
            header_comment: Optional comment to include at the top of the file
            
        Returns:
            Complete BibTeX file content as a string
        """
        contents = []
        
        # Add header comment if provided
        if header_comment:
            contents.append(f"% {header_comment}")
            contents.append("")
        
        # Add papers
        for paper in papers:
            contents.append(cls.paper_to_bibtex(paper))
            contents.append("")  # Empty line between entries
        
        return "\n".join(contents)
    
    @classmethod
    def format_citation_command(cls, paper: Dict[str, Any], style: str = "cite") -> str:
        """
        Format a LaTeX citation command for a paper.
        
        Args:
            paper: arXiv paper metadata
            style: Citation style (cite, citep, citet, etc.)
            
        Returns:
            LaTeX citation command
        """
        cite_key = cls.generate_cite_key(paper)
        return f"\\{style}{{{cite_key}}}"
