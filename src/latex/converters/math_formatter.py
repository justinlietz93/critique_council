"""
Formatter for mathematical expressions in LaTeX documents.

This module provides a formatter that detects and properly formats
mathematical expressions for LaTeX documents with KaTeX compatibility.
"""

import re
from typing import Dict, Any, Optional, List, Match, Tuple


class MathFormatter:
    """
    Formatter for mathematical expressions in LaTeX documents.
    
    This formatter detects and formats mathematical expressions in content,
    supporting both inline and display math with KaTeX compatibility.
    """
    
    # Regular expressions for detecting common mathematical patterns
    MATH_PATTERNS = [
        # Inline math with $ delimiters
        (r'\$([^$]+?)\$', r'$\1$'),
        
        # Display math with $$ delimiters
        (r'\$\$([^$]+?)\$\$', r'\\begin{equation*}\1\\end{equation*}'),
        
        # Inline math with \( \) delimiters
        (r'\\[\(]([^\\]+?)\\[\)]', r'$\1$'),
        
        # Display math with \[ \] delimiters
        (r'\\[\[]([^\\]+?)\\[\]]', r'\\begin{equation*}\1\\end{equation*}')
    ]
    
    # Common mathematical notation that might need special handling
    NOTATION_PATTERNS = [
        # Fractions: a/b -> \frac{a}{b}
        (r'(\b[a-zA-Z0-9]+\b)/(\b[a-zA-Z0-9]+\b)', r'\\frac{\1}{\2}'),
        
        # Superscripts: x^2 -> x^{2} (for multi-digit/letter exponents)
        (r'(\b[a-zA-Z0-9]\b)\^([a-zA-Z0-9]{2,})', r'\1^{\2}'),
        
        # Subscripts: x_n -> x_{n} (for multi-digit/letter subscripts)
        (r'(\b[a-zA-Z0-9]\b)_([a-zA-Z0-9]{2,})', r'\1_{\2}')
    ]
    
    # Common mathematical symbols to detect and convert to LaTeX commands
    SYMBOL_REPLACEMENTS = {
        '≤': r'\leq',
        '≥': r'\geq',
        '≠': r'\neq',
        '≈': r'\approx',
        '∞': r'\infty',
        '∫': r'\int',
        '∑': r'\sum',
        '∏': r'\prod',
        '∂': r'\partial',
        '√': r'\sqrt',
        '∇': r'\nabla',
        '∆': r'\Delta',
        '∈': r'\in',
        '∉': r'\notin',
        '∩': r'\cap',
        '∪': r'\cup',
        '⊂': r'\subset',
        '⊃': r'\supset',
        '⊆': r'\subseteq',
        '⊇': r'\supseteq',
        '∀': r'\forall',
        '∃': r'\exists',
        '∄': r'\nexists',
        '→': r'\rightarrow',
        '←': r'\leftarrow',
        '↔': r'\leftrightarrow',
        '⇒': r'\Rightarrow',
        '⇐': r'\Leftarrow',
        '⇔': r'\Leftrightarrow',
        '·': r'\cdot',
        '×': r'\times',
        '÷': r'\div',
        '±': r'\pm',
        '∥': r'\parallel',
        '⊥': r'\perp',
        '∠': r'\angle',
        '°': r'^{\circ}',
        '…': r'\ldots',
        '⋯': r'\cdots',
        '⋮': r'\vdots',
        '⋱': r'\ddots'
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the math formatter.
        
        Args:
            config: Optional configuration dictionary for customizing formatting behavior.
        """
        self.config = config or {}
        self.katex_compatibility = self.config.get('katex_compatibility', True)
    
    def format(self, content: str) -> str:
        """
        Format mathematical expressions in the content for LaTeX with KaTeX compatibility.
        
        Args:
            content: The content containing mathematical expressions.
            
        Returns:
            The content with properly formatted mathematical expressions.
        """
        print(f"Math formatter: content begins with {repr(content[:50])}")
        try:
            # First detect and preserve existing LaTeX math environments
            preserved_math, content = self._preserve_existing_environments(content)
        
            # Detect and format inline and display math delimiters
            for pattern, replacement in self.MATH_PATTERNS:
                try:
                    content = re.sub(pattern, replacement, content)
                except Exception as e:
                    print(f"Error in math pattern replacement: {pattern} -> {replacement}: {e}")
                    # Continue with other patterns
        
            # Replace common mathematical symbols with LaTeX commands
            for symbol, command in self.SYMBOL_REPLACEMENTS.items():
                try:
                    # Only replace within math delimiters
                    content = self._replace_in_math(content, symbol, command)
                except Exception as e:
                    print(f"Error replacing symbol {repr(symbol)} with {repr(command)}: {e}")
                    # Continue with other symbols
        
            # Format common mathematical notation
            for pattern, replacement in self.NOTATION_PATTERNS:
                try:
                    # Only apply within math delimiters
                    content = self._replace_in_math_regex(content, pattern, replacement)
                except Exception as e:
                    print(f"Error in math notation replacement: {pattern} -> {replacement}: {e}")
                    # Continue with other patterns
            
            # Restore preserved environments
            content = self._restore_preserved_environments(content, preserved_math)
            
            print(f"Math formatter completed. Result begins with {repr(content[:50])}")
            return content
        except Exception as e:
            print(f"Critical error in math formatter: {e}")
            # Return the original content to avoid breaking the pipeline
            return content
    
    def _preserve_existing_environments(self, content: str) -> Tuple[Dict[str, str], str]:
        """
        Preserve existing LaTeX math environments to prevent double processing.
        
        Args:
            content: The content to process.
            
        Returns:
            A tuple of (preserved_environments, modified_content)
        """
        preserved = {}
        
        # Patterns for existing LaTeX math environments
        env_patterns = [
            (r'\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}', 'EQN'),
            (r'\\begin\{align\*?\}(.*?)\\end\{align\*?\}', 'ALN'),
            (r'\\begin\{gather\*?\}(.*?)\\end\{gather\*?\}', 'GTH'),
            (r'\\begin\{multline\*?\}(.*?)\\end\{multline\*?\}', 'MTL')
        ]
        
        # Replace existing environments with placeholders
        for i, (pattern, prefix) in enumerate(env_patterns):
            matches = re.finditer(pattern, content, re.DOTALL)
            for j, match in enumerate(matches):
                placeholder = f'__{prefix}{i}{j}__'
                preserved[placeholder] = match.group(0)
                content = content.replace(match.group(0), placeholder)
        
        return preserved, content
    
    def _restore_preserved_environments(self, content: str, preserved: Dict[str, str]) -> str:
        """
        Restore preserved LaTeX math environments.
        
        Args:
            content: The content with placeholders.
            preserved: Dictionary of placeholders to original content.
            
        Returns:
            The content with preserved environments restored.
        """
        for placeholder, original in preserved.items():
            content = content.replace(placeholder, original)
        
        return content
    
    def _replace_in_math(self, content: str, symbol: str, command: str) -> str:
        """
        Replace a symbol with a LaTeX command, but only within math delimiters.
        
        Args:
            content: The content to process.
            symbol: The symbol to replace.
            command: The LaTeX command to replace it with.
            
        Returns:
            The processed content.
        """
        # Identify math blocks
        math_blocks = []
        
        # Find inline math blocks ($...$)
        inline_matches = re.finditer(r'\$(.*?)\$', content)
        for match in inline_matches:
            math_blocks.append((match.start(1), match.end(1), match.group(1)))
        
        # Find display math blocks ($$...$$, \begin{equation}...\end{equation}, etc.)
        display_matches = re.finditer(r'\$\$(.*?)\$\$', content)
        for match in display_matches:
            math_blocks.append((match.start(1), match.end(1), match.group(1)))
        
        # Sort blocks by start position, in reverse order so replacements don't affect indices
        math_blocks.sort(key=lambda x: x[0], reverse=True)
        
        # List to build result
        result_parts = list(content)
        
        # Replace symbols only within math blocks
        for start, end, block in math_blocks:
            block_with_replacements = block.replace(symbol, command)
            
            # Replace the block in the result
            for i, char in enumerate(block_with_replacements):
                if start + i < end:
                    result_parts[start + i] = char
        
        return ''.join(result_parts)
    
    def _replace_in_math_regex(self, content: str, pattern: str, replacement: str) -> str:
        """
        Apply a regex replacement, but only within math delimiters.
        
        Args:
            content: The content to process.
            pattern: The regex pattern to match.
            replacement: The replacement string.
            
        Returns:
            The processed content.
        """
        # Regex to find math blocks
        math_patterns = [
            r'\$(.*?)\$',  # Inline math
            r'\$\$(.*?)\$\$',  # Display math
            r'\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}',  # Equation environment
            r'\\begin\{align\*?\}(.*?)\\end\{align\*?\}'  # Align environment
        ]
        
        for math_pattern in math_patterns:
            # Find all math blocks of this type
            math_blocks = re.finditer(math_pattern, content, re.DOTALL)
            
            # Process each block
            for match in math_blocks:
                # Get the math content without delimiters
                full_match = match.group(0)
                math_content = match.group(1)
                
                # Apply the replacement within the math content
                replaced_content = re.sub(pattern, replacement, math_content)
                
                # Reconstruct the full math block with delimiters
                if math_pattern == r'\$(.*?)\$':
                    new_block = f'${replaced_content}$'
                elif math_pattern == r'\$\$(.*?)\$\$':
                    new_block = f'$${replaced_content}$$'
                else:
                    # For environments, we need to preserve the begin/end tags
                    env_match = re.match(r'\\begin\{(.*?)(\*?)\}', full_match)
                    if env_match:
                        env_name = env_match.group(1)
                        star = env_match.group(2)
                        new_block = f'\\begin{{{env_name}{star}}}{replaced_content}\\end{{{env_name}{star}}}'
                
                # Replace the original block in the content
                content = content.replace(full_match, new_block)
        
        return content
