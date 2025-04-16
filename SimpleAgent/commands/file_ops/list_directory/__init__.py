"""
List directory command for SimpleAgent.

This module provides the list_directory command for listing the contents of a directory.
"""

import os
from typing import List
from commands import register_command


def list_directory(directory_path: str = '.') -> List[str]:
    """
    List the contents of a directory.
    
    Args:
        directory_path: Path to the directory to list (defaults to current directory)
        
    Returns:
        List of files and directories in the specified directory
    """
    try:
        return os.listdir(directory_path)
    except Exception as e:
        return [f"Error listing directory: {str(e)}"]


# Define the schema for the list_directory command
LIST_DIRECTORY_SCHEMA = {
    "type": "function",
    "function": {
        "name": "list_directory",
        "description": "List the contents of a directory",
        "parameters": {
            "type": "object",
            "properties": {
                "directory_path": {
                    "type": "string",
                    "description": "Path to the directory to list (defaults to current directory)"
                }
            },
            "required": []
        }
    }
}

# Register the command
register_command("list_directory", list_directory, LIST_DIRECTORY_SCHEMA) 