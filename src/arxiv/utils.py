"""
ArXiv Utilities Module

This module provides helper functions for the ArXiv reference service,
including text processing and search term extraction.
"""

import re
from typing import List, Dict, Set, Any, Optional

class TextProcessor:
    """
    Utility class for processing text and extracting relevant information.
    """
    
    # Common English stopwords that should be filtered out
    STOPWORDS = {
        'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
        'which', 'this', 'that', 'these', 'those', 'then', 'just', 'so', 'than',
        'such', 'both', 'through', 'about', 'for', 'is', 'of', 'while', 'during',
        'to', 'from', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'once',
        'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both',
        'each', 'few', 'more', 'most', 'some', 'such', 'no', 'nor', 'not', 'only',
        'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will',
        'don', 'should', 'now', 'with', 'been', 'being', 'have', 'has', 'had',
        'are', 'was', 'were', 'be', 'by', 'use', 'used'
    }
    
    @classmethod
    def extract_keywords(cls, text: str, max_keywords: int = 15) -> List[str]:
        """
        Extract important keywords from text content.
        
        Args:
            text: The input text to extract keywords from
            max_keywords: Maximum number of keywords to extract
            
        Returns:
            List of extracted keywords
        """
        # 1. Extract individual words
        words = re.findall(r'\b[A-Za-z][A-Za-z-]{3,}\b', text)
        word_freq = {}
        
        # Count word frequencies
        for word in words:
            word = word.lower()
            if word not in word_freq:
                word_freq[word] = 0
            word_freq[word] += 1
        
        # Filter out stopwords
        for word in cls.STOPWORDS:
            if word in word_freq:
                del word_freq[word]
        
        # Sort by frequency and take top terms
        max_single_words = max(1, max_keywords * 2 // 3)
        top_terms = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:max_single_words]
        
        # 2. Extract important phrases (simple approach)
        phrases = re.findall(r'\b[A-Za-z][A-Za-z-]+ [A-Za-z][A-Za-z-]+\b', text)
        phrase_freq = {}
        
        # Count phrase frequencies
        for phrase in phrases:
            phrase = phrase.lower()
            # Skip phrases that contain only stopwords
            words_in_phrase = phrase.split()
            if all(word in cls.STOPWORDS for word in words_in_phrase):
                continue
            
            if phrase not in phrase_freq:
                phrase_freq[phrase] = 0
            phrase_freq[phrase] += 1
        
        # Sort phrases by frequency
        max_phrases = max(1, max_keywords // 3)
        top_phrases = []
        if phrase_freq:
            top_phrases = sorted(phrase_freq.items(), key=lambda x: x[1], reverse=True)[:max_phrases]
        
        # Combine terms and phrases
        results = [term for term, _ in top_terms] + [phrase for phrase, _ in top_phrases]
        
        # Deduplicate and limit results
        seen = set()
        deduped_results = []
        for term in results:
            if term not in seen:
                seen.add(term)
                deduped_results.append(term)
                if len(deduped_results) >= max_keywords:
                    break
        
        return deduped_results
    
    @classmethod
    def extract_domain_specific_terms(
        cls,
        text: str,
        domains: Optional[List[str]] = None,
        max_terms: int = 10
    ) -> List[str]:
        """
        Extract domain-specific terminology from text.
        
        Args:
            text: The input text to extract terms from
            domains: Optional list of domain names to prioritize (e.g., ["physics", "mathematics"])
            max_terms: Maximum number of terms to extract
            
        Returns:
            List of domain-specific terms
        """
        # Domain-specific patterns
        patterns = [
            # Scientific notation
            r'\b\d+\.\d+e[+-]?\d+\b',
            # Units of measurement
            r'\b\d+(\.\d+)?\s*(cm|mm|km|m|kg|g|mg|Hz|GHz|MHz|s|ms|A|V|W|J|K|mol|cd|rad|sr)\b',
            # Chemical formulas
            r'\b[A-Z][a-z]?\d*(?:[A-Z][a-z]?\d*)+\b',
            # Mathematical symbols with surrounding text
            r'\b[A-Za-z]+\s*[+\-*/=<>≤≥≈≠∝∞∫∑∏√∂∇]\s*[A-Za-z]+\b'
        ]
        
        # Add domain-specific patterns based on provided domains
        if domains:
            for domain in domains:
                domain = domain.lower()
                if domain == "physics":
                    patterns.extend([
                        r'\b(?:quantum|relativity|momentum|velocity|acceleration|force|energy|mass|gravity|electromagnetism|particle)\b',
                        r'\bfield\s+(?:theory|equation|constant)\b'
                    ])
                elif domain == "mathematics":
                    patterns.extend([
                        r'\b(?:theorem|lemma|corollary|proof|equation|formula|function|variable|constant|algorithm|complexity)\b',
                        r'\b(?:matrix|vector|scalar|tensor|topology|manifold|space|transformation)\b'
                    ])
                elif domain == "computer science":
                    patterns.extend([
                        r'\b(?:algorithm|complexity|function|recursion|iteration|optimization|heuristic|approximation)\b',
                        r'\b(?:neural\s+network|machine\s+learning|deep\s+learning|artificial\s+intelligence|data\s+mining)\b'
                    ])
        
        # Extract terms using patterns
        found_terms = set()
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                found_terms.add(match.group(0).lower())
        
        # Combine with any multi-word technical terms
        technical_terms = re.findall(r'\b(?:[A-Z][a-z]*\s+)+[A-Z][a-z]*\b', text)
        for term in technical_terms:
            if len(term.split()) >= 2:  # At least two words
                found_terms.add(term.lower())
        
        # Convert to list and limit number of results
        result = list(found_terms)[:max_terms]
        
        return result
    
    @classmethod
    def create_arxiv_search_query(cls, terms: List[str], operator: str = "OR") -> str:
        """
        Create an arXiv search query from a list of terms.
        
        Args:
            terms: List of search terms
            operator: Boolean operator to join terms ("AND" or "OR")
            
        Returns:
            arXiv search query string
        """
        if not terms:
            return ""
        
        # Validate operator
        valid_operators = ["AND", "OR"]
        if operator.upper() not in valid_operators:
            operator = "OR"
        operator = operator.upper()
        
        # If any term contains spaces, use quotes
        quoted_terms = []
        for term in terms:
            if " " in term:
                quoted_terms.append(f'all:"{term}"')
            else:
                quoted_terms.append(f'all:{term}')
        
        # Join with the specified operator
        return f" {operator} ".join(quoted_terms)
