# Reasoning Council Critique Module

## Purpose

This Python module provides a framework for critiquing text documents using a simulated "Reasoning Council." The council consists of multiple asynchronous agents, each embodying the philosophical principles of a specific thinker (Aristotle, Descartes, Kant, Leibniz, Popper, Russell). These agents analyze the input text using an underlying Large Language Model (LLM), engage in self-critique based on peer assessments, and produce a synthesized, objective assessment highlighting potential areas for improvement.

## Structure

*   **`src/`**: Contains the core module code.
    *   **`main.py`**: Main asynchronous entry point function `critique_goal_document(file_path, config)`.
    *   **`input_reader.py`**: Handles reading the input text file.
    *   **`council_orchestrator.py`**: Manages the asynchronous council workflow, including agent instantiation, critique rounds (initial + self-critique), and synthesis.
    *   **`reasoning_agent.py`**: Defines the base `ReasoningAgent` and concrete `PhilosopherAgent` classes which load detailed directives from the `prompts/` directory.
    *   **`reasoning_tree.py`**: Implements the recursive critique generation logic, making calls to the configured LLM client.
    *   **`output_formatter.py`**: Formats the final synthesized critique into an objective report string.
    *   **`providers/`**: Contains LLM client implementations.
        *   **`gemini_client.py`**: Client for Google Gemini API, including retry logic and structured output handling.
        *   **`deepseek_v3_client.py`**: Client for DeepSeek API, used as a fallback for Gemini rate limits.
        *   **`exceptions.py`**: Custom exceptions for provider interactions.
    *   **`__init__.py`**: Makes the module importable and exposes the main function.
*   **`prompts/`**: Contains enhanced (V2.0) text files defining the detailed philosophical directives for each agent.
*   **`tests/`**: Contains unit, integration, and end-to-end tests using `pytest`.
*   **`docs/`**: Contains requirements, design, and test log documentation.
*   **`config.json`**: Central configuration file for model parameters, thresholds, etc.
*   **`.env`**: (Recommended) File to store sensitive API keys (see Configuration).
*   **`.gitignore`**: Standard Python gitignore file.
*   **`.editorconfig`**: Defines basic editor settings.
*   **`README.md`**: This file.
*   Standard policy files (`LICENSE`, `CODE_OF_CONDUCT.md`, etc.)

## Configuration

The module uses a combination of `config.json` for general settings and `.env` for sensitive API keys. The `run_critique.py` script loads both and passes a combined configuration dictionary to the core module.

**1. `config.json`:**
   - Located in the project root.
   - Defines parameters like LLM model names, API retries, temperature, reasoning tree depth, confidence thresholds, etc.
   - You can modify these values to tune the critique process.

**2. `.env` File (for API Keys):**
   - Create this file in the project root (it's ignored by git).
   - Store sensitive API keys here:

```dotenv
# .env file
GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE
DEEPSEEK_API_KEY=YOUR_DEEPSEEK_API_KEY_HERE # Optional, for fallback
```

You would then need a mechanism (e.g., using `python-dotenv` in your calling script) to load these variables and construct the configuration dictionary passed to the module. The `gemini_client` looks for `config['api']['resolved_key']` for the Gemini key and `config['deepseek']['api_key']` for the DeepSeek key.

## Usage

```python
# Example: Run from a script in the 'critique_council' directory
import asyncio
import os
from dotenv import load_dotenv # Requires 'pip install python-dotenv'
from src import critique_goal_document

async def main():
    load_dotenv() # Load variables from .env file

    # --- Configuration ---
    # Construct the config dict expected by the module
    # Ensure API keys are loaded securely (e.g., from environment variables)
    config = {
        'api': {
            'resolved_key': os.getenv('GEMINI_API_KEY'),
            'retries': 3,
            'model_name': 'gemini-1.5-flash', # Example model
            'temperature': 0.6,
            # Add other Gemini parameters if needed (top_p, top_k, max_output_tokens)
        },
        'deepseek': { # Optional fallback configuration
            'api_key': os.getenv('DEEPSEEK_API_KEY'),
            # 'base_url': 'https://api.deepseek.com/v1' # Default
        }
        # Add other config sections if needed by other components
    }

    # Check if essential config is present
    if not config.get('api', {}).get('resolved_key'):
        print("Error: GEMINI_API_KEY not found. Please set it in the .env file or environment.")
        return

    # Assumes 'goal.txt' is in the 'critique_council' directory
    input_file = 'goal.txt'

    print(f"Initiating critique for: {input_file}")
    try:
        # Call the asynchronous main function
        final_critique_report = await critique_goal_document(input_file, config)
        print("\n--- Critique Report ---")
        print(final_critique_report)
        print("--- End of Report ---")
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_file}")
    except Exception as e:
        print(f"An error occurred during critique: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Direct Execution (Limited):**
Running `python -m src.main` provides a basic demonstration but uses dummy configuration and may not fully exercise the LLM integration without modification.

## Dependencies

*   Python 3.x (tested with 3.8+, requires `asyncio`)
*   `google-generativeai`: Google Gemini client library.
*   `pytest`: For running tests.
*   `python-dotenv`: (Recommended) For loading configuration from `.env` files.
*   (Implied by `deepseek_v3_client`): Likely `requests` or similar HTTP client library.

Install dependencies (excluding `pytest` and `python-dotenv` if managed separately):
```bash
pip install google-generativeai requests # Add other specific dependencies if identified
```

## Testing

Unit, integration, and end-to-end tests are located in the `tests/` directory. Run tests using `pytest` from the `critique_council` directory:

```bash
# Run from the 'critique_council' directory
python -m pytest tests/ -v
```
*Note: Some tests might be skipped if external resources like `goal.txt` are missing.*

## Documentation

*   **Requirements:** `docs/critique_module_requirements.md`
*   **Design:** `docs/critique_module_design.md`
*   **Test Log:** `docs/Critique_Module_Test_Log.md`
*   **Philosopher Prompts:** `prompts/critique_*.txt` (Enhanced V2.0)
