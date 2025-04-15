"""
Unified client module for interacting with DeepSeek API.
Provides standalone functions for the Syncretic Catalyst.
Supports both the DeepSeek Reasoner and DeepSeek Chat models.
"""

import os
import requests
import json
import logging
from typing import Dict, Any, Optional, List, Tuple, Union

# Import the model configuration
from .model_config import get_deepseek_config

# Import custom exceptions
from .exceptions import ApiKeyError, ApiCallError, ApiResponseError, JsonParsingError

logger = logging.getLogger(__name__)

class DeepseekClientError(Exception):
    """Base exception for DeepSeek client errors."""
    pass

# Global client state
_deepseek_api_key = None
_deepseek_base_url = None
_deepseek_configured = False

def configure_client(api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
    """
    Configure the DeepSeek client.
    
    Args:
        api_key: Optional API key (will use environment variable if not provided)
        base_url: Optional base URL for the API
        
    Raises:
        ApiKeyError: If no API key is provided
    """
    global _deepseek_api_key, _deepseek_base_url, _deepseek_configured
    
    # Get from environment if not provided
    key = api_key or os.environ.get("DEEPSEEK_API_KEY", "missing-api-key")
    
    if key == "missing-api-key":
        logger.error("No DeepSeek API key provided")
        raise ApiKeyError("API key is required for DeepSeek client.")
    
    # Get config settings
    config = get_deepseek_config()
    
    # Use provided base URL or get from config or use default
    url = base_url or config.get('base_url', 'https://api.deepseek.com/v1')
    
    _deepseek_api_key = key
    _deepseek_base_url = url
    _deepseek_configured = True
    
    logger.info(f"DeepSeek client configured for URL: {_deepseek_base_url}")

def generate_content(
    messages: List[Dict[str, str]], 
    model_name: str = "deepseek-reasoner",
    max_tokens: int = 8000,
    temperature: float = 0.0,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None
) -> Tuple[str, bool]:
    """
    Generate content using DeepSeek API.
    
    Args:
        messages: List of message objects with "role" and "content" keys
        model_name: DeepSeek model to use
        max_tokens: Maximum tokens in the response
        temperature: Temperature for generation
        api_key: Optional API key to override environment variable
        base_url: Optional base URL for the API
        
    Returns:
        Tuple of (generated_content, has_reasoning)
        
    Raises:
        DeepseekClientError: For any errors during API call
    """
    try:
        # Configure client if needed
        if not _deepseek_configured:
            configure_client(api_key, base_url)
        
        model_name_used = f"DeepSeek: {model_name}"
        logger.info(f"Using model: {model_name_used}")
        
        headers = {
            "Authorization": f"Bearer {_deepseek_api_key}",
            "Content-Type": "application/json"
        }
        
        # Check if any message contains reasoning
        has_reasoning = False
        for msg in messages:
            if "reasoning" in msg.get("content", "").lower():
                has_reasoning = True
                break
        
        # Prepare API request
        payload = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        # Determine API endpoint based on model
        if "chat" in model_name.lower():
            api_endpoint = f"{_deepseek_base_url}/chat/completions"
        else:
            api_endpoint = f"{_deepseek_base_url}/chat/completions"  # Default to chat API
        
        logger.debug(f"Sending request to DeepSeek API at {api_endpoint}")
        logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
        
        # Make API request
        response = requests.post(
            api_endpoint,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        # Handle response
        response.raise_for_status()
        data = response.json()
        
        # Process response
        if not data.get('choices') or not data['choices'][0].get('message'):
            logger.error(f"DeepSeek response missing expected content: {data}")
            raise ApiResponseError("DeepSeek response structure invalid")
        
        # Extract content
        content = data['choices'][0]['message'].get('content', '')
        
        logger.info(f"DeepSeek response received - length: {len(content)} characters")
        
        return content, has_reasoning
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during DeepSeek API call: {e}")
        raise DeepseekClientError(f"Error during DeepSeek API call: {e}") from e
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON response from DeepSeek: {e}")
        raise DeepseekClientError(f"DeepSeek response was not valid JSON: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error in DeepSeek client: {e}")
        raise DeepseekClientError(f"Unexpected error in DeepSeek client: {e}") from e

def generate_structured_content(
    prompt: str,
    model_name: str = "deepseek-reasoner", 
    structure_hint: str = "Return only JSON.",
    max_tokens: int = 8000,
    temperature: float = 0.0,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None
) -> Tuple[Dict[str, Any], str]:
    """
    Generate structured content (JSON) using DeepSeek API.
    
    Args:
        prompt: The prompt to send to the model
        model_name: DeepSeek model to use
        structure_hint: Instruction for structured output
        max_tokens: Maximum tokens in the response
        temperature: Temperature for generation
        api_key: Optional API key to override environment variable
        base_url: Optional base URL for the API
        
    Returns:
        Tuple of (parsed_json, model_name_used)
        
    Raises:
        DeepseekClientError: For any errors during API call
    """
    try:
        # Combine prompt with structure hint
        full_prompt = f"{prompt}\n\n{structure_hint}"
        
        # Create messages format
        messages = [{"role": "user", "content": full_prompt}]
        
        # Generate response
        raw_response, _ = generate_content(
            messages=messages,
            model_name=model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            api_key=api_key,
            base_url=base_url
        )
        
        # Process response to extract JSON
        cleaned_response = raw_response.strip()
        
        # Handle markdown code blocks
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
            
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
            
        cleaned_response = cleaned_response.strip()
        
        if not cleaned_response:
            logger.error("DeepSeek returned an empty response after cleaning for structured content.")
            raise ApiResponseError("DeepSeek returned an empty response after cleaning.")
        
        # Parse as JSON
        parsed_json = json.loads(cleaned_response)
        
        model_name_used = f"DeepSeek: {model_name}"
        logger.debug("Successfully parsed JSON response from DeepSeek.")
        
        return parsed_json, model_name_used
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON response from DeepSeek: {e}")
        raise JsonParsingError(f"DeepSeek response was not valid JSON: {e}") from e
    except Exception as e:
        logger.error(f"Error processing DeepSeek structured response: {e}")
        raise DeepseekClientError(f"Error processing DeepSeek structured response: {e}") from e

def run_deepseek_client(
    messages: List[Dict[str, str]], 
    model_name: str = "deepseek-reasoner",
    max_tokens: int = 8000,
    temperature: float = 0.0
) -> str:
    """
    High-level function to run the DeepSeek client.
    This is the main function to call from the AI client interface.
    
    Args:
        messages: List of message objects
        model_name: DeepSeek model name
        max_tokens: Maximum tokens
        temperature: Temperature for generation
        
    Returns:
        Generated response
    """
    try:
        logger.info(f"Using DeepSeek model: {model_name}")
        
        # Get API key from environment
        api_key = os.environ.get("DEEPSEEK_API_KEY", "missing-api-key")
        
        # Get config settings
        config = get_deepseek_config()
        base_url = config.get('base_url')
        
        # Generate content
        content, has_reasoning = generate_content(
            messages=messages,
            model_name=model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            api_key=api_key,
            base_url=base_url
        )
        
        return content
    except Exception as e:
        error_msg = f"ERROR from DeepSeek: {str(e)}"
        logger.error(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg
