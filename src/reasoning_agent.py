# src/critique_module/reasoning_agent.py

"""
Defines the base class and specific implementations for reasoning agents
within the critique council.
"""

import os
import logging
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

# Import reasoning tree logic
from .reasoning_tree import execute_reasoning_tree # Now synchronous
# Import provider factory for LLM clients
from .providers import call_with_retry

# Define the base path for prompts relative to this file's location
PROMPT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'prompts'))

# Define the Peer Review enhancement text
PEER_REVIEW_ENHANCEMENT = """

--- PEER REVIEW ENHANCEMENT ---
Additionally, adopt the rigorous perspective of a deeply technical scientific researcher and subject matter expert within the specific domain of the input content. You must create a specific scientific persona with the following:

1. Full name with appropriate title (e.g., "Dr. Elizabeth Chen")
2. Academic credentials (Ph.D. or equivalent in a field directly relevant to the content)
3. Institutional affiliation (university, research institute, etc.)
4. Relevant specialization and experience (e.g., "15 years of research in quantum computing")

Your analysis must reflect this expertise, focusing on technical accuracy, methodological soundness, and advanced domain-specific insights, while still adhering to your core philosophical persona instructions. You should introduce yourself with these credentials at the beginning of your critique.
--- END PEER REVIEW ENHANCEMENT ---
"""

module_logger = logging.getLogger(__name__)

class ReasoningAgent(ABC):
    """
    Abstract base class for a reasoning agent in the critique council.
    """
    def __init__(self, style_name: str):
        self.style = style_name
        self.logger = module_logger

    def set_logger(self, logger: logging.Logger):
         self.logger = logger
         self.logger.info(f"Agent logger initialized for {self.style}")

    @abstractmethod
    def get_style_directives(self) -> str:
        pass

    # Synchronous
    def critique(self, content: str, config: Dict[str, Any], agent_logger: Optional[logging.Logger] = None, peer_review: bool = False) -> Dict[str, Any]: # Added peer_review flag
        """
        Generates an initial critique synchronously. Applies peer review enhancement if flag is set.
        """
        current_logger = agent_logger or self.logger
        current_logger.info(f"Starting initial critique... (Peer Review: {peer_review})")

        # Get base directives
        base_style_directives = self.get_style_directives()
        if "ERROR:" in base_style_directives:
             current_logger.error(f"Cannot perform critique due to prompt loading error: {base_style_directives}")
             return {
                 'agent_style': self.style,
                 'critique_tree': {},
                 'error': f"Failed to load style directives: {base_style_directives}"
             }

        # Apply enhancement if needed
        final_style_directives = base_style_directives
        if peer_review:
            final_style_directives += PEER_REVIEW_ENHANCEMENT
            current_logger.info("Peer Review enhancement applied to style directives.")

        critique_tree_result = execute_reasoning_tree(
            initial_content=content,
            style_directives=final_style_directives, # Use potentially enhanced directives
            agent_style=self.style,
            config=config,
            agent_logger=current_logger
        )

        if critique_tree_result is None:
             current_logger.warning("Critique generation terminated early (e.g., max depth or low confidence).")
             critique_tree_result = {
                 'id': 'root-terminated',
                 'claim': f'Critique generation terminated early for {self.style}.',
                 'evidence': '', 'confidence': 0.0, 'severity': 'N/A', 'sub_critiques': []
             }

        current_logger.info(f"Finished initial critique.")
        return {
            'agent_style': self.style,
            'critique_tree': critique_tree_result
        }

    # Synchronous
    def self_critique(self, own_critique: Dict[str, Any], other_critiques: List[Dict[str, Any]], config: Dict[str, Any], agent_logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
        """
        Performs self-critique synchronously (placeholder). Unused in Arbiter flow.
        """
        current_logger = agent_logger or self.logger
        current_logger.info(f"Starting self-critique (Placeholder - Currently Unused)...")
        adjustments = []
        own_tree_id = own_critique.get('critique_tree', {}).get('id', 'N/A')
        if own_tree_id != 'root-terminated' and own_tree_id != 'N/A':
            current_logger.info(f"Applying placeholder self-critique adjustment to claim ID: {own_tree_id}")
            adjustments.append(
                {
                    'target_claim_id': own_tree_id,
                    'confidence_delta': -0.05,
                    'reasoning': f'Placeholder self-critique adjustment by {self.style}.'
                }
            )
        else:
             current_logger.info("Skipping self-critique adjustment (invalid/terminated initial critique).")

        current_logger.info(f"Finished self-critique (Placeholder - Currently Unused).")
        return {
            'agent_style': self.style,
            'adjustments': adjustments
        }

# --- Concrete Philosopher Agent Implementations ---

class PhilosopherAgent(ReasoningAgent):
    """Base class for agents loading directives from prompt files."""
    def __init__(self, name: str, prompt_filename: str):
        super().__init__(name)
        self.prompt_filepath = os.path.join(PROMPT_DIR, prompt_filename)
        self._directives_cache: str | None = None

    def get_style_directives(self) -> str:
        """Loads and returns the directives from the agent's prompt file."""
        current_logger = self.logger
        if self._directives_cache is None:
            # Simplified error handling for brevity
            try:
                with open(self.prompt_filepath, 'r', encoding='utf-8') as f:
                    self._directives_cache = f.read()
                current_logger.debug(f"Directives loaded from {self.prompt_filepath}")
            except Exception as e:
                error_msg = f"Failed to read prompt file {self.prompt_filepath}: {e}"
                current_logger.error(error_msg, exc_info=True)
                self._directives_cache = f"ERROR: Failed to read prompt file for {self.style}."
        return self._directives_cache if self._directives_cache is not None else ""

# --- Specific Philosopher Agents ---

class AristotleAgent(PhilosopherAgent):
    """Critiques based on Aristotelian principles."""
    def __init__(self):
        super().__init__('Aristotle', 'critique_aristotle.txt')

class DescartesAgent(PhilosopherAgent):
    """Critiques based on Cartesian principles."""
    def __init__(self):
        super().__init__('Descartes', 'critique_descartes.txt')

class KantAgent(PhilosopherAgent):
    """Critiques based on Kantian principles."""
    def __init__(self):
        super().__init__('Kant', 'critique_kant.txt')

class LeibnizAgent(PhilosopherAgent):
    """Critiques based on Leibnizian principles."""
    def __init__(self):
        super().__init__('Leibniz', 'critique_leibniz.txt')

class PopperAgent(PhilosopherAgent):
    """Critiques based on Popperian principles."""
    def __init__(self):
        super().__init__('Popper', 'critique_popper.txt')

class RussellAgent(PhilosopherAgent):
    """Critiques based on Russellian principles."""
    def __init__(self):
        super().__init__('Russell', 'critique_russell.txt')

# --- Expert Arbiter Agent ---

class ExpertArbiterAgent(ReasoningAgent):
    """
    Agent responsible for evaluating philosophical critiques from a subject-matter
    expert perspective, providing context, adjustments, and an overall score.
    Uses the 'expert_arbiter.txt' prompt.
    """
    def __init__(self):
        super().__init__('ExpertArbiter')
        self.prompt_filepath = os.path.join(PROMPT_DIR, 'expert_arbiter.txt')
        self._directives_cache: str | None = None

    def get_style_directives(self) -> str:
        """Loads and returns the directives from the arbiter's prompt file."""
        # Same loading logic as PhilosopherAgent
        current_logger = self.logger
        if self._directives_cache is None:
            try:
                with open(self.prompt_filepath, 'r', encoding='utf-8') as f:
                    self._directives_cache = f.read()
                current_logger.debug(f"Directives loaded from {self.prompt_filepath}")
            except Exception as e:
                error_msg = f"Failed to read arbiter prompt file {self.prompt_filepath}: {e}"
                current_logger.error(error_msg, exc_info=True)
                self._directives_cache = f"ERROR: {error_msg}"
        return self._directives_cache if self._directives_cache is not None else ""

    def critique(self, content: str, config: Dict[str, Any], agent_logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
        raise NotImplementedError("ExpertArbiterAgent does not perform initial critique.")

    def self_critique(self, own_critique: Dict[str, Any], other_critiques: List[Dict[str, Any]], config: Dict[str, Any], agent_logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
         raise NotImplementedError("ExpertArbiterAgent does not perform self-critique.")

    # Synchronous arbitration method
    def arbitrate(self, original_content: str, initial_critiques: List[Dict[str, Any]], config: Dict[str, Any], agent_logger: Optional[logging.Logger] = None, peer_review: bool = False) -> Dict[str, Any]: # Added peer_review flag
        """
        Evaluates critiques, provides adjustments, and calculates an arbiter score.
        Applies peer review enhancement if flag is set.
        Returns a dictionary including 'adjustments', 'arbiter_overall_score',
        'arbiter_score_justification', and potentially 'error'.
        """
        current_logger = agent_logger or self.logger
        current_logger.info(f"Starting arbitration... (Peer Review: {peer_review})")

        # Get base directives
        base_style_directives = self.get_style_directives()
        if "ERROR:" in base_style_directives:
             current_logger.error(f"Cannot perform arbitration due to prompt loading error: {base_style_directives}")
             # Return structure indicating error but including expected keys if possible
             return {'agent_style': self.style, 'adjustments': [], 'arbiter_overall_score': None, 'arbiter_score_justification': None, 'error': base_style_directives}

        # Apply enhancement if needed
        final_style_directives = base_style_directives
        if peer_review:
            final_style_directives += PEER_REVIEW_ENHANCEMENT
            current_logger.info("Peer Review enhancement applied to arbiter directives.")

        try:
            critiques_json_str = json.dumps(initial_critiques, indent=2)
        except TypeError as e:
            error_msg = f"Failed to serialize critiques to JSON: {e}"
            current_logger.error(error_msg, exc_info=True)
            return {'agent_style': self.style, 'adjustments': [], 'arbiter_overall_score': None, 'arbiter_score_justification': None, 'error': error_msg}

        arbitration_context = {
            "original_content": original_content,
            "philosophical_critiques_json": critiques_json_str
        }

        try:
            # Expecting structured JSON with adjustments, score, and justification
            arbitration_result, model_used = call_with_retry(
                prompt_template=final_style_directives, # Use potentially enhanced directives
                context=arbitration_context,
                config=config,
                is_structured=True
            )

            # Validate the richer structure
            if (isinstance(arbitration_result, dict) and
                    'adjustments' in arbitration_result and
                    isinstance(arbitration_result['adjustments'], list) and
                    'arbiter_overall_score' in arbitration_result and
                    'arbiter_score_justification' in arbitration_result):

                 adj_count = len(arbitration_result['adjustments'])
                 score = arbitration_result['arbiter_overall_score']
                 justification = arbitration_result['arbiter_score_justification']
                 current_logger.info(f"Arbitration completed using {model_used}. Score={score}. Found {adj_count} adjustments.")
                 current_logger.debug(f"Arbiter Score Justification: {justification}")
                 # Return the full result including score and justification
                 return {
                     'agent_style': self.style,
                     'adjustments': arbitration_result['adjustments'],
                     'arbiter_overall_score': score,
                     'arbiter_score_justification': justification
                 }
            else:
                 current_logger.warning(f"Unexpected arbitration result structure received from {model_used}: {arbitration_result}")
                 return {'agent_style': self.style, 'adjustments': [], 'arbiter_overall_score': None, 'arbiter_score_justification': None, 'error': 'Invalid arbitration result structure'}

        except Exception as e:
            error_msg = f"Arbitration failed: {e}"
            current_logger.error(error_msg, exc_info=True)
            return {'agent_style': self.style, 'adjustments': [], 'arbiter_overall_score': None, 'arbiter_score_justification': None, 'error': error_msg}
