# src/critique_module/output_formatter.py

"""
Component responsible for formatting the final critique output into Markdown.
"""

from typing import Dict, List, Any
import datetime

def format_critique_output(critique_data: Dict[str, Any]) -> str:
    """
    Formats the synthesized critique data into a final Markdown report string.

    Args:
        critique_data: Dictionary from the council orchestrator.
                       Expected keys: 'final_assessment' (str),
                                      'points' (list[dict]),
                                      'no_findings' (bool),
                                      'score_metrics' (dict).
                       Each dict in 'points' should have 'area', 'critique', 'severity', 'confidence'.
                       'score_metrics' should have 'overall_score', 'high_severity_points', etc.

    Returns:
        A formatted Markdown string.
    """
    output_lines = []
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    output_lines.append(f"# Critique Assessment Report")
    output_lines.append(f"**Generated:** {now}")
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
    output_lines.append("") # Add spacing

    # --- Overall Assessment ---
    output_lines.append("## Assessment Summary")
    assessment = critique_data.get('final_assessment', 'Assessment data unavailable.')
    output_lines.append(f"{assessment}")
    output_lines.append("") # Add spacing

    # --- Detailed Points ---
    output_lines.append("## Detailed Critique Points")
    if critique_data.get('no_findings', True):
        output_lines.append("No significant points for improvement identified meeting the reporting threshold.")
    else:
        points: List[Dict[str, Any]] = critique_data.get('points', [])
        if points:
            for i, point in enumerate(points):
                area = point.get('area', 'N/A')
                critique = point.get('critique', 'N/A')
                severity = point.get('severity', 'N/A')
                confidence_str = f"{point['confidence']:.0%}" if 'confidence' in point else "N/A" # Format as percentage

                output_lines.append(f"### Point {i+1}")
                output_lines.append(f"- **Area:** {area}")
                output_lines.append(f"- **Severity:** {severity}")
                output_lines.append(f"- **Confidence:** {confidence_str}")
                output_lines.append(f"- **Critique:** {critique}")
                output_lines.append("") # Add spacing between points
        else:
            # This case should ideally be covered by 'no_findings', but added for robustness
            output_lines.append("No specific points were detailed despite findings being indicated.")

    output_lines.append("\n--- End of Report ---")
    return "\n".join(output_lines)

# Example usage (for testing) - Updated for new structure
if __name__ == '__main__':
    test_data_findings = {
        'final_assessment': 'The document exhibits structural deficiencies and lacks clarity in critical sections.',
        'points': [
            {'area': 'Section 2.1', 'critique': 'Logical flow is inconsistent, assumptions are not clearly stated.', 'severity': 'High', 'confidence': 0.85},
            {'area': 'Definitions', 'critique': 'Term \'Synergy\' used ambiguously without precise definition.', 'severity': 'Medium', 'confidence': 0.75},
            {'area': 'Requirements (CRIT-SIM-01)', 'critique': 'Reference to \'amd_hip\' backend lacks context for alternative implementations.', 'severity': 'Low', 'confidence': 0.55}
        ],
        'no_findings': False,
        'score_metrics': { # Example metrics
            'overall_score': 78,
            'high_severity_points': 1,
            'medium_severity_points': 1,
            'low_severity_points': 1,
        }
    }
    test_data_no_findings = {
        'final_assessment': 'Council analysis concluded. No points met the significance threshold for reporting after deliberation.',
        'points': [],
        'no_findings': True,
         'score_metrics': {
            'overall_score': 100,
            'high_severity_points': 0,
            'medium_severity_points': 0,
            'low_severity_points': 0,
        }
    }

    print("--- Formatting Test: With Findings (Markdown) ---")
    print(format_critique_output(test_data_findings))
    print("\n--- Formatting Test: No Findings (Markdown) ---")
    print(format_critique_output(test_data_no_findings))
