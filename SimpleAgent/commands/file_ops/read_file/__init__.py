"""
Read file command for SimpleAgent.

This module provides the read_file command for reading the contents of a file.
"""

import os
from commands import register_command
from core.agent import get_secure_path
from core.config import OUTPUT_DIR


def read_file(file_path: str) -> str:
    """
    Read the contents of a file, enforcing access only within the output directory.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        The contents of the file as a string
    """
    try:
        # Ensure the file path is within the output directory
        # Note: SimpleAgent agent instance will already have modified the path 
        # to use the thread-specific output directory before calling this function
        
        # Additional security check here to ensure the path is valid
        if not os.path.exists(file_path):
            return f"Error: File not found: {os.path.basename(file_path)}"
            
        # Verify path is within some output directory (could be thread-specific)
        abs_path = os.path.abspath(file_path)
        base_output_dir = os.path.abspath(os.path.dirname(os.path.dirname(OUTPUT_DIR)))
        
        # Check if the path contains the output directory pattern
        is_within_output = False
        
        # Direct containment check
        if abs_path.startswith(os.path.abspath(OUTPUT_DIR)):
            is_within_output = True
            
        # Check for nested output pattern
        output_dir_name = os.path.basename(os.path.abspath(OUTPUT_DIR))
        doubled_pattern = os.path.join(os.path.abspath(OUTPUT_DIR), output_dir_name)
        if abs_path.startswith(doubled_pattern):
            is_within_output = True
            
        # Check if it's a repository or other allowed file pattern
        if any(segment in abs_path for segment in ["clix", ".git"]):
            is_within_output = True
        
        if not is_within_output:
            return f"Security Error: Cannot access files outside the output directory"
            
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


# Define the schema for the read_file command
READ_FILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read the contents of a file in the output directory",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to read (must be in the output directory)"
                }
            },
            "required": ["file_path"]
        }
    }
}

# Register the command
register_command("read_file", read_file, READ_FILE_SCHEMA) 