# run_critique.py
# import asyncio # No longer needed
import os
import logging
import json
import datetime
import argparse # Added argparse
from dotenv import load_dotenv
from src import critique_goal_document # Now synchronous
from src.scientific_review_formatter import format_scientific_peer_review
from src.latex.cli import add_latex_arguments, handle_latex_output

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
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    system_log_file = os.path.join(log_dir, "system.log")
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                        filename=system_log_file,
                        filemode='w',
                        encoding='utf-8')
    logging.info("Root logging configured. System logs in logs/system.log")
# -------------------------

# Make main synchronous
def main():
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Run the Critique Council on a given input file.")
    parser.add_argument("input_file", help="Path to the input content file (e.g., content.txt).")
    parser.add_argument("--PR", "--peer-review", action="store_true",
                        help="Enable Peer Review mode, enhancing personas with SME perspective.")
    parser.add_argument("--scientific", action="store_true",
                        help="Use scientific methodology agents instead of philosophical agents.")
    # Add LaTeX-related arguments
    parser = add_latex_arguments(parser)
    args = parser.parse_args()
    # -------------------------

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
    # Structure the configuration to include all available providers
    module_config = {
        'api': {
            'providers': {},  # Provider configuration container
            'primary_provider': app_config.get('api', {}).get('primary_provider', 'gemini'),
        },
        'reasoning_tree': app_config.get('reasoning_tree', {}),
        'council_orchestrator': app_config.get('council_orchestrator', {})
    }
    
    # Add Gemini configuration if available
    if 'gemini' in app_config.get('api', {}):
        module_config['api']['providers']['gemini'] = {
            **app_config.get('api', {}).get('gemini', {}),
            'resolved_key': os.getenv('GEMINI_API_KEY'),
        }
        # Also add at top level for backward compatibility with older provider modules
        module_config['api']['gemini'] = module_config['api']['providers']['gemini']
        
    # Add DeepSeek configuration if available
    if 'deepseek' in app_config.get('api', {}) or os.getenv('DEEPSEEK_API_KEY'):
        module_config['api']['providers']['deepseek'] = {
            **app_config.get('api', {}).get('deepseek', {}),
            'api_key': os.getenv('DEEPSEEK_API_KEY'),
        }
        # Also add at top level for backward compatibility with older provider modules
        module_config['api']['deepseek'] = module_config['api']['providers']['deepseek']
        
    # Add OpenAI configuration if available
    if 'openai' in app_config.get('api', {}) or os.getenv('OPENAI_API_KEY'):
        module_config['api']['providers']['openai'] = {
            **app_config.get('api', {}).get('openai', {}),
            'resolved_key': os.getenv('OPENAI_API_KEY'),
        }
        # Also add at top level for backward compatibility with older provider modules
        module_config['api']['openai'] = module_config['api']['providers']['openai']
    
    # For backward compatibility with older components
    primary_provider = module_config['api']['primary_provider']
    if primary_provider in module_config['api']['providers'] and 'resolved_key' in module_config['api']['providers'][primary_provider]:
        module_config['api']['resolved_key'] = module_config['api']['providers'][primary_provider]['resolved_key']
    
    root_logger.info("Module configuration prepared.")
    # -------------------------

    # --- Validate Primary Provider API Key ---
    primary_provider = module_config['api']['primary_provider']
    # Check both locations (providers nested and direct)
    api_key_missing = (
        (primary_provider not in module_config['api']['providers'] or 
         not module_config['api']['providers'][primary_provider].get('resolved_key', module_config['api']['providers'][primary_provider].get('api_key')))
        and
        (primary_provider not in module_config['api'] or 
         not module_config['api'][primary_provider].get('resolved_key', module_config['api'][primary_provider].get('api_key')))
    )
    
    if api_key_missing:
        error_msg = f"Primary provider '{primary_provider}' API key not found in .env file or environment. Cannot proceed."
        print(f"Error: {error_msg}")
        root_logger.error(error_msg)
        return
    # -------------------------

    # Use parsed arguments
    input_file = args.input_file
    peer_review_mode = args.PR # or args.peer_review

    scientific_mode = args.scientific
    
    root_logger.info(f"Initiating critique for: {input_file} (Peer Review Mode: {peer_review_mode}, Scientific Mode: {scientific_mode})")
    try:
        # Pass peer_review_mode and scientific_mode to the critique function
        final_critique_report = critique_goal_document(
            input_file, 
            module_config, 
            peer_review=peer_review_mode,
            scientific_mode=scientific_mode
        )

        # Save standard critique report
        output_dir = "critiques"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        input_basename = os.path.splitext(os.path.basename(input_file))[0]
        output_filename = os.path.join(output_dir, f"{input_basename}_critique_{timestamp}.md")

        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(final_critique_report)
            
        success_msg = f"Critique report successfully saved to {output_filename}"
        root_logger.info(success_msg)
        print(f"\n{success_msg}")
        
        # If peer review mode is active, generate formal scientific peer review
        if peer_review_mode:
            root_logger.info(f"Peer Review mode active - Generating scientific peer review format... (Scientific Mode: {scientific_mode})")
            try:
                # Read the original content
                with open(input_file, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                
                # Generate the scientific peer review
                scientific_review = format_scientific_peer_review(
                    original_content=original_content,
                    critique_report=final_critique_report,
                    config=module_config,
                    scientific_mode=scientific_mode
                )
                
                # Save the scientific peer review to a separate file
                pr_output_filename = os.path.join(output_dir, f"{input_basename}_peer_review_{timestamp}.md")
                with open(pr_output_filename, 'w', encoding='utf-8') as f:
                    f.write(scientific_review)
                
                pr_success_msg = f"Scientific Peer Review successfully saved to {pr_output_filename}"
                root_logger.info(pr_success_msg)
                print(f"\n{pr_success_msg}")
                
                # Generate LaTeX document if requested
                if args.latex:
                    try:
                        # Read the original content again to be safe
                        with open(input_file, 'r', encoding='utf-8') as f:
                            original_content = f.read()
                            
                        # Generate the LaTeX document
                        latex_success, tex_path, pdf_path = handle_latex_output(
                            args, 
                            original_content,
                            final_critique_report,
                            scientific_review,
                            scientific_mode  # Pass the scientific mode flag
                        )
                        
                        if latex_success:
                            if tex_path:
                                latex_success_msg = f"LaTeX document successfully saved to {tex_path}"
                                root_logger.info(latex_success_msg)
                                print(f"\n{latex_success_msg}")
                            if pdf_path:
                                pdf_success_msg = f"PDF document successfully saved to {pdf_path}"
                                root_logger.info(pdf_success_msg)
                                print(f"\n{pdf_success_msg}")
                        else:
                            latex_error_msg = "Failed to generate LaTeX document"
                            root_logger.error(latex_error_msg)
                            print(f"\nWarning: {latex_error_msg}")
                    except Exception as e:
                        latex_error_msg = f"Error generating LaTeX document: {e}"
                        root_logger.error(latex_error_msg, exc_info=True)
                        print(f"\nWarning: {latex_error_msg}")
                
            except Exception as e:
                pr_error_msg = f"Error generating scientific peer review: {e}"
                root_logger.error(pr_error_msg, exc_info=True)
                print(f"\nWarning: {pr_error_msg}")
                
        # If LaTeX is requested but peer review is not, generate LaTeX with just the critique
        elif args.latex:
            try:
                # Read the original content
                with open(input_file, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                    
                # Generate the LaTeX document without peer review
                latex_success, tex_path, pdf_path = handle_latex_output(
                    args, 
                    original_content,
                    final_critique_report,
                    scientific_mode=scientific_mode  # Pass the scientific mode flag
                )
                
                if latex_success:
                    if tex_path:
                        latex_success_msg = f"LaTeX document successfully saved to {tex_path}"
                        root_logger.info(latex_success_msg)
                        print(f"\n{latex_success_msg}")
                    if pdf_path:
                        pdf_success_msg = f"PDF document successfully saved to {pdf_path}"
                        root_logger.info(pdf_success_msg)
                        print(f"\n{pdf_success_msg}")
                else:
                    latex_error_msg = "Failed to generate LaTeX document"
                    root_logger.error(latex_error_msg)
                    print(f"\nWarning: {latex_error_msg}")
            except Exception as e:
                latex_error_msg = f"Error generating LaTeX document: {e}"
                root_logger.error(latex_error_msg, exc_info=True)
                print(f"\nWarning: {latex_error_msg}")

    except FileNotFoundError as e:
        error_msg = f"Input file not found at {input_file}"
        print(f"Error: {error_msg}")
        root_logger.error(error_msg, exc_info=True)
    except Exception as e:
        error_msg = f"An unexpected error occurred during critique: {e}"
        print(f"Error: {error_msg}")
        root_logger.error(error_msg, exc_info=True)

if __name__ == "__main__":
    main() # Call main directly
