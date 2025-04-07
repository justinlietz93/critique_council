# src/critique_module/output_formatter.py

"""
Component responsible for formatting the final critique output.
"""

from typing import Dict, List, Any

def format_critique_output(critique_data: Dict[str, Any]) -> str:
    """
    Formats the synthesized critique data into a final string with an
    objective, unempathetic, robotic tone.

    Args:
        critique_data: Dictionary from the council orchestrator.
                       Expected keys: 'final_assessment' (str),
                                      'points' (list[dict]),
                                      'no_findings' (bool).
                       Each dict in 'points' should have 'area', 'critique', 'severity'.

    Returns:
        A formatted string adhering to the objective/robotic tone requirement.
    """
    output_lines = []
    output_lines.append("=== CRITIQUE ASSESSMENT REPORT ===")

    if critique_data.get('no_findings', True):
        output_lines.append("\nANALYSIS COMPLETE. NO SIGNIFICANT POINTS FOR IMPROVEMENT IDENTIFIED.")
    else:
        assessment = critique_data.get('final_assessment', 'Assessment data unavailable.')
        points: List[Dict[str, Any]] = critique_data.get('points', [])

        output_lines.append("\nOVERALL ASSESSMENT:")
        output_lines.append(f"- {assessment}")

        if points:
            output_lines.append("\nIDENTIFIED POINTS:")
            for i, point in enumerate(points):
                area = point.get('area', 'N/A')
                critique = point.get('critique', 'N/A')
                severity = point.get('severity', 'N/A')
                # Include confidence if available in the point data
                confidence_str = f" (Confidence: {point['confidence']:.2f})" if 'confidence' in point else ""
                output_lines.append(f"  {i+1}. AREA: {area}")
                output_lines.append(f"     SEVERITY: {severity}{confidence_str}")
                output_lines.append(f"     CRITIQUE: {critique}")
        else:
            # This case should ideally be covered by 'no_findings', but added for robustness
            output_lines.append("\n- No specific points were detailed despite findings being indicated.")

    output_lines.append("\n=== END OF REPORT ===")
    return "\n".join(output_lines)

# Example usage (for testing)
if __name__ == '__main__':
    test_data_findings = {
        'final_assessment': 'The document exhibits structural deficiencies and lacks clarity in critical sections.',
        'points': [
            {'area': 'Section 2.1', 'critique': 'Logical flow is inconsistent, assumptions are not clearly stated.', 'severity': 'High', 'confidence': 0.85},
            {'area': 'Definitions', 'critique': 'Term \'Synergy\' used ambiguously without precise definition.', 'severity': 'Medium', 'confidence': 0.75},
            {'area': 'Requirements (CRIT-SIM-01)', 'critique': 'Reference to \'amd_hip\' backend lacks context for alternative implementations.', 'severity': 'Low', 'confidence': 0.55}
        ],
        'no_findings': False
    }
    test_data_no_findings = {
        'final_assessment': '',
        'points': [],
        'no_findings': True
    }
    test_data_edge_case = {
         'final_assessment': 'Findings indicated but no points provided.',
         'points': [],
         'no_findings': False
    }


    print("--- Formatting Test: With Findings ---")
    print(format_critique_output(test_data_findings))
    print("\n--- Formatting Test: No Findings ---")
    print(format_critique_output(test_data_no_findings))
    print("\n--- Formatting Test: Edge Case (Findings=True, No Points) ---")
    print(format_critique_output(test_data_edge_case))
