# src/critique_module/reasoning_agent.py

"""
Defines the base class and specific implementations for reasoning agents
within the critique council.
"""

import os
import logging
import json # Import json <<<< ADDED IMPORT
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

# Import reasoning tree logic
from .reasoning_tree import execute_reasoning_tree # Now synchronous
# Import LLM client for Arbiter
from .providers import gemini_client # <<<< ADDED IMPORT

# Define the base path for prompts relative to this file's location
PROMPT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'prompts'))

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
    def critique(self, content: str, config: Dict[str, Any], agent_logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
        """
        Generates an initial critique synchronously.
        """
        current_logger = agent_logger or self.logger
        current_logger.info(f"Starting initial critique...")
        style_directives = self.get_style_directives()
        if "ERROR:" in style_directives:
             current_logger.error(f"Cannot perform critique due to prompt loading error: {style_directives}")
             return {
                 'agent_style': self.style,
                 'critique_tree': {},
                 'error': f"Failed to load style directives: {style_directives}"
             }

        # Call the synchronous reasoning tree function
        critique_tree_result = execute_reasoning_tree(
            initial_content=content,
            style_directives=style_directives,
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
        Performs self-critique synchronously (placeholder).
        NOTE: This method is no longer called by the orchestrator using the ExpertArbiterAgent approach.
              It remains here but is effectively unused in the current flow.
        """
        current_logger = agent_logger or self.logger
        current_logger.info(f"Starting self-critique (Placeholder - Currently Unused)...")
        # Placeholder logic remains synchronous
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
            if not os.path.exists(self.prompt_filepath):
                 alt_prompt_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'prompts'))
                 alt_filepath = os.path.join(alt_prompt_dir, os.path.basename(self.prompt_filepath))
                 if os.path.exists(alt_filepath):
                      self.prompt_filepath = alt_filepath
                 else:
                      error_msg = f"Prompt file not found at {self.prompt_filepath} or {alt_filepath}"
                      current_logger.error(error_msg)
                      self._directives_cache = f"ERROR: Prompt file not found for {self.style}."
                      return self._directives_cache
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
    def __init__(self): super().__init__('Aristotle', 'critique_aristotle.txt')
class DescartesAgent(PhilosopherAgent):
    def __init__(self): super().__init__('Descartes', 'critique_descartes.txt')
class KantAgent(PhilosopherAgent):
    def __init__(self): super().__init__('Kant', 'critique_kant.txt')
class LeibnizAgent(PhilosopherAgent):
    def __init__(self): super().__init__('Leibniz', 'critique_leibniz.txt')
class PopperAgent(PhilosopherAgent):
    def __init__(self): super().__init__('Popper', 'critique_popper.txt')
class RussellAgent(PhilosopherAgent):
    def __init__(self): super().__init__('Russell', 'critique_russell.txt')

# --- Expert Arbiter Agent ---

class ExpertArbiterAgent(ReasoningAgent):
    """
    Agent responsible for evaluating philosophical critiques from a subject-matter
    expert perspective, providing context and adjustments.
    Uses the 'expert_arbiter.txt' prompt.
    """
    def __init__(self):
        super().__init__('ExpertArbiter')
        self.prompt_filepath = os.path.join(PROMPT_DIR, 'expert_arbiter.txt')
        self._directives_cache: str | None = None

    def get_style_directives(self) -> str:
        """Loads and returns the directives from the arbiter's prompt file."""
        current_logger = self.logger
        if self._directives_cache is None:
            if not os.path.exists(self.prompt_filepath):
                 error_msg = f"Arbiter prompt file not found at {self.prompt_filepath}"
                 current_logger.error(error_msg)
                 self._directives_cache = f"ERROR: {error_msg}"
                 return self._directives_cache
            try:
                with open(self.prompt_filepath, 'r', encoding='utf-8') as f:
                    self._directives_cache = f.read()
                current_logger.debug(f"Directives loaded from {self.prompt_filepath}")
            except Exception as e:
                error_msg = f"Failed to read arbiter prompt file {self.prompt_filepath}: {e}"
                current_logger.error(error_msg, exc_info=True)
                self._directives_cache = f"ERROR: Failed to read prompt file for {self.style}."

        return self._directives_cache if self._directives_cache is not None else ""

    def critique(self, content: str, config: Dict[str, Any], agent_logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
        raise NotImplementedError("ExpertArbiterAgent does not perform initial critique.")

    def self_critique(self, own_critique: Dict[str, Any], other_critiques: List[Dict[str, Any]], config: Dict[str, Any], agent_logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
         raise NotImplementedError("ExpertArbiterAgent does not perform self-critique.")

    # Synchronous arbitration method
    def arbitrate(self, original_content: str, initial_critiques: List[Dict[str, Any]], config: Dict[str, Any], agent_logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
        """
        Evaluates philosophical critiques against original content from an expert view.
        """
        current_logger = agent_logger or self.logger
        current_logger.info("Starting arbitration...")

        style_directives = self.get_style_directives()
        if "ERROR:" in style_directives:
             current_logger.error(f"Cannot perform arbitration due to prompt loading error: {style_directives}")
             return {'agent_style': self.style, 'adjustments': [], 'error': style_directives}

        try:
            critiques_json_str = json.dumps(initial_critiques, indent=2)
        except TypeError as e:
            current_logger.error(f"Failed to serialize critiques to JSON: {e}", exc_info=True)
            return {'agent_style': self.style, 'adjustments': [], 'error': f"Failed to serialize critiques: {e}"}

        arbitration_context = {
            "original_content": original_content,
            "philosophical_critiques_json": critiques_json_str
        }

        try:
            # Call synchronous LLM function
            arbitration_result, model_used = gemini_client.call_gemini_with_retry( # No await
                prompt_template=style_directives,
                context=arbitration_context,
                config=config,
                is_structured=True
            )

            if isinstance(arbitration_result, dict) and 'adjustments' in arbitration_result and isinstance(arbitration_result['adjustments'], list):
                 current_logger.info(f"Arbitration completed using {model_used}. Found {len(arbitration_result['adjustments'])} adjustments.")
                 return {
                     'agent_style': self.style,
                     'adjustments': arbitration_result['adjustments']
                 }
            else:
                 current_logger.warning(f"Unexpected arbitration result structure received from {model_used}: {arbitration_result}")
                 return {'agent_style': self.style, 'adjustments': [], 'error': 'Invalid arbitration result structure'}

        except Exception as e:
            current_logger.error(f"Arbitration failed: {e}", exc_info=True)
            return {'agent_style': self.style, 'adjustments': [], 'error': f"Arbitration failed: {e}"}
