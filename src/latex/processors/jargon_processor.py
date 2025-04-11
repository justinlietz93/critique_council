"""
Processor for replacing philosophical jargon with scientific terminology.

This module provides a processor that transforms philosophical jargon and subjective
language into more objective, scientific terminology.
"""

import re
from typing import Dict, Any, Optional, List, Tuple, Pattern
from .content_processor import ContentProcessor


class JargonProcessor(ContentProcessor):
    """
    Processor that replaces philosophical jargon with scientific terminology.
    
    This processor identifies philosophical terms, subjective language, and
    philosopher-specific vocabulary, replacing them with more objective, 
    scientific equivalents to increase the document's scientific rigor.
    """
    
    # Dictionary of philosophical terms mapped to scientific equivalents
    JARGON_REPLACEMENTS = {
        # Philosophical terms to scientific equivalents
        r"\b(?:teleology|telos|final cause)\b": "functional outcome",
        r"\bfinal cause\b": "mechanistic outcome",
        r"\bformal cause\b": "structural properties",
        r"\bmaterial cause\b": "physical composition",
        r"\befficient cause\b": "causal mechanism",
        r"\bnoumen(?:a|on)\b": "unobservable entity",
        r"\bphenomen(?:a|on)\b": "observable entity",
        r"\ba priori\b": "deductively reasoned",
        r"\ba posteriori\b": "empirically derived",
        r"\beudaimonia\b": "optimal functioning",
        r"\bsufficient reason\b": "causal explanation",
        r"\bCartesian doubt\b": "methodological skepticism",
        r"\btranscendental\b": "foundational",
        r"\bontology\b": "existence theory",
        r"\bepistemology\b": "knowledge theory",
        r"\bsynthetic a priori\b": "non-empirical knowledge claim",
        r"\bphronesis\b": "practical reasoning",
        r"\bteological\b": "function-oriented",
        r"\baxiology\b": "value theory",
        r"\bapodeictic\b": "necessarily true",
        
        # Philosophical perspectives to scientific approaches
        r"\bAristotelian perspective\b": "functional systems analysis",
        r"\bAristotelian analysis\b": "functional systems analysis",
        r"\bCartesian (?:perspective|approach)\b": "methodological analysis",
        r"\bCartesian analysis\b": "methodological analysis",
        r"\bKantian (?:perspective|approach)\b": "transcendental analysis",
        r"\bKantian analysis\b": "boundary condition analysis",
        r"\bLeibnizian (?:perspective|approach)\b": "explanatory analysis",
        r"\bLeibnizian analysis\b": "causal sufficiency analysis",
        r"\bPopperian (?:perspective|approach)\b": "falsification analysis",
        r"\bPopperian analysis\b": "falsifiability analysis",
        r"\bRussellian (?:perspective|approach)\b": "logical-analytical approach",
        r"\bRussellian analysis\b": "logical structure analysis",
        
        # Philosopher names to analytical approaches
        r"\bAristotle would\b": "Functional analysis would",
        r"\bDescartes would\b": "Methodological skepticism would",
        r"\bKant would\b": "Boundary condition analysis would",
        r"\bLeibniz would\b": "Causal sufficiency analysis would",
        r"\bPopper would\b": "Falsifiability testing would",
        r"\bRussell would\b": "Logical structure analysis would",
        
        # Subjective language to objective terminology
        r"\bI believe\b": "evidence suggests",
        r"\bI think\b": "analysis indicates",
        r"\bin my view\b": "based on the evidence",
        r"\bin my opinion\b": "analytical assessment suggests",
    }
    
    # Patterns for replacing first-person language with third-person scientific voice
    PERSPECTIVE_REPLACEMENTS = [
        # First-person perspective to third-person scientific voice
        (r"I am Dr\. ([^,]+), Ph\.D\. in ([^,]+)", r"The following analysis is presented from the perspective of \1, Ph.D. in \2"),
        (r"I have found that", "Analysis demonstrates that"),
        (r"I observe that", "Observation indicates that"),
        (r"I recommend", "Recommended approach:"),
        (r"I note that", "It is noteworthy that"),
    ]
    
    # Section title replacements
    SECTION_REPLACEMENTS = {
        r"Aristotelian Analysis": "Functional Systems Analysis",
        r"Cartesian Analysis": "Methodological Analysis",
        r"Kantian Analysis": "Boundary Condition Analysis",
        r"Leibnizian Analysis": "Causal Sufficiency Analysis",
        r"Popperian Analysis": "Falsifiability Analysis",
        r"Russellian Analysis": "Logical Structure Analysis",
        r"Perspective-Specific Contributions": "Methodological Analysis Frameworks"
    }
    
    def __init__(self, objectivity_level: str = "high"):
        """
        Initialize the JargonProcessor.
        
        Args:
            objectivity_level: Level of scientific objectivity to apply.
                              Options: "low", "medium", "high"
        """
        self._objectivity_level = objectivity_level
        self._compiled_patterns = self._compile_patterns()
        self._compiled_perspective_patterns = [(re.compile(pattern, re.IGNORECASE), replacement) 
                                             for pattern, replacement in self.PERSPECTIVE_REPLACEMENTS]
        self._compiled_section_patterns = {re.compile(pattern, re.IGNORECASE): replacement 
                                         for pattern, replacement in self.SECTION_REPLACEMENTS.items()}
    
    def _compile_patterns(self) -> Dict[Pattern, str]:
        """
        Compile regex patterns for jargon replacement.
        
        Returns:
            Dictionary of compiled patterns to replacement strings.
        """
        patterns = {}
        
        # Only include a subset of replacements for lower objectivity levels
        if self._objectivity_level == "low":
            # Just replace the most obvious philosophical jargon
            subset = {k: v for k, v in self.JARGON_REPLACEMENTS.items() 
                     if any(term in k for term in ["teleology", "noumena", "synthetic", "efficient cause"])}
        elif self._objectivity_level == "medium":
            # Replace philosophical jargon and some perspective language
            subset = {k: v for k, v in self.JARGON_REPLACEMENTS.items() 
                     if "would" not in k and "I " not in k}
        else:
            # High objectivity - use all replacements
            subset = self.JARGON_REPLACEMENTS
            
        # Compile all the patterns
        for pattern, replacement in subset.items():
            patterns[re.compile(pattern, re.IGNORECASE)] = replacement
            
        return patterns
    
    def process(self, content: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process the input content by replacing philosophical jargon with scientific terminology.
        
        Args:
            content: The input content to process.
            context: Optional dictionary providing additional context or settings.
            
        Returns:
            The processed content with philosophical jargon replaced.
        """
        processed_content = content
        
        # Override objectivity level if provided in context
        objectivity_level = context.get("scientific_objectivity_level", self._objectivity_level) if context else self._objectivity_level
        
        # Replace section titles
        for pattern, replacement in self._compiled_section_patterns.items():
            processed_content = pattern.sub(replacement, processed_content)
        
        # Replace jargon with scientific terminology
        for pattern, replacement in self._compiled_patterns.items():
            processed_content = pattern.sub(replacement, processed_content)
            
        # Replace first-person perspective with third-person scientific voice
        if objectivity_level in ["medium", "high"]:
            for pattern, replacement in self._compiled_perspective_patterns:
                processed_content = pattern.sub(replacement, processed_content)
        
        return processed_content
    
    @property
    def name(self) -> str:
        """
        Get the name of the processor.
        
        Returns:
            The processor name.
        """
        return "jargon_processor"
    
    @property
    def description(self) -> str:
        """
        Get a description of what the processor does.
        
        Returns:
            The processor description.
        """
        return "Replaces philosophical jargon with scientific terminology"
