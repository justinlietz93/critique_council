"""
Client module for interacting with the Google Generative AI (Gemini) API.
Provides functions for the Syncretic Catalyst.
"""
import google.generativeai as genai
import json
import logging
import os
import time
from typing import Dict, Any, Tuple, Union, List, Optional

# Import the model configuration
from .model_config import get_gemini_config

# Local imports for exceptions
from .exceptions import ApiKeyError, ApiCallError, ApiResponseError, ApiBlockedError, JsonParsingError, JsonProcessingError
# Import DeepSeek client (will also be made synchronous)
from . import deepseek_v3_client

logger = logging.getLogger(__name__)

_gemini_model = None
_gemini_model_name = None
_client_configured = False
_deepseek_fallback_enabled = False

def configure_client(api_key: str):
    """Configures the Gemini client with the API key."""
    global _client_configured
    if _client_configured: return
    if not api_key:
        logger.error("Attempted to configure Gemini client without an API key.")
        raise ApiKeyError("API key is required to configure the Gemini client.")
    try:
        genai.configure(api_key=api_key)
        logger.info("Gemini client configured successfully.")
        _client_configured = True
    except Exception as e:
        logger.error(f"Failed to configure Gemini client: {e}", exc_info=True)
        raise ApiKeyError(f"Failed to configure Gemini client: {e}") from e

def configure_deepseek_fallback(config: Dict[str, Any]):
    """Configure the DeepSeek client for fallback."""
    global _deepseek_fallback_enabled
    deepseek_config = config.get('deepseek', {})
    api_key = deepseek_config.get('api_key')
    base_url = deepseek_config.get('base_url', 'https://api.deepseek.com/v1')
    if not api_key:
        logger.warning("DeepSeek fallback is disabled because no API key was provided")
        _deepseek_fallback_enabled = False
        return False
    try:
        # Assuming deepseek client also has a sync configure function
        deepseek_v3_client.configure_client(api_key, base_url)
        _deepseek_fallback_enabled = True
        logger.info("DeepSeek fallback is enabled and configured successfully")
        return True
    except Exception as e:
        logger.warning(f"Failed to configure DeepSeek fallback: {e}")
        _deepseek_fallback_enabled = False
        return False

def get_gemini_model(config: Dict[str, Any]):
    """Initializes and returns the Gemini generative model."""
    global _gemini_model, _gemini_model_name
    
    # Get config from the model_config module or use provided config
    gemini_config = get_gemini_config()
    
    # Override with config if provided
    if config and 'api' in config and 'gemini' in config['api']:
        gemini_config.update(config.get('api', {}).get('gemini', {}))
    
    api_key = config.get('api', {}).get('resolved_key') or os.environ.get("GEMINI_API_KEY")
    model_name = gemini_config.get('model_name', 'gemini-2.5-pro-exp-03-25')
    if _gemini_model is not None and _gemini_model_name == model_name:
        return _gemini_model
    configure_client(api_key)
    generation_config = {
        "temperature": gemini_config.get('temperature', 0.7),
        "top_p": gemini_config.get('top_p', 1.0),
        "top_k": gemini_config.get('top_k', 32),
        "max_output_tokens": gemini_config.get('max_output_tokens', 8192),
    }
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]
    try:
        _gemini_model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        _gemini_model_name = model_name
        logger.info(f"Gemini model '{model_name}' initialized.")
        return _gemini_model
    except Exception as e:
        logger.error(f"Failed to initialize Gemini model '{model_name}': {e}", exc_info=True)
        raise ApiCallError(f"Failed to initialize Gemini model '{model_name}': {e}") from e

def is_rate_limit_error(exception: Exception) -> bool:
    """Check if the exception is due to rate limiting."""
    error_msg = str(exception).lower()
    return ("429" in error_msg or "quota" in error_msg or
            "rate limit" in error_msg or "too many requests" in error_msg or
            "resource exhausted" in error_msg)

# Make synchronous
def generate_content(prompt: str, config: Dict[str, Any]) -> Tuple[str, str]:
    """
    Sends a prompt synchronously and returns text response and model name.
    """
    try:
        model = get_gemini_model(config)
        model_name_used = f"Gemini: {model.model_name}"
        logger.debug(f"Sending prompt to {model_name_used}:\n{prompt[:200]}...")
        # Use synchronous generate_content call
        response = model.generate_content(prompt) # No _async

        # Error handling remains largely the same structure
        if not response.candidates:
            blockage_reason = "Unknown"
            safety_ratings = None
            if response.prompt_feedback:
                try:
                    if hasattr(response.prompt_feedback.block_reason, 'name'):
                        blockage_reason = response.prompt_feedback.block_reason.name
                    else: blockage_reason = str(response.prompt_feedback.block_reason)
                    safety_ratings = response.prompt_feedback.safety_ratings
                except AttributeError: pass
            msg = f"Gemini API call failed or blocked. No candidates returned."
            logger.error(f"{msg} Reason: {blockage_reason}. Safety Ratings: {safety_ratings}")
            raise ApiBlockedError(msg, reason=blockage_reason, ratings=safety_ratings)

        candidate = response.candidates[0]
        if not candidate.content or not candidate.content.parts:
            finish_reason_value = getattr(candidate, 'finish_reason', "UNKNOWN")
            if hasattr(finish_reason_value, 'name'): finish_reason_str = finish_reason_value.name
            else: finish_reason_str = str(finish_reason_value)
            safety_ratings = getattr(candidate, 'safety_ratings', None)
            msg = f"Gemini API response candidate has no content parts. Finish Reason: {finish_reason_str}."
            logger.error(f"{msg} Safety Ratings: {safety_ratings}")
            if finish_reason_str == "SAFETY":
                raise ApiBlockedError(msg, reason=finish_reason_str, ratings=safety_ratings)
            else: raise ApiResponseError(msg)

        logger.debug("Gemini response received successfully.")
        text_parts = [part.text for part in candidate.content.parts if hasattr(part, 'text')]
        result_text = ''.join(text_parts)
        return result_text, model_name_used

    except (ApiBlockedError, ApiResponseError) as e: raise e
    except Exception as e:
        # Handle specific exceptions if the sync library raises different ones
        if e.__class__.__name__ == 'StopCandidateException': # Assuming name is same
            logger.error(f"Gemini API call stopped: {e}", exc_info=True)
            raise ApiBlockedError(f"Gemini API call stopped: {e}", reason="STOPPED") from e
        logger.error(f"Error during Gemini API call: {e}", exc_info=True)
        raise ApiCallError(f"Error during Gemini API call: {e}") from e

# Make synchronous
def generate_structured_content(prompt: str, config: Dict[str, Any], structure_hint: str = "Return only JSON.") -> Tuple[dict, str]:
    """
    Sends a prompt synchronously expecting structured JSON.
    """
    full_prompt = f"{prompt}\n\n{structure_hint}"
    try:
        # Call synchronous generate_content
        raw_response, model_name_used = generate_content(full_prompt, config) # No await

        cleaned_response = raw_response.strip()
        if cleaned_response.startswith("```json"): cleaned_response = cleaned_response[7:]
        elif cleaned_response.startswith("```"): cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"): cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()

        if not cleaned_response:
            logger.error("Gemini returned an empty response after cleaning for structured content.")
            raise ApiResponseError("Gemini returned an empty response after cleaning.")

        parsed_json = json.loads(cleaned_response)
        logger.debug("Successfully parsed JSON response from Gemini.")
        return parsed_json, model_name_used
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON response: {e}. Raw response was:\n---\n{raw_response}\n---", exc_info=True)
        raise JsonParsingError(f"Gemini response was not valid JSON: {e}") from e
    except (ApiCallError, ApiResponseError) as e: raise e
    except Exception as e:
        logger.error(f"Error processing Gemini structured response: {e}", exc_info=True)
        raise JsonProcessingError(f"Error processing Gemini structured response: {e}") from e

# Make synchronous
def call_gemini_with_retry(prompt_template: str, context: dict, config: Dict[str, Any], is_structured: bool = True) -> Tuple[Union[dict, str], str]:
    """
    Calls the appropriate Gemini client function synchronously with retries.
    """
    global _deepseek_fallback_enabled
    # Ensure fallback is configured if needed (sync check)
    if not _deepseek_fallback_enabled and 'deepseek' in config and config.get('deepseek',{}).get('api_key'):
        configure_deepseek_fallback(config)

    prompt = prompt_template.format(**context)
    last_exception = None
    max_retries = config.get('api', {}).get('gemini', {}).get('retries', 3)

    for attempt in range(max_retries):
        try:
            logger.debug(f"Gemini call attempt {attempt + 1}/{max_retries}...")
            if is_structured:
                response, model_name = generate_structured_content(prompt, config) # No await
            else:
                response, model_name = generate_content(prompt, config) # No await
            logger.debug(f"Gemini call successful after {attempt + 1} attempt(s) using {model_name}.")
            return response, model_name
        except Exception as e:
            last_exception = e
            logger.warning(f"Gemini call attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Retrying Gemini call in {wait_time} seconds...")
                time.sleep(wait_time) # Use synchronous sleep
            else:
                logger.error(f"Max retries ({max_retries}) reached for Gemini. Last error: {last_exception}", exc_info=True)
                if _deepseek_fallback_enabled and is_rate_limit_error(last_exception):
                    logger.info("Falling back to DeepSeek model after Gemini failure...")
                    try:
                        # Call synchronous deepseek client
                        if is_structured:
                            response, model_name = deepseek_v3_client.generate_structured_content(prompt, config) # No await
                        else:
                            response, model_name = deepseek_v3_client.generate_content(prompt, config) # No await
                        logger.info(f"DeepSeek fallback successful using {model_name}.")
                        return response, model_name
                    except Exception as fallback_error:
                        logger.error(f"DeepSeek fallback also failed: {fallback_error}", exc_info=True)

                raise ApiCallError(f"Gemini API call failed after {max_retries} retries and fallback attempt (if applicable).") from last_exception

    raise ApiCallError(f"Gemini API call failed unexpectedly after {max_retries} retries.") from last_exception


def run_gemini_client(
    messages: List[Dict[str, str]],
    model_name: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None
) -> str:
    """
    High-level function to run the Gemini client.
    This is the main function to call from the AI client interface.
    
    Args:
        messages: List of message objects
        model_name: Gemini model name (optional, will use config if not provided)
        max_tokens: Maximum tokens (optional, will use config if not provided)
        temperature: Temperature for generation (optional, will use config if not provided)
        
    Returns:
        Generated response
    """
    try:
        # Get config
        gemini_config = get_gemini_config()
        
        # Use provided values or get from config
        model = model_name or gemini_config.get('model_name', 'gemini-2.5-pro-exp-03-25')
        max_output_tokens = max_tokens or gemini_config.get('max_output_tokens', 8192)
        temp = temperature if temperature is not None else gemini_config.get('temperature', 0.6)
        
        logger.info(f"Using Gemini model: {model} with temperature: {temp}")
        
        # Convert messages format to single prompt
        system_msg = None
        user_content = ""
        
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            elif msg["role"] == "user":
                user_content += msg["content"] + "\n"
        
        # Combine system message with user prompt
        if system_msg:
            full_prompt = f"System instruction: {system_msg}\n\nUser message: {user_content}"
        else:
            full_prompt = user_content
        
        # Create config for call_gemini_with_retry
        config = {
            'api': {
                'gemini': {
                    'model_name': model,
                    'max_output_tokens': max_output_tokens,
                    'temperature': temp,
                    'retries': 3
                }
            }
        }
        
        # Call with retry logic
        response, model_used = call_gemini_with_retry(
            prompt_template="{content}",
            context={"content": full_prompt},
            config=config,
            is_structured=False
        )
        
        logger.info(f"Gemini response received from {model_used} - length: {len(response) if isinstance(response, str) else 'unknown'} characters")
        return response
        
    except Exception as e:
        error_msg = f"ERROR from Gemini: {str(e)}"
        logger.error(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg
