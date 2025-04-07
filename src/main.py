# src/critique_module/main.py

"""
Main entry point for the Reasoning Council Critique Module.
"""
from typing import Dict, Any # Import Dict and Any for type hints

# Component Imports
from .input_reader import read_file_content
import asyncio # Import asyncio
from .input_reader import read_file_content
from .council_orchestrator import run_critique_council
from .output_formatter import format_critique_output

# Make the main function async to await the orchestrator
async def critique_goal_document(file_path: str, config: Dict[str, Any]) -> str: # Add config, make async
    """
    Reads content from the specified file, runs the Reasoning Council critique,
    and returns a formatted, objective assessment string.

    Args:
        file_path: Path to the input text file (e.g., 'goal.txt').

    Returns:
        A string containing the final formatted critique or a "no significant findings" message.

    Raises:
        FileNotFoundError: If the input file_path does not exist.
        IOError: If the file cannot be read.
        Exception: For unexpected errors during critique processing.
    """
    # print(f"Initiating critique for: {file_path}") # Temporary print removed

    try:
        # 1. Read Input
        # print("Step 1: Reading input...") # Temporary print removed
        content = read_file_content(file_path)
        # print("Input read successfully.") # Temporary print removed

        # 2. Run Council
        # print("Step 2: Running critique council...") # Temporary print removed
        critique_data = await run_critique_council(content, config) # Use await, pass config
        # print("Council finished.") # Temporary print removed

        # 3. Format Output
        # print("Step 3: Formatting output...") # Temporary print removed
        formatted_output = format_critique_output(critique_data)
        # print("Output formatted.") # Temporary print removed

        # print("Critique process completed.") # Temporary print removed
        return formatted_output

    except FileNotFoundError as e:
        # Consider using logging instead of print for errors
        # print(f"Error: Input file not found at {file_path}")
        raise e
    except IOError as e:
        # Consider using logging instead of print for errors
        # print(f"Error: Could not read input file at {file_path}")
        raise e
    except Exception as e:
        # Consider using logging instead of print for errors
        # print(f"An unexpected error occurred during critique: {e}")
        # Potentially log the full error details here
        raise Exception(f"Critique module failed unexpectedly: {e}") # Re-raise generic exception

if __name__ == '__main__':
    # Example usage (for direct execution testing)
    # Adjust path for direct script execution vs. module execution
    import sys
    import os
    # Add project root to path to allow absolute imports for direct execution
    # *** NOTE: This assumes the script is run from within the 'critique_council' directory ***
    # *** Or that 'critique_council' is in the PYTHONPATH ***
    # For a truly independent module, consider a different structure or entry point.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')) # This points to critique_council parent
    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) # This points to critique_council/src
    if project_root not in sys.path:
         sys.path.insert(0, project_root) # Add parent to find 'src' potentially
    if src_root not in sys.path:
         sys.path.insert(0, src_root) # Add src to find sibling modules

    # Now use absolute imports relative to the new 'src' directory
    # This might still fail depending on how it's run.
    # A better approach for independence is often a dedicated runner script outside 'src'.
    try:
        from input_reader import read_file_content as direct_read
        from council_orchestrator import run_critique_council as direct_run_council # Import orchestrator
        from output_formatter import format_critique_output as direct_format
    except ImportError:
        print("ImportError: Could not import module components directly. Try running as 'python -m src.main' from 'critique_council' directory.")
        sys.exit(1)


    # Redefine the function slightly for direct execution context to use absolute imports
    # This avoids modifying the main function's relative imports used during package execution
    # Keep prints here for example usage output
    # Make this test function async as well
    async def direct_critique_test(file_path: str) -> str:
        print(f"Initiating direct critique test for: {file_path}")
        # Dummy config for direct test execution
        dummy_config = {
            'api': {'retries': 1},
            # Add other necessary config keys if gemini_client requires them
            # Ensure API key is handled appropriately if needed for direct run
            # For now, assuming mocks in tests handle API key requirement
        }
        try:
            print("Step 1: Reading input (direct)...")
            content = direct_read(file_path)
            print("Input read successfully (direct).")

            print("Step 2: Running critique council (direct)...")
            critique_data = await direct_run_council(content, dummy_config) # Use await, pass dummy_config
            print("Council finished (direct).")

            print("Step 3: Formatting output (direct)...")
            formatted_output = direct_format(critique_data)
            print("Output formatted (direct).")

            print("Direct critique test process completed.")
            return formatted_output
        except FileNotFoundError as e:
            print(f"Error (direct): Input file not found at {file_path}")
            raise e
        except IOError as e:
            print(f"Error (direct): Could not read input file at {file_path}")
            raise e
        except Exception as e:
            print(f"An unexpected error occurred during direct critique test: {e}")
            raise Exception(f"Direct critique test failed unexpectedly: {e}")

    # Path relative to the 'critique_council' directory
    test_file = '../goal.txt' # Assumes goal.txt is copied to critique_council/
    print(f"--- Running Example Usage (Direct Execution Context) ---")
    # Ensure the test file path is correct relative to critique_council/src/main.py
    test_file_abs = os.path.abspath(os.path.join(os.path.dirname(__file__), test_file))

    if not os.path.exists(test_file_abs):
         print(f"Error: Test file '{test_file}' (abs: {test_file_abs}) not found relative to main.py.")
         # Attempt fallback relative to project root (critique_council) - simplified
         test_file_abs_fallback = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'goal.txt')) # Assumes goal.txt in parent
         if os.path.exists(test_file_abs_fallback):
             print(f"Attempting fallback path: {test_file_abs_fallback}")
             test_file_abs = test_file_abs_fallback
         else:
             print(f"Error: Fallback path also not found: {test_file_abs_fallback}")
             sys.exit(1)


    try:
        # Run the async test function using asyncio.run
        final_critique = asyncio.run(direct_critique_test(test_file_abs))
        print("\n--- Final Critique Output (Direct Execution Context) ---")
        print(final_critique)
    except Exception as e:
        print(f"\n--- Example Usage Failed (Direct Execution Context) ---")
        print(f"Error: {e}")
    print(f"--- End Example Usage (Direct Execution Context) ---")
