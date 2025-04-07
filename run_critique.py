# run_critique.py
import asyncio
import os
import logging
import json
import datetime # Import datetime
from dotenv import load_dotenv
from src import critique_goal_document

# Function to load configuration from JSON file
def load_config(path="config.json"):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file '{path}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Configuration file '{path}' contains invalid JSON.")
        return None

# --- Configure Logging ---
def setup_logging():
    """Configures root logger to write to system.log and agent loggers."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True) # Ensure logs dir exists
    system_log_file = os.path.join(log_dir, "system.log")
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                        filename=system_log_file,
                        filemode='w',
                        encoding='utf-8')
    logging.info("Root logging configured. System logs in logs/system.log")
# -------------------------

async def main():
    setup_logging()
    root_logger = logging.getLogger(__name__)

    # --- Load Configuration ---
    app_config = load_config()
    if app_config is None:
        root_logger.error("Exiting due to configuration file error.")
        return

    load_dotenv()
    root_logger.info("Environment variables loaded from .env (if found).")
    # -------------------------

    # --- Prepare Module Config ---
    module_config = {
        'api': {
            **app_config.get('api', {}).get('gemini', {}),
            'resolved_key': os.getenv('GEMINI_API_KEY'),
        },
        'deepseek': {
            **app_config.get('api', {}).get('deepseek', {}),
            'api_key': os.getenv('DEEPSEEK_API_KEY'),
        },
        'reasoning_tree': app_config.get('reasoning_tree', {}),
        'council_orchestrator': app_config.get('council_orchestrator', {})
    }
    root_logger.info("Module configuration prepared.")
    # -------------------------

    # --- Validate API Key ---
    if not module_config.get('api', {}).get('resolved_key'):
        error_msg = "GEMINI_API_KEY not found in .env file or environment. Cannot proceed."
        print(f"Error: {error_msg}")
        root_logger.error(error_msg)
        return
    # -------------------------

    input_file = 'content.txt' # Default input file

    root_logger.info(f"Initiating critique for: {input_file}")
    try:
        final_critique_report = await critique_goal_document(input_file, module_config)

        # --- Generate Output Filename ---
        output_dir = "critiques"
        os.makedirs(output_dir, exist_ok=True) # Ensure critiques dir exists
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        input_basename = os.path.splitext(os.path.basename(input_file))[0]
        output_filename = os.path.join(output_dir, f"{input_basename}_critique_{timestamp}.md")
        # --------------------------------

        # Save the report to the generated filename
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(final_critique_report)

        success_msg = f"Critique report successfully saved to {output_filename}"
        root_logger.info(success_msg)
        print(f"\n{success_msg}")

    except FileNotFoundError as e:
        error_msg = f"Input file not found at {input_file}"
        print(f"Error: {error_msg}")
        root_logger.error(error_msg, exc_info=True)
    except Exception as e:
        error_msg = f"An unexpected error occurred during critique: {e}"
        print(f"Error: {error_msg}")
        root_logger.error(error_msg, exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
