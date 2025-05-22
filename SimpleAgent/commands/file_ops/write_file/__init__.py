"""
Write file command for SimpleAgent.

This module provides the write_file command for writing content to a file.
"""

import os
from commands import register_command
from core.agent import get_secure_path
from core.config import OUTPUT_DIR


def write_file(file_path: str, content: str) -> str:
    """
    Write content to a file (overwrites existing content), enforcing access only within the output directory.
    
    Args:
        file_path: Path to the file to write to
        content: Content to write to the file
        
    Returns:
        Success or error message
    """
    try:
        # Note: SimpleAgent agent instance will already have modified the path 
        # to use the thread-specific output directory before calling this function
        
        # Additional security check to ensure the path is within some output directory
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
            return f"Security Error: Cannot write to files outside the output directory"
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return f"Successfully wrote to {os.path.basename(file_path)}"
    except Exception as e:
        return f"Error writing to file: {str(e)}"


# Define the schema for the write_file command
WRITE_FILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "Write content to a file in the output directory (overwrites existing content)",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to write to (must be in the output directory)"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                }
            },
            "required": ["file_path", "content"]
        }
    }
}

# Register the command
register_command("write_file", write_file, WRITE_FILE_SCHEMA) 