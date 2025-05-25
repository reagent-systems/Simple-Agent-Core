"""
Test Cases for Problem-Solving Implementation

This module contains test cases that will be used to benchmark and compare
the old and new problem-solving implementations.
"""

from test_framework import TestCase

# Test Case 1: Simple File Creation
FILE_CREATION_TEST = TestCase(
    task_id="file_creation",
    description="Create a file with specific content and verify its existence and content",
    initial_state={
        "target_file": "test_output/test_file.txt",
        "expected_content": "Hello, World!"
    },
    success_criteria=[
        {
            "name": "file_exists",
            "description": "The target file should exist",
            "check": lambda state: state.get("file_exists", False)
        },
        {
            "name": "content_matches",
            "description": "The file content should match the expected content",
            "check": lambda state: state.get("file_content", "") == state.get("expected_content", "")
        }
    ]
)

# Test Case 2: Complex File Operations
FILE_OPERATIONS_TEST = TestCase(
    task_id="file_operations",
    description="Perform multiple file operations including creation, modification, and cleanup",
    initial_state={
        "files_to_create": [
            {"path": "test_output/file1.txt", "content": "Content 1"},
            {"path": "test_output/file2.txt", "content": "Content 2"}
        ],
        "modifications": [
            {"file": "test_output/file1.txt", "new_content": "Updated Content 1"}
        ],
        "files_to_delete": ["test_output/file2.txt"]
    },
    success_criteria=[
        {
            "name": "all_files_created",
            "description": "All specified files should be created",
            "check": lambda state: all(state.get("created_files", {}).values())
        },
        {
            "name": "modifications_applied",
            "description": "All modifications should be applied correctly",
            "check": lambda state: state.get("modifications_successful", False)
        },
        {
            "name": "deletions_successful",
            "description": "All specified files should be deleted",
            "check": lambda state: all(not state.get("file_exists", {}).get(f, True) 
                                     for f in state.get("files_to_delete", []))
        }
    ]
)

# Test Case 3: API Interaction
API_TEST = TestCase(
    task_id="api_interaction",
    description="Interact with a test API endpoint and process the response",
    initial_state={
        "api_url": "https://jsonplaceholder.typicode.com/posts",
        "expected_status": 200,
        "expected_fields": ["id", "title", "body"]
    },
    success_criteria=[
        {
            "name": "api_accessible",
            "description": "The API endpoint should be accessible",
            "check": lambda state: state.get("api_status", 0) == state.get("expected_status", 0)
        },
        {
            "name": "response_valid",
            "description": "The response should contain the expected fields",
            "check": lambda state: all(field in state.get("response_fields", [])
                                     for field in state.get("expected_fields", []))
        }
    ]
)

# Test Case 4: Error Recovery
ERROR_RECOVERY_TEST = TestCase(
    task_id="error_recovery",
    description="Handle and recover from various error conditions",
    initial_state={
        "operations": [
            {"type": "file_write", "path": "test_output/nonexistent_dir/file.txt", "content": "test"},
            {"type": "file_read", "path": "test_output/nonexistent_file.txt"},
            {"type": "api_call", "url": "https://invalid-url.example.com"}
        ]
    },
    success_criteria=[
        {
            "name": "errors_handled",
            "description": "All errors should be properly handled",
            "check": lambda state: all(state.get("error_handling", {}).values())
        },
        {
            "name": "recovery_successful",
            "description": "System should recover and continue operation",
            "check": lambda state: state.get("recovery_successful", False)
        }
    ]
)

# Test Case 5: Complex Problem Solving
COMPLEX_PROBLEM_TEST = TestCase(
    task_id="complex_problem",
    description="Solve a complex problem requiring multiple steps and error handling",
    initial_state={
        "problem": {
            "type": "data_processing",
            "input_files": ["test_output/input1.txt", "test_output/input2.txt"],
            "transformations": [
                {"type": "filter", "condition": "value > 0"},
                {"type": "sort", "key": "timestamp"},
                {"type": "aggregate", "operation": "sum"}
            ],
            "output_format": "json"
        }
    },
    success_criteria=[
        {
            "name": "all_steps_completed",
            "description": "All processing steps should be completed",
            "check": lambda state: all(state.get("step_completion", {}).values())
        },
        {
            "name": "output_valid",
            "description": "Output should be in the correct format",
            "check": lambda state: state.get("output_format_valid", False)
        },
        {
            "name": "data_integrity",
            "description": "Data integrity should be maintained throughout processing",
            "check": lambda state: state.get("data_integrity_maintained", False)
        }
    ]
)

# List of all test cases
TEST_CASES = [
    FILE_CREATION_TEST,
    FILE_OPERATIONS_TEST,
    API_TEST,
    ERROR_RECOVERY_TEST,
    COMPLEX_PROBLEM_TEST
] 