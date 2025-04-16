"""
Append file command for SimpleAgent.

This module provides the append_file command for appending content to a file.
"""

import os
from commands import register_command


def append_file(file_path: str, content: str) -> str:
    """
    Append content to a file.
    
    Args:
        file_path: Path to the file to append to
        content: Content to append to the file
        
    Returns:
        Success or error message
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(content)
        return f"Successfully appended to {file_path}"
    except Exception as e:
        return f"Error appending to file: {str(e)}"


# Define the schema for the append_file command
APPEND_FILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "append_file",
        "description": "Append content to a file",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to append to"
                },
                "content": {
                    "type": "string",
                    "description": "Content to append to the file"
                }
            },
            "required": ["file_path", "content"]
        }
    }
}

# Register the command
register_command("append_file", append_file, APPEND_FILE_SCHEMA) 