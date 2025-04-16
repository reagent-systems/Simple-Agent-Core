"""
Create directory command for SimpleAgent.

This module provides the create_directory command for creating a directory.
"""

import os
from commands import register_command


def create_directory(directory_path: str) -> str:
    """
    Create a directory.
    
    Args:
        directory_path: Path to the directory to create
        
    Returns:
        Success or error message
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return f"Successfully created directory {directory_path}"
    except Exception as e:
        return f"Error creating directory: {str(e)}"


# Define the schema for the create_directory command
CREATE_DIRECTORY_SCHEMA = {
    "type": "function",
    "function": {
        "name": "create_directory",
        "description": "Create a directory",
        "parameters": {
            "type": "object",
            "properties": {
                "directory_path": {
                    "type": "string",
                    "description": "Path to the directory to create"
                }
            },
            "required": ["directory_path"]
        }
    }
}

# Register the command
register_command("create_directory", create_directory, CREATE_DIRECTORY_SCHEMA) 