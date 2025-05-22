"""
Tests for file operation commands.

This module contains benchmark tests for all file operation commands.
"""

import os
import json
import tempfile
from typing import Tuple, Dict, Any

from benchmark.test_framework import TEST_OUTPUT_DIR
from commands.file_ops.read_file import read_file
from commands.file_ops.write_file import write_file
from commands.file_ops.edit_file import edit_file
from commands.file_ops.append_file import append_file
from commands.file_ops.delete_file import delete_file
from commands.file_ops.create_directory import create_directory
from commands.file_ops.list_directory import list_directory
from commands.file_ops.file_exists import file_exists
from commands.file_ops.save_json import save_json
from commands.file_ops.load_json import load_json
from commands.file_ops.advanced_edit_file import advanced_edit_file

# Test files
TEST_FILE = os.path.join(TEST_OUTPUT_DIR, 'test_file.txt')
TEST_JSON = os.path.join(TEST_OUTPUT_DIR, 'test_data.json')
TEST_DIR = os.path.join(TEST_OUTPUT_DIR, 'test_dir')
TEST_EDIT_FILE = os.path.join(TEST_OUTPUT_DIR, 'test_edit.txt')
TEST_APPEND_FILE = os.path.join(TEST_OUTPUT_DIR, 'test_append.txt')

def test_write_file() -> Tuple[bool, str]:
    """Test the write_file command."""
    try:
        content = "This is a test file.\nIt has multiple lines.\nCreated for testing."
        result = write_file(TEST_FILE, content)
        
        # Verify the file was created
        if not os.path.exists(TEST_FILE):
            return False, "File was not created"
            
        # Verify the content was written correctly
        with open(TEST_FILE, 'r', encoding='utf-8') as f:
            file_content = f.read()
            
        if file_content != content:
            return False, f"Content mismatch: {file_content} != {content}"
            
        return True, "File written successfully"
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_read_file() -> Tuple[bool, str]:
    """Test the read_file command."""
    try:
        # First ensure there's a file to read
        content = "Test content for read_file test."
        with open(TEST_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # Read the file
        result = read_file(TEST_FILE)
        
        # Verify
        if result != content:
            return False, f"Content mismatch: {result} != {content}"
            
        return True, "File read successfully"
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_edit_file() -> Tuple[bool, str]:
    """Test the edit_file command."""
    try:
        # Create a file to edit
        original_content = "Line 1\nLine 2\nLine 3\n"
        with open(TEST_EDIT_FILE, 'w', encoding='utf-8') as f:
            f.write(original_content)
            
        # Edit the file
        new_content = "Line 1\nEdited Line 2\nLine 3\n"
        result = edit_file(TEST_EDIT_FILE, new_content)
        
        # Verify
        with open(TEST_EDIT_FILE, 'r', encoding='utf-8') as f:
            file_content = f.read()
            
        if file_content != new_content:
            return False, f"Content mismatch after edit: {file_content} != {new_content}"
            
        return True, "File edited successfully"
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_append_file() -> Tuple[bool, str]:
    """Test the append_file command."""
    try:
        # Create a file to append to
        original_content = "First line.\n"
        with open(TEST_APPEND_FILE, 'w', encoding='utf-8') as f:
            f.write(original_content)
            
        # Append to the file
        append_content = "Appended line.\n"
        result = append_file(TEST_APPEND_FILE, append_content)
        
        # Verify
        expected_content = original_content + append_content
        with open(TEST_APPEND_FILE, 'r', encoding='utf-8') as f:
            file_content = f.read()
            
        if file_content != expected_content:
            return False, f"Content mismatch after append: {file_content} != {expected_content}"
            
        return True, "Content appended successfully"
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_delete_file() -> Tuple[bool, str]:
    """Test the delete_file command."""
    try:
        # Create a file to delete
        with open(TEST_FILE, 'w', encoding='utf-8') as f:
            f.write("This file will be deleted.")
            
        # Verify it exists
        if not os.path.exists(TEST_FILE):
            return False, "Could not create file for deletion test"
            
        # Delete the file
        result = delete_file(TEST_FILE)
        
        # Verify deletion
        if os.path.exists(TEST_FILE):
            return False, "File was not deleted"
            
        return True, "File deleted successfully"
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_create_directory() -> Tuple[bool, str]:
    """Test the create_directory command."""
    try:
        # Delete the directory if it already exists
        if os.path.exists(TEST_DIR):
            os.rmdir(TEST_DIR)
            
        # Create directory
        result = create_directory(TEST_DIR)
        
        # Verify
        if not os.path.exists(TEST_DIR) or not os.path.isdir(TEST_DIR):
            return False, "Directory was not created"
            
        return True, "Directory created successfully"
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_list_directory() -> Tuple[bool, str]:
    """Test the list_directory command."""
    try:
        # Create a directory with known content
        if not os.path.exists(TEST_DIR):
            os.makedirs(TEST_DIR)
            
        # Create some files
        test_files = ['file1.txt', 'file2.txt', 'file3.txt']
        for file in test_files:
            with open(os.path.join(TEST_DIR, file), 'w') as f:
                f.write(f"Content of {file}")
                
        # List the directory
        result = list_directory(TEST_DIR)
        
        # Verify all test files are listed
        for file in test_files:
            if file not in result:
                return False, f"File {file} was not listed in result: {result}"
                
        return True, "Directory listed successfully"
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_file_exists() -> Tuple[bool, str]:
    """Test the file_exists command."""
    try:
        # Ensure a file exists
        with open(TEST_FILE, 'w') as f:
            f.write("Test file")
            
        # Check existing file
        result1 = file_exists(TEST_FILE)
        if not result1:
            return False, f"file_exists reported False for existing file"
            
        # Check non-existing file
        result2 = file_exists(TEST_FILE + ".nonexistent")
        if result2:
            return False, f"file_exists reported True for non-existent file"
            
        return True, "file_exists checked successfully"
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_save_json() -> Tuple[bool, str]:
    """Test the save_json command."""
    try:
        # Data to save
        test_data = {
            "name": "Test Data",
            "values": [1, 2, 3, 4, 5],
            "nested": {
                "key": "value",
                "flag": True
            }
        }
        
        # Save the data
        result = save_json(TEST_JSON, test_data)
        
        # Verify the file was created
        if not os.path.exists(TEST_JSON):
            return False, "JSON file was not created"
            
        # Verify content
        with open(TEST_JSON, 'r') as f:
            loaded_data = json.load(f)
            
        if loaded_data != test_data:
            return False, f"JSON data mismatch: {loaded_data} != {test_data}"
            
        return True, "JSON saved successfully"
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_load_json() -> Tuple[bool, str]:
    """Test the load_json command."""
    try:
        # Data to save and load
        test_data = {
            "name": "Test Data",
            "values": [1, 2, 3, 4, 5],
            "nested": {
                "key": "value",
                "flag": True
            }
        }
        
        # Create the file
        with open(TEST_JSON, 'w') as f:
            json.dump(test_data, f)
            
        # Load the data
        result = load_json(TEST_JSON)
        
        # Verify
        if result != test_data:
            return False, f"Loaded JSON data mismatch: {result} != {test_data}"
            
        return True, "JSON loaded successfully"
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_advanced_edit_file() -> Tuple[bool, str]:
    """Test the advanced_edit_file command."""
    try:
        # Create a file with multiple lines
        original_content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n"
        with open(TEST_EDIT_FILE, 'w', encoding='utf-8') as f:
            f.write(original_content)
            
        # Test advanced edit: replace line 3
        edits = [
            {"operation": "replace", "line_number": 3, "content": "New Line 3"},
        ]
        
        result = advanced_edit_file(TEST_EDIT_FILE, edits)
        
        # Verify
        expected_content = "Line 1\nLine 2\nNew Line 3\nLine 4\nLine 5\n"
        with open(TEST_EDIT_FILE, 'r', encoding='utf-8') as f:
            file_content = f.read()
            
        if file_content != expected_content:
            return False, f"Content mismatch after advanced edit: {file_content} != {expected_content}"
            
        return True, "Advanced edit successful"
    except Exception as e:
        return False, f"Exception: {str(e)}" 