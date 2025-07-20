"""
Access Input File Command

This command allows the agent to securely access files from the input directory.
It provides read-only access to user-placed files with proper security validation.
"""

import json
from typing import Dict, Any, List

from core.execution.tool_manager import register_command
from core.utils.input_manager import InputManager


def access_input_file(filename: str = "", operation: str = "read", search_term: str = None, encoding: str = "utf-8") -> str:
    """
    Access and read input files securely.
    
    Args:
        filename: Name of the file to access
        operation: Operation to perform ("read", "info", "list", "search", "json", "csv")
        search_term: Term to search for (only used with "search" operation)
        encoding: Text encoding to use for reading (default: utf-8)
        
    Returns:
        String containing the requested information or file content
    """
    input_manager = InputManager()
    
    try:
        if operation == "list":
            # List all available input files
            files = input_manager.list_input_files()
            if not files:
                return "No input files found in the input directory."
            
            result = "Available input files:\n"
            for file_info in files:
                size_kb = file_info.size / 1024
                result += f"- {file_info.name} ({size_kb:.1f} KB, {file_info.extension}, modified: {file_info.modified_time.strftime('%Y-%m-%d %H:%M')})\n"
            
            return result.strip()
        
        elif operation == "info":
            # Get detailed information about a specific file
            if not filename:
                return "Error: filename is required for 'info' operation"
            
            file_info = input_manager.get_input_file_info(filename)
            size_kb = file_info.size / 1024
            
            return f"""File Information for '{filename}':
- Size: {file_info.size} bytes ({size_kb:.1f} KB)
- Type: {file_info.extension} ({file_info.mime_type})
- Modified: {file_info.modified_time.strftime('%Y-%m-%d %H:%M:%S')}
- Text file: {'Yes' if file_info.is_text else 'No'}
- Encoding: {file_info.encoding or 'Unknown'}"""
        
        elif operation == "read":
            # Read the full content of a file
            if not filename:
                return "Error: filename is required for 'read' operation"
            
            content = input_manager.read_input_file(filename, encoding)
            
            # Add a header with file info
            file_info = input_manager.get_input_file_info(filename)
            size_kb = file_info.size / 1024
            
            header = f"=== Content of '{filename}' ({size_kb:.1f} KB) ===\n"
            return header + content
        
        elif operation == "search":
            # Search for a term within a file
            if not filename:
                return "Error: filename is required for 'search' operation"
            if not search_term:
                return "Error: search_term is required for 'search' operation"
            
            results = input_manager.search_file_content(filename, search_term, case_sensitive=False)
            
            if not results:
                return f"No matches found for '{search_term}' in '{filename}'"
            
            result = f"Found {len(results)} matches for '{search_term}' in '{filename}':\n\n"
            for line_num, line_content in results:
                result += f"Line {line_num}: {line_content.strip()}\n"
            
            return result.strip()
        
        elif operation == "json":
            # Read and parse a JSON file
            if not filename:
                return "Error: filename is required for 'json' operation"
            
            data = input_manager.read_json_file(filename)
            
            # Format the JSON nicely
            formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
            
            header = f"=== JSON Content of '{filename}' ===\n"
            return header + formatted_json
        
        elif operation == "csv":
            # Read a CSV file and return lines
            if not filename:
                return "Error: filename is required for 'csv' operation"
            
            lines = input_manager.read_csv_lines(filename)
            
            if not lines:
                return f"CSV file '{filename}' is empty or contains no valid lines"
            
            result = f"=== CSV Content of '{filename}' ({len(lines)} lines) ===\n"
            for i, line in enumerate(lines[:50], 1):  # Show first 50 lines
                result += f"{i}: {line}\n"
            
            if len(lines) > 50:
                result += f"\n... and {len(lines) - 50} more lines"
            
            return result.strip()
        
        elif operation == "summary":
            # Get a summary of all input files
            summary = input_manager.get_file_summary()
            
            result = f"Input Directory Summary:\n"
            result += f"- Total files: {summary['total_files']}\n"
            result += f"- Total size: {summary['total_size'] / 1024:.1f} KB\n"
            
            if summary['file_types']:
                result += f"- File types: {', '.join(f'{ext}({count})' for ext, count in summary['file_types'].items())}\n"
            
            if summary['files']:
                result += f"\nFiles:\n"
                for file_data in summary['files']:
                    result += f"  - {file_data['name']} ({file_data['size']/1024:.1f} KB)\n"
            
            return result.strip()
        
        else:
            return f"Error: Unknown operation '{operation}'. Available operations: read, info, list, search, json, csv, summary"
    
    except FileNotFoundError as e:
        return f"Error: File not found - {str(e)}"
    except PermissionError as e:
        return f"Error: Access denied - {str(e)}"
    except ValueError as e:
        return f"Error: Invalid file or operation - {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


# Command schema for the tool manager
ACCESS_INPUT_FILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "access_input_file",
        "description": "Access and read files from the input directory. Supports various operations like reading content, getting file info, listing files, searching content, and parsing JSON/CSV files.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Name of the file to access (required for most operations except 'list' and 'summary')"
                },
                "operation": {
                    "type": "string",
                    "enum": ["read", "info", "list", "search", "json", "csv", "summary"],
                    "description": "Operation to perform: 'read' (read full content), 'info' (get file details), 'list' (list all files), 'search' (search for text), 'json' (parse JSON), 'csv' (read CSV lines), 'summary' (get directory summary)",
                    "default": "read"
                },
                "search_term": {
                    "type": "string",
                    "description": "Term to search for (only used with 'search' operation)"
                },
                "encoding": {
                    "type": "string",
                    "description": "Text encoding to use for reading files",
                    "default": "utf-8"
                }
            },
            "required": []
        }
    }
}

# Register the command
register_command("access_input_file", access_input_file, ACCESS_INPUT_FILE_SCHEMA)
