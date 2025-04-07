"""
Client module for interacting with the Google Generative AI (Gemini) API.

Provides functions for configuring the client, initializing the model,
generating text content, generating structured JSON content, and handling retries.
"""
import google.generativeai as genai
import json
import logging
import asyncio
from typing import Dict, Any
# Remove the specific generation_types import
# from google.generativeai.types import generation_types 

# Local imports for exceptions
from .exceptions import ApiKeyError, ApiCallError, ApiResponseError, ApiBlockedError, JsonParsingError, JsonProcessingError
# Import DeepSeek client for fallback
from . import deepseek_v3_client

# Configure logger for this module
logger = logging.getLogger(__name__)

# Global variables to store initialized model
_gemini_model = None
_gemini_model_name = None
_client_configured = False
_deepseek_fallback_enabled = False

def configure_client(api_key: str):
    """Configures the Gemini client with the API key."""
    global _client_configured
    
    # Skip if already configured
    if _client_configured:
        return
        
    if not api_key:
        # This check might be redundant if config_loader ensures key exists
        # but kept for safety.
        logger.error("Attempted to configure Gemini client without an API key.")
        raise ApiKeyError("API key is required to configure the Gemini client.") # Use custom exception
    try:
        genai.configure(api_key=api_key)
        logger.info("Gemini client configured successfully.")
        _client_configured = True
    except Exception as e:
        # Catch potential configuration errors from the library
        logger.error(f"Failed to configure Gemini client: {e}", exc_info=True)
        raise ApiKeyError(f"Failed to configure Gemini client: {e}") from e # Use custom exception

def configure_deepseek_fallback(config: Dict[str, Any]):
    """Configure the DeepSeek client for fallback if API key is available."""
    global _deepseek_fallback_enabled
    
    deepseek_config = config.get('deepseek', {})
    api_key = deepseek_config.get('api_key')
    base_url = deepseek_config.get('base_url', 'https://api.deepseek.com/v1')
    
    if not api_key:
        logger.warning("DeepSeek fallback is disabled because no API key was provided")
        _deepseek_fallback_enabled = False
        return False
        
    try:
        deepseek_v3_client.configure_client(api_key, base_url)
        _deepseek_fallback_enabled = True
        logger.info("DeepSeek fallback is enabled and configured successfully")
        return True
    except Exception as e:
        logger.warning(f"Failed to configure DeepSeek fallback: {e}")
        _deepseek_fallback_enabled = False
        return False

def get_gemini_model(config: Dict[str, Any]):
    """Initializes and returns the Gemini generative model based on config."""
    global _gemini_model, _gemini_model_name
    
    api_config = config.get('api', {})
    api_key = api_config.get('resolved_key')
    model_name = api_config.get('model_name', 'gemini-2.5-pro-exp-03-25') # Default if missing
    
    # If model is already initialized with the same model name, reuse it
    if _gemini_model is not None and _gemini_model_name == model_name:
        return _gemini_model

    # Configure client if model is not yet initialized or model name has changed
    configure_client(api_key)

    # Configuration for safety settings and generation from config
    generation_config = {
        "temperature": api_config.get('temperature', 0.7),
        "top_p": api_config.get('top_p', 1.0), # Added default
        "top_k": api_config.get('top_k', 32),   # Added default
        "max_output_tokens": api_config.get('max_output_tokens', 8192),
    }
    # Default safety settings (can be made configurable later if needed)
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
            safety_settings=safety_settings # Use the defined settings
        )
        _gemini_model_name = model_name
        logger.info(f"Gemini model '{model_name}' initialized.")
        return _gemini_model
    except Exception as e:
        logger.error(f"Failed to initialize Gemini model '{model_name}': {e}", exc_info=True)
        # Catch potential model initialization errors
        raise ApiCallError(f"Failed to initialize Gemini model '{model_name}': {e}") from e # Use custom exception

def is_rate_limit_error(exception: Exception) -> bool:
    """Check if the exception is due to rate limiting."""
    error_msg = str(exception).lower()
    return (
        "429" in error_msg or 
        "quota" in error_msg or 
        "rate limit" in error_msg or
        "too many requests" in error_msg or
        "resource exhausted" in error_msg
    )

async def generate_content(prompt: str, config: Dict[str, Any]) -> str:
    """
    Sends a prompt to the configured Gemini model and returns the text response.

    Args:
        prompt: The prompt string to send to the model.
        config: The application configuration dictionary.

    Returns:
        The generated text content.

    Raises:
        ApiCallError: If the API call fails.
        ApiResponseError: If the response is invalid or empty.
        ApiBlockedError: If the request is blocked.
    """
    try:
        model = get_gemini_model(config)
        logger.debug(f"Sending prompt to Gemini model {model.model_name}:\n{prompt[:200]}...") # Log truncated prompt
        response = await model.generate_content_async(prompt)

        # More robust checking based on library structure
        if not response.candidates:
            blockage_reason = "Unknown"
            safety_ratings = None
            if response.prompt_feedback:
                try:
                    # Handle both string and enum types for block_reason
                    if hasattr(response.prompt_feedback.block_reason, 'name'):
                        blockage_reason = response.prompt_feedback.block_reason.name
                    else:
                        blockage_reason = str(response.prompt_feedback.block_reason)
                    safety_ratings = response.prompt_feedback.safety_ratings
                except AttributeError:
                    pass # Ignore if attributes don't exist
            msg = f"Gemini API call failed or blocked. No candidates returned."
            logger.error(f"{msg} Reason: {blockage_reason}. Safety Ratings: {safety_ratings}")
            raise ApiBlockedError(msg, reason=blockage_reason, ratings=safety_ratings)

        # Check the content of the first candidate
        candidate = response.candidates[0]
        if not candidate.content or not candidate.content.parts:
            # Check finish reason if content is missing
            finish_reason_value = getattr(candidate, 'finish_reason', "UNKNOWN")
            # Handle both string and enum types for finish_reason
            if hasattr(finish_reason_value, 'name'):
                finish_reason_str = finish_reason_value.name
            else:
                finish_reason_str = str(finish_reason_value)
                
            safety_ratings = getattr(candidate, 'safety_ratings', None)
            msg = f"Gemini API response candidate has no content parts. Finish Reason: {finish_reason_str}."
            logger.error(f"{msg} Safety Ratings: {safety_ratings}")
            # Treat safety block as ApiBlockedError, others as ApiResponseError
            if finish_reason_str == "SAFETY":
                raise ApiBlockedError(msg, reason=finish_reason_str, ratings=safety_ratings)
            else:
                raise ApiResponseError(msg)

        logger.debug("Gemini response received successfully.")
        # Extract the text from the response
        text_parts = []
        for part in candidate.content.parts:
            if hasattr(part, 'text'):
                text_parts.append(part.text)
        
        # Join all text parts into a single string
        result_text = ''.join(text_parts)
        return result_text

    except (ApiBlockedError, ApiResponseError) as e:
        # Re-raise specific errors already handled
        raise e
    except Exception as e:
        # Handle StopCandidateException by name instead of by type
        if e.__class__.__name__ == 'StopCandidateException':
            # Specific exception for stopped candidates (often safety)
            logger.error(f"Gemini API call stopped: {e}", exc_info=True)
            raise ApiBlockedError(f"Gemini API call stopped: {e}", reason="STOPPED") from e
        # Catch other potential API errors (network, auth, etc.)
        logger.error(f"Error during Gemini API call: {e}", exc_info=True)
        raise ApiCallError(f"Error during Gemini API call: {e}") from e


async def generate_structured_content(prompt: str, config: Dict[str, Any], structure_hint: str = "Return only JSON.") -> dict:
    """
    Sends a prompt expecting a structured (JSON) response from Gemini.

    Args:
        prompt: The prompt string, instructing the model to return JSON.
        config: The application configuration dictionary.
        structure_hint: A hint added to the prompt to reinforce JSON output.

    Returns:
        A dictionary parsed from the JSON response.

    Raises:
        ApiCallError: If the underlying text generation fails.
        ApiResponseError: If the response is empty after cleaning.
        JsonParsingError: If the response is not valid JSON.
    """
    full_prompt = f"{prompt}\n\n{structure_hint}"
    try:
        # Pass config down to generate_content
        raw_response = await generate_content(full_prompt, config)

        # Attempt to clean and parse the JSON response
        # Basic cleaning: remove potential markdown code fences and leading/trailing whitespace
        cleaned_response = raw_response.strip()
        # Remove markdown code blocks if present (compatible with all Python versions)
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:] # Remove ```json prefix
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:] # Remove ``` prefix
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3] # Remove ``` suffix
        cleaned_response = cleaned_response.strip()

        # Handle potential empty responses after cleaning
        if not cleaned_response:
            logger.error("Gemini returned an empty response after cleaning for structured content.")
            raise ApiResponseError("Gemini returned an empty response after cleaning.")

        parsed_json = json.loads(cleaned_response)
        logger.debug("Successfully parsed JSON response from Gemini.")
        return parsed_json
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON response: {e}. Raw response was:\n---\n{raw_response}\n---", exc_info=True)
        raise JsonParsingError(f"Gemini response was not valid JSON: {e}") from e
    except (ApiCallError, ApiResponseError) as e:
        # Re-raise errors from generate_content
        raise e
    except Exception as e:
        # Catch other potential errors during processing
        logger.error(f"Error processing Gemini structured response: {e}", exc_info=True)
        raise JsonProcessingError(f"Error processing Gemini structured response: {e}") from e


# --- Helper Function (Moved from main.py) ---

async def call_gemini_with_retry(prompt_template: str, context: dict, config: Dict[str, Any], is_structured: bool = True):
    """Calls the appropriate Gemini client function with retries, using config."""
    global _deepseek_fallback_enabled
    
    # Make sure DeepSeek fallback is configured if available in config
    if not _deepseek_fallback_enabled and 'deepseek' in config:
        configure_deepseek_fallback(config)
        
    prompt = prompt_template.format(**context)
    last_exception = None
    max_retries = config.get('api', {}).get('retries', 3) # Get retries from config

    for attempt in range(max_retries):
        try:
            if is_structured:
                # Pass config to generate_structured_content
                response = await generate_structured_content(prompt, config)
            else:
                 # Pass config to generate_content
                 # This branch might not be used if all prompts request JSON
                response = await generate_content(prompt, config)
            logger.debug(f"Gemini call successful after {attempt + 1} attempt(s).")
            return response
        except Exception as e:
            last_exception = e
            logger.warning(f"Gemini call attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time) # Exponential backoff
            else:
                logger.error(f"Max retries ({max_retries}) reached for prompt. Last error: {last_exception}", exc_info=True)
                
                # Check if this was a rate limit error and if DeepSeek fallback is available
                if _deepseek_fallback_enabled and is_rate_limit_error(last_exception):
                    logger.info("Falling back to DeepSeek model after Gemini rate limit...")
                    try:
                        if is_structured:
                            return await deepseek_v3_client.generate_structured_content(prompt, config)
                        else:
                            return await deepseek_v3_client.generate_content(prompt, config)
                    except Exception as fallback_error:
                        logger.error(f"DeepSeek fallback also failed: {fallback_error}", exc_info=True)
                        # If fallback also fails, raise the original error
                
                # Raise ApiCallError after all retries and fallbacks fail
                raise ApiCallError(f"Gemini API call failed after {max_retries} retries.") from last_exception
