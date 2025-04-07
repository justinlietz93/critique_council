"""
Synchronous client module for interacting with the DeepSeek API.
Used as a fallback for the Gemini client.
"""
import logging
import requests # Use synchronous requests library
import json
from typing import Dict, Any, Tuple, Union

# Import custom exceptions from the same directory
from .exceptions import ApiKeyError, ApiCallError, ApiResponseError, JsonParsingError

logger = logging.getLogger(__name__)

_deepseek_api_key = None
_deepseek_base_url = None
_deepseek_configured = False

def configure_client(api_key: str, base_url: str = 'https://api.deepseek.com/v1'):
    """Configures the DeepSeek client."""
    global _deepseek_api_key, _deepseek_base_url, _deepseek_configured
    if not api_key:
        logger.error("Attempted to configure DeepSeek client without an API key.")
        raise ApiKeyError("API key is required for DeepSeek client.")

    _deepseek_api_key = api_key
    _deepseek_base_url = base_url
    _deepseek_configured = True
    logger.info(f"DeepSeek client configured for URL: {_deepseek_base_url}")

# Make synchronous
def generate_content(prompt: str, config: Dict[str, Any]) -> Tuple[str, str]:
    """
    Sends a prompt synchronously to the DeepSeek model using requests.
    Returns the text response and the model name used.
    """
    if not _deepseek_configured:
        raise ApiCallError("DeepSeek client not configured.")

    deepseek_config = config.get('deepseek', {})
    model_name = deepseek_config.get('model_name', 'deepseek-chat')
    model_name_used = f"DeepSeek: {model_name}"

    headers = {
        "Authorization": f"Bearer {_deepseek_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
    }

    api_url = f"{_deepseek_base_url}/chat/completions"
    logger.debug(f"Sending prompt to {model_name_used} at {api_url}...")

    try:
        # Use synchronous requests.post
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status() # Raise HTTPError for bad responses
        data = response.json()

        if not data.get('choices') or not data['choices'][0].get('message') or not data['choices'][0]['message'].get('content'):
            logger.error(f"DeepSeek response missing expected content: {data}")
            raise ApiResponseError("DeepSeek response structure invalid or content missing.")

        result_text = data['choices'][0]['message']['content']
        logger.debug("DeepSeek response received successfully.")
        return result_text.strip(), model_name_used

    except requests.exceptions.RequestException as e:
        logger.error(f"Error during DeepSeek API call: {e}", exc_info=True)
        raise ApiCallError(f"Error during DeepSeek API call: {e}") from e
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON response from DeepSeek: {e}. Raw response: {response.text}", exc_info=True)
        raise JsonParsingError(f"DeepSeek response was not valid JSON: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error during DeepSeek call: {e}", exc_info=True)
        raise ApiCallError(f"Unexpected error during DeepSeek call: {e}") from e

# Make synchronous
def generate_structured_content(prompt: str, config: Dict[str, Any], structure_hint: str = "Return only JSON.") -> Tuple[dict, str]:
    """
    Sends a prompt synchronously expecting structured JSON from DeepSeek.
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
            logger.error("DeepSeek returned an empty response after cleaning for structured content.")
            raise ApiResponseError("DeepSeek returned an empty response after cleaning.")

        parsed_json = json.loads(cleaned_response)
        logger.debug("Successfully parsed JSON response from DeepSeek.")
        return parsed_json, model_name_used

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON response from DeepSeek: {e}. Raw response was:\n---\n{raw_response}\n---", exc_info=True)
        raise JsonParsingError(f"DeepSeek response was not valid JSON: {e}") from e
    except (ApiCallError, ApiResponseError) as e: raise e
    except Exception as e:
        logger.error(f"Error processing DeepSeek structured response: {e}", exc_info=True)
        raise JsonParsingError(f"Error processing DeepSeek structured response: {e}") from e
