"""
Client module for interacting with Anthropic's Claude 3.7 Sonnet API.
Provides standalone functions for the Syncretic Catalyst.
"""

import os
import anthropic
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ClaudeClientError(Exception):
    """Base exception for Claude client errors."""
    pass

def configure_client(api_key: Optional[str] = None) -> anthropic.Anthropic:
    """
    Configure and return an Anthropic client instance.
    
    Args:
        api_key: Optional API key (will use environment variable if not provided)
        
    Returns:
        Configured Anthropic client
        
    Raises:
        ClaudeClientError: If the API key is missing or invalid
    """
    try:
        # Use provided API key or get from environment
        key = api_key or os.environ.get("ANTHROPIC_API_KEY", "missing-api-key")
        
        if key == "missing-api-key":
            logger.error("No Anthropic API key provided")
            raise ClaudeClientError("Anthropic API key not found in environment or configuration")
            
        client = anthropic.Anthropic(api_key=key)
        return client
    except Exception as e:
        logger.error(f"Failed to configure Anthropic client: {e}")
        raise ClaudeClientError(f"Failed to configure Anthropic client: {e}") from e

def generate_content(
    messages: List[Dict[str, str]], 
    model_name: str = "claude-3-7-sonnet-20250219",
    max_tokens: int = 20000,
    temperature: float = 0.2,
    enable_thinking: bool = True,
    thinking_budget: Optional[int] = None,
    api_key: Optional[str] = None
) -> str:
    """
    Generate content using Claude API.
    
    Args:
        messages: List of message objects with "role" and "content" keys
        model_name: Claude model to use
        max_tokens: Maximum tokens in the response
        temperature: Temperature for generation
        enable_thinking: Whether to enable Claude's extended thinking capability
        thinking_budget: Number of tokens for thinking (min 1024, default: max_tokens - 1000)
        api_key: Optional API key to override environment variable
        
    Returns:
        Generated text content
        
    Raises:
        ClaudeClientError: For any errors during API call
    """
    try:
        logger.debug(f"Claude client - Running with enable_thinking={enable_thinking}, temperature={temperature}")
        
        # Get the client
        client = configure_client(api_key)
        
        # Extract system message if present
        system_prompt = None
        filtered_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                filtered_messages.append(msg)
        
        # Set temperature to 1.0 if thinking is enabled (Claude API requirement)
        actual_temperature = 1.0 if enable_thinking else temperature
                
        # Create the request parameters
        params = {
            "model": model_name,
            "messages": filtered_messages,
            "max_tokens": max_tokens,
            "temperature": actual_temperature,
            "stream": True  # Enable streaming
        }
        
        # Add system prompt if present
        if system_prompt:
            params["system"] = system_prompt
        
        # Add thinking if enabled
        if enable_thinking:
            # Default thinking budget is max_tokens minus a buffer, or 1024 if that would be too small
            if thinking_budget is None:
                thinking_budget = max(1024, max_tokens - 1000)
            
            # Ensure minimum of 1024 tokens and less than max_tokens
            thinking_budget = max(1024, min(thinking_budget, max_tokens - 100))
            
            params["thinking"] = {
                "type": "enabled",
                "budget_tokens": thinking_budget
            }
        
        # Debug print final params
        logger.debug(f"Claude API parameters: model={params['model']}, max_tokens={params['max_tokens']}, temperature={params['temperature']}")
        if 'thinking' in params:
            logger.debug(f"Thinking enabled with budget: {params['thinking']['budget_tokens']} tokens")
        
        # Start the stream
        stream = client.messages.create(**params)
        
        # Initialize variables for tracking response
        response_text = ""  # This will hold only the text content (not thinking)
        
        # Initialize variables to track the current context
        current_block_index = -1
        current_block_type = None
        
        logger.info("Streaming response from Claude...")
        
        for chunk in stream:
            # Handle message_start event
            if hasattr(chunk, 'type') and chunk.type == "message_start":
                # Just initialize the message, nothing to capture yet
                pass
            
            # Handle content_block_start event - this signals the start of a new content block
            elif hasattr(chunk, 'type') and chunk.type == "content_block_start":
                if hasattr(chunk, 'index'):
                    current_block_index = chunk.index
                if hasattr(chunk, 'content_block') and hasattr(chunk.content_block, 'type'):
                    current_block_type = chunk.content_block.type
                    if current_block_type == "thinking":
                        logger.debug("----- CLAUDE'S THINKING (not saved to file) -----")
                    elif current_block_type == "text":
                        logger.debug("----- CLAUDE'S RESPONSE -----")
            
            # Handle content_block_delta event - this contains the actual content
            elif hasattr(chunk, 'type') and chunk.type == "content_block_delta":
                if hasattr(chunk, 'delta'):
                    delta = chunk.delta
                    
                    # Handle thinking delta
                    if hasattr(delta, 'type') and delta.type == "thinking_delta" and hasattr(delta, 'thinking'):
                        # Just log thinking but don't add to response_text
                        logger.debug(f"Thinking: {delta.thinking}")
                    
                    # Handle text delta
                    elif hasattr(delta, 'type') and delta.type == "text_delta" and hasattr(delta, 'text'):
                        # Add to response_text
                        text = delta.text
                        response_text += text
            
            # Handle content_block_stop event - this signals the end of a content block
            elif hasattr(chunk, 'type') and chunk.type == "content_block_stop":
                if current_block_type == "thinking":
                    logger.debug("----- END OF THINKING -----")
                current_block_type = None
            
            # Handle message_stop event - this signals the end of the message
            elif hasattr(chunk, 'type') and chunk.type == "message_stop":
                logger.debug("----- RESPONSE COMPLETE -----")
        
        logger.info(f"Claude streaming complete - Response length: {len(response_text)} characters")
        return response_text
            
    except Exception as e:
        error_msg = f"Error from Claude API: {str(e)}"
        logger.error(error_msg)
        raise ClaudeClientError(error_msg) from e
