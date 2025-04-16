"""
Delete file command for SimpleAgent.

This module provides the delete_file command for deleting a file.
"""

import os
from commands import register_command


def delete_file(file_path: str) -> str:
    """
    Delete a file.
    
    Args:
        file_path: Path to the file to delete
        
    Returns:
        Success or error message
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return f"Successfully deleted {file_path}"
        else:
            return f"File {file_path} does not exist"
    except Exception as e:
        return f"Error deleting file: {str(e)}"


# Define the schema for the delete_file command
DELETE_FILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "delete_file",
        "description": "Delete a file",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to delete"
                }
            },
            "required": ["file_path"]
        }
    }
}

# Register the command
register_command("delete_file", delete_file, DELETE_FILE_SCHEMA) 