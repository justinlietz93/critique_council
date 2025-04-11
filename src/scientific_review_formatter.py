# src/scientific_review_formatter.py

"""
Module for formatting critique results into a formal scientific peer review format.
This is used when the --PR (peer review) flag is active to transform the normal
critique output into a standard scientific peer review document.
"""

import logging
import json
from typing import Dict, Any, Optional

# Import provider factory for LLM clients
from .providers import call_with_retry

logger = logging.getLogger(__name__)

def format_scientific_peer_review(
    original_content: str,
    critique_report: str,
    config: Dict[str, Any]
) -> str:
    """
    Formats the critique report into a formal scientific peer review document.
    
    Args:
        original_content: The original content that was critiqued
        critique_report: The generated critique report from the council
        config: Configuration dictionary
        
    Returns:
        A formatted scientific peer review document
    """
    logger.info("Formatting critique into formal scientific peer review document...")
    
    system_message = """
    You are an expert academic peer reviewer responsible for transforming a critique report into a formal 
    scientific peer review document. Follow these peer review best practices:
    
    1. Structure the review with these sections:
       - Brief summary of the entire manuscript (1-2 paragraphs)
       - Clear recommendation (accept, reject, or revise)
       - Major concerns (internal inconsistencies, missing data, methodological issues)
       - Minor concerns (grammar, typos, references, clarity issues)
    
    2. Maintain a professional, constructive tone throughout
    
    3. Number each concern and organize them in order of appearance in the manuscript
    
    4. For each concern, cite specific page/paragraph/section numbers when possible
    
    5. Suggest specific improvements for each concern identified
    
    6. Keep recommendations reasonable and within the scope of the original work
    
    Your review should be 1-2 pages long when printed, comprehensive yet concise.
    """
    
    # Format the OpenAI prompt
    prompt = f"""
    Your task is to transform a philosophical critique report into a formal scientific peer review document.

    You have access to:
    1. The ORIGINAL CONTENT that was analyzed
    2. A CRITIQUE REPORT produced by a council of philosophical critics
    
    Create a formal peer review following scientific publishing standards. 
    Present yourself as a domain expert with credentials relevant to the content.
    Focus on methodology, evidence, logic, scientific accuracy, and scholarly merit.
    
    The beginning of your review MUST include:
    1. Your full academic name and credentials (e.g., "Dr. Jonathan Smith, Ph.D.")
    2. Your institutional affiliation
    3. Your area of expertise
    
    Structure the review following standard academic peer review format:
    1. Brief summary of the work (1-2 paragraphs)
    2. Clear recommendation (accept/reject/revise)
    3. Major concerns (numbered)
    4. Minor concerns (numbered)
    5. Conclusion
    
    # ORIGINAL CONTENT:
    {original_content}
    
    # CRITIQUE REPORT:
    {critique_report}
    """
    
    try:
        # Create a new config that forces OpenAI to be the provider
        # This ensures we use OpenAI for this specific formatting task which is better suited for it
        formatter_config = {
            "api": {
                **config.get("api", {}),
                "primary_provider": "openai"  # Force OpenAI for scientific formatting
            }
        }
        
        # Make sure we have formatting-specific settings for OpenAI
        if "openai" not in formatter_config["api"]:
            # If no OpenAI config, try to use nested providers structure
            if "providers" in formatter_config["api"] and "openai" in formatter_config["api"]["providers"]:
                formatter_config["api"]["openai"] = formatter_config["api"]["providers"]["openai"]
                
        # Attempt to set system message in OpenAI config
        if "openai" in formatter_config["api"]:
            formatter_config["api"]["openai"]["system_message"] = system_message
            
            # Get max tokens from config if available and set in OpenAI config
            max_tokens = config.get("api", {}).get("openai", {}).get("max_tokens")
            if max_tokens:
                formatter_config["api"]["openai"]["max_tokens"] = max_tokens
        
        # Call provider factory with OpenAI set as primary provider
        review_content, model_used = call_with_retry(
            prompt_template=prompt,
            context={},  # Context is already embedded in the prompt template
            config=formatter_config,
            is_structured=False
        )
        
        logger.info(f"Scientific peer review formatting completed using {model_used}")
        
        # Add a metadata header to the document
        review_with_header = f"""# Scientific Peer Review Report
Generated using the Critique Council PR module

---

{review_content}

---
End of Peer Review
"""
        
        return review_with_header
        
    except Exception as e:
        logger.error(f"Failed to format scientific peer review: {e}", exc_info=True)
        return f"""# ERROR: Scientific Peer Review Formatting Failed

The system encountered an error while attempting to format the critique as a scientific peer review:

{str(e)}

The original critique report is still available.
"""
