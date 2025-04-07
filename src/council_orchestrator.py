# src/critique_module/council_orchestrator.py

"""
Manages the Reasoning Council workflow, including agent interaction
and critique synthesis.
"""

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

async def run_critique_council(content: str, config: Dict[str, Any]) -> Dict[str, Any]: # Make async, add config
    """
    Orchestrates the reasoning council critique process using async agent calls.

    Args:
        content: The text content to be critiqued.

    Returns:
        A dictionary containing the synthesized critique data.
        Example: {'final_assessment': '...', 'points': [], 'no_findings': bool}
    """
    # print("Council Orchestrator: Starting critique process.") # Removed trace

    if not AGENT_CLASSES:
         # This should not happen now, but keep as a safeguard
         # print("Council Orchestrator: FATAL - No agent classes defined.") # Removed trace
         raise ValueError("AGENT_CLASSES list is empty in council_orchestrator.")

    # 1. Instantiate Agents
    # print(f"Council Orchestrator: Instantiating {len(AGENT_CLASSES)} agents.") # Removed trace
    agents: List[ReasoningAgent] = [agent_cls() for agent_cls in AGENT_CLASSES]

    # 2. Initial Critique Round (Run concurrently)
    # print("Council Orchestrator: Starting initial critique round.") # Removed trace
    critique_tasks = [agent.critique(content, config) for agent in agents] # Pass config
    initial_critiques_results = await asyncio.gather(*critique_tasks, return_exceptions=True)

    initial_critiques: List[Dict[str, Any]] = []
    for i, result in enumerate(initial_critiques_results):
        agent_style = agents[i].style
        if isinstance(result, Exception):
            logger.error(f"Council Orchestrator: Error during initial critique from agent '{agent_style}': {result}", exc_info=result)
            initial_critiques.append({'agent_style': agent_style, 'critique_tree': {}, 'error': str(result)})
        else:
            initial_critiques.append(result) # Add successful critique result
    # print(f"Council Orchestrator: Initial critique round completed with {len(initial_critiques)} results.") # Removed trace

    # 3. Self-Critique Round (Run concurrently)
    # print("Council Orchestrator: Starting self-critique round.") # Removed trace
    self_critique_tasks = []
    valid_initial_critiques = [(i, c) for i, c in enumerate(initial_critiques) if 'error' not in c]

    for i, own_critique in valid_initial_critiques:
        other_critiques = [c for j, c in valid_initial_critiques if i != j]
        self_critique_tasks.append(agents[i].self_critique(own_critique, other_critiques, config)) # Pass config

    self_critique_results = await asyncio.gather(*self_critique_tasks, return_exceptions=True)

    self_critique_adjustments: List[Dict[str, Any]] = []
    valid_indices = [i for i, c in enumerate(initial_critiques) if 'error' not in c] # Indices of agents that ran self-critique
    for k, result in enumerate(self_critique_results):
         original_agent_index = valid_indices[k]
         agent_style = agents[original_agent_index].style
         if isinstance(result, Exception):
              logger.error(f"Council Orchestrator: Error during self-critique from agent '{agent_style}': {result}", exc_info=result)
              self_critique_adjustments.append({'agent_style': agent_style, 'adjustments': [], 'error': str(result)})
         else:
              self_critique_adjustments.append(result)
    # print(f"Council Orchestrator: Self-critique round completed with {len(self_critique_adjustments)} results.") # Removed trace


    # 4. Synthesize Results (Refined Placeholder Logic)
    # print("Council Orchestrator: Synthesizing final results...") # Removed trace
    final_assessment = "Council deliberation summary (placeholder)."
    final_points = []
    synthesis_confidence_threshold = 0.4 # Min confidence after self-critique to include point

    # Create a map of adjustments for easier lookup
    adjustment_map: Dict[str, Dict[str, Any]] = {}
    for adj_data in self_critique_adjustments:
        if 'error' not in adj_data:
            for adj in adj_data.get('adjustments', []):
                 # Use target_claim_id as key, store adjustment details
                 # Assumes one adjustment per claim ID per agent for simplicity now
                 adjustment_map[adj.get('target_claim_id')] = adj

    # Process initial critiques and apply adjustments
    processed_claims = set() # Avoid duplicating points if multiple agents raise similar top-level claims
    for critique in initial_critiques:
        if 'error' in critique or not critique.get('critique_tree'):
            continue

        tree = critique['critique_tree']
        claim_id = tree.get('id')
        initial_confidence = tree.get('confidence', 0.0)
        adjusted_confidence = initial_confidence

        # Apply self-critique adjustment if found
        if claim_id in adjustment_map:
            adjustment = adjustment_map[claim_id]
            adjusted_confidence += adjustment.get('confidence_delta', 0.0)
            adjusted_confidence = max(0.0, min(1.0, adjusted_confidence)) # Clamp confidence
            # print(f"Council Orchestrator: Adjusted confidence for claim '{claim_id}' from {initial_confidence:.2f} to {adjusted_confidence:.2f} based on self-critique.") # Removed trace

        # Include point if adjusted confidence is sufficient and claim not already added
        claim_text = tree.get('claim', 'N/A')
        if adjusted_confidence >= synthesis_confidence_threshold and claim_text not in processed_claims:
            final_points.append({
                'area': f"General ({critique.get('agent_style', 'N/A')})",
                'critique': claim_text,
                'severity': tree.get('severity', 'N/A'),
                'confidence': round(adjusted_confidence, 2) # Include adjusted confidence
            })
            processed_claims.add(claim_text)
            # print(f"Council Orchestrator: Included point: '{claim_text[:50]}...'") # Removed trace
        # Note: This simple synthesis only considers top-level claims.
        # A full implementation should traverse the tree and handle sub-critiques.

    # Determine final assessment based on points
    if final_points:
        no_findings = False
        final_assessment = f"Council identified {len(final_points)} primary point(s) for review based on synthesized analysis."
    else:
        no_findings = True
        final_assessment = "Council analysis concluded. No points met the significance threshold for reporting after deliberation."

    synthesized_data = {
        'final_assessment': final_assessment,
        'points': final_points,
        'no_findings': no_findings
        # Potentially include raw critiques/adjustments for traceability
        # 'raw_initial_critiques': initial_critiques,
        # 'raw_self_critiques': self_critique_adjustments
    }
    # print("Council Orchestrator: Synthesis complete.") # Removed trace
    # print("Council Orchestrator: Critique process finished.") # Removed trace
    return synthesized_data
