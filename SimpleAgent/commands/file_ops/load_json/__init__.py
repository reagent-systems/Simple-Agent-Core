"""
Load JSON command for SimpleAgent.

This module provides the load_json command for loading JSON data from a file.
"""

import json
from typing import Dict, Any
from commands import register_command


def load_json(file_path: str) -> Dict[str, Any]:
    """
    Load JSON data from a file.
    
    Args:
        file_path: Path to the file to load from
        
    Returns:
        The loaded JSON data as a dictionary
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        return {"error": f"Error loading JSON: {str(e)}"}


# Define the schema for the load_json command
LOAD_JSON_SCHEMA = {
    "type": "function",
    "function": {
        "name": "load_json",
        "description": "Load JSON data from a file",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to load from"
                }
            },
            "required": ["file_path"]
        }
    }
}

# Register the command
register_command("load_json", load_json, LOAD_JSON_SCHEMA) 