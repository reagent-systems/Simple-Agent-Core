"""
File exists command for SimpleAgent.

This module provides the file_exists command for checking if a file exists.
"""

import os
from commands import register_command


def file_exists(file_path: str) -> bool:
    """
    Check if a file exists.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        True if the file exists, False otherwise
    """
    return os.path.exists(file_path)


# Define the schema for the file_exists command
FILE_EXISTS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "file_exists",
        "description": "Check if a file exists",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to check"
                }
            },
            "required": ["file_path"]
        }
    }
}

# Register the command
register_command("file_exists", file_exists, FILE_EXISTS_SCHEMA) 