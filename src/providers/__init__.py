"""
Provider implementations for various AI models.

This package contains implementations for different AI model providers:
- anthropic_client.py: Anthropic's Claude API (replaces claude_client.py)
- deepseek_client.py: DeepSeek's API (consolidates deepseek_client.py and deepseek_v3_client.py)
- openai_client.py: OpenAI's API
- gemini_client.py: Google's Gemini API
- model_config.py: Centralized configuration for all model providers
- decorators.py: Useful decorators for error handling, retries, caching, and other cross-cutting concerns

These implementations are used by both:
1) The AI clients interface in src/syncretic_catalyst/ai_clients.py
2) The main critique council application

Each provider module now exposes a high-level run_*_client function that accepts a standard
message format and handles all the provider-specific details internally.
"""

# Import the main client modules to make them available through the package
from . import anthropic_client
from . import deepseek_client
from . import openai_client
from . import gemini_client
from . import model_config
from . import decorators

# Import all the exception classes from our exceptions module for backwards compatibility
from .exceptions import (
    ProviderError,
    ApiCallError, 
    ApiResponseError, 
    ApiBlockedError,
    ApiKeyError,
    MaxRetriesExceededError,
    JsonParsingError, 
    JsonProcessingError
)

# Import decorator functions to make them easily available
from .decorators import (
    with_retry,
    with_error_handling,
    with_fallback,
    cache_result
)

# For backwards compatibility with existing code:
# Re-export the call_with_retry function that uses openai_client (default provider)
def call_with_retry(
    prompt_template, 
    context, 
    config, 
    is_structured=False
):
    """
    Compatibility function that forwards calls to the OpenAI client.
    Used by the main critique council application.
    
    Args:
        prompt_template: The template string with placeholders
        context: Dictionary with values for the placeholders
        config: Configuration options
        is_structured: Whether to expect structured (JSON) output
        
    Returns:
        Tuple of (response, model_used)
    """
    # Use openai_client by default
    return openai_client.call_openai_with_retry(
        prompt_template=prompt_template,
        context=context,
        config=config,
        is_structured=is_structured
    )
