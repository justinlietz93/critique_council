"""
File management utilities for LaTeX document generation.

This module provides file handling utilities for reading templates and writing
output files for LaTeX document generation.
"""

import os
import shutil
import logging
from typing import Dict, Any, Optional, List, Union, TextIO

logger = logging.getLogger(__name__)


class FileManager:
    """
    Utility class for file operations related to LaTeX document generation.
    
    This class handles file operations such as reading templates, writing output
    files, and copying resources to the output directory.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the file manager.
        
        Args:
            config: Optional configuration dictionary containing file paths and options.
        """
        self.config = config or {}
        self.template_dir = self.config.get('template_dir', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'))
        self.output_dir = self.config.get('output_dir', 'latex_output')
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def read_template(self, template_name: str) -> str:
        """
        Read a template file from the template directory.
        
        Args:
            template_name: The name of the template file to read.
            
        Returns:
            The content of the template file.
            
        Raises:
            FileNotFoundError: If the template file doesn't exist.
        """
        template_path = os.path.join(self.template_dir, template_name)
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Template file not found: {template_path}")
            raise FileNotFoundError(f"Template file not found: {template_path}")
    
    def write_output_file(self, file_name: str, content: str) -> str:
        """
        Write content to an output file in the output directory.
        
        Args:
            file_name: The name of the output file.
            content: The content to write to the file.
            
        Returns:
            The path to the output file.
        """
        output_path = os.path.join(self.output_dir, file_name)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info(f"Output file written: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to write output file: {output_path}. Error: {e}")
            raise
    
    def copy_resource(self, source_path: str, dest_name: Optional[str] = None) -> str:
        """
        Copy a resource file to the output directory.
        
        Args:
            source_path: The path to the source file.
            dest_name: Optional name for the destination file. If not provided,
                       the basename of the source file is used.
            
        Returns:
            The path to the copied resource in the output directory.
            
        Raises:
            FileNotFoundError: If the source file doesn't exist.
        """
        if not os.path.exists(source_path):
            logger.error(f"Resource file not found: {source_path}")
            raise FileNotFoundError(f"Resource file not found: {source_path}")
        
        dest_name = dest_name or os.path.basename(source_path)
        dest_path = os.path.join(self.output_dir, dest_name)
        
        try:
            shutil.copy2(source_path, dest_path)
            logger.info(f"Resource copied: {source_path} -> {dest_path}")
            return dest_path
        except Exception as e:
            logger.error(f"Failed to copy resource: {source_path} -> {dest_path}. Error: {e}")
            raise
    
    def copy_templates_to_output(self, template_names: List[str]) -> List[str]:
        """
        Copy template files to the output directory.
        
        Args:
            template_names: List of template file names to copy.
            
        Returns:
            List of paths to the copied templates in the output directory.
        """
        copied_paths = []
        
        for template_name in template_names:
            template_path = os.path.join(self.template_dir, template_name)
            
            if not os.path.exists(template_path):
                logger.warning(f"Template file not found: {template_path}, skipping")
                continue
                
            dest_path = os.path.join(self.output_dir, template_name)
            
            try:
                shutil.copy2(template_path, dest_path)
                logger.info(f"Template copied: {template_path} -> {dest_path}")
                copied_paths.append(dest_path)
            except Exception as e:
                logger.error(f"Failed to copy template: {template_path} -> {dest_path}. Error: {e}")
                continue
                
        return copied_paths
    
    def render_template(self, template_content: str, context: Dict[str, Any]) -> str:
        """
        Render a template with the given context.
        
        This is a simple placeholder replacement implementation. For more complex
        templates, consider using a proper template engine like Jinja2.
        
        Args:
            template_content: The template content to render.
            context: The context dictionary with values to replace placeholders.
            
        Returns:
            The rendered template.
        """
        rendered = template_content
        
        # Simple placeholder replacement
        for key, value in context.items():
            placeholder = f"${key}$"
            rendered = rendered.replace(placeholder, str(value))
            
        # Handle conditional sections
        for key, value in context.items():
            if_start = f"$if({key})$"
            if_end = f"$endif({key})$"
            
            if if_start in rendered:
                # Find the if block
                if_pos = rendered.find(if_start)
                endif_pos = rendered.find(if_end)
                
                if endif_pos > if_pos:
                    # Extract the block content
                    block_start = if_pos + len(if_start)
                    block_content = rendered[block_start:endif_pos]
                    
                    # Replace the entire block
                    if value:
                        # Keep the content
                        rendered = rendered[:if_pos] + block_content + rendered[endif_pos + len(if_end):]
                    else:
                        # Remove the content
                        rendered = rendered[:if_pos] + rendered[endif_pos + len(if_end):]
        
        return rendered

    def clean_output_directory(self) -> None:
        """
        Clean the output directory by removing all files.
        
        This method removes all files from the output directory but keeps the
        directory itself.
        """
        if os.path.exists(self.output_dir):
            for item in os.listdir(self.output_dir):
                item_path = os.path.join(self.output_dir, item)
                
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except Exception as e:
                    logger.error(f"Failed to remove item: {item_path}. Error: {e}")
                    
            logger.info(f"Output directory cleaned: {self.output_dir}")
        else:
            logger.info(f"Output directory doesn't exist, creating: {self.output_dir}")
            os.makedirs(self.output_dir, exist_ok=True)
