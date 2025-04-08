# src/critique_module/reasoning_tree.py

"""
Implements the recursive reasoning tree logic for critique generation.
"""

import logging
from typing import Dict, List, Any, Optional
import uuid
import json

# Import the Gemini client function
from .providers import gemini_client

# Default configuration values
DEFAULT_MAX_DEPTH = 3
DEFAULT_CONFIDENCE_THRESHOLD = 0.3

module_logger = logging.getLogger(__name__)

# Synchronous version
def execute_reasoning_tree(
    initial_content: str,
    style_directives: str,
    agent_style: str,
    config: Dict[str, Any],
    agent_logger: Optional[logging.Logger] = None,
    depth: int = 0
) -> Optional[Dict[str, Any]]:
    """
    Recursively generates a critique tree synchronously.
    """
    current_logger = agent_logger or module_logger
    current_logger.info(f"Depth {depth}: Starting analysis...")

    tree_config = config.get('reasoning_tree', {})
    max_depth = tree_config.get('max_depth', DEFAULT_MAX_DEPTH)
    confidence_threshold = tree_config.get('confidence_threshold', DEFAULT_CONFIDENCE_THRESHOLD)

    # 1. Base Case Check
    if depth >= max_depth:
        current_logger.info(f"Depth {depth}: Terminating branch (Reason: Max Depth Reached [{max_depth}])")
        return None
    if len(initial_content) < 50:
         current_logger.info(f"Depth {depth}: Terminating branch (Reason: Content too small)")
         return None

    # --- LLM Integration ---
    node_id = str(uuid.uuid4())
    claim = f"Error generating claim at depth {depth}."
    evidence = "N/A"
    confidence = 0.0
    severity = "N/A"
    recommendation = "N/A"
    concession = "N/A" # Initialize concession field
    sub_topics_for_recursion = []
    model_used_for_assessment = "N/A"
    model_used_for_decomposition = "N/A"

    # 2. Generate Assessment (Synchronous Call)
    # Use the prompt loaded by the agent, which now includes concession request
    assessment_prompt_template = style_directives # Use the full prompt content directly
    assessment_context = {
        # Context needed by the prompt template placeholders
        "context": "Critiquing provided steps.", # Generic context if not passed separately
        "goal": config.get("goal", "N/A"), # Pass goal if available in config
        "steps": initial_content # Pass the current content segment as 'steps'
    }
    try:
        assessment_result, model_used_for_assessment = gemini_client.call_gemini_with_retry(
            prompt_template=assessment_prompt_template,
            context=assessment_context,
            config=config,
            is_structured=True # Expecting JSON output
        )
        # Expect recommendation and concession fields now
        if isinstance(assessment_result, dict) and all(k in assessment_result for k in ["claim", "confidence", "severity", "recommendation", "concession"]):
            claim = assessment_result.get("claim", claim)
            evidence = assessment_result.get("evidence", evidence)
            confidence = float(assessment_result.get("confidence", 0.0))
            severity = assessment_result.get("severity", severity)
            recommendation = assessment_result.get("recommendation", recommendation)
            concession = assessment_result.get("concession", concession) # Extract concession
        else:
             current_logger.warning(f"Depth {depth}: Unexpected assessment structure received from {model_used_for_assessment}: {assessment_result}")
             pass

    except (gemini_client.ApiCallError, gemini_client.ApiResponseError, gemini_client.JsonParsingError, gemini_client.JsonProcessingError) as e:
        current_logger.error(f"Depth {depth}: Failed to generate assessment: {e}")
        confidence = 0.0
    except Exception as e:
        current_logger.error(f"Depth {depth}: Unexpected error during assessment: {e}", exc_info=True)
        confidence = 0.0

    current_logger.info(f"Depth {depth}: [Model: {model_used_for_assessment}] Claim='{claim}', Confidence={confidence:.2f}, Severity='{severity}'")
    if evidence != "N/A" and evidence: current_logger.debug(f"Depth {depth}: Evidence='{evidence}'")
    if recommendation != "N/A" and recommendation: current_logger.debug(f"Depth {depth}: Recommendation='{recommendation}'")
    if concession != "N/A" and concession and concession.lower() != "none": current_logger.debug(f"Depth {depth}: Concession='{concession}'") # Log concession if not "None"

    if confidence < confidence_threshold:
        current_logger.info(f"Depth {depth}: Terminating branch (Reason: Confidence {confidence:.2f} < Threshold {confidence_threshold})")
        return None

    # 3. Decomposition Identification (Synchronous Call)
    # (Decomposition logic remains the same, uses a separate prompt)
    decomposition_prompt_template = """
Based on the primary critique claim "{claim}", identify specific sub-topics, sub-arguments, or distinct sections within the following content segment that warrant deeper, more focused critique in the next level of analysis.

Style Directives (for context):
{style_directives}

Content Segment:
```
{content}
```

Return ONLY a JSON list of strings, where each string is a concise description of a sub-topic to analyze further. If no further decomposition is necessary or possible, return an empty list []. Example:
["The definition of 'synergy' in paragraph 2", "The causality argument in section 3.1", "The empirical evidence cited for claim X"]
"""
    decomposition_context = {
        "claim": claim,
        "style_directives": style_directives, # Pass original style directives for context
        "content": initial_content
    }
    try:
        decomposition_result, model_used_for_decomposition = gemini_client.call_gemini_with_retry(
            prompt_template=decomposition_prompt_template,
            context=decomposition_context,
            config=config,
            is_structured=True
        )
        if isinstance(decomposition_result, list) and all(isinstance(item, str) for item in decomposition_result):
            sub_topics_for_recursion = decomposition_result
            current_logger.info(f"Depth {depth}: [Model: {model_used_for_decomposition}] Identified {len(sub_topics_for_recursion)} sub-topics for recursion.")
        else:
            current_logger.warning(f"Depth {depth}: Unexpected decomposition structure received from {model_used_for_decomposition}: {decomposition_result}")
            pass

    except (gemini_client.ApiCallError, gemini_client.ApiResponseError, gemini_client.JsonParsingError, gemini_client.JsonProcessingError) as e:
        current_logger.error(f"Depth {depth}: Failed to identify decomposition points: {e}")
    except Exception as e:
        current_logger.error(f"Depth {depth}: Unexpected error during decomposition: {e}")


    # 4. Recursive Calls (Synchronous)
    sub_critiques = []
    if sub_topics_for_recursion:
        current_logger.debug(f"Depth {depth}: Using placeholder content division for recursion based on {len(sub_topics_for_recursion)} identified topics.")
        num_sub_points = len(sub_topics_for_recursion)
        segment_len = len(initial_content) // num_sub_points if num_sub_points > 0 else len(initial_content)

        for i, sub_topic in enumerate(sub_topics_for_recursion):
            sub_content = initial_content[i * segment_len : (i + 1) * segment_len]
            current_logger.info(f"Depth {depth}: Recursing on sub-topic {i+1} ('{sub_topic}')...")
            child_node = execute_reasoning_tree(
                initial_content=sub_content,
                style_directives=style_directives,
                agent_style=agent_style,
                config=config,
                agent_logger=current_logger,
                depth=depth + 1
            )
            if child_node:
                sub_critiques.append(child_node)

    # 5. Node Construction
    current_node = {
        'id': node_id,
        'claim': claim,
        'evidence': evidence,
        'confidence': confidence,
        'severity': severity,
        'recommendation': recommendation,
        'concession': concession, # Add concession to node
        'sub_critiques': sub_critiques
    }

    current_logger.info(f"Depth {depth}: Analysis complete for this level.")
    return current_node

# --- Example Usage ---
def run_example():
    print("NOTE: Reasoning tree example usage needs update for new recommendation/concession fields.")
    pass

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_example()
