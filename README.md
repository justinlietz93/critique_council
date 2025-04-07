# Reasoning Council Critique Module

## Purpose

This Python module provides a framework for critiquing text documents using a simulated "Reasoning Council." The council consists of multiple agents, each embodying the philosophical principles of a specific thinker (e.g., Aristotle, Descartes, Kant). These agents analyze the input text, engage in self-critique, and produce a synthesized, objective assessment highlighting potential areas for improvement.

**Note:** This version utilizes placeholder logic for the core reasoning tree generation and self-critique analysis. The framework is in place, but the depth and quality of the critique depend on replacing these placeholders with actual reasoning mechanisms (e.g., calls to a capable Large Language Model configured with the specific philosophical directives).

## Structure

*   **`src/`**: Contains the core module code.
    *   **`main.py`**: Main entry point function `critique_goal_document(file_path)`.
    *   **`input_reader.py`**: Handles reading the input text file.
    *   **`reasoning_agent.py`**: Defines the base `ReasoningAgent` and concrete `PhilosopherAgent` classes (Aristotle, Descartes, Kant, Leibniz, Popper, Russell) which load directives from the `prompts/` directory (expected to be sibling to `src/`).
    *   **`reasoning_tree.py`**: Contains the (currently placeholder) logic for recursive critique generation.
    *   **`council_orchestrator.py`**: Manages the council workflow, including agent instantiation, critique rounds, self-critique, and synthesis (currently placeholder synthesis).
    *   **`output_formatter.py`**: Formats the final synthesized critique into an objective report string.
    *   **`__init__.py`**: Makes the module importable and exposes the main function.
*   **`prompts/`**: Contains the text files defining the philosophical directives for each agent.
*   **`tests/`**: Contains unit, integration, and end-to-end tests.
*   **`docs/`**: Contains requirements, design, and test log documentation.
*   **`README.md`**: This file.

## Usage

```python
# Example: Run from the 'critique_council' directory
from src import critique_goal_document

# Assumes 'goal.txt' is in the 'critique_council' directory
input_file = 'goal.txt'

try:
    final_critique_report = critique_goal_document(input_file)
    print(final_critique_report)
except FileNotFoundError:
    print(f"Error: Input file not found at {input_file}")
except Exception as e:
    print(f"An error occurred: {e}")

```

Alternatively, run the main script directly for a demonstration using `goal.txt` (ensure `goal.txt` exists in the `critique_council` directory):

```bash
# Run from the 'critique_council' directory
python -m src.main
```

## Dependencies

*   Python 3.x (including `asyncio`)
*   `pytest` (for running tests)
*   `google-generativeai` (for the integrated Gemini client)
*   Potentially `python-dotenv` if API keys are loaded via `.env` files (client code suggests this possibility).
*   **Note:** The current implementation integrates `gemini_client.py` but still uses placeholder logic within the reasoning tree calls. Full functionality requires API key configuration and potentially adjustments to the client/prompts.

## Testing

Unit and integration tests are located in the `tests/` directory. Run tests using `pytest` from the `critique_council` directory:

```bash
# Run from the 'critique_council' directory
python -m pytest tests/ -v
```

## Documentation

*   **Requirements:** `docs/critique_module_requirements.md`
*   **Design:** `docs/critique_module_design.md`
*   **Test Log:** `docs/Critique_Module_Test_Log.md`
*   **Philosopher Prompts:** `prompts/critique_*.txt`
