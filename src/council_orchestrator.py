# src/critique_module/council_orchestrator.py

"""
Manages the Reasoning Council workflow. Includes initial content assessment,
critiques by either philosophical agents or scientific methodology agents,
followed by arbitration from a subject-matter expert agent.
Runs agents sequentially and distributes content points among critics.
"""
import logging
import sys
import os
import json
import random
from typing import Dict, List, Any, Type, Optional, Union

# Import agent implementations
from .reasoning_agent import (
    ReasoningAgent, 
    # Philosophical agents
    AristotleAgent, DescartesAgent, KantAgent, LeibnizAgent, PopperAgent, RussellAgent,
    # Scientific methodology agents
    SystemsAnalystAgent, FirstPrinciplesAnalystAgent, BoundaryConditionAnalystAgent,
    OptimizationAnalystAgent, EmpiricalValidationAnalystAgent, LogicalStructureAnalystAgent,
    # Arbiters
    ExpertArbiterAgent, ScientificExpertArbiterAgent
)
from .content_assessor import ContentAssessor

# Define agent types
PHILOSOPHER_AGENT_CLASSES: List[Type[ReasoningAgent]] = [
    AristotleAgent, DescartesAgent, KantAgent, LeibnizAgent, PopperAgent, RussellAgent
]

SCIENTIFIC_AGENT_CLASSES: List[Type[ReasoningAgent]] = [
    SystemsAnalystAgent, FirstPrinciplesAnalystAgent, BoundaryConditionAnalystAgent,
    OptimizationAnalystAgent, EmpiricalValidationAnalystAgent, LogicalStructureAnalystAgent
]

# --- Agent-Specific Logging Setup ---
LOG_DIR = "logs"
PHILOSOPHY_LOG_DIR = os.path.join(LOG_DIR, "philosophy")
SCIENCE_LOG_DIR = os.path.join(LOG_DIR, "science")

# Create all necessary log directories
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(PHILOSOPHY_LOG_DIR, exist_ok=True)
os.makedirs(SCIENCE_LOG_DIR, exist_ok=True)

def setup_agent_logger(agent_name: str, scientific_mode: bool = False) -> logging.Logger:
    """
    Sets up a dedicated file logger for an agent.
    
    Args:
        agent_name: Name of the agent for the logger
        scientific_mode: Whether to use science subdirectory (vs philosophy)
        
    Returns:
        Configured logger instance
    """
    # Determine the appropriate log directory
    agent_log_dir = SCIENCE_LOG_DIR if scientific_mode else PHILOSOPHY_LOG_DIR
    
    # Create the log file path
    log_file = os.path.join(agent_log_dir, f"agent_{agent_name}.log")
    
    # Configure the logger
    logger = logging.getLogger(f"agent.{agent_name}")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    
    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
    
    # Add a file handler that overwrites previous logs
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
# ------------------------------------

# --- Helper function to apply adjustments recursively ---
def apply_adjustments_to_tree(node: Optional[Dict[str, Any]], adjustment_map: Dict[str, Dict[str, Any]], logger: logging.Logger):
    """Recursively applies arbitration adjustments to a critique tree node."""
    if not node or not isinstance(node, dict): return

    node_id = node.get('id')
    if node_id and node_id in adjustment_map:
        adjustment = adjustment_map[node_id]
        original_confidence = node.get('confidence', 0.0)
        delta = adjustment.get('confidence_delta', 0.0)
        adjusted_confidence = original_confidence + delta
        adjusted_confidence = max(0.0, min(1.0, adjusted_confidence))
        node['confidence'] = adjusted_confidence
        node['arbitration'] = adjustment.get('arbitration_comment')
        # Log application within the helper for clarity
        logger.debug(f"Applied arbitration to claim '{node_id}': Delta={delta:+.2f}, NewConf={adjusted_confidence:.2f}.")

    if 'sub_critiques' in node and isinstance(node['sub_critiques'], list):
        for sub_node in node['sub_critiques']:
            apply_adjustments_to_tree(sub_node, adjustment_map, logger)
# ---------------------------------------------------------


# Synchronous version
def run_critique_council(
    content: str, 
    config: Dict[str, Any], 
    peer_review: bool = False,
    scientific_mode: bool = False
) -> Dict[str, Any]:
    """
    Orchestrates the critique process: initial content assessment, critics evaluate, then expert arbitrates.
    
    Args:
        content: The content to analyze
        config: Configuration settings
        peer_review: Whether to use peer review enhancements (default: False)
        scientific_mode: Whether to use scientific methodology agents instead of philosophers (default: False)
        
    Returns:
        Dictionary with adjusted critique trees and arbitration details including score
    """
    root_logger = logging.getLogger(__name__)

    # Determine which agent classes to use based on mode
    agent_classes = SCIENTIFIC_AGENT_CLASSES if scientific_mode else PHILOSOPHER_AGENT_CLASSES
    agent_type_name = "scientific methodology" if scientific_mode else "philosopher"
    
    if not agent_classes:
         root_logger.error(f"{agent_type_name.capitalize()} agent classes list is empty.")
         raise ValueError(f"{agent_type_name.capitalize()} agent classes list is empty.")
    
    # 1. Initialize and Run Content Assessor to extract objective points
    print("Starting Initial Content Assessment...")
    content_assessor = ContentAssessor()
    assessor_logger = setup_agent_logger(content_assessor.style, scientific_mode)
    if hasattr(content_assessor, 'set_logger'): content_assessor.set_logger(assessor_logger)
    
    try:
        extracted_points = content_assessor.extract_points(content, config)
        print(f"Initial Content Assessment completed. Extracted {len(extracted_points)} objective points.")
    except Exception as e:
        root_logger.error(f"Error during content assessment: {e}", exc_info=True)
        assessor_logger.error(f"Content assessment failed: {e}", exc_info=True)
        # If assessment fails, proceed without points
        extracted_points = []
        print("Content Assessment failed. Proceeding without extracted points.")
    
    # Distribute points among agents if points were extracted
    points_per_agent = {}
    if extracted_points:
        # Create a roughly equal distribution of points for each agent
        total_agents = len(agent_classes)
        points_per_agent_count = max(1, len(extracted_points) // total_agents)
        
        # Shuffle points for random distribution
        shuffled_points = extracted_points.copy()
        random.shuffle(shuffled_points)
        
        # Distribute points to agents
        for i, agent_cls in enumerate(agent_classes):
            start_idx = i * points_per_agent_count
            end_idx = start_idx + points_per_agent_count if i < total_agents - 1 else len(shuffled_points)
            points_per_agent[agent_cls.__name__] = shuffled_points[start_idx:end_idx]
            
        print(f"Distributed extracted points among {total_agents} {agent_type_name} agents.")

    # 1. Instantiate Agents and Setup Loggers
    reasoning_agents: List[ReasoningAgent] = []
    agent_loggers: Dict[str, logging.Logger] = {}
    for agent_cls in agent_classes:
        agent = agent_cls()
        agent_logger = setup_agent_logger(agent.style, scientific_mode)
        agent_loggers[agent.style] = agent_logger
        if hasattr(agent, 'set_logger'): agent.set_logger(agent_logger)
        reasoning_agents.append(agent)
    total_agents = len(reasoning_agents)

    # 2. Initial Critique Round (Agents run sequentially with their assigned points)
    print(f"Starting Initial Critique Round ({total_agents} {agent_type_name} agents)...")
    initial_critiques: List[Dict[str, Any]] = []
    initial_errors = 0
    for i, agent in enumerate(reasoning_agents):
        agent_style = agent.style
        agent_logger = agent_loggers[agent_style]
        status = "OK"
        print(f"  Running Initial Critique for Agent '{agent_style}' (Peer Review: {peer_review})...")
        try:
            # Pass peer_review flag and assigned points to agent's critique method
            agent_points = points_per_agent.get(type(agent).__name__, [])
            result = agent.critique(content, config, agent_logger, peer_review=peer_review, assigned_points=agent_points)
            initial_critiques.append(result)
        except Exception as e:
            root_logger.error(f"Error during initial critique from agent '{agent_style}' (Peer Review: {peer_review}): {e}", exc_info=True)
            agent_logger.error(f"Initial critique failed: {e}", exc_info=True)
            initial_critiques.append({'agent_style': agent_style, 'critique_tree': {}, 'error': str(e)})
            initial_errors += 1
            status = f"ERROR ({type(e).__name__})"
        print(f"  Agent '{agent_style}' Initial Critique completed ({status})")
    print(f"Initial Critique Round Finished. Errors: {initial_errors}")

    # 3. Arbitration Round (Expert Arbiter runs once)
    print(f"Starting Arbitration Round...")
    # Use the appropriate arbiter based on mode
    arbiter_agent = ScientificExpertArbiterAgent() if scientific_mode else ExpertArbiterAgent()
    arbiter_logger = setup_agent_logger(arbiter_agent.style, scientific_mode)
    if hasattr(arbiter_agent, 'set_logger'): arbiter_agent.set_logger(arbiter_logger)

    # Initialize arbiter result structure
    arbitration_result_data = {'adjustments': [], 'arbiter_overall_score': None, 'arbiter_score_justification': None, 'error': None}
    status = "OK"
    try:
        valid_critiques_for_arbiter = [c for c in initial_critiques if 'error' not in c]
        if valid_critiques_for_arbiter:
             print(f"  Running Arbiter Agent '{arbiter_agent.style}' (Peer Review: {peer_review})...")
             # Capture the full result dictionary from arbitrate, passing peer_review flag
             arbitration_result = arbiter_agent.arbitrate(content, valid_critiques_for_arbiter, config, arbiter_logger, peer_review=peer_review)
             # Update the result data structure
             arbitration_result_data['adjustments'] = arbitration_result.get('adjustments', [])
             arbitration_result_data['arbiter_overall_score'] = arbitration_result.get('arbiter_overall_score')
             arbitration_result_data['arbiter_score_justification'] = arbitration_result.get('arbiter_score_justification')
             arbitration_result_data['error'] = arbitration_result.get('error') # Capture potential error string

             if arbitration_result_data['error']:
                  status = f"ERROR ({arbitration_result_data['error']})"
                  root_logger.error(f"Arbitration failed: {arbitration_result_data['error']}")
        else:
             status = "SKIPPED (No valid initial critiques)"
             print("  Skipping arbitration (no valid initial critiques).")

    except Exception as e:
        root_logger.error(f"Error during arbitration call for agent '{arbiter_agent.style}': {e}", exc_info=True)
        arbiter_logger.error(f"Arbitration call failed: {e}", exc_info=True)
        status = f"ERROR ({type(e).__name__})"
        arbitration_result_data['error'] = str(e) # Store exception string

    print(f"Arbitration Round Completed ({status}). Found {len(arbitration_result_data['adjustments'])} adjustments. Arbiter Score: {arbitration_result_data['arbiter_overall_score']}")


    # 4. Apply Arbitration Adjustments to Trees
    print("Applying arbitration adjustments to critique trees...")
    adjustment_map: Dict[str, Dict[str, Any]] = {
        adj.get('target_claim_id'): adj for adj in arbitration_result_data['adjustments'] if adj.get('target_claim_id')
    }
    adjusted_critique_trees = []
    for critique in initial_critiques:
         # Apply adjustments recursively
         if 'critique_tree' in critique and isinstance(critique['critique_tree'], dict):
              apply_adjustments_to_tree(critique['critique_tree'], adjustment_map, root_logger)
         adjusted_critique_trees.append(critique)


    # 5. Synthesize Final Data (Calculate severity counts based on adjusted trees)
    print("Synthesizing final results...")
    final_points_for_scoring = []
    orchestrator_config = config.get('council_orchestrator', {})
    synthesis_confidence_threshold = orchestrator_config.get('synthesis_confidence_threshold', 0.4)

    def extract_significant_points(node: Optional[Dict[str, Any]], agent_style: str):
        # (Helper function remains the same as before)
        points = []
        if not node or not isinstance(node, dict): return points
        confidence = node.get('confidence', 0.0)
        claim_text = node.get('claim', 'N/A')
        if confidence >= synthesis_confidence_threshold:
             point_data = {
                 'area': f"Philosopher: {agent_style}", 'critique': claim_text,
                 'severity': node.get('severity', 'N/A'), 'confidence': round(confidence, 2)
             }
             if node.get('arbitration'): point_data['arbitration'] = node['arbitration']
             points.append(point_data)
        if 'sub_critiques' in node and isinstance(node['sub_critiques'], list):
            for sub_node in node['sub_critiques']:
                points.extend(extract_significant_points(sub_node, agent_style))
        return points

    processed_claims_for_scoring = set()
    for adjusted_critique in adjusted_critique_trees:
         if 'error' not in adjusted_critique and 'critique_tree' in adjusted_critique:
              agent_style = adjusted_critique.get('agent_style', 'Unknown')
              extracted_points = extract_significant_points(adjusted_critique['critique_tree'], agent_style)
              for point in extracted_points:
                   if point['critique'] not in processed_claims_for_scoring:
                        final_points_for_scoring.append(point)
                        processed_claims_for_scoring.add(point['critique'])

    # Calculate severity counts based on the points meeting the threshold AFTER arbitration
    high_severity_count = 0
    medium_severity_count = 0
    low_severity_count = 0
    if final_points_for_scoring:
        no_findings = False
        final_assessment_summary = f"Council synthesis complete. Identified {len(final_points_for_scoring)} significant point(s) across all critique levels after expert arbitration."
        for point in final_points_for_scoring:
             severity = point.get('severity', 'N/A').lower()
             if severity == 'critical' or severity == 'high': high_severity_count += 1
             elif severity == 'medium': medium_severity_count += 1
             elif severity == 'low': low_severity_count += 1
    else:
        no_findings = True
        final_assessment_summary = "Council synthesis complete. No points met the significance threshold for reporting after expert arbitration."

    # Return the full data needed by the new formatter
    synthesized_data = {
        'final_assessment_summary': final_assessment_summary,
        'adjusted_critique_trees': adjusted_critique_trees,
        'arbitration_adjustments': arbitration_result_data['adjustments'], # Pass raw adjustments
        'arbiter_overall_score': arbitration_result_data['arbiter_overall_score'], # Pass arbiter score
        'arbiter_score_justification': arbitration_result_data['arbiter_score_justification'], # Pass justification
        'no_findings': no_findings,
        'score_metrics': { # Only severity counts needed now
            'high_severity_points': high_severity_count,
            'medium_severity_points': medium_severity_count,
            'low_severity_points': low_severity_count,
        }
    }
    print("Synthesis complete.")
    return synthesized_data
