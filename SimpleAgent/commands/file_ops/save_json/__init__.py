"""
Save JSON command for SimpleAgent.

This module provides the save_json command for saving data as JSON to a file.
"""

import os
import json
from typing import Dict, Any
from commands import register_command


def save_json(file_path: str, data: Dict[str, Any]) -> str:
    """
    Save data as JSON to a file.
    
    Args:
        file_path: Path to the file to save to
        data: Data to save as JSON
        
    Returns:
        Success or error message
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2)
        return f"Successfully saved JSON to {file_path}"
    except Exception as e:
        return f"Error saving JSON: {str(e)}"


# Define the schema for the save_json command
SAVE_JSON_SCHEMA = {
    "type": "function",
    "function": {
        "name": "save_json",
        "description": "Save data as JSON to a file",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to save to"
                },
                "data": {
                    "type": "object",
                    "description": "Data to save as JSON"
                }
            },
            "required": ["file_path", "data"]
        }
    }
}

# Register the command
register_command("save_json", save_json, SAVE_JSON_SCHEMA) 