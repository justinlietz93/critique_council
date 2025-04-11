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
        *   **`openai_client.py`**: Client for OpenAI API, used for scientific peer review formatting in PR mode.
        *   **`exceptions.py`**: Custom exceptions for provider interactions.
    *   **`scientific_review_formatter.py`**: Formats critique reports into formal scientific peer review documents when PR mode is active.
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
OPENAI_API_KEY=YOUR_OPENAI_API_KEY_HERE # Required for PR mode
```

You would then need a mechanism (e.g., using `python-dotenv` in your calling script) to load these variables and construct the configuration dictionary passed to the module. The `gemini_client` looks for `config['api']['resolved_key']` for the Gemini key and `config['deepseek']['api_key']` for the DeepSeek key.

## Usage

The easiest way to run the Critique Council is using the provided `run_critique.py` script:

```bash
# Run with standard philosophical critique
python run_critique.py content.txt

# Run with peer review mode (see below)
python run_critique.py content.txt --PR
```

For programmatic usage:

```python
# Example programmatic usage
import os
from dotenv import load_dotenv # Requires 'pip install python-dotenv'
from src import critique_goal_document

def main():
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
            'openai': {
                'resolved_key': os.getenv('OPENAI_API_KEY'), # Required for PR mode
                'model': 'gpt-4-turbo-preview',
                'temperature': 0.2
            }
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

    # Assumes 'content.txt' is in the 'critique_council' directory
    input_file = 'content.txt'
    
    # Enable peer review mode (optional)
    peer_review = True

    print(f"Initiating critique for: {input_file}")
    try:
        # Call the synchronous main function (with optional peer review flag)
        final_critique_report = critique_goal_document(input_file, config, peer_review=peer_review)
        print("\n--- Critique Report ---")
        print(final_critique_report)
        print("--- End of Report ---")
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_file}")
    except Exception as e:
        print(f"An error occurred during critique: {e}")

if __name__ == "__main__":
    main()
```

**Direct Execution (Limited):**
Running `python -m src.main` provides a basic demonstration but uses dummy configuration and may not fully exercise the LLM integration without modification.

## Peer Review Mode

The Critique Council now supports a "Peer Review" mode, which enhances the philosophical critique with domain-specific scientific expertise. When enabled with the `--PR` flag:

1. All philosophical critics, the arbiter, and the judge gain academic credentials and domain-specific expertise relevant to the input content
2. The critics evaluate the content from both their philosophical perspective and as scientific subject matter experts
3. The system generates an additional formal scientific peer review document following academic publishing standards

This mode is particularly useful for:
- Academic papers and research content
- Technical documentation that requires domain expertise 
- Content where scientific accuracy is as important as philosophical coherence

The peer review document includes:
- A reviewer with relevant credentials (name, title, affiliation)
- A brief summary of the work
- A clear recommendation (accept/reject/revise)
- Numbered major and minor concerns
- Specific suggestions for improvement

To use peer review mode:
```bash
python run_critique.py content.txt --PR
```

**Note:** Peer Review mode requires an OpenAI API key in your `.env` file for the final formatting stage.

## Dependencies

*   Python 3.x (tested with 3.8+)
*   `google-generativeai`: Google Gemini client library
*   `openai>=1.0.0`: OpenAI API client (required for PR mode)
*   `pytest`: For running tests
*   `python-dotenv`: For loading configuration from `.env` files
*   `requests`: HTTP client library
*   `aiohttp`: Asynchronous HTTP client library

Install dependencies:
```bash
pip install -r requirements.txt
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
*   **Arbiter Prompt:** `prompts/expert_arbiter.txt`
*   **Judge Prompt:** `prompts/judge_summary.txt`

## Output Reports

The system generates the following outputs:

### Standard Critique Report (`critiques/*_critique_*.md`)

The detailed philosophical critique report saved in the `critiques/` directory, named using the input file and a timestamp (e.g., `critiques/content_critique_YYYYMMDD_HHMMSS.md`). The report includes:

1.  **Overall Judge Summary:** An unbiased summary generated by an LLM synthesizing all critiques and arbiter feedback.
2.  **Overall Scores & Metrics:** Includes the final **Judge Overall Score**, the **Expert Arbiter Score**, and counts of high/medium/low severity points identified post-arbitration.
3.  **Expert Arbiter Adjustment Summary:** A list of all specific comments and confidence adjustments made by the Expert Arbiter agent to the philosopher critiques.
4.  **Detailed Agent Critiques:** Separate sections for each philosopher agent, displaying their full critique tree (including sub-points, evidence, severity, and confidence adjusted by the arbiter) along with any specific arbitration comments applied directly to their points.

### Peer Review Document (`critiques/*_peer_review_*.md`) (PR Mode Only)

When running in Peer Review mode (`--PR` flag), the system also generates a formal scientific peer review document, saved as `critiques/content_peer_review_YYYYMMDD_HHMMSS.md`. This document follows academic publishing conventions and includes:

1. **Reviewer Credentials:** Academic name, title, affiliation, and area of expertise.
2. **Brief Summary:** Concise overview of the manuscript and its claims.
3. **Recommendation:** Clear indication to accept, reject, or revise the work.
4. **Major Concerns:** Numbered list of significant issues found in the work.
5. **Minor Concerns:** Numbered list of smaller issues and suggestions.
6. **Conclusion:** Final thoughts and synthesis.
