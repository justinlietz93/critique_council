"""
ai_clients.py

Minimal approach to calling:
1) Claude 3.7 Sonnet (Anthropic-based)
2) DeepSeek R1 (OpenAI-based approach)

No streaming, no chunker, just a single .run(...) method that returns final text.
"""

import os
import anthropic
import openai

class Claude37SonnetClient:
    """
    Minimal client for Claude 3.7 Sonnet. 
    Uses environment variables:
      - ANTHROPIC_API_KEY: The key for Anthropic
      - CLAUDE_MODEL (optional, default "claude-3-7-sonnet-20250219")
    """

    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "missing-api-key")
        self.model_name = os.environ.get("CLAUDE_MODEL", "claude-3-7-sonnet-20250219")
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def run(self, messages, max_tokens=20000, temperature=0.2, enable_thinking=True, thinking_budget=None):
        """
        Stream-enabled call to the Claude 3.7 Sonnet model.
        :param messages: list of { "role": "user"/"assistant"/"system", "content": "..."}
        :param max_tokens: limit for the generated text
        :param temperature: Controls randomness (0.0 to 1.0)
        :param enable_thinking: Whether to enable Claude's extended thinking capability
        :param thinking_budget: Number of tokens for thinking (min 1024, default to max_tokens - 1000)
        :return: final string
        """
        try:
            print(f"\n[DEBUG] Claude client - Running with enable_thinking={enable_thinking}, temperature={temperature}")
            
            # Extract system message if present
            system_prompt = None
            filtered_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_prompt = msg["content"]
                else:
                    filtered_messages.append(msg)
            
            # Set temperature to 1.0 if thinking is enabled (Claude API requirement)
            if enable_thinking:
                temperature = 1.0
                
            # Create the request parameters
            params = {
                "model": self.model_name,
                "messages": filtered_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
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
            else:
                # Make sure thinking is explicitly NOT included in params when disabled
                if "thinking" in params:
                    del params["thinking"]
                print("[DEBUG] Thinking mode is explicitly disabled for this request")
            
            # Debug print final params
            print(f"\n[DEBUG] Final API parameters:")
            print(f"  - model: {params['model']}")
            print(f"  - max_tokens: {params['max_tokens']}")
            print(f"  - temperature: {params['temperature']}")
            print(f"  - thinking: {'present' if 'thinking' in params else 'DISABLED'}")
            if 'thinking' in params:
                print(f"    - type: {params['thinking']['type']}")
                print(f"    - budget: {params['thinking']['budget_tokens']} tokens")
            
            # Start the stream
            stream = self.client.messages.create(**params)
            
            # Initialize variables for tracking response
            response_text = ""  # This will hold only the text content (not thinking)
            
            # Initialize variables to track the current context
            current_block_index = -1
            current_block_type = None
            
            print("\nStreaming response from Claude...")
            
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
                            print("\n----- CLAUDE'S THINKING (not saved to file) -----\n", flush=True)
                        elif current_block_type == "text":
                            print("\n----- CLAUDE'S RESPONSE -----\n", flush=True)
                
                # Handle content_block_delta event - this contains the actual content
                elif hasattr(chunk, 'type') and chunk.type == "content_block_delta":
                    if hasattr(chunk, 'delta'):
                        delta = chunk.delta
                        
                        # Handle thinking delta
                        if hasattr(delta, 'type') and delta.type == "thinking_delta" and hasattr(delta, 'thinking'):
                            # Print thinking but don't add to response_text
                            print(delta.thinking, end="", flush=True)
                        
                        # Handle text delta
                        elif hasattr(delta, 'type') and delta.type == "text_delta" and hasattr(delta, 'text'):
                            # Add to response_text AND print
                            text = delta.text
                            response_text += text
                            print(text, end="", flush=True)
                
                # Handle content_block_stop event - this signals the end of a content block
                elif hasattr(chunk, 'type') and chunk.type == "content_block_stop":
                    if current_block_type == "thinking":
                        print("\n----- END OF THINKING -----\n", flush=True)
                    current_block_type = None
                
                # Handle message_stop event - this signals the end of the message
                elif hasattr(chunk, 'type') and chunk.type == "message_stop":
                    print("\n----- RESPONSE COMPLETE -----", flush=True)
            
            print(f"\n\nStreaming complete - Final response length: {len(response_text)} characters")
            return response_text
                
        except Exception as e:
            error_msg = f"ERROR from Claude: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return error_msg


class DeepseekR1Client:
    """
    Minimal client for DeepSeek R1 using openai library with a custom base URL.
    Env variables:
      - DEEPSEEK_API_KEY
    """

    def __init__(self):
        self.api_key = os.environ.get("DEEPSEEK_API_KEY", "missing-deepseek-key")
        # Create a proper client instance using the modern SDK pattern
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
        self.model_name = "deepseek-reasoner"

    def run(self, messages, max_tokens=8000, temperature=0.0):
        """
        Non-stream call to DeepSeek R1
        
        :param messages: list of { "role": "user"/"assistant"/"system", "content": "..."}
        :param max_tokens: limit for the generated text
        :param temperature: Controls randomness (0.0 to 2.0, lower is better for coding)
        :return: final string including reasoning if available
        """
        try:
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False
            )
            
            if resp.choices and len(resp.choices) > 0:
                # Check if reasoning content is available (deepseek-reasoner specific)
                reasoning = getattr(resp.choices[0].message, 'reasoning_content', None)
                content = resp.choices[0].message.content
                
                # If reasoning is available, prepend it to the content
                if reasoning:
                    return f"Reasoning:\n{reasoning}\n\nAnswer:\n{content}"
                return content
            return ""
        except Exception as e:
            return f"ERROR from DeepSeek: {str(e)}"


class AIOrchestrator:
    """
    A minimal orchestrator that picks either Claude3.7Sonnet or DeepseekR1
    and calls .run(...) with system+user messages.
    """

    def __init__(self, model_name: str):
        """
        model_name can be "claude37sonnet" or "deepseekr1"
        """
        self.model_name = model_name.lower()
        if self.model_name == "claude37sonnet":
            self.client = Claude37SonnetClient()
        elif self.model_name == "deepseekr1":
            self.client = DeepseekR1Client()
        else:
            raise ValueError(f"Unknown model: {model_name}")

    def call_llm(self, system_prompt: str, user_prompt: str, max_tokens: int = 20000, step_number: int = 0) -> str:
        """
        Minimal synergy: just pass system+user messages, get final text.
        Set parameters based on the step number to ensure consistent behavior.
        """
        print(f"\n\n====== PROCESSING STEP NUMBER: {step_number} ======\n\n")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Set LLM parameters based on step number
        if self.model_name == "claude37sonnet":
            # DISABLE THINKING FOR ALL STEPS
            print("=" * 80)
            print(f"THINKING MODE IS COMPLETELY DISABLED FOR ALL STEPS")
            print(f"enable_thinking = FALSE, temperature = 0.2")
            print("=" * 80)
            return self.client.run(
                messages, 
                max_tokens=max_tokens, 
                enable_thinking=False,  # Disable thinking for ALL steps
                temperature=0.2  # Use default temperature when thinking is disabled
            )
        else:
            return self.client.run(messages, max_tokens=max_tokens)
