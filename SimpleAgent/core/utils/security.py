"""
SimpleAgent Security Module

This module contains security functions for SimpleAgent, particularly
for handling file paths securely to prevent directory traversal attacks.

Security Notes:
- All file operations are restricted to the output directory
- Multiple layers of path validation prevent directory traversal attacks
- Absolute paths and path traversal attempts (../) are sanitized
"""

import os
from core.utils.config import OUTPUT_DIR, INPUT_DIR, MAX_INPUT_FILE_SIZE, ALLOWED_INPUT_EXTENSIONS

def get_secure_path(file_path: str, base_dir: str = OUTPUT_DIR) -> str:
    """
    Securely convert any file path to be within the specified base directory.
    This prevents path traversal attacks and ensures file operations are contained.
    
    Args:
        file_path: Original file path
        base_dir: Base directory to contain the file (defaults to OUTPUT_DIR)
        
    Returns:
        Modified file path within the base directory
    """
    # Normalize path separators to system default
    file_path = file_path.replace('/', os.path.sep).replace('\\', os.path.sep)
    
    # Check if the path already starts with the output directory pattern
    # This handles cases where the path might already have the output directory in it
    abs_file_path = os.path.abspath(file_path)
    abs_base_dir = os.path.abspath(base_dir)
    
    # If the path is already within the output directory, return it as is
    if abs_file_path.startswith(abs_base_dir):
        return file_path
    
    # Get just the basename to handle absolute paths or traversal attempts
    file_name = os.path.basename(file_path)
    
    # If the path is absolute or empty, just use the filename in base dir
    if os.path.isabs(file_path) or not file_path:
        return os.path.join(base_dir, file_name)
    
    # Remove any leading dots, slashes, or path traversal patterns
    # This prevents patterns like '../../../.env' from working
    clean_path = file_path
    while clean_path.startswith(('.', os.path.sep)):
        clean_path = clean_path.lstrip('.' + os.path.sep)
        
    # If path is empty after cleaning, just use filename
    if not clean_path:
        return os.path.join(base_dir, file_name)
        
    # For security, resolve absolute paths after joining with output directory
    # to ensure the final path is always within output directory
    combined_path = os.path.normpath(os.path.join(base_dir, clean_path))
    
    # Final security check: ensure the resolved path is within output directory
    # by comparing the absolute paths
    abs_combined_path = os.path.abspath(combined_path)
    
    if not abs_combined_path.startswith(abs_base_dir):
        # If the path escapes output directory, block access
        raise PermissionError(f"Security Error: Attempted to access file outside the output directory: {abs_combined_path}")

    return combined_path


def get_secure_input_path(file_path: str) -> str:
    """
    Securely convert any file path to be within the input directory.
    This prevents path traversal attacks and ensures input file operations are contained.
    
    Args:
        file_path: Original file path
        
    Returns:
        Modified file path within the input directory
        
    Raises:
        PermissionError: If the path attempts to escape the input directory
        FileNotFoundError: If the input file doesn't exist
        ValueError: If the file extension is not allowed or file is too large
    """
    # Normalize path separators to system default
    file_path = file_path.replace('/', os.path.sep).replace('\\', os.path.sep)
    
    # Get just the basename to handle absolute paths or traversal attempts
    file_name = os.path.basename(file_path)
    
    # If no filename provided, raise error
    if not file_name:
        raise ValueError("No filename provided")
    
    # Remove any leading dots, slashes, or path traversal patterns
    clean_path = file_path
    while clean_path.startswith(('.', os.path.sep)):
        clean_path = clean_path.lstrip('.' + os.path.sep)
        
    # If path is empty after cleaning, just use filename
    if not clean_path:
        clean_path = file_name
        
    # Construct the full path within input directory
    combined_path = os.path.normpath(os.path.join(INPUT_DIR, clean_path))
    
    # Final security check: ensure the resolved path is within input directory
    abs_combined_path = os.path.abspath(combined_path)
    abs_input_dir = os.path.abspath(INPUT_DIR)
    
    if not abs_combined_path.startswith(abs_input_dir):
        raise PermissionError(f"Security Error: Attempted to access file outside the input directory: {abs_combined_path}")
    
    # Check if file exists
    if not os.path.exists(combined_path):
        raise FileNotFoundError(f"Input file not found: {file_name}")
    
    # Check if it's actually a file (not a directory)
    if not os.path.isfile(combined_path):
        raise ValueError(f"Path is not a file: {file_name}")
    
    # Check file extension
    file_ext = os.path.splitext(file_name)[1].lower()
    if file_ext not in ALLOWED_INPUT_EXTENSIONS:
        raise ValueError(f"File extension '{file_ext}' not allowed. Allowed extensions: {', '.join(ALLOWED_INPUT_EXTENSIONS)}")
    
    # Check file size
    file_size = os.path.getsize(combined_path)
    if file_size > MAX_INPUT_FILE_SIZE:
        raise ValueError(f"File too large: {file_size} bytes. Maximum allowed: {MAX_INPUT_FILE_SIZE} bytes")
    
    return combined_path


def validate_input_file(file_path: str) -> bool:
    """
    Validate if an input file can be safely accessed.
    
    Args:
        file_path: Path to the input file
        
    Returns:
        True if file is valid and safe to access, False otherwise
    """
    try:
        get_secure_input_path(file_path)
        return True
    except (PermissionError, FileNotFoundError, ValueError):
        return False
