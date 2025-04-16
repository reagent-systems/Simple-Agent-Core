"""
Advanced file editing command for SimpleAgent.

This module provides the advanced_edit_file command for making more complex edits to a file.
"""

import os
from commands import register_command


def advanced_edit_file(file_path: str, edit_operations: list) -> str:
    """
    Perform multiple edit operations on a file.
    
    Args:
        file_path: Path to the file to edit
        edit_operations: List of edit operations to perform
            Each operation is a dict with:
            - operation: Type of operation (insert_line, replace_line, delete_line)
            - line_number: Line number to operate on (1-based)
            - content: Content to insert or replace (not needed for delete)
        
    Returns:
        Success or error message
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return f"Error: File {file_path} does not exist"
            
        # Read the current content
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            
        # Apply each edit operation
        for op in edit_operations:
            operation = op.get("operation")
            line_number = op.get("line_number")
            content = op.get("content", "")
            
            # Validate line number
            if line_number is None:
                return "Error: Missing line_number in edit operation"
            
            # Convert to 0-based index
            line_idx = line_number - 1
            
            # Ensure line_idx is valid
            if line_idx < 0:
                return f"Error: Invalid line number {line_number}"
                
            # Extend lines list if needed
            while len(lines) <= line_idx:
                lines.append("\n")
                
            # Apply the operation
            if operation == "insert_line":
                # Ensure content ends with newline
                if not content.endswith("\n"):
                    content += "\n"
                lines.insert(line_idx, content)
            elif operation == "replace_line":
                # Ensure content ends with newline
                if not content.endswith("\n"):
                    content += "\n"
                lines[line_idx] = content
            elif operation == "delete_line":
                if 0 <= line_idx < len(lines):
                    lines.pop(line_idx)
            else:
                return f"Error: Unsupported operation '{operation}'"
                
        # Write the modified content back to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
            
        return f"Successfully applied {len(edit_operations)} edit operations to {file_path}"
    except Exception as e:
        return f"Error editing file: {str(e)}"


# Define the schema for the advanced_edit_file command
ADVANCED_EDIT_FILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "advanced_edit_file",
        "description": "Perform multiple line-specific edit operations on a file",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to edit"
                },
                "edit_operations": {
                    "type": "array",
                    "description": "List of edit operations to perform",
                    "items": {
                        "type": "object",
                        "properties": {
                            "operation": {
                                "type": "string",
                                "description": "Type of operation",
                                "enum": ["insert_line", "replace_line", "delete_line"]
                            },
                            "line_number": {
                                "type": "integer",
                                "description": "Line number to operate on (1-based)"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to insert or replace (not needed for delete)"
                            }
                        },
                        "required": ["operation", "line_number"]
                    }
                }
            },
            "required": ["file_path", "edit_operations"]
        }
    }
}

# Register the command
register_command("advanced_edit_file", advanced_edit_file, ADVANCED_EDIT_FILE_SCHEMA)