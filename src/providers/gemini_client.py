"""
Client module for interacting with the Google Generative AI (Gemini) API.

Provides functions for configuring the client, initializing the model,
generating text content, generating structured JSON content, and handling retries.
"""
import google.generativeai as genai
import json
import logging
import asyncio
from typing import Dict, Any, Tuple, Union # Import Tuple, Union

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
    if _client_configured: return # Skip if already configured
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
    api_config = config.get('api', {}).get('gemini', {}) # Look under 'gemini' sub-key
    api_key = config.get('api', {}).get('resolved_key') # Key is still top-level under 'api'
    model_name = api_config.get('model_name', 'gemini-2.5-pro-exp-03-25')
    if _gemini_model is not None and _gemini_model_name == model_name:
        return _gemini_model
    configure_client(api_key)
    generation_config = {
        "temperature": api_config.get('temperature', 0.7),
        "top_p": api_config.get('top_p', 1.0),
        "top_k": api_config.get('top_k', 32),
        "max_output_tokens": api_config.get('max_output_tokens', 8192),
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

async def generate_content(prompt: str, config: Dict[str, Any]) -> Tuple[str, str]:
    """
    Sends a prompt to the configured Gemini model and returns the text response
    along with the model name used.

    Returns:
        Tuple[str, str]: (Generated text content, model name used)
    """
    try:
        model = get_gemini_model(config)
        model_name_used = f"Gemini: {model.model_name}"
        logger.debug(f"Sending prompt to {model_name_used}:\n{prompt[:200]}...")
        response = await model.generate_content_async(prompt)

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
        return result_text, model_name_used # Return text and model name

    except (ApiBlockedError, ApiResponseError) as e: raise e
    except Exception as e:
        if e.__class__.__name__ == 'StopCandidateException':
            logger.error(f"Gemini API call stopped: {e}", exc_info=True)
            raise ApiBlockedError(f"Gemini API call stopped: {e}", reason="STOPPED") from e
        logger.error(f"Error during Gemini API call: {e}", exc_info=True)
        raise ApiCallError(f"Error during Gemini API call: {e}") from e

async def generate_structured_content(prompt: str, config: Dict[str, Any], structure_hint: str = "Return only JSON.") -> Tuple[dict, str]:
    """
    Sends a prompt expecting a structured (JSON) response from Gemini.

    Returns:
        Tuple[dict, str]: (Parsed JSON dictionary, model name used)
    """
    full_prompt = f"{prompt}\n\n{structure_hint}"
    try:
        raw_response, model_name_used = await generate_content(full_prompt, config) # Get model name too

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
        return parsed_json, model_name_used # Return JSON and model name
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON response: {e}. Raw response was:\n---\n{raw_response}\n---", exc_info=True)
        raise JsonParsingError(f"Gemini response was not valid JSON: {e}") from e
    except (ApiCallError, ApiResponseError) as e: raise e
    except Exception as e:
        logger.error(f"Error processing Gemini structured response: {e}", exc_info=True)
        raise JsonProcessingError(f"Error processing Gemini structured response: {e}") from e

async def call_gemini_with_retry(prompt_template: str, context: dict, config: Dict[str, Any], is_structured: bool = True) -> Tuple[Union[dict, str], str]:
    """
    Calls the appropriate Gemini client function with retries, using config.
    Returns the result and the name of the model that successfully responded.
    """
    global _deepseek_fallback_enabled
    if not _deepseek_fallback_enabled and 'deepseek' in config and config.get('deepseek',{}).get('api_key'):
        configure_deepseek_fallback(config)

    prompt = prompt_template.format(**context)
    last_exception = None
    max_retries = config.get('api', {}).get('gemini', {}).get('retries', 3) # Get retries from gemini config

    for attempt in range(max_retries):
        try:
            logger.debug(f"Gemini call attempt {attempt + 1}/{max_retries}...")
            if is_structured:
                response, model_name = await generate_structured_content(prompt, config)
            else:
                response, model_name = await generate_content(prompt, config)
            logger.debug(f"Gemini call successful after {attempt + 1} attempt(s) using {model_name}.")
            return response, model_name # Return result and model name
        except Exception as e:
            last_exception = e
            logger.warning(f"Gemini call attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Retrying Gemini call in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Max retries ({max_retries}) reached for Gemini. Last error: {last_exception}", exc_info=True)
                if _deepseek_fallback_enabled and is_rate_limit_error(last_exception):
                    logger.info("Falling back to DeepSeek model after Gemini failure...")
                    try:
                        if is_structured:
                            # DeepSeek client needs to return model name too
                            response, model_name = await deepseek_v3_client.generate_structured_content(prompt, config)
                        else:
                            response, model_name = await deepseek_v3_client.generate_content(prompt, config)
                        logger.info(f"DeepSeek fallback successful using {model_name}.")
                        return response, model_name # Return result and model name
                    except Exception as fallback_error:
                        logger.error(f"DeepSeek fallback also failed: {fallback_error}", exc_info=True)
                        # Fall through to raise original error if fallback fails

                raise ApiCallError(f"Gemini API call failed after {max_retries} retries and fallback attempt (if applicable).") from last_exception

    # This part should ideally not be reached if logic above is correct, but added for safety
    raise ApiCallError(f"Gemini API call failed unexpectedly after {max_retries} retries.") from last_exception
