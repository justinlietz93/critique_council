# src/providers/__init__.py

"""
Provider factory module for LLM clients.
Dynamically selects the appropriate provider client based on configuration.
"""

import logging
import importlib
from typing import Dict, Any, Tuple, Union, Callable, Optional

# Import exceptions for re-export
from .exceptions import (
    ProviderError, ApiKeyError, ApiCallError, ApiResponseError, 
    ApiBlockedError, JsonParsingError, JsonProcessingError,
    ModelCallError, MaxRetriesExceededError
)

logger = logging.getLogger(__name__)

# Define provider module mapping
PROVIDER_MODULES = {
    "gemini": "gemini_client",
    "deepseek": "deepseek_v3_client",
    "openai": "openai_client"
}

# Cache for loaded provider modules
_loaded_providers = {}

def get_provider_client(config: Dict[str, Any]) -> Tuple[str, Any]:
    """
    Returns the appropriate provider client module based on configuration.
    
    Args:
        config: Configuration dictionary containing API settings
        
    Returns:
        Tuple of (provider name, provider module)
    """
    # Get primary provider from config with fallback to gemini
    primary_provider = config.get("api", {}).get("primary_provider", "gemini")
    
    # Validate provider name
    if primary_provider not in PROVIDER_MODULES:
        valid_providers = ", ".join(PROVIDER_MODULES.keys())
        logger.error(f"Invalid provider '{primary_provider}'. Valid options: {valid_providers}")
        logger.warning(f"Falling back to 'gemini' provider")
        primary_provider = "gemini"
    
    # Return cached provider if available
    if primary_provider in _loaded_providers:
        return primary_provider, _loaded_providers[primary_provider]
    
    # Load provider module dynamically
    module_name = PROVIDER_MODULES[primary_provider]
    try:
        provider_module = importlib.import_module(f".{module_name}", package="src.providers")
        _loaded_providers[primary_provider] = provider_module
        logger.info(f"Loaded provider module: {primary_provider} ({module_name})")
        return primary_provider, provider_module
    except ImportError as e:
        logger.error(f"Failed to import provider module '{module_name}': {e}")
        if primary_provider != "gemini":
            logger.warning(f"Falling back to 'gemini' provider")
            return get_provider_client({**config, "api": {**config.get("api", {}), "primary_provider": "gemini"}})
        raise ImportError(f"Failed to import required provider module 'gemini_client': {e}")

def normalize_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes config structure to ensure compatibility with provider modules.
    Handles both older flat structure and newer nested providers structure.
    
    Args:
        config: Configuration dictionary to normalize
        
    Returns:
        Normalized configuration dictionary
    """
    api_config = config.get('api', {})
    normalized_config = {**config}  # Make a copy
    
    # Handle the newer nested 'providers' structure if present
    if 'providers' in api_config:
        # Copy the provider configs directly under 'api'
        providers = api_config.get('providers', {})
        normalized_api = {
            **api_config,  # Keep existing keys
        }
        
        # Move each provider config directly under 'api'
        for provider, provider_config in providers.items():
            if provider not in normalized_api:
                normalized_api[provider] = provider_config
        
        # Ensure resolved_key is present for backward compatibility
        primary_provider = api_config.get('primary_provider', 'gemini')
        if primary_provider in providers and 'resolved_key' in providers[primary_provider]:
            normalized_api['resolved_key'] = providers[primary_provider]['resolved_key']
        
        normalized_config['api'] = normalized_api
        
    logger.debug("Config normalized for provider compatibility")
    return normalized_config

def call_with_retry(
    prompt_template: str,
    context: Dict[str, Any],
    config: Dict[str, Any],
    is_structured: bool = False,
    **kwargs
) -> Tuple[Union[Dict[str, Any], str], str]:
    """
    Universal function to call the appropriate LLM provider based on configuration.
    
    Args:
        prompt_template: The prompt template to use
        context: Context dictionary to format into the prompt
        config: Configuration dictionary
        is_structured: Whether to expect and parse a JSON response
        
    Returns:
        Tuple of (response content, model name used)
    """
    # Normalize config to ensure compatibility with all provider modules
    normalized_config = normalize_config(config)
    provider_name, provider_module = get_provider_client(normalized_config)
    
    # Call the appropriate function based on the provider
    if provider_name == "gemini":
        return provider_module.call_gemini_with_retry(
            prompt_template=prompt_template,
            context=context,
            config=normalized_config,
            is_structured=is_structured
        )
    elif provider_name == "deepseek":
        # For deepseek, we need to handle direct calls differently
        full_prompt = prompt_template.format(**context)
        if is_structured:
            return provider_module.generate_structured_content(full_prompt, normalized_config)
        else:
            return provider_module.generate_content(full_prompt, normalized_config)
    elif provider_name == "openai":
        # Pass through any additional kwargs for OpenAI-specific parameters
        return provider_module.call_openai_with_retry(
            prompt_template=prompt_template,
            context=context,
            config=normalized_config,
            is_structured=is_structured,
            **kwargs
        )
    else:
        raise ValueError(f"Provider '{provider_name}' has no implementation in call_with_retry")
