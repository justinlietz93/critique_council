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

# Default configuration values (used if not found in passed config)
DEFAULT_MAX_DEPTH = 3
DEFAULT_CONFIDENCE_THRESHOLD = 0.3

# Get a logger for this module (used if no agent-specific logger is provided)
module_logger = logging.getLogger(__name__)

async def execute_reasoning_tree(
    initial_content: str,
    style_directives: str,
    agent_style: str,
    config: Dict[str, Any],
    agent_logger: Optional[logging.Logger] = None, # Add logger param
    depth: int = 0
) -> Optional[Dict[str, Any]]:
    """
    Recursively generates a critique tree based on prompts and content using Gemini.

    Args:
        initial_content: The content being analyzed at this level.
        style_directives: Instructions defining the agent's reasoning style.
        agent_style: The style name of the calling agent.
        config: Application configuration.
        agent_logger: Optional dedicated logger for this agent's run.
        depth: Current recursion depth.

    Returns:
        A dictionary representing the critique (sub)tree, or None if terminated early.
    """
    current_logger = agent_logger or module_logger # Use specific logger if provided
    current_logger.info(f"Depth {depth}: Starting analysis...")

    # --- Get settings from config ---
    tree_config = config.get('reasoning_tree', {})
    max_depth = tree_config.get('max_depth', DEFAULT_MAX_DEPTH)
    confidence_threshold = tree_config.get('confidence_threshold', DEFAULT_CONFIDENCE_THRESHOLD)
    # -----------------------------

    # 1. Base Case Check
    if depth >= max_depth:
        current_logger.info(f"Depth {depth}: Terminating branch (Reason: Max Depth Reached [{max_depth}])")
        return None
    if len(initial_content) < 50:
         current_logger.info(f"Depth {depth}: Terminating branch (Reason: Content too small)")
         return None

    # --- Gemini Integration ---
    node_id = str(uuid.uuid4())
    claim = f"Error generating claim at depth {depth}."
    evidence = "N/A"
    confidence = 0.0
    severity = "N/A"
    sub_topics_for_recursion = []
    model_used_for_assessment = "N/A"
    model_used_for_decomposition = "N/A"

    # 2. Generate Assessment using Gemini
    assessment_prompt_template = """
Critique the following content segment based on the principles of {style_name}.
Focus on identifying a single, primary claim or critique point at this level of analysis.
Provide supporting evidence or reasoning. Estimate your confidence (0.0-1.0) and the severity ('Low', 'Medium', 'High', 'Critical').

Style Directives:
{style_directives}

Content Segment:
```
{content}
```

Return ONLY a JSON object with the keys "claim", "evidence", "confidence", "severity". Example:
{{
  "claim": "The argument lacks sufficient empirical grounding.",
  "evidence": "Lines 15-20 make assertions without citing sources.",
  "confidence": 0.75,
  "severity": "Medium"
}}
"""
    assessment_context = {
        "style_name": agent_style,
        "style_directives": style_directives,
        "content": initial_content
    }
    try:
        # current_logger.debug(f"Depth {depth}: Generating assessment...") # Removed debug log
        assessment_result, model_used_for_assessment = await gemini_client.call_gemini_with_retry(
            prompt_template=assessment_prompt_template,
            context=assessment_context,
            config=config,
            is_structured=True
        )
        if isinstance(assessment_result, dict) and all(k in assessment_result for k in ["claim", "confidence"]):
            claim = assessment_result.get("claim", claim)
            evidence = assessment_result.get("evidence", evidence)
            confidence = float(assessment_result.get("confidence", 0.0))
            severity = assessment_result.get("severity", severity)
            # current_logger.debug(f"Depth {depth}: Assessment generated (Conf: {confidence:.2f}). Claim: {claim[:80]}...") # Removed debug log
        else:
             # Log warning to agent log if structure is wrong
             current_logger.warning(f"Depth {depth}: Unexpected assessment structure received from {model_used_for_assessment}: {assessment_result}")
             pass

    except (gemini_client.ApiCallError, gemini_client.ApiResponseError, gemini_client.JsonParsingError, gemini_client.JsonProcessingError) as e:
        # Log only the failure reason to agent log, root logger captures full error
        current_logger.error(f"Depth {depth}: Failed to generate assessment: {e}")
        confidence = 0.0
    except Exception as e:
        # Log only the failure reason to agent log
        current_logger.error(f"Depth {depth}: Unexpected error during assessment: {e}")
        confidence = 0.0

    # Log the generated claim details including the model used
    current_logger.info(f"Depth {depth}: [Model: {model_used_for_assessment}] Claim='{claim}', Confidence={confidence:.2f}, Severity='{severity}'")
    if evidence != "N/A" and evidence:
         current_logger.debug(f"Depth {depth}: Evidence='{evidence}'") # Keep evidence as debug


    # Terminate branch if confidence is too low
    if confidence < confidence_threshold:
        current_logger.info(f"Depth {depth}: Terminating branch (Reason: Confidence {confidence:.2f} < Threshold {confidence_threshold})")
        return None

    # 3. Decomposition Identification using Gemini (only if confidence is sufficient)
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
        "style_directives": style_directives,
        "content": initial_content
    }
    try:
        # current_logger.debug(f"Depth {depth}: Identifying decomposition points...") # Removed debug log
        decomposition_result, model_used_for_decomposition = await gemini_client.call_gemini_with_retry(
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


    # 4. Recursive Calls
    sub_critiques = []
    if sub_topics_for_recursion:
        # current_logger.debug(f"Depth {depth}: Using placeholder content division for recursion based on {len(sub_topics_for_recursion)} identified topics.") # Removed debug log
        num_sub_points = len(sub_topics_for_recursion)
        segment_len = len(initial_content) // num_sub_points if num_sub_points > 0 else len(initial_content)

        for i, sub_topic in enumerate(sub_topics_for_recursion):
            sub_content = initial_content[i * segment_len : (i + 1) * segment_len]
            current_logger.info(f"Depth {depth}: Recursing on sub-topic {i+1} ('{sub_topic}')...")
            # Pass the same agent_logger down for the recursive call
            child_node = await execute_reasoning_tree(
                initial_content=sub_content,
                style_directives=style_directives,
                agent_style=agent_style,
                config=config,
                agent_logger=current_logger, # Pass logger down
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
        'sub_critiques': sub_critiques
        # Optionally add model_used_for_assessment here if needed downstream
    }

    current_logger.info(f"Depth {depth}: Analysis complete for this level.")
    return current_node

# --- Async Wrapper for Example Usage ---
# (Example usage remains unchanged)
async def run_example():
    dummy_content = "This is the main document content. " * 20 + \
                    "It contains several sections. Section one discusses apples. " * 10 + \
                    "Section two discusses oranges, which are different from apples. " * 10 + \
                    "Finally, section three compares them. " * 5
    dummy_directives = "Be very critical."
    dummy_style = "Tester"
    dummy_config = {
        'api': {'gemini': {'retries': 1}}, # Adjusted dummy config structure
        'reasoning_tree': {},
        'council_orchestrator': {}
    }

    print("\n--- Running Reasoning Tree Example ---")
    try:
        from unittest.mock import patch
    except ImportError:
        print("unittest.mock not found, skipping example patching.")
        return

    # Patch needs to target the updated function signature returning a tuple
    with patch('src.providers.gemini_client.call_gemini_with_retry') as mock_gemini:
        call_count = 0
        def gemini_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            prompt = kwargs.get('prompt_template', '')
            context = kwargs.get('context', {})
            agent = context.get('style_name', 'Unknown')
            model_name = "Gemini: MockModel" # Mock model name

            if "Return ONLY a JSON object" in prompt: # Assessment call
                result = {
                    "claim": f"Mock claim by {agent} at call {call_count}.",
                    "evidence": "Mock evidence.",
                    "confidence": 0.7,
                    "severity": "Medium"
                }
                return result, model_name
            elif "Return ONLY a JSON list" in prompt: # Decomposition call
                 result = ["Sub-topic 1", "Sub-topic 2"] if call_count < 4 else []
                 return result, model_name
            else:
                return {}, model_name

        mock_gemini.side_effect = gemini_side_effect

        critique_result = await execute_reasoning_tree(
            dummy_content, dummy_directives, dummy_style, dummy_config
        )
        print("\n--- Reasoning Tree Result ---")
        import json
        print(json.dumps(critique_result, indent=2))
        print("--- End Reasoning Tree Example ---")


if __name__ == '__main__':
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_example())
