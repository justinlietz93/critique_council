#!/usr/bin/env python3
"""
Direct LaTeX generator specifically for peer review files.

This module provides a DirectLatexGenerator class that converts peer review
content (assumed to be simple markdown) directly into a basic LaTeX document,
bypassing complex markdown parsing for robustness.
"""

import re
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class DirectLatexGenerator:
    """
    Generates LaTeX directly from simple markdown content, optimized for peer reviews.

    This class takes markdown text as input and applies minimal transformations
    to produce a compilable LaTeX document. It focuses on handling basic
    structures like headings, lists, and emphasis, while escaping special
    LaTeX characters.
    """

    # LaTeX special characters and their escaped versions
    LATEX_SPECIAL_CHARS: Dict[str, str] = {
        '%': r'\%',
        '&': r'\&',
        '$': r'\$',
        '_': r'\_',
        '#': r'\#',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
        '\\': r'\textbackslash{}',
    }

    # Additional character replacements for common issues
    CHARACTER_REPLACEMENTS: List[Tuple[str, str]] = [
        ('─', '-'),        # Replace Unicode dash with ASCII dash
        ('…', '...'),      # Replace ellipsis with periods
        ('—', '--'),       # Replace em dash
        ('–', '-'),        # Replace en dash
        ('"', '"'),        # Replace smart quotes (left)
        ('"', '"'),        # Replace smart quotes (right)
        (''', "'"),        # Replace smart apostrophes (left)
        (''', "'"),        # Replace smart apostrophes (right)
        ('≈', '$\\approx$'),  # Replace approximate symbol
        ('≠', '$\\neq$'),   # Replace not equal symbol
        ('°', '$^{\\circ}$'),  # Replace degree symbol
        ('\t', '    '),    # Replace tabs with spaces
    ]

    def __init__(self, content: str, title: Optional[str] = None):
        """
        Initialize the generator with the markdown content.

        Args:
            content: The raw markdown content of the peer review.
            title: Optional override for the document title. If None, it will
                   attempt to extract from the first H1 heading.
        """
        self.raw_content: str = content
        self.title: str = title if title else self._extract_title(content)
        self.processed_lines: List[str] = []

    def _extract_title(self, content: str) -> str:
        """
        Extracts the title from the first H1 markdown heading.

        Args:
            content: The markdown content.

        Returns:
            The extracted title or a default title.
        """
        title_match = re.search(r'^# (.+?)$', content, re.MULTILINE)
        if title_match:
            return title_match.group(1).strip()
        logger.warning("Could not extract title from H1, using default.")
        return "Scientific Peer Review"

    def _escape_latex_chars(self, text: str) -> str:
        """
        Escapes special LaTeX characters in a given string.

        Args:
            text: The string to escape.

        Returns:
            The string with special characters escaped.
        """
        # Apply specific replacements first
        for old, new in self.CHARACTER_REPLACEMENTS:
            text = text.replace(old, new)
        # Apply standard LaTeX escapes
        for char, escaped in self.LATEX_SPECIAL_CHARS.items():
            # Avoid double-escaping backslashes if they are part of commands
            if char == '\\':
                 # Use negative lookbehind to avoid escaping already escaped chars or commands
                 text = re.sub(r'(?<!\\)\\{1}(?![a-zA-Z@])', escaped, text)
            else:
                text = text.replace(char, escaped)
        return text

    def _process_line(self, line: str) -> str:
        """
        Processes a single line of markdown content for LaTeX conversion.

        Handles headings, horizontal rules, and basic formatting.

        Args:
            line: The line to process.

        Returns:
            The processed line in LaTeX format.
        """
        stripped_line = line.strip()

        # Handle headings first to avoid escaping '#'
        if stripped_line.startswith('# '):
            return f"\\section*{{{self._escape_latex_chars(stripped_line[2:].strip())}}}"
        elif stripped_line.startswith('## '):
            return f"\\subsection*{{{self._escape_latex_chars(stripped_line[3:].strip())}}}"
        elif stripped_line.startswith('### '):
            return f"\\subsubsection*{{{self._escape_latex_chars(stripped_line[4:].strip())}}}"
        # Handle numbered sections (assuming simple format like "1. Section Title")
        elif re.match(r'^\d+\.\s+.+$', stripped_line):
            match = re.match(r'^(\d+)\.\s+(.+)$', stripped_line)
            if match:
                # Using subsection* for unnumbered sections in TOC
                return f"\\subsection*{{{self._escape_latex_chars(match.group(2).strip())}}}"
        # Handle horizontal rules
        elif stripped_line in ['---', '***', '___', '───']:
            return "\\par\\noindent\\hrulefill\\par" # More robust rule

        # Escape remaining special characters for regular lines
        processed_line = self._escape_latex_chars(line)

        # Convert basic markdown emphasis (after escaping)
        # Use non-greedy matching (.+?)
        processed_line = re.sub(r'\\\*\\\*(.+?)\\\*\\\*', r'\\textbf{\1}', processed_line) # Matches escaped **
        processed_line = re.sub(r'\\\*(.+?)\\\*', r'\\textit{\1}', processed_line)     # Matches escaped *

        # Handle lists (simple bullet points) - needs context, handled in generate_latex_body
        # Handle blockquotes - remove '>'
        processed_line = re.sub(r'^>\s*', '', processed_line)

        # Skip any remaining raw markdown section headers
        if processed_line.strip().startswith('\\#'): # Check for escaped '#'
             logger.debug(f"Skipping potential raw markdown header remnant: {processed_line}")
             return "" # Return empty string to effectively remove the line

        return processed_line

    def _process_content_body(self) -> str:
        """
        Processes the main body of the markdown content.

        Handles line-by-line processing and list environments.

        Returns:
            The processed body content as a single LaTeX string.
        """
        processed_lines: List[str] = []
        in_itemize = False
        lines = self.raw_content.splitlines()

        for i, line in enumerate(lines):
            is_list_item = line.strip().startswith('* ')
            processed_line = self._process_line(line)

            # Manage itemize environment
            if is_list_item and not in_itemize:
                processed_lines.append("\\begin{itemize}")
                in_itemize = True
            elif not is_list_item and in_itemize:
                processed_lines.append("\\end{itemize}")
                in_itemize = False

            # Format list items
            if is_list_item:
                 # Extract item text after '* ' and process it
                 item_text = self._process_line(line.strip()[2:])
                 processed_lines.append(f"  \\item {item_text}")
            elif processed_line: # Add non-empty, non-list lines
                 processed_lines.append(processed_line)
            elif not line.strip() and i > 0 and lines[i-1].strip():
                 # Add paragraph break for blank lines unless previous was also blank
                 processed_lines.append("\\par")


        # Close any remaining itemize environments
        while list_depth > 0:
            processed_lines.append('  ' * (list_depth - 1) + "\\end{itemize}")
            list_depth -= 1

        # Final cleanup: remove redundant paragraph breaks
        final_output = []
        for i, l in enumerate(processed_lines):
            if l == "\\par" and (i == 0 or processed_lines[i-1] == "\\par"):
                continue
            final_output.append(l)


        return '\n'.join(final_output)


    def generate_latex_document(self) -> str:
        """
        Generates the full LaTeX document string.

        Combines the preamble, title section, processed body, and closing tags.

        Returns:
            The complete LaTeX document as a string.
        """
        latex_body = self._process_content_body()

        # Basic LaTeX document structure
        document = f"""\\documentclass{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{amsmath}} % For math symbols like approx, neq
\\usepackage{{geometry}} % For margins
\\geometry{{a4paper, margin=1in}}
\\usepackage{{hyperref}} % For clickable links (if any)
\\hypersetup{{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,
    urlcolor=cyan,
}}

% Document metadata
\\title{{{self._escape_latex_chars(self.title)}}}
\\author{{Scientific Peer Review}} % Placeholder author
\\date{{\\today}}

\\begin{{document}}

\\maketitle

{latex_body}

\\end{{document}}
"""
        logger.info("Direct LaTeX document generated.")
        return document

# Example usage (for testing purposes if run directly)
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger.info("Testing DirectLatexGenerator...")

    # Sample markdown content
    sample_markdown = """
# Peer Review Report: Example Paper

This is a *sample* peer review report.

## Section 1: Summary

The paper presents an **interesting** approach.

Key points:
* Point 1: Strength A
* Point 2: Strength B

---

## Section 2: Major Concerns

1. Concern one about methodology.
2. Concern two regarding data interpretation.

### Subsection 2.1: Details

Further details on the methodology concern. Special chars: % & $ _ # { } ~ ^ \\

> This is a blockquote that should just become normal text.

Another paragraph with ≈ ≠ ° symbols.

## Section 3: Minor Suggestions

- Suggestion alpha.
- Suggestion beta.

Final thoughts.
"""

    generator = DirectLatexGenerator(sample_markdown)
    latex_output = generator.generate_latex_document()

    print("\n--- Generated LaTeX Output ---")
    print(latex_output)
    print("--- End Generated LaTeX Output ---\n")

    # You could add code here to write to a file and compile with pdflatex
    # import subprocess
    # output_path = "test_direct_output.tex"
    # with open(output_path, "w", encoding="utf-8") as f:
    #     f.write(latex_output)
    # print(f"LaTeX written to {output_path}")
    # try:
    #     subprocess.run(["pdflatex", "-interaction=nonstopmode", output_path], check=True)
    #     print("PDF compilation successful (test_direct_output.pdf)")
    # except Exception as e:
    #     print(f"PDF compilation failed: {e}")
