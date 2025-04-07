# src/critique_module/output_formatter.py

"""
Component responsible for formatting the final critique output into Markdown,
including summaries and detailed agent trees.
"""

import logging
import datetime
import json
import os # <<<< ADDED IMPORT
from typing import Dict, List, Any, Optional

# Import LLM client for Judge summary
from .providers import gemini_client # Assuming sync version

# Get logger for this module
logger = logging.getLogger(__name__)

# --- Helper function to format critique tree recursively ---
def format_critique_node(node: Optional[Dict[str, Any]], depth: int = 0) -> List[str]:
    """Recursively formats a critique node and its children into Markdown lines."""
    lines = []
    if not node or not isinstance(node, dict):
        return lines

    indent = "  " * depth
    claim = node.get('claim', 'N/A')
    severity = node.get('severity', 'N/A')
    confidence = node.get('confidence', 0.0) # Use adjusted confidence
    evidence = node.get('evidence')
    arbitration = node.get('arbitration') # Get arbiter comment
    sub_critiques = node.get('sub_critiques', [])

    # Format current node
    lines.append(f"{indent}- **Claim:** {claim}")
    lines.append(f"{indent}  - **Severity:** {severity}")
    lines.append(f"{indent}  - **Confidence (Adjusted):** {confidence:.0%}")
    if evidence:
        evidence_lines = evidence.strip().split('\n')
        lines.append(f"{indent}  - **Evidence:**")
        for line in evidence_lines:
            lines.append(f"{indent}    > {line}")
    if arbitration:
        lines.append(f"{indent}  - **Expert Arbitration:** {arbitration}")

    # Recursively format children
    if sub_critiques:
        lines.append(f"{indent}  - **Sub-Critiques:**")
        for sub_node in sub_critiques:
            lines.extend(format_critique_node(sub_node, depth + 1))

    return lines
# ---------------------------------------------------------

# --- Helper function to generate Judge summary ---
def generate_judge_summary(original_content: str, adjusted_trees: List[Dict[str, Any]], arbiter_adjustments: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
    """Calls LLM with Judge prompt to generate overall summary."""
    judge_logger = logging.getLogger('JudgeSummary') # Use a specific logger name
    judge_logger.info("Attempting to generate Judge Summary...")
    try:
        # Load Judge prompt
        # Construct path relative to this file's directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(base_dir, '..', 'prompts', 'judge_summary.txt')
        judge_logger.debug(f"Loading Judge prompt from: {prompt_path}")
        with open(prompt_path, 'r', encoding='utf-8') as f:
            judge_prompt_template = f.read()

        # Prepare context
        context = {
            "original_content": original_content,
            "adjusted_critique_trees_json": json.dumps(adjusted_trees, indent=2),
            "arbitration_adjustments_json": json.dumps(arbiter_adjustments, indent=2)
        }

        # Call LLM (synchronously)
        summary_text, model_used = gemini_client.call_gemini_with_retry(
            prompt_template=judge_prompt_template,
            context=context,
            config=config,
            is_structured=False # Expecting Markdown text block
        )
        judge_logger.info(f"Judge Summary generated successfully using {model_used}.")
        return summary_text.strip()

    except FileNotFoundError:
        error_msg = f"Judge summary prompt file not found at {prompt_path}"
        judge_logger.error(error_msg)
        return f"Error: {error_msg}"
    except Exception as e:
        error_msg = f"Failed to generate Judge summary: {e}"
        judge_logger.error(error_msg, exc_info=True) # Log full traceback for unexpected errors
        return f"Error generating Judge summary: {e}"
# --------------------------------------------------


def format_critique_output(critique_data: Dict[str, Any], original_content: str, config: Dict[str, Any]) -> str:
    """
    Formats the synthesized critique data into a detailed Markdown report string.
    """
    output_lines = []
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    output_lines.append(f"# Critique Assessment Report")
    output_lines.append(f"**Generated:** {now}")
    output_lines.append("---")

    # --- Judge Summary ---
    output_lines.append("## Overall Judge Summary")
    judge_summary = generate_judge_summary(
        original_content,
        critique_data.get('adjusted_critique_trees', []),
        critique_data.get('arbitration_adjustments', []),
        config
    )
    output_lines.append(judge_summary)
    output_lines.append("")
    output_lines.append("---")


    # --- Scoring Summary ---
    metrics = critique_data.get('score_metrics', {})
    score = metrics.get('overall_score', 'N/A')
    high_sev = metrics.get('high_severity_points', 0)
    med_sev = metrics.get('medium_severity_points', 0)
    low_sev = metrics.get('low_severity_points', 0)

    output_lines.append("## Overall Score & Metrics")
    output_lines.append(f"- **Overall Score:** {score}/100")
    output_lines.append(f"- **High/Critical Severity Points:** {high_sev}")
    output_lines.append(f"- **Medium Severity Points:** {med_sev}")
    output_lines.append(f"- **Low Severity Points:** {low_sev}")
    output_lines.append("")
    output_lines.append("---")

    # --- Arbiter Summary ---
    output_lines.append("## Expert Arbiter Summary")
    arbiter_adjustments = critique_data.get('arbitration_adjustments', [])
    if arbiter_adjustments:
        output_lines.append(f"The Expert Arbiter reviewed the philosophical critiques and provided {len(arbiter_adjustments)} specific comments/adjustments:")
        for i, adj in enumerate(arbiter_adjustments):
            target_id = adj.get('target_claim_id', 'N/A')
            comment = adj.get('arbitration_comment', 'N/A')
            delta = adj.get('confidence_delta', 0.0)
            output_lines.append(f"{i+1}. **Target Claim ID:** `{target_id}`")
            output_lines.append(f"   - **Comment:** {comment}")
            output_lines.append(f"   - **Confidence Delta:** {delta:+.2f}")
    else:
        output_lines.append("The Expert Arbiter provided no specific adjustments.")
    output_lines.append("")
    output_lines.append("---")


    # --- Detailed Agent Critiques ---
    output_lines.append("## Detailed Agent Critiques")
    adjusted_trees = critique_data.get('adjusted_critique_trees', [])
    if not adjusted_trees:
         output_lines.append("No critique data available.")
    else:
        for agent_critique in adjusted_trees:
            agent_style = agent_critique.get('agent_style', 'Unknown Agent')
            output_lines.append(f"### Agent: {agent_style}")
            if 'error' in agent_critique:
                output_lines.append(f"- **Error during critique:** {agent_critique['error']}")
            elif 'critique_tree' in agent_critique and agent_critique['critique_tree']:
                tree_lines = format_critique_node(agent_critique['critique_tree'], depth=0)
                output_lines.extend(tree_lines)
            else:
                output_lines.append("- No valid critique tree generated.")
            output_lines.append("")
            output_lines.append("---")


    output_lines.append("\n--- End of Report ---")
    return "\n".join(output_lines)

# Example usage - Needs update if run directly
if __name__ == '__main__':
    print("NOTE: Direct execution of output_formatter.py example is limited.")
    pass
