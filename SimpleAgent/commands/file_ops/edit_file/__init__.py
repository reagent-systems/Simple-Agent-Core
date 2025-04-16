"""
Edit file command for SimpleAgent.

This module provides the edit_file command for making targeted edits to a file.
"""

import os
from commands import register_command


def edit_file(file_path: str, content: str, edit_type: str = "replace") -> str:
    """
    Edit a file with various operations.
    
    Args:
        file_path: Path to the file to edit
        content: New content or content to insert
        edit_type: Type of edit operation (replace, insert_at_line, replace_line, append)
        
    Returns:
        Success or error message
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return f"Error: File {file_path} does not exist"
            
        # Read the current content
        with open(file_path, 'r', encoding='utf-8') as file:
            current_content = file.read()
            
        new_content = ""
        
        if edit_type == "replace":
            # Replace the entire file content
            new_content = content
        elif edit_type == "append":
            # Append to the end of the file
            new_content = current_content + content
        else:
            return f"Error: Unsupported edit type '{edit_type}'"
            
        # Write the modified content back to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(new_content)
            
        return f"Successfully edited {file_path} with operation: {edit_type}"
    except Exception as e:
        return f"Error editing file: {str(e)}"


# Define the schema for the edit_file command
EDIT_FILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "edit_file",
        "description": "Edit a file with various operations (replace entire content or append)",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to edit"
                },
                "content": {
                    "type": "string",
                    "description": "New content or content to insert"
                },
                "edit_type": {
                    "type": "string",
                    "description": "Type of edit operation",
                    "enum": ["replace", "append"],
                    "default": "replace"
                }
            },
            "required": ["file_path", "content"]
        }
    }
}

# Register the command
register_command("edit_file", edit_file, EDIT_FILE_SCHEMA)