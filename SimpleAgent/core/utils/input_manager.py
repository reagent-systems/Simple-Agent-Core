"""
Input Manager Module

This module provides secure input file management for SimpleAgent.
It handles reading, listing, and validating input files while maintaining security.

Security Notes:
- All input file operations are restricted to the input directory
- File size and extension validation prevents malicious files
- Read-only access ensures input files cannot be modified
"""

import os
import json
import mimetypes
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from core.utils.config import INPUT_DIR, MAX_INPUT_FILE_SIZE, ALLOWED_INPUT_EXTENSIONS
from core.utils.security import get_secure_input_path, validate_input_file


@dataclass
class InputFileInfo:
    """Information about an input file."""
    name: str
    path: str
    size: int
    extension: str
    mime_type: str
    modified_time: datetime
    is_text: bool
    encoding: Optional[str] = None


class InputManager:
    """
    Manages secure access to input files for SimpleAgent.
    Provides methods to list, read, and validate input files.
    """
    
    def __init__(self):
        self.input_dir = INPUT_DIR
        self._ensure_input_dir_exists()
    
    def _ensure_input_dir_exists(self):
        """Ensure the input directory exists."""
        if not os.path.exists(self.input_dir):
            os.makedirs(self.input_dir)
    
    def list_input_files(self) -> List[InputFileInfo]:
        """
        List all valid input files in the input directory.
        
        Returns:
            List of InputFileInfo objects for valid files
        """
        files = []
        
        if not os.path.exists(self.input_dir):
            return files
        
        try:
            for filename in os.listdir(self.input_dir):
                file_path = os.path.join(self.input_dir, filename)
                
                # Skip directories and hidden files
                if not os.path.isfile(file_path) or filename.startswith('.'):
                    continue
                
                # Validate the file
                if validate_input_file(filename):
                    try:
                        file_info = self._get_file_info(filename)
                        files.append(file_info)
                    except Exception:
                        # Skip files that can't be processed
                        continue
        
        except Exception:
            # If we can't list the directory, return empty list
            pass
        
        return sorted(files, key=lambda f: f.name.lower())
    
    def _get_file_info(self, filename: str) -> InputFileInfo:
        """
        Get detailed information about a file.
        
        Args:
            filename: Name of the file
            
        Returns:
            InputFileInfo object with file details
        """
        secure_path = get_secure_input_path(filename)
        stat = os.stat(secure_path)
        
        # Get file extension and MIME type
        extension = os.path.splitext(filename)[1].lower()
        mime_type, encoding = mimetypes.guess_type(filename)
        
        # Determine if it's a text file
        is_text = (
            mime_type and mime_type.startswith('text/') or
            extension in ['.txt', '.md', '.json', '.csv', '.py', '.js', '.html', '.css', '.xml', '.yaml', '.yml']
        )
        
        return InputFileInfo(
            name=filename,
            path=secure_path,
            size=stat.st_size,
            extension=extension,
            mime_type=mime_type or 'application/octet-stream',
            modified_time=datetime.fromtimestamp(stat.st_mtime),
            is_text=is_text,
            encoding=encoding
        )
    
    def read_input_file(self, filename: str, encoding: str = 'utf-8') -> str:
        """
        Securely read the contents of an input file.
        
        Args:
            filename: Name of the file to read
            encoding: Text encoding to use (default: utf-8)
            
        Returns:
            File contents as string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file access is not allowed
            ValueError: If file is invalid or too large
            UnicodeDecodeError: If file can't be decoded with specified encoding
        """
        secure_path = get_secure_input_path(filename)
        
        try:
            with open(secure_path, 'r', encoding=encoding) as f:
                content = f.read()
            return content
        except UnicodeDecodeError as e:
            # Try with different encodings
            for fallback_encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(secure_path, 'r', encoding=fallback_encoding) as f:
                        content = f.read()
                    return content
                except UnicodeDecodeError:
                    continue
            # If all encodings fail, raise the original error
            raise e
    
    def read_input_file_binary(self, filename: str) -> bytes:
        """
        Read the binary contents of an input file.
        
        Args:
            filename: Name of the file to read
            
        Returns:
            File contents as bytes
            
        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file access is not allowed
            ValueError: If file is invalid or too large
        """
        secure_path = get_secure_input_path(filename)
        
        with open(secure_path, 'rb') as f:
            content = f.read()
        return content
    
    def get_input_file_info(self, filename: str) -> InputFileInfo:
        """
        Get information about a specific input file.
        
        Args:
            filename: Name of the file
            
        Returns:
            InputFileInfo object with file details
            
        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file access is not allowed
            ValueError: If file is invalid
        """
        # Validate file first
        if not validate_input_file(filename):
            raise ValueError(f"Invalid input file: {filename}")
        
        return self._get_file_info(filename)
    
    def file_exists(self, filename: str) -> bool:
        """
        Check if an input file exists and is valid.
        
        Args:
            filename: Name of the file to check
            
        Returns:
            True if file exists and is valid, False otherwise
        """
        return validate_input_file(filename)
    
    def get_file_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all input files.
        
        Returns:
            Dictionary with file summary information
        """
        files = self.list_input_files()
        
        total_size = sum(f.size for f in files)
        file_types = {}
        
        for file_info in files:
            ext = file_info.extension or 'no extension'
            file_types[ext] = file_types.get(ext, 0) + 1
        
        return {
            'total_files': len(files),
            'total_size': total_size,
            'file_types': file_types,
            'files': [
                {
                    'name': f.name,
                    'size': f.size,
                    'type': f.extension,
                    'modified': f.modified_time.isoformat()
                }
                for f in files
            ]
        }
    
    def read_json_file(self, filename: str) -> Dict[str, Any]:
        """
        Read and parse a JSON input file.
        
        Args:
            filename: Name of the JSON file
            
        Returns:
            Parsed JSON data as dictionary
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not valid JSON
        """
        content = self.read_input_file(filename)
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file {filename}: {e}")
    
    def read_csv_lines(self, filename: str) -> List[str]:
        """
        Read a CSV file and return lines.
        
        Args:
            filename: Name of the CSV file
            
        Returns:
            List of lines from the CSV file
        """
        content = self.read_input_file(filename)
        return [line.strip() for line in content.splitlines() if line.strip()]
    
    def search_file_content(self, filename: str, search_term: str, case_sensitive: bool = False) -> List[Tuple[int, str]]:
        """
        Search for a term within a file's content.
        
        Args:
            filename: Name of the file to search
            search_term: Term to search for
            case_sensitive: Whether search should be case sensitive
            
        Returns:
            List of tuples (line_number, line_content) containing the search term
        """
        content = self.read_input_file(filename)
        lines = content.splitlines()
        results = []
        
        search_term_processed = search_term if case_sensitive else search_term.lower()
        
        for i, line in enumerate(lines, 1):
            line_processed = line if case_sensitive else line.lower()
            if search_term_processed in line_processed:
                results.append((i, line))
        
        return results
