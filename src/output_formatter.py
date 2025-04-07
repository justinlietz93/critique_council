# src/critique_module/output_formatter.py

"""
Component responsible for formatting the final critique output into Markdown,
including summaries, scores, and detailed agent trees.
"""

import logging
import datetime
import json
import os
from typing import Dict, List, Any, Optional, Tuple

# Import LLM client for Judge summary
from .providers import gemini_client # Assuming sync version

logger = logging.getLogger(__name__)

# --- Helper function to format critique tree recursively ---
def format_critique_node(node: Optional[Dict[str, Any]], depth: int = 0) -> List[str]:
    """Recursively formats a critique node and its children into Markdown lines."""
    lines = []
    if not node or not isinstance(node, dict): return lines

    indent = "  " * depth
    claim = node.get('claim', 'N/A')
    severity = node.get('severity', 'N/A')
    confidence = node.get('confidence', 0.0)
    evidence = node.get('evidence')
    arbitration = node.get('arbitration')
    sub_critiques = node.get('sub_critiques', [])

    lines.append(f"{indent}- **Claim:** {claim}")
    lines.append(f"{indent}  - **Severity:** {severity}")
    lines.append(f"{indent}  - **Confidence (Adjusted):** {confidence:.0%}")
    if evidence:
        evidence_lines = evidence.strip().split('\n')
        lines.append(f"{indent}  - **Evidence:**")
        for line in evidence_lines: lines.append(f"{indent}    > {line}")
    if arbitration:
        lines.append(f"{indent}  - **Expert Arbitration:** {arbitration}")

    if sub_critiques:
        lines.append(f"{indent}  - **Sub-Critiques:**")
        for sub_node in sub_critiques:
            lines.extend(format_critique_node(sub_node, depth + 1))
    return lines
# ---------------------------------------------------------

# --- Helper function to generate Judge summary and score ---
def generate_judge_summary_and_score(original_content: str, adjusted_trees: List[Dict[str, Any]], arbiter_data: Dict[str, Any], config: Dict[str, Any]) -> Tuple[str, Optional[int], str]:
    """Calls LLM with Judge prompt to generate summary, score, and justification."""
    judge_logger = logging.getLogger('JudgeSummary')
    judge_logger.info("Attempting to generate Judge Summary and Score...")
    default_return = ("Error: Judge summary generation failed.", None, "N/A")
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(base_dir, '..', 'prompts', 'judge_summary.txt')
        judge_logger.debug(f"Loading Judge prompt from: {prompt_path}")
        with open(prompt_path, 'r', encoding='utf-8') as f:
            judge_prompt_template = f.read()

        context = {
            "original_content": original_content,
            "adjusted_critique_trees_json": json.dumps(adjusted_trees, indent=2),
            "arbitration_data_json": json.dumps(arbiter_data, indent=2) # Pass full arbiter data
        }

        # Expecting JSON: {"judge_summary_text": "...", "judge_overall_score": N, "judge_score_justification": "..."}
        judge_result, model_used = gemini_client.call_gemini_with_retry(
            prompt_template=judge_prompt_template,
            context=context,
            config=config,
            is_structured=True # Expecting JSON now
        )

        if isinstance(judge_result, dict) and all(k in judge_result for k in ['judge_summary_text', 'judge_overall_score', 'judge_score_justification']):
            summary = judge_result['judge_summary_text'].strip()
            score = int(judge_result['judge_overall_score'])
            justification = judge_result['judge_score_justification'].strip()
            judge_logger.info(f"Judge Summary and Score generated successfully using {model_used}. Score={score}")
            judge_logger.debug(f"Judge Score Justification: {justification}")
            return summary, score, justification
        else:
            judge_logger.warning(f"Unexpected Judge result structure received from {model_used}: {judge_result}")
            return ("Error: Invalid Judge result structure.", None, "N/A")

    except FileNotFoundError:
        error_msg = f"Judge summary prompt file not found at {prompt_path}"
        judge_logger.error(error_msg)
        return f"Error: {error_msg}", None, "N/A"
    except Exception as e:
        error_msg = f"Failed to generate Judge summary/score: {e}"
        judge_logger.error(error_msg, exc_info=True)
        return f"Error generating Judge summary: {e}", None, "N/A"
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

    # --- Get Data ---
    adjusted_trees = critique_data.get('adjusted_critique_trees', [])
    arbiter_data = { # Pass arbiter data needed for Judge prompt
        'adjustments': critique_data.get('arbitration_adjustments', []),
        'arbiter_overall_score': critique_data.get('arbiter_overall_score'),
        'arbiter_score_justification': critique_data.get('arbiter_score_justification')
    }
    score_metrics = critique_data.get('score_metrics', {}) # Severity counts

    # --- Generate Judge Summary and Score ---
    judge_summary, judge_score, judge_justification = generate_judge_summary_and_score(
        original_content, adjusted_trees, arbiter_data, config
    )

    # --- Judge Summary Section ---
    output_lines.append("## Overall Judge Summary")
    output_lines.append(judge_summary)
    output_lines.append("")
    output_lines.append("---")

    # --- Scoring Summary Section ---
    arbiter_score = arbiter_data.get('arbiter_overall_score', 'N/A')
    high_sev = score_metrics.get('high_severity_points', 0)
    med_sev = score_metrics.get('medium_severity_points', 0)
    low_sev = score_metrics.get('low_severity_points', 0)

    output_lines.append("## Overall Scores & Metrics")
    output_lines.append(f"- **Final Judge Score:** {judge_score if judge_score is not None else 'N/A'}/100")
    if judge_score is not None:
         output_lines.append(f"  - *Justification:* {judge_justification}")
    output_lines.append(f"- **Expert Arbiter Score:** {arbiter_score if arbiter_score is not None else 'N/A'}/100")
    if arbiter_data.get('arbiter_score_justification'):
         output_lines.append(f"  - *Justification:* {arbiter_data['arbiter_score_justification']}")
    output_lines.append(f"- **High/Critical Severity Points (Post-Arbitration):** {high_sev}")
    output_lines.append(f"- **Medium Severity Points (Post-Arbitration):** {med_sev}")
    output_lines.append(f"- **Low Severity Points (Post-Arbitration):** {low_sev}")
    output_lines.append("")
    output_lines.append("---")

    # --- Arbiter Adjustments Summary ---
    output_lines.append("## Expert Arbiter Adjustment Summary")
    arbiter_adjustments = arbiter_data.get('adjustments', [])
    if arbiter_adjustments:
        output_lines.append(f"The Expert Arbiter provided {len(arbiter_adjustments)} specific comments/adjustments:")
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
    if not adjusted_trees:
         output_lines.append("No critique data available.")
    else:
        for agent_critique in adjusted_trees:
            agent_style = agent_critique.get('agent_style', 'Unknown Agent')
            # Skip arbiter pseudo-agent if it ended up in the list
            if agent_style == 'ExpertArbiter': continue
            output_lines.append(f"### Agent: {agent_style}")
            if 'error' in agent_critique:
                output_lines.append(f"- **Error during critique:** {agent_critique['error']}")
            elif 'critique_tree' in agent_critique and agent_critique['critique_tree']:
                # Format the full tree recursively
                tree_lines = format_critique_node(agent_critique['critique_tree'], depth=0)
                if not tree_lines: # Handle case where root node itself was invalid/terminated
                     output_lines.append("- Critique terminated early or no valid points generated.")
                else:
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
