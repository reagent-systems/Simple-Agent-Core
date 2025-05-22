"""
Tests for GitHub operation commands.

This module contains benchmark tests for all GitHub operation commands.
Tests use mocked GitHub API responses to avoid real API calls.
"""

import os
import json
import unittest.mock as mock
from typing import Tuple, Dict, Any

from benchmark.test_framework import TEST_OUTPUT_DIR

# Import GitHub operation functions
try:
    from commands.github_ops.repo_reader import repo_reader
    from commands.github_ops.issue_reader import issue_reader
    from commands.github_ops.pr_reader import pr_reader
    from commands.github_ops.github_create_issue import github_create_issue
    from commands.github_ops.github_create_pr import github_create_pr
    from commands.github_ops.github_comment import github_comment
    from commands.github_ops.github_create_repo import github_create_repo
    from commands.github_ops.github_read_files import github_read_files
    
    # Flag to track if imports succeeded
    GITHUB_OPS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import github_ops modules: {e}")
    GITHUB_OPS_AVAILABLE = False

# Test data
TEST_REPO = "example/repo"
TEST_ISSUE_NUMBER = 42
TEST_PR_NUMBER = 123
TEST_COMMENT = "This is a test comment."
TEST_REPO_DATA = {
    "name": "repo",
    "full_name": "example/repo",
    "description": "Test repository",
    "html_url": "https://github.com/example/repo",
    "owner": {
        "login": "example"
    },
    "default_branch": "main"
}
TEST_ISSUE_DATA = {
    "number": TEST_ISSUE_NUMBER,
    "title": "Test Issue",
    "body": "This is a test issue body.",
    "html_url": f"https://github.com/example/repo/issues/{TEST_ISSUE_NUMBER}",
    "user": {
        "login": "testuser"
    },
    "state": "open",
    "created_at": "2023-01-01T00:00:00Z",
    "comments": 5
}
TEST_PR_DATA = {
    "number": TEST_PR_NUMBER,
    "title": "Test PR",
    "body": "This is a test PR body.",
    "html_url": f"https://github.com/example/repo/pull/{TEST_PR_NUMBER}",
    "user": {
        "login": "testuser"
    },
    "state": "open",
    "created_at": "2023-01-01T00:00:00Z",
    "comments": 3,
    "merged": False
}
TEST_ISSUES_LIST = [TEST_ISSUE_DATA]
TEST_PR_LIST = [TEST_PR_DATA]
TEST_FILE_CONTENT = "This is the content of a mock GitHub file."

# Mock GitHub methods
def mock_github_repo():
    """Create a mock GitHub Repository object."""
    mock_repo = mock.Mock()
    mock_repo.name = TEST_REPO_DATA["name"]
    mock_repo.full_name = TEST_REPO_DATA["full_name"]
    mock_repo.description = TEST_REPO_DATA["description"]
    mock_repo.html_url = TEST_REPO_DATA["html_url"]
    mock_repo.owner.login = TEST_REPO_DATA["owner"]["login"]
    mock_repo.default_branch = TEST_REPO_DATA["default_branch"]
    
    # Mock get_issues method
    mock_issues = []
    for issue_data in TEST_ISSUES_LIST:
        mock_issue = mock.Mock()
        for key, value in issue_data.items():
            setattr(mock_issue, key, value)
        mock_issues.append(mock_issue)
    mock_repo.get_issues.return_value = mock_issues
    
    # Mock get_pulls method
    mock_prs = []
    for pr_data in TEST_PR_LIST:
        mock_pr = mock.Mock()
        for key, value in pr_data.items():
            setattr(mock_pr, key, value)
        mock_prs.append(mock_pr)
    mock_repo.get_pulls.return_value = mock_prs
    
    # Mock get_issue method
    mock_issue = mock.Mock()
    for key, value in TEST_ISSUE_DATA.items():
        setattr(mock_issue, key, value)
    mock_repo.get_issue.return_value = mock_issue
    
    # Mock create_issue method
    mock_repo.create_issue.return_value = mock_issue
    
    # Mock get_pull method
    mock_pr = mock.Mock()
    for key, value in TEST_PR_DATA.items():
        setattr(mock_pr, key, value)
    mock_repo.get_pull.return_value = mock_pr
    
    # Mock get_contents method
    mock_content = mock.Mock()
    mock_content.decoded_content.decode.return_value = TEST_FILE_CONTENT
    mock_repo.get_contents.return_value = mock_content
    
    return mock_repo

def test_repo_reader() -> Tuple[bool, str]:
    """Test the repo_reader command."""
    if not GITHUB_OPS_AVAILABLE:
        return False, "github_ops modules not available"
    
    try:
        # Mock the GitHub client
        with mock.patch('github.Github') as mock_github:
            # Set up the mock repository
            mock_github.return_value.get_repo.return_value = mock_github_repo()
            
            # Call the function
            result = repo_reader(TEST_REPO)
            
            # Verify mocks were called
            mock_github.return_value.get_repo.assert_called_once_with(TEST_REPO)
            
            # Check that the result contains expected info
            if not result or not isinstance(result, dict):
                return False, f"Expected dict result, got: {result}"
                
            if "repo" not in result or "issues" not in result or "pulls" not in result:
                return False, f"Missing expected keys in result: {result.keys()}"
                
            return True, "Repo reader test passed"
            
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_issue_reader() -> Tuple[bool, str]:
    """Test the issue_reader command."""
    if not GITHUB_OPS_AVAILABLE:
        return False, "github_ops modules not available"
    
    try:
        # Mock the GitHub client
        with mock.patch('github.Github') as mock_github:
            # Set up the mock repository
            mock_github.return_value.get_repo.return_value = mock_github_repo()
            
            # Call the function
            result = issue_reader(TEST_REPO, TEST_ISSUE_NUMBER)
            
            # Verify mocks were called
            mock_github.return_value.get_repo.assert_called_once_with(TEST_REPO)
            
            # Check that the result contains expected info
            if not result or not isinstance(result, dict):
                return False, f"Expected dict result, got: {result}"
                
            if "title" not in result or "body" not in result:
                return False, f"Missing expected keys in result: {result.keys()}"
                
            return True, "Issue reader test passed"
            
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_pr_reader() -> Tuple[bool, str]:
    """Test the pr_reader command."""
    if not GITHUB_OPS_AVAILABLE:
        return False, "github_ops modules not available"
    
    try:
        # Mock the GitHub client
        with mock.patch('github.Github') as mock_github:
            # Set up the mock repository
            mock_github.return_value.get_repo.return_value = mock_github_repo()
            
            # Call the function
            result = pr_reader(TEST_REPO, TEST_PR_NUMBER)
            
            # Verify mocks were called
            mock_github.return_value.get_repo.assert_called_once_with(TEST_REPO)
            
            # Check that the result contains expected info
            if not result or not isinstance(result, dict):
                return False, f"Expected dict result, got: {result}"
                
            if "title" not in result or "body" not in result:
                return False, f"Missing expected keys in result: {result.keys()}"
                
            return True, "PR reader test passed"
            
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_github_create_issue() -> Tuple[bool, str]:
    """Test the github_create_issue command."""
    if not GITHUB_OPS_AVAILABLE:
        return False, "github_ops modules not available"
    
    try:
        # Mock the GitHub client
        with mock.patch('github.Github') as mock_github:
            # Set up the mock repository
            mock_repo = mock_github_repo()
            mock_github.return_value.get_repo.return_value = mock_repo
            
            # Call the function
            result = github_create_issue(TEST_REPO, "Test Issue Title", "Test issue body")
            
            # Verify mocks were called
            mock_github.return_value.get_repo.assert_called_once_with(TEST_REPO)
            mock_repo.create_issue.assert_called_once_with(
                title="Test Issue Title", 
                body="Test issue body"
            )
            
            # Check that the result contains expected info
            if not result or not isinstance(result, dict):
                return False, f"Expected dict result, got: {result}"
                
            if "url" not in result or "number" not in result:
                return False, f"Missing expected keys in result: {result.keys()}"
                
            return True, "GitHub create issue test passed"
            
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_github_comment() -> Tuple[bool, str]:
    """Test the github_comment command."""
    if not GITHUB_OPS_AVAILABLE:
        return False, "github_ops modules not available"
    
    try:
        # Mock the GitHub client
        with mock.patch('github.Github') as mock_github:
            # Set up the mock repository and issue
            mock_repo = mock_github_repo()
            mock_github.return_value.get_repo.return_value = mock_repo
            mock_issue = mock_repo.get_issue.return_value
            mock_issue.create_comment.return_value = mock.Mock(
                html_url=f"https://github.com/example/repo/issues/{TEST_ISSUE_NUMBER}#comment-1"
            )
            
            # Call the function
            result = github_comment(TEST_REPO, TEST_ISSUE_NUMBER, TEST_COMMENT)
            
            # Verify mocks were called
            mock_github.return_value.get_repo.assert_called_once_with(TEST_REPO)
            mock_repo.get_issue.assert_called_once_with(TEST_ISSUE_NUMBER)
            mock_issue.create_comment.assert_called_once_with(TEST_COMMENT)
            
            # Check that the result contains expected info
            if not result or not isinstance(result, dict):
                return False, f"Expected dict result, got: {result}"
                
            if "url" not in result:
                return False, f"Missing expected key 'url' in result: {result.keys()}"
                
            return True, "GitHub comment test passed"
            
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_github_read_files() -> Tuple[bool, str]:
    """Test the github_read_files command."""
    if not GITHUB_OPS_AVAILABLE:
        return False, "github_ops modules not available"
    
    try:
        # Mock the GitHub client
        with mock.patch('github.Github') as mock_github:
            # Set up the mock repository
            mock_repo = mock_github_repo()
            mock_github.return_value.get_repo.return_value = mock_repo
            
            # Call the function
            result = github_read_files(TEST_REPO, "path/to/file.txt")
            
            # Verify mocks were called
            mock_github.return_value.get_repo.assert_called_once_with(TEST_REPO)
            mock_repo.get_contents.assert_called_once_with("path/to/file.txt")
            
            # Check that the result contains expected content
            if not result or not isinstance(result, str):
                return False, f"Expected string result, got: {type(result)}"
                
            if TEST_FILE_CONTENT not in result:
                return False, f"Expected file content not in result: {result}"
                
            return True, "GitHub read files test passed"
            
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_github_create_repo() -> Tuple[bool, str]:
    """Test the github_create_repo command."""
    if not GITHUB_OPS_AVAILABLE:
        return False, "github_ops modules not available"
    
    try:
        # Mock the GitHub client
        with mock.patch('github.Github') as mock_github:
            # Set up the mock user
            mock_user = mock.Mock()
            mock_user.create_repo.return_value = mock_github_repo()
            mock_github.return_value.get_user.return_value = mock_user
            
            # Call the function
            result = github_create_repo("test-repo", "Test repository description", private=True)
            
            # Verify mocks were called
            mock_github.return_value.get_user.assert_called_once()
            mock_user.create_repo.assert_called_once_with(
                "test-repo", 
                description="Test repository description", 
                private=True
            )
            
            # Check that the result contains expected info
            if not result or not isinstance(result, dict):
                return False, f"Expected dict result, got: {result}"
                
            if "url" not in result or "full_name" not in result:
                return False, f"Missing expected keys in result: {result.keys()}"
                
            return True, "GitHub create repo test passed"
            
    except Exception as e:
        return False, f"Exception: {str(e)}" 