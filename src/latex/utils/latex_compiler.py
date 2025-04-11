"""
LaTeX compilation utilities.

This module provides utilities for compiling LaTeX documents to PDF.
"""

import os
import re
import subprocess
import logging
import platform
from typing import Dict, Any, Optional, List, Tuple

try:
    from src.config_loader import config_loader
except ImportError:
    # Handle case when running from different directory
    import sys
    import os.path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
    from src.config_loader import config_loader

logger = logging.getLogger(__name__)


class LatexCompiler:
    """
    Utility class for compiling LaTeX documents to PDF.
    
    This class provides methods for compiling LaTeX source files to PDF using
    external LaTeX compilers like pdflatex.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LaTeX compiler.
        
        Args:
            config: Optional configuration dictionary containing compiler options.
                   If not provided, will use the global configuration from config.yaml.
        """
        # If no config provided, use the global config
        if config is None:
            latex_config = config_loader.get_latex_config()
            self.config = latex_config
        else:
            self.config = config
            
        # Set up basic configuration
        self.latex_engine = self.config.get('latex_engine', 'pdflatex')
        self.bibtex_run = self.config.get('bibtex_run', True)
        self.latex_runs = self.config.get('latex_runs', 2)
        self.keep_intermediates = self.config.get('keep_intermediates', False)
        
        # Get MiKTeX specific configuration
        self.miktex_config = self.config.get('miktex', {})
        self.custom_miktex_path = self.miktex_config.get('custom_path', '')
        self.additional_search_paths = self.miktex_config.get('additional_search_paths', [])
        
        # Check if the LaTeX engine is available, try alternatives if not
        self.latex_available, self.latex_engine = self._find_available_latex_engine()
        
        if self.latex_available:
            logger.info(f"LaTeX compiler initialized successfully with engine: {self.latex_engine}")
        else:
            logger.warning(f"Failed to initialize LaTeX compiler. No LaTeX engine found.")
    
    def _find_available_latex_engine(self) -> Tuple[bool, str]:
        """
        Try to find an available LaTeX engine on the system.
        
        First tries the configured engine, then falls back to alternatives.
        If no engines are found in the PATH, tries to find them in common
        installation locations on Windows.
        
        Returns:
            A tuple of (is_available, engine_name)
        """
        # Try the configured engine first
        if self._check_engine_available(self.latex_engine):
            return True, self.latex_engine
            
        # Try alternatives
        alternatives = ['pdflatex', 'pdftex', 'latex', 'xelatex', 'lualatex']
        
        # Remove the already tried engine from alternatives
        if self.latex_engine in alternatives:
            alternatives.remove(self.latex_engine)
            
        # Try each alternative
        for engine in alternatives:
            if self._check_engine_available(engine):
                print(f"Using alternative LaTeX engine: {engine}")
                return True, engine
                
        # On Windows, try to find MiKTeX or TeX Live in common installation locations
        if platform.system() == 'Windows':
            print("Checking for LaTeX engines in common Windows installation locations...")
            engine_path = self._find_latex_in_common_locations(self.latex_engine)
            if engine_path:
                print(f"Found LaTeX engine at {engine_path}")
                # Store the full path to the engine for later use
                self._engine_path = engine_path
                return True, self.latex_engine
                
            # Try alternatives in common locations
            for engine in alternatives:
                engine_path = self._find_latex_in_common_locations(engine)
                if engine_path:
                    print(f"Found alternative LaTeX engine '{engine}' at {engine_path}")
                    # Store the full path to the engine for later use
                    self._engine_path = engine_path
                    return True, engine
        
        # No LaTeX engine found
        print("No LaTeX engine found on the system")
        self._engine_path = None
        return False, self.latex_engine
        
    def _find_latex_in_common_locations(self, engine: str) -> Optional[str]:
        """
        Look for LaTeX engine in common installation locations on Windows.
        
        Args:
            engine: The LaTeX engine to look for.
            
        Returns:
            The full path to the engine executable if found, None otherwise.
        """
        if platform.system() != 'Windows':
            return None
            
        # Get current username
        username = os.environ.get('USERNAME', '')
        
        # Check custom MiKTeX path first if specified
        if self.custom_miktex_path:
            logger.info(f"Checking custom MiKTeX path: {self.custom_miktex_path}")
            if os.path.exists(self.custom_miktex_path):
                engine_path = os.path.join(self.custom_miktex_path, f"{engine}.exe")
                if os.path.exists(engine_path) and os.path.isfile(engine_path):
                    logger.info(f"Found LaTeX engine '{engine}' at custom path: {engine_path}")
                    # Test if the engine works
                    try:
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        result = subprocess.run(
                            [engine_path, '--version'],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            startupinfo=startupinfo,
                            check=False,
                            text=True
                        )
                        if result.returncode == 0:
                            version_info = result.stdout.strip().split('\n')[0] if result.stdout else "Unknown version"
                            print(f"Successfully tested LaTeX engine: {version_info}")
                            return engine_path
                    except Exception as e:
                        print(f"Error testing LaTeX engine at {engine_path}: {e}")
                        return None
            else:
                logger.warning(f"Custom MiKTeX path doesn't exist: {self.custom_miktex_path}")
                
        # Common MiKTeX installation paths
        common_paths = [
            # MiKTeX 25.x paths
            f"C:\\Users\\{username}\\AppData\\Local\\Programs\\MiKTeX 25.3\\miktex\\bin\\x64",
            f"C:\\Program Files\\MiKTeX 25.3\\miktex\\bin\\x64",
            # Older MiKTeX paths
            f"C:\\Users\\{username}\\AppData\\Local\\Programs\\MiKTeX\\miktex\\bin\\x64",
            f"C:\\Users\\{username}\\AppData\\Local\\MiKTeX\\miktex\\bin\\x64",
            f"C:\\Program Files\\MiKTeX\\miktex\\bin\\x64",
            f"C:\\Program Files (x86)\\MiKTeX\\miktex\\bin",
            # TeX Live installation paths
            "C:\\texlive\\2023\\bin\\win32",
            "C:\\texlive\\2024\\bin\\win32",
            "C:\\texlive\\2023\\bin\\x64",
            "C:\\texlive\\2024\\bin\\x64"
        ]
        
        # Add any additional search paths from configuration
        if self.additional_search_paths:
            logger.info(f"Adding {len(self.additional_search_paths)} additional search paths from config")
            common_paths.extend(self.additional_search_paths)
        
        # Check each path for the engine
        for base_path in common_paths:
            engine_path = os.path.join(base_path, f"{engine}.exe")
            if os.path.exists(engine_path) and os.path.isfile(engine_path):
                print(f"Found LaTeX engine '{engine}' at {engine_path}")
                try:
                    # Test if the engine actually works
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    result = subprocess.run(
                        [engine_path, '--version'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        startupinfo=startupinfo,
                        check=False,
                        text=True
                    )
                    if result.returncode == 0:
                        version_info = result.stdout.strip().split('\n')[0] if result.stdout else "Unknown version"
                        print(f"Successfully tested LaTeX engine: {version_info}")
                        return engine_path
                except Exception as e:
                    print(f"Error testing LaTeX engine at {engine_path}: {e}")
                    continue
        
        return None
        
    def _check_engine_available(self, engine: str) -> bool:
        """
        Check if a specific LaTeX engine is available on the system.
        
        Args:
            engine: The LaTeX engine to check.
            
        Returns:
            True if the engine is available, False otherwise.
        """
        try:
            print(f"Checking if LaTeX engine '{engine}' is available...")
            if platform.system() == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                result = subprocess.run(
                    [engine, '--version'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    startupinfo=startupinfo,
                    check=False,
                    text=True
                )
            else:
                result = subprocess.run(
                    [engine, '--version'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                    text=True
                )
            
            if result.returncode == 0:
                version_info = result.stdout.strip().split('\n')[0] if result.stdout else "Unknown version"
                print(f"Found LaTeX engine: {version_info}")
                return True
            else:
                print(f"LaTeX engine '{engine}' not found. Error: {result.stderr}")
                return False
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"LaTeX engine '{engine}' not found on the system: {str(e)}")
            return False
    
    def compile_document(self, tex_path: str) -> Tuple[bool, str]:
        """
        Compile a LaTeX document to PDF.
        
        Args:
            tex_path: Path to the LaTeX source file.
            
        Returns:
            A tuple of (success, output_pdf_path), where success is a boolean
            indicating whether compilation was successful, and output_pdf_path
            is the path to the generated PDF file (or an error message if compilation failed).
        """
        print(f"Attempting to compile LaTeX document: {tex_path}")
        if not self.latex_available:
            print(f"Error: LaTeX engine '{self.latex_engine}' is not available on the system")
            return False, "LaTeX engine not available on the system"
        
        if not os.path.exists(tex_path):
            print(f"Error: LaTeX source file not found: {tex_path}")
            return False, f"LaTeX source file not found: {tex_path}"
        
        # Get the directory and filename
        tex_dir = os.path.dirname(tex_path)
        tex_file = os.path.basename(tex_path)
        tex_name = os.path.splitext(tex_file)[0]
        
        # Change to the directory containing the LaTeX file
        original_dir = os.getcwd()
        os.chdir(tex_dir)
        
        try:
            # First LaTeX run
            result = self._run_latex(tex_file)
            if not result:
                os.chdir(original_dir)
                return False, f"LaTeX compilation failed for {tex_path}"
            
            # BibTeX run if enabled
            if self.bibtex_run and os.path.exists(f"{tex_name}.aux"):
                result = self._run_bibtex(tex_name)
                if not result:
                    os.chdir(original_dir)
                    return False, f"BibTeX compilation failed for {tex_path}"
            
            # Additional LaTeX runs to resolve references
            for _ in range(1, self.latex_runs):
                result = self._run_latex(tex_file)
                if not result:
                    os.chdir(original_dir)
                    return False, f"LaTeX compilation failed for {tex_path} (pass {_ + 1})"
            
            # Check if the PDF was generated
            pdf_path = os.path.join(tex_dir, f"{tex_name}.pdf")
            if not os.path.exists(pdf_path):
                print(f"Error: PDF file not generated for {tex_path}")
                print("Checking for error logs...")
                self._check_error_logs(tex_dir, tex_name)
                os.chdir(original_dir)
                return False, f"PDF file not generated for {tex_path}"
            
            # Clean up intermediate files if not keeping them
            if not self.keep_intermediates:
                self._clean_intermediates(tex_dir, tex_name)
            
            print(f"Successfully generated PDF: {pdf_path}")
            os.chdir(original_dir)
            return True, pdf_path
        except Exception as e:
            os.chdir(original_dir)
            logger.error(f"Exception during LaTeX compilation: {e}")
            return False, f"Exception during LaTeX compilation: {e}"
    
    def _check_error_logs(self, tex_dir: str, tex_name: str) -> None:
        """
        Check LaTeX log files for errors.
        
        Args:
            tex_dir: The directory containing the LaTeX file.
            tex_name: The base name of the LaTeX file (without extension).
        """
        log_file = os.path.join(tex_dir, f"{tex_name}.log")
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    log_content = f.read()
                    
                # Look for error patterns in the log
                error_patterns = [
                    r'(?i)error:[ \t]*(.+?)(?=\n)',
                    r'(?i)! (.+?)(?=\n)',
                    r'(?i)fatal error[ \t]*(.+?)(?=\n)'
                ]
                
                errors_found = False
                print("LaTeX log errors:")
                for pattern in error_patterns:
                    for match in re.finditer(pattern, log_content, re.MULTILINE):
                        errors_found = True
                        print(f"  - {match.group(1).strip()}")
                
                if not errors_found:
                    print("  No specific errors found in log, but compilation still failed.")
            except Exception as e:
                print(f"  Error reading log file: {e}")
        else:
            print(f"  No log file found at {log_file}")
    
    def _run_latex(self, tex_file: str) -> bool:
        """
        Run the LaTeX engine on a source file.
        
        Args:
            tex_file: The LaTeX source file to compile.
            
        Returns:
            True if compilation was successful, False otherwise.
        """
        try:
            # Use the full path if we found the engine in a common location
            engine = getattr(self, '_engine_path', None) or self.latex_engine
            
            print(f"Running {engine} on {tex_file}")
            logger.info(f"Running {engine} on {tex_file}")
            
            # Build the command
            cmd = [
                engine,
                '-interaction=nonstopmode',
                '-halt-on-error',
                tex_file
            ]
            
            # Add any additional arguments from config
            additional_args = self.config.get('latex_args', [])
            if additional_args:
                cmd.extend(additional_args)
            
            # Run the command
            if platform.system() == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    startupinfo=startupinfo,
                    check=False
                )
            else:
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False
                )
            
            if result.returncode != 0:
                print(f"LaTeX compilation failed with return code {result.returncode}")
                if result.stderr:
                    print(f"Error output: {result.stderr}")
                logger.error(f"LaTeX compilation failed: {result.stderr}")
                return False
            
            print(f"LaTeX compilation successful for {tex_file}")
            logger.info(f"LaTeX compilation successful for {tex_file}")
            return True
        except Exception as e:
            print(f"Exception during LaTeX compilation: {e}")
            logger.error(f"Exception during LaTeX compilation: {e}")
            return False
    
    def _run_bibtex(self, tex_name: str) -> bool:
        """
        Run BibTeX on the auxiliary file.
        
        Args:
            tex_name: The base name of the LaTeX file (without extension).
            
        Returns:
            True if compilation was successful, False otherwise.
        """
        try:
            logger.info(f"Running bibtex on {tex_name}")
            
            # For BibTeX, we need to find the correct executable
            bibtex_cmd = 'bibtex'
            
            # If we're using a full path for the LaTeX engine, we should also look for BibTeX
            # in the same directory on Windows
            if platform.system() == 'Windows' and hasattr(self, '_engine_path') and self._engine_path:
                # Get the directory containing the LaTeX engine
                engine_dir = os.path.dirname(self._engine_path)
                bibtex_path = os.path.join(engine_dir, 'bibtex.exe')
                
                # Check if BibTeX exists in the same directory
                if os.path.exists(bibtex_path) and os.path.isfile(bibtex_path):
                    bibtex_cmd = bibtex_path
                    print(f"Using BibTeX from {bibtex_path}")
            
            # Run the command
            if platform.system() == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                result = subprocess.run(
                    [bibtex_cmd, tex_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    startupinfo=startupinfo,
                    check=False
                )
            else:
                result = subprocess.run(
                    [bibtex_cmd, tex_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False
                )
            
            if result.returncode != 0:
                logger.error(f"BibTeX compilation failed: {result.stderr}")
                return False
            
            logger.info(f"BibTeX compilation successful for {tex_name}")
            return True
        except Exception as e:
            logger.error(f"Exception during BibTeX compilation: {e}")
            return False
    
    def _clean_intermediates(self, tex_dir: str, tex_name: str) -> None:
        """
        Clean up intermediate files generated during LaTeX compilation.
        
        Args:
            tex_dir: The directory containing the LaTeX file.
            tex_name: The base name of the LaTeX file (without extension).
        """
        # List of extensions for intermediate files
        extensions = ['.aux', '.log', '.out', '.toc', '.lof', '.lot', '.bbl', '.blg', '.dvi']
        
        for ext in extensions:
            file_path = os.path.join(tex_dir, f"{tex_name}{ext}")
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"Failed to remove intermediate file {file_path}: {e}")
