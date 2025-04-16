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
        
        if not abs_path.startswith(base_output_dir):
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