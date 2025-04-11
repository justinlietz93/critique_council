# src/providers/openai_client.py

"""
Client interface for OpenAI API.
Provides functions to call OpenAI models with retry logic.
"""

import logging
import json
import time
import os
from typing import Dict, Any, Tuple, Optional, List, Union
from openai import OpenAI
from .exceptions import ModelCallError, MaxRetriesExceededError

logger = logging.getLogger(__name__)

def call_openai_with_retry(
    prompt_template: str,
    context: Dict[str, Any],
    config: Dict[str, Any],
    is_structured: bool = False,
    **kwargs
) -> Tuple[Union[str, Dict[str, Any]], str]:
    """
    Calls OpenAI API with the given prompt template and context.
    Implements retry logic for transient errors.
    
    Args:
        prompt_template: The base prompt template
        context: Dictionary of variables to be formatted into the template
        config: Configuration dictionary containing API settings
        is_structured: Whether to expect and parse a JSON response
        system_message: Optional system message to override the default
        max_tokens: Optional maximum token limit for the response
        
    Returns:
        Tuple of (response content, model used)
    """
    # Extract configuration - check both direct and nested paths
    api_config = config.get('api', {})
    openai_config = api_config.get('openai', {})
    
    # Handle system message from either kwargs or config
    system_message = kwargs.get('system_message') or openai_config.get('system_message')
    max_tokens = kwargs.get('max_tokens') or openai_config.get('max_tokens')
    
    # Get model and API key
    default_model = openai_config.get('model', 'o1')  # Use o1 as default model
    api_key = openai_config.get('resolved_key') or os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        raise ModelCallError("OpenAI API key not found in configuration or environment")
    
    # Configure retries
    max_retries = openai_config.get('retries', 3)
    retry_delay_base = openai_config.get('retry_delay_base', 2)
    
    # Create OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Format prompt with context
    formatted_prompt = prompt_template
    for key, value in context.items():
        placeholder = f"{{{key}}}"
        if placeholder in formatted_prompt:
            formatted_prompt = formatted_prompt.replace(placeholder, str(value))
    
    # Prepare system message
    if not system_message:
        system_message = "You are a highly knowledgeable assistant specialized in scientific and philosophical critique."
    
    if is_structured:
        system_message += " Respond strictly in valid JSON format."
    
    # Prepare message structure
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": formatted_prompt}
    ]
    
    # Prepare model parameters
    model_params = {
        "model": default_model,
        "messages": messages,
        "temperature": api_config.get('temperature', 0.2),
    }
    
    # Handle token limits based on model 
    if max_tokens:
        # O1 models use max_completion_tokens instead of max_tokens
        if 'o1' in default_model.lower():
            model_params["max_completion_tokens"] = max_tokens
        else:
            model_params["max_tokens"] = max_tokens
    
    if is_structured:
        model_params["response_format"] = {"type": "json_object"}
    
    # Implement retry logic
    retry_count = 0
    last_exception = None
    
    while retry_count <= max_retries:
        try:
            logger.debug(f"Calling OpenAI API with model {default_model} (attempt {retry_count + 1})")
            
            # Make the API call
            response = client.chat.completions.create(**model_params)
            
            # Extract content
            content = response.choices[0].message.content
            
            # Parse JSON if structured
            if is_structured and content:
                try:
                    content_dict = json.loads(content)
                    return content_dict, default_model
                except json.JSONDecodeError as e:
                    raise ModelCallError(f"Failed to parse JSON response: {e}")
            
            return content, default_model
            
        except Exception as e:
            last_exception = e
            retry_count += 1
            
            if retry_count <= max_retries:
                delay = retry_delay_base ** retry_count
                logger.warning(f"OpenAI API call failed, retrying in {delay}s: {e}")
                time.sleep(delay)
            else:
                logger.error(f"OpenAI API call failed after {max_retries} retries: {e}")
                break
    
    if last_exception:
        raise MaxRetriesExceededError(f"Maximum retries exceeded: {last_exception}")
    else:
        raise ModelCallError("Unknown error occurred during OpenAI API call")
