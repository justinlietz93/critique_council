"""
ArXiv Semantic Scorer Module

This module provides advanced relevance scoring for ArXiv papers 
to better match content points with academic references.
"""

import re
import math
import logging
from typing import Dict, List, Any, Set, Tuple
from collections import Counter

# Set up logging
logger = logging.getLogger(__name__)

class SemanticScorer:
    """
    Advanced semantic relevance scoring for academic papers.
    
    This class provides methods to:
    1. Calculate relevance scores between content and papers
    2. Rank papers by relevance
    3. Filter papers by relevance threshold
    """
    
    # Common English stopwords to exclude from scoring
    STOPWORDS = {
        'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while',
        'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through',
        'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in',
        'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here',
        'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 
        'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
        'same', 'so', 'than', 'too', 'very', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'will',
        'would', 'shall', 'should', 'can', 'could', 'may', 'might', 'must', 'that',
        'which', 'who', 'whom', 'this', 'these', 'those', 'am', 'im', 'ive', 'id',
        'youre', 'youve', 'youll', 'youve', 'hes', 'shes', 'its', 'were', 'theyve',
        'theyll', 'theyre'
    }
    
    # Domain-specific terms by field
    DOMAIN_TERMS = {
        "computer_science": {
            "algorithm", "complexity", "computation", "data", "software", "hardware",
            "programming", "code", "compiler", "database", "network", "internet",
            "security", "encryption", "artificial", "intelligence", "neural", "learning",
            "quantum", "computing", "parallel", "distributed", "architecture", "memory",
            "processor", "operating", "system", "interface", "logic", "boolean", "binary",
            "optimization", "efficiency", "performance", "virtual", "cloud", "server",
            "client", "web", "mobile", "graphics", "simulation", "modeling", "machine",
            "deep", "reinforcement", "supervised", "unsupervised", "nlp", "vision",
            "recognition", "classification", "regression", "clustering", "adversarial"
        },
        "physics": {
            "quantum", "relativity", "particle", "wave", "field", "force", "energy",
            "matter", "mass", "gravity", "electromagnetic", "nuclear", "atom", "electron",
            "proton", "neutron", "quark", "boson", "fermion", "photon", "radiation",
            "thermodynamics", "entropy", "temperature", "heat", "pressure", "mechanics",
            "dynamics", "kinematics", "velocity", "acceleration", "momentum", "inertia",
            "oscillation", "vibration", "frequency", "wavelength", "amplitude", "phase",
            "interference", "diffraction", "reflection", "refraction", "optics", "laser",
            "spectrometer", "detector", "accelerator", "collider", "plasma", "fusion",
            "fission", "radioactive", "isotope", "superconductor", "magnetism"
        },
        "mathematics": {
            "theorem", "proof", "lemma", "corollary", "conjecture", "axiom", "postulate",
            "algebra", "geometry", "calculus", "topology", "analysis", "probability",
            "statistics", "number", "integer", "rational", "real", "complex", "function",
            "derivative", "integral", "limit", "series", "sequence", "convergence",
            "divergence", "equation", "inequality", "polynomial", "matrix", "determinant",
            "eigenvalue", "eigenvector", "vector", "scalar", "tensor", "group", "ring",
            "field", "morphism", "homomorphism", "isomorphism", "category", "functor",
            "graph", "tree", "network", "algorithm", "complexity", "combinatorics"
        },
        "biology": {
            "cell", "organism", "tissue", "organ", "species", "evolution", "genetics",
            "dna", "rna", "protein", "enzyme", "chromosome", "gene", "genome", "mutation",
            "selection", "adaptation", "ecology", "ecosystem", "population", "community",
            "diversity", "symbiosis", "parasite", "host", "predator", "prey", "metabolism",
            "photosynthesis", "respiration", "fermentation", "digestion", "circulation",
            "nervous", "immune", "endocrine", "reproductive", "development", "embryo",
            "fetus", "growth", "differentiation", "homeostasis", "stimulus", "response",
            "behavior", "taxonomy", "phylogeny", "homology", "analogy", "morphology",
            "physiology", "anatomy", "histology", "cytology", "microbiology", "virology"
        },
        "philosophy": {
            "ethics", "morality", "virtue", "justice", "rights", "duty", "deontology",
            "consequentialism", "utilitarianism", "metaethics", "epistemology", "knowledge",
            "belief", "justification", "truth", "skepticism", "empiricism", "rationalism",
            "metaphysics", "ontology", "being", "existence", "essence", "identity", "mind",
            "consciousness", "qualia", "intentionality", "dualism", "materialism", "idealism",
            "phenomenology", "existentialism", "hermeneutics", "logic", "fallacy", "validity",
            "soundness", "induction", "deduction", "abduction", "aesthetics", "beauty",
            "sublime", "representation", "political", "social", "liberty", "equality",
            "authority", "language", "meaning", "reference", "pragmatics", "semantics"
        }
    }
    
    @classmethod
    def extract_keywords(cls, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract significant keywords from text, excluding common stopwords.
        
        Args:
            text: The text to extract keywords from
            max_keywords: Maximum number of keywords to extract
            
        Returns:
            List of extracted keywords
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation and split into words
        words = re.findall(r'\b\w+\b', text)
        
        # Remove stopwords and single-letter words
        filtered_words = [word for word in words if word not in cls.STOPWORDS and len(word) > 1]
        
        # Count word frequencies
        word_counts = Counter(filtered_words)
        
        # Get most common words
        keywords = [word for word, count in word_counts.most_common(max_keywords)]
        
        return keywords
    
    @classmethod
    def extract_domain_specific_terms(cls, text: str, domains: List[str]) -> List[str]:
        """
        Extract domain-specific terms from text.
        
        Args:
            text: The text to extract terms from
            domains: List of domains to extract terms for
            
        Returns:
            List of extracted domain-specific terms
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation and split into words
        words = re.findall(r'\b\w+\b', text)
        
        # Get domain-specific terms for the specified domains
        domain_terms = set()
        for domain in domains:
            if domain in cls.DOMAIN_TERMS:
                domain_terms.update(cls.DOMAIN_TERMS[domain])
        
        # Filter words to only include domain-specific terms
        extracted_terms = [word for word in words if word in domain_terms]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_terms = [term for term in extracted_terms if not (term in seen or seen.add(term))]
        
        return unique_terms
    
    @staticmethod
    def calculate_term_frequency(term: str, text: str) -> float:
        """
        Calculate the term frequency (TF) of a term in text.
        
        Args:
            term: The term to calculate frequency for
            text: The text to analyze
            
        Returns:
            Term frequency (normalized by text length)
        """
        # Convert to lowercase for case-insensitive matching
        text_lower = text.lower()
        term_lower = term.lower()
        
        # Count occurrences of the term
        term_count = text_lower.count(term_lower)
        
        # Get total word count
        words = re.findall(r'\b\w+\b', text_lower)
        total_words = len(words)
        
        # Calculate term frequency (normalized)
        return term_count / max(1, total_words)
    
    @staticmethod
    def calculate_inverse_document_frequency(term: str, documents: List[str]) -> float:
        """
        Calculate the inverse document frequency (IDF) of a term across documents.
        
        Args:
            term: The term to calculate IDF for
            documents: List of documents to analyze
            
        Returns:
            Inverse document frequency
        """
        # Convert to lowercase for case-insensitive matching
        term_lower = term.lower()
        
        # Count documents containing the term
        term_docs = sum(1 for doc in documents if term_lower in doc.lower())
        
        # Calculate IDF (with smoothing to avoid division by zero)
        return math.log((1 + len(documents)) / (1 + term_docs)) + 1
    
    @classmethod
    def calculate_tfidf_scores(cls, query_terms: List[str], text: str, corpus: List[str]) -> Dict[str, float]:
        """
        Calculate TF-IDF scores for query terms in a text.
        
        Args:
            query_terms: List of query terms
            text: The text to analyze
            corpus: Corpus of documents for IDF calculation
            
        Returns:
            Dictionary of terms with their TF-IDF scores
        """
        scores = {}
        
        for term in query_terms:
            tf = cls.calculate_term_frequency(term, text)
            idf = cls.calculate_inverse_document_frequency(term, corpus)
            scores[term] = tf * idf
        
        return scores
    
    @classmethod
    def calculate_content_similarity(cls, content: str, paper: Dict[str, Any]) -> float:
        """
        Calculate similarity score between content and a paper.
        
        Args:
            content: The content text
            paper: Paper metadata dictionary
            
        Returns:
            Similarity score (0.0-1.0)
        """
        # Extract text fields from paper
        paper_title = paper.get('title', '')
        paper_summary = paper.get('summary', '')
        paper_text = f"{paper_title} {paper_summary}"
        
        # Extract keywords from content and paper
        content_keywords = cls.extract_keywords(content, max_keywords=15)
        paper_keywords = cls.extract_keywords(paper_text, max_keywords=15)
        
        # Calculate direct match score
        direct_matches = sum(1 for keyword in content_keywords if keyword in paper_text.lower())
        direct_score = direct_matches / max(1, len(content_keywords))
        
        # Calculate keyword overlap score
        common_keywords = set(content_keywords) & set(paper_keywords)
        overlap_score = len(common_keywords) / max(1, len(set(content_keywords + paper_keywords)))
        
        # Combine scores (direct matches are weighted more)
        final_score = (direct_score * 0.7) + (overlap_score * 0.3)
        
        return min(1.0, final_score)
    
    @classmethod
    def rank_papers_by_relevance(cls, content: str, papers: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], float]]:
        """
        Rank papers by relevance to content.
        
        Args:
            content: The content text
            papers: List of paper metadata dictionaries
            
        Returns:
            List of (paper, score) tuples, sorted by descending score
        """
        # Calculate similarity scores
        scored_papers = [(paper, cls.calculate_content_similarity(content, paper)) for paper in papers]
        
        # Sort by score (descending)
        sorted_papers = sorted(scored_papers, key=lambda x: x[1], reverse=True)
        
        return sorted_papers
    
    @classmethod
    def filter_papers_by_relevance(cls, content: str, papers: List[Dict[str, Any]], threshold: float = 0.1) -> List[Dict[str, Any]]:
        """
        Filter papers by relevance score.
        
        Args:
            content: The content text
            papers: List of paper metadata dictionaries
            threshold: Minimum relevance score (0.0-1.0)
            
        Returns:
            List of papers with relevance score >= threshold
        """
        # Rank papers by relevance
        ranked_papers = cls.rank_papers_by_relevance(content, papers)
        
        # Filter by threshold
        filtered_papers = [paper for paper, score in ranked_papers if score >= threshold]
        
        return filtered_papers
