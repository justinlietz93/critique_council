# src/critique_module/council_orchestrator.py

"""
Manages the Reasoning Council workflow. Includes initial critique by philosophical
agents followed by arbitration from a subject-matter expert agent.
Runs agents sequentially.
"""
import logging
import sys
import os
import json
from typing import Dict, List, Any, Type, Optional # Import Optional
# Import agent implementations
from .reasoning_agent import (
    ReasoningAgent, AristotleAgent, DescartesAgent, KantAgent,
    LeibnizAgent, PopperAgent, RussellAgent, ExpertArbiterAgent
)

# Define philosopher agent types
PHILOSOPHER_AGENT_CLASSES: List[Type[ReasoningAgent]] = [
    AristotleAgent, DescartesAgent, KantAgent, LeibnizAgent, PopperAgent, RussellAgent
]

# --- Agent-Specific Logging Setup ---
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def setup_agent_logger(agent_name: str) -> logging.Logger:
    """Sets up a dedicated file logger for an agent."""
    log_file = os.path.join(LOG_DIR, f"agent_{agent_name}.log")
    logger = logging.getLogger(f"agent.{agent_name}")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger
# ------------------------------------

# --- Helper function to apply adjustments recursively ---
def apply_adjustments_to_tree(node: Optional[Dict[str, Any]], adjustment_map: Dict[str, Dict[str, Any]], logger: logging.Logger):
    """Recursively applies arbitration adjustments to a critique tree node."""
    if not node or not isinstance(node, dict):
        return

    node_id = node.get('id')
    if node_id and node_id in adjustment_map:
        adjustment = adjustment_map[node_id]
        original_confidence = node.get('confidence', 0.0)
        delta = adjustment.get('confidence_delta', 0.0)
        adjusted_confidence = original_confidence + delta
        adjusted_confidence = max(0.0, min(1.0, adjusted_confidence)) # Clamp
        node['confidence'] = adjusted_confidence # Update confidence in the tree
        node['arbitration'] = adjustment.get('arbitration_comment') # Add comment
        logger.info(f"Applied arbitration to claim '{node_id}': Delta={delta:.2f}, NewConf={adjusted_confidence:.2f}. Comment: {node['arbitration']}")

    # Recurse on sub-critiques
    if 'sub_critiques' in node and isinstance(node['sub_critiques'], list):
        for sub_node in node['sub_critiques']:
            apply_adjustments_to_tree(sub_node, adjustment_map, logger)
# ---------------------------------------------------------


# Synchronous version
def run_critique_council(content: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orchestrates the critique process: philosophers critique, then expert arbitrates.
    Returns full adjusted trees and arbitration details.
    """
    root_logger = logging.getLogger(__name__)

    if not PHILOSOPHER_AGENT_CLASSES:
         root_logger.error("PHILOSOPHER_AGENT_CLASSES list is empty.")
         raise ValueError("PHILOSOPHER_AGENT_CLASSES list is empty.")

    # 1. Instantiate Philosopher Agents and Setup Loggers
    philosopher_agents: List[ReasoningAgent] = []
    agent_loggers: Dict[str, logging.Logger] = {}
    for agent_cls in PHILOSOPHER_AGENT_CLASSES:
        agent = agent_cls()
        agent_logger = setup_agent_logger(agent.style)
        agent_loggers[agent.style] = agent_logger
        if hasattr(agent, 'set_logger'):
             agent.set_logger(agent_logger)
        philosopher_agents.append(agent)
    total_philosophers = len(philosopher_agents)

    # 2. Initial Critique Round (Philosophers run sequentially)
    print(f"Starting Initial Critique Round ({total_philosophers} philosopher agents)...")
    initial_critiques: List[Dict[str, Any]] = []
    initial_errors = 0
    for i, agent in enumerate(philosopher_agents):
        agent_style = agent.style
        agent_logger = agent_loggers[agent_style]
        status = "OK"
        print(f"  Running Initial Critique for Agent '{agent_style}'...")
        try:
            result = agent.critique(content, config, agent_logger)
            initial_critiques.append(result)
        except Exception as e:
            root_logger.error(f"Error during initial critique from agent '{agent_style}': {e}", exc_info=True)
            agent_logger.error(f"Initial critique failed: {e}", exc_info=True)
            initial_critiques.append({'agent_style': agent_style, 'critique_tree': {}, 'error': str(e)})
            initial_errors += 1
            status = f"ERROR ({type(e).__name__})"
        print(f"  Agent '{agent_style}' Initial Critique completed ({status})")
    print(f"Initial Critique Round Finished. Errors: {initial_errors}")

    # 3. Arbitration Round (Expert Arbiter runs once)
    print(f"Starting Arbitration Round...")
    arbiter_agent = ExpertArbiterAgent()
    arbiter_logger = setup_agent_logger(arbiter_agent.style)
    if hasattr(arbiter_agent, 'set_logger'):
        arbiter_agent.set_logger(arbiter_logger)

    arbitration_adjustments = []
    status = "OK"
    try:
        valid_critiques_for_arbiter = [c for c in initial_critiques if 'error' not in c]
        if valid_critiques_for_arbiter:
             arbitration_result = arbiter_agent.arbitrate(content, valid_critiques_for_arbiter, config, arbiter_logger)
             if 'error' in arbitration_result and arbitration_result['error']: # Check if error is not None or empty
                  status = f"ERROR ({arbitration_result['error']})"
                  root_logger.error(f"Arbitration failed: {arbitration_result['error']}")
             else:
                  arbitration_adjustments = arbitration_result.get('adjustments', [])
        else:
             status = "SKIPPED (No valid initial critiques)"
             print("  Skipping arbitration (no valid initial critiques).")

    except Exception as e:
        root_logger.error(f"Error during arbitration by agent '{arbiter_agent.style}': {e}", exc_info=True)
        arbiter_logger.error(f"Arbitration failed: {e}", exc_info=True)
        status = f"ERROR ({type(e).__name__})"
        arbitration_adjustments = [] # Ensure adjustments list is empty on error

    print(f"Arbitration Round Completed ({status}). Found {len(arbitration_adjustments)} adjustments.")


    # 4. Apply Arbitration Adjustments to Trees
    print("Applying arbitration adjustments to critique trees...")
    adjustment_map: Dict[str, Dict[str, Any]] = {
        adj.get('target_claim_id'): adj for adj in arbitration_adjustments if adj.get('target_claim_id')
    }
    adjusted_critique_trees = []
    for critique in initial_critiques:
         # Deep copy might be safer here if trees are very complex, but try direct modification first
         if 'critique_tree' in critique and isinstance(critique['critique_tree'], dict):
              apply_adjustments_to_tree(critique['critique_tree'], adjustment_map, root_logger)
         adjusted_critique_trees.append(critique) # Add the potentially modified critique object


    # 5. Synthesize Final Data (Score based on adjusted trees)
    print("Synthesizing final results...")
    final_points_for_scoring = [] # Separate list for scoring based on threshold
    orchestrator_config = config.get('council_orchestrator', {})
    synthesis_confidence_threshold = orchestrator_config.get('synthesis_confidence_threshold', 0.4)

    # Function to recursively extract points meeting threshold from adjusted tree
    def extract_significant_points(node: Optional[Dict[str, Any]], agent_style: str):
        points = []
        if not node or not isinstance(node, dict):
            return points
        
        confidence = node.get('confidence', 0.0) # Use adjusted confidence
        claim_text = node.get('claim', 'N/A')
        
        # Check threshold
        if confidence >= synthesis_confidence_threshold:
             point_data = {
                 'area': f"Philosopher: {agent_style}",
                 'critique': claim_text,
                 'severity': node.get('severity', 'N/A'),
                 'confidence': round(confidence, 2)
             }
             if node.get('arbitration'):
                  point_data['arbitration'] = node['arbitration']
             points.append(point_data)

        # Recurse on sub-critiques regardless of parent threshold (to find nested significant points)
        if 'sub_critiques' in node and isinstance(node['sub_critiques'], list):
            for sub_node in node['sub_critiques']:
                points.extend(extract_significant_points(sub_node, agent_style))
        return points

    # Extract significant points from all adjusted trees for scoring
    processed_claims_for_scoring = set()
    for adjusted_critique in adjusted_critique_trees:
         if 'error' not in adjusted_critique and 'critique_tree' in adjusted_critique:
              agent_style = adjusted_critique.get('agent_style', 'Unknown')
              extracted_points = extract_significant_points(adjusted_critique['critique_tree'], agent_style)
              for point in extracted_points:
                   # Avoid duplicate claims in scoring list
                   if point['critique'] not in processed_claims_for_scoring:
                        final_points_for_scoring.append(point)
                        processed_claims_for_scoring.add(point['critique'])


    # Calculate score based on extracted significant points
    placeholder_score = 100
    high_severity_count = 0
    medium_severity_count = 0
    low_severity_count = 0

    if final_points_for_scoring:
        no_findings = False
        final_assessment = f"Council synthesis complete. Identified {len(final_points_for_scoring)} significant point(s) across all critique levels after expert arbitration."
        for point in final_points_for_scoring:
             severity = point.get('severity', 'N/A').lower()
             if severity == 'critical' or severity == 'high':
                 placeholder_score -= 15
                 high_severity_count += 1
             elif severity == 'medium':
                 placeholder_score -= 5
                 medium_severity_count += 1
             elif severity == 'low':
                 placeholder_score -= 2
                 low_severity_count += 1
        placeholder_score = max(0, placeholder_score)
    else:
        no_findings = True
        final_assessment = "Council synthesis complete. No points met the significance threshold for reporting after expert arbitration."

    # Return the full data needed by the new formatter
    synthesized_data = {
        'final_assessment_summary': final_assessment, # Summary text for top section
        'adjusted_critique_trees': adjusted_critique_trees, # Full trees with adjustments
        'arbitration_adjustments': arbitration_adjustments, # Raw adjustments list
        'no_findings': no_findings, # Still useful for formatter logic
        'score_metrics': {
            'overall_score': placeholder_score,
            'high_severity_points': high_severity_count,
            'medium_severity_points': medium_severity_count,
            'low_severity_points': low_severity_count,
        }
    }
    print("Synthesis complete.")
    return synthesized_data
