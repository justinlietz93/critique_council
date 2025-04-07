# src/critique_module/council_orchestrator.py

"""
Manages the Reasoning Council workflow, including agent interaction
and critique synthesis.
"""
import asyncio
import logging
import sys
import os
from typing import Dict, List, Any, Type
# Import concrete philosopher agent implementations
from .reasoning_agent import (
    ReasoningAgent, AristotleAgent, DescartesAgent, KantAgent,
    LeibnizAgent, PopperAgent, RussellAgent
)

# Define concrete philosopher agent types to be used by the council
AGENT_CLASSES: List[Type[ReasoningAgent]] = [
    AristotleAgent,
    DescartesAgent,
    KantAgent,
    LeibnizAgent,
    PopperAgent,
    RussellAgent
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


async def run_critique_council(content: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orchestrates the reasoning council critique process using async agent calls.
    """
    root_logger = logging.getLogger(__name__)

    if not AGENT_CLASSES:
         root_logger.error("AGENT_CLASSES list is empty in council_orchestrator.")
         raise ValueError("AGENT_CLASSES list is empty in council_orchestrator.")

    # 1. Instantiate Agents and Setup Loggers
    agents: List[ReasoningAgent] = []
    agent_loggers: Dict[str, logging.Logger] = {}
    for agent_cls in AGENT_CLASSES:
        agent = agent_cls()
        agent_logger = setup_agent_logger(agent.style)
        agent_loggers[agent.style] = agent_logger
        if hasattr(agent, 'set_logger'):
             agent.set_logger(agent_logger)
        agents.append(agent)
    total_agents = len(agents)

    # 2. Initial Critique Round (Run concurrently with progress using as_completed)
    print(f"Running Initial Critique Round ({total_agents} agents)...")
    initial_critiques: List[Dict[str, Any]] = [{} for _ in range(total_agents)]
    # Create tasks and store mapping from task to index
    initial_task_to_index = {
        asyncio.create_task(agent.critique(content, config, agent_loggers[agent.style])): i
        for i, agent in enumerate(agents)
    }
    initial_completed = 0
    initial_errors = 0

    for future in asyncio.as_completed(initial_task_to_index.keys()):
        original_index = initial_task_to_index[future] # Get index from map
        agent_style = agents[original_index].style
        agent_logger = agent_loggers[agent_style]
        status = "OK"
        try:
            result = await future
            initial_critiques[original_index] = result
            initial_completed += 1
        except Exception as e:
            root_logger.error(f"Council Orchestrator: Error during initial critique from agent '{agent_style}': {e}", exc_info=True)
            agent_logger.error(f"Initial critique failed: {e}", exc_info=True)
            initial_critiques[original_index] = {'agent_style': agent_style, 'critique_tree': {}, 'error': str(e)}
            initial_errors += 1
            initial_completed += 1
            status = f"ERROR ({type(e).__name__})"

        # Print progress update to console
        print(f"  Initial Critique {initial_completed}/{total_agents}: Agent '{agent_style}' completed ({status})")

    print(f"Initial Critique Round Finished. Completed: {initial_completed}, Errors: {initial_errors}")

    # 3. Self-Critique Round (Run concurrently with progress using as_completed)
    print(f"Running Self-Critique Round...")
    valid_initial_critiques_map = {i: c for i, c in enumerate(initial_critiques) if 'error' not in c}
    agents_doing_self_critique = len(valid_initial_critiques_map)
    self_critique_adjustments: List[Dict[str, Any]] = [{} for _ in range(total_agents)]
    self_critique_completed = 0
    self_critique_errors = 0

    if agents_doing_self_critique > 0:
        # Create tasks and store mapping from task to index
        self_critique_task_to_index = {}
        for i, own_critique in valid_initial_critiques_map.items():
            other_critiques = [c for j, c in valid_initial_critiques_map.items() if i != j]
            agent_logger = agent_loggers[agents[i].style]
            task = asyncio.create_task(agents[i].self_critique(own_critique, other_critiques, config, agent_logger))
            self_critique_task_to_index[task] = i

        for future in asyncio.as_completed(self_critique_task_to_index.keys()):
            original_agent_index = self_critique_task_to_index[future] # Get index from map
            agent_style = agents[original_agent_index].style
            agent_logger = agent_loggers[agent_style]
            status = "OK"
            try:
                result = await future
                self_critique_adjustments[original_agent_index] = result
                self_critique_completed += 1
            except Exception as e:
                root_logger.error(f"Council Orchestrator: Error during self-critique from agent '{agent_style}': {e}", exc_info=True)
                agent_logger.error(f"Self-critique failed: {e}", exc_info=True)
                self_critique_adjustments[original_agent_index] = {'agent_style': agent_style, 'adjustments': [], 'error': str(e)}
                self_critique_errors += 1
                self_critique_completed += 1
                status = f"ERROR ({type(e).__name__})"

            # Print progress update to console
            print(f"  Self-Critique {self_critique_completed}/{agents_doing_self_critique}: Agent '{agent_style}' completed ({status})")

        print(f"Self-Critique Round Finished. Completed: {self_critique_completed}, Errors: {self_critique_errors}")
    else:
        print("  Skipping self-critique (no valid initial critiques).")


    # 4. Synthesize Results
    print("Synthesizing final results...")
    final_assessment = "Council deliberation summary."
    final_points = []
    orchestrator_config = config.get('council_orchestrator', {})
    synthesis_confidence_threshold = orchestrator_config.get('synthesis_confidence_threshold', 0.4)

    adjustment_map: Dict[str, Dict[str, Any]] = {}
    for adj_data in filter(None, self_critique_adjustments):
        if 'error' not in adj_data:
            for adj in adj_data.get('adjustments', []):
                 adjustment_map[adj.get('target_claim_id')] = adj

    processed_claims = set()
    for critique in initial_critiques:
         if not critique or 'error' in critique or not critique.get('critique_tree'):
             continue

         tree = critique['critique_tree']
         claim_id = tree.get('id')
         initial_confidence = tree.get('confidence', 0.0)
         adjusted_confidence = initial_confidence

         if claim_id in adjustment_map:
             adjustment = adjustment_map[claim_id]
             adjusted_confidence += adjustment.get('confidence_delta', 0.0)
             adjusted_confidence = max(0.0, min(1.0, adjusted_confidence))

         claim_text = tree.get('claim', 'N/A')
         if adjusted_confidence >= synthesis_confidence_threshold and claim_text not in processed_claims:
             final_points.append({
                 'area': f"General ({critique.get('agent_style', 'N/A')})",
                 'critique': claim_text,
                 'severity': tree.get('severity', 'N/A'),
                 'confidence': round(adjusted_confidence, 2)
             })
             processed_claims.add(claim_text)

    placeholder_score = 100
    high_severity_count = 0
    medium_severity_count = 0
    low_severity_count = 0

    if final_points:
        no_findings = False
        final_assessment = f"Council synthesis complete. Identified {len(final_points)} primary point(s) meeting significance threshold."
        for point in final_points:
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
        final_assessment = "Council synthesis complete. No points met the significance threshold for reporting after deliberation."

    synthesized_data = {
        'final_assessment': final_assessment,
        'points': final_points,
        'no_findings': no_findings,
        'score_metrics': {
            'overall_score': placeholder_score,
            'high_severity_points': high_severity_count,
            'medium_severity_points': medium_severity_count,
            'low_severity_points': low_severity_count,
        }
    }
    print("Synthesis complete.")
    return synthesized_data
