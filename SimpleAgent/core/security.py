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
from core.config import OUTPUT_DIR

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
    abs_base_dir = os.path.abspath(base_dir)
    abs_combined_path = os.path.abspath(combined_path)
    
    if not abs_combined_path.startswith(abs_base_dir):
        # If the path escapes output directory, fall back to just using filename in output dir
        return os.path.join(base_dir, file_name)
        
    return combined_path 