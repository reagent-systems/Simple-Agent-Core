"""
Tests for web operation commands.

This module contains benchmark tests for all web operation commands.
Note that these tests use mocked HTTP responses to avoid real network requests.
"""

import os
import json
import unittest.mock as mock
from typing import Tuple, Dict, Any

from benchmark.test_framework import TEST_OUTPUT_DIR
import requests

# Import web operation functions
try:
    from commands.web_ops.web_search import web_search
    from commands.web_ops.web_scrape import web_scrape
    from commands.web_ops.fetch_json_api import fetch_json_api
    from commands.web_ops.raw_web_read import raw_web_read
    from commands.web_ops.extract_links import extract_links
    
    # Flag to track if imports succeeded
    WEB_OPS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import web_ops modules: {e}")
    WEB_OPS_AVAILABLE = False

# Test URLs
TEST_URL = "https://example.com"
TEST_API_URL = "https://api.example.com/data"
TEST_SEARCH_QUERY = "test query"
TEST_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
</head>
<body>
    <h1>Test Page Header</h1>
    <p>This is a test paragraph.</p>
    <a href="https://example.com/link1">Link 1</a>
    <a href="https://example.com/link2">Link 2</a>
    <a href="https://example.com/link3">Link 3</a>
</body>
</html>
"""

TEST_JSON_RESPONSE = {
    "status": "success",
    "data": {
        "items": [1, 2, 3, 4, 5],
        "meta": {
            "total": 5,
            "page": 1
        }
    }
}

def mock_response(content=None, json_data=None, status_code=200, url=TEST_URL):
    """Create a mock requests.Response object."""
    mock_resp = mock.Mock()
    mock_resp.status_code = status_code
    mock_resp.url = url
    
    # Set content or json response
    if content is not None:
        mock_resp.text = content
        mock_resp.content = content.encode('utf-8')
    
    if json_data is not None:
        mock_resp.json = mock.Mock(return_value=json_data)
    
    return mock_resp

def test_web_search() -> Tuple[bool, str]:
    """Test the web_search command."""
    if not WEB_OPS_AVAILABLE:
        return False, "web_ops modules not available"
    
    try:
        # Mock the requests.get function to avoid actual web requests
        with mock.patch('requests.get') as mock_get:
            # Set up the mock response
            mock_resp = mock_response(
                content='{"results": [{"title": "Test Result", "url": "https://example.com"}]}',
                json_data={"results": [{"title": "Test Result", "url": "https://example.com"}]}
            )
            mock_get.return_value = mock_resp
            
            # Call the function with the test query
            result = web_search(TEST_SEARCH_QUERY)
            
            # Verify mock was called with the correct URL
            mock_get.assert_called_once()
            
            # Check that the result is not empty
            if not result or not isinstance(result, list):
                return False, f"Expected list of results, got: {result}"
                
            return True, "Web search test passed"
            
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_web_scrape() -> Tuple[bool, str]:
    """Test the web_scrape command."""
    if not WEB_OPS_AVAILABLE:
        return False, "web_ops modules not available"
    
    try:
        # Mock the requests.get function
        with mock.patch('requests.get') as mock_get:
            # Set up the mock response
            mock_resp = mock_response(content=TEST_HTML)
            mock_get.return_value = mock_resp
            
            # Call the function
            result = web_scrape(TEST_URL)
            
            # Verify mock was called with the correct URL
            mock_get.assert_called_once_with(
                TEST_URL,
                headers=mock.ANY,
                timeout=mock.ANY
            )
            
            # Check that the result contains expected content
            if not result or "Test Page Header" not in result:
                return False, f"Expected HTML content with 'Test Page Header', got: {result[:100]}..."
                
            return True, "Web scrape test passed"
            
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_fetch_json_api() -> Tuple[bool, str]:
    """Test the fetch_json_api command."""
    if not WEB_OPS_AVAILABLE:
        return False, "web_ops modules not available"
    
    try:
        # Mock the requests.get function
        with mock.patch('requests.get') as mock_get:
            # Set up the mock response
            mock_resp = mock_response(json_data=TEST_JSON_RESPONSE)
            mock_get.return_value = mock_resp
            
            # Call the function
            result = fetch_json_api(TEST_API_URL)
            
            # Verify mock was called with the correct URL
            mock_get.assert_called_once_with(
                TEST_API_URL,
                headers=mock.ANY,
                timeout=mock.ANY
            )
            
            # Check that the result contains expected JSON
            if not result or result.get('status') != 'success':
                return False, f"Expected JSON with status 'success', got: {result}"
                
            return True, "JSON API fetch test passed"
            
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_raw_web_read() -> Tuple[bool, str]:
    """Test the raw_web_read command."""
    if not WEB_OPS_AVAILABLE:
        return False, "web_ops modules not available"
    
    try:
        # Mock the requests.get function
        with mock.patch('requests.get') as mock_get:
            # Set up the mock response
            mock_resp = mock_response(content=TEST_HTML)
            mock_get.return_value = mock_resp
            
            # Call the function
            result = raw_web_read(TEST_URL)
            
            # Verify mock was called with the correct URL
            mock_get.assert_called_once_with(
                TEST_URL,
                headers=mock.ANY,
                timeout=mock.ANY
            )
            
            # Check that the result contains the raw HTML
            if not result or "<!DOCTYPE html>" not in result:
                return False, f"Expected raw HTML with DOCTYPE, got: {result[:100]}..."
                
            return True, "Raw web read test passed"
            
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_extract_links() -> Tuple[bool, str]:
    """Test the extract_links command."""
    if not WEB_OPS_AVAILABLE:
        return False, "web_ops modules not available"
    
    try:
        # Mock the requests.get function
        with mock.patch('requests.get') as mock_get:
            # Set up the mock response
            mock_resp = mock_response(content=TEST_HTML)
            mock_get.return_value = mock_resp
            
            # Call the function
            result = extract_links(TEST_URL)
            
            # Verify mock was called
            mock_get.assert_called_once()
            
            # Check that the result contains the expected links
            expected_links = [
                "https://example.com/link1",
                "https://example.com/link2",
                "https://example.com/link3"
            ]
            
            if not result or not isinstance(result, list):
                return False, f"Expected list of links, got: {result}"
                
            # Check if expected links are in the result
            missing_links = [link for link in expected_links if link not in result]
            if missing_links:
                return False, f"Missing expected links: {missing_links}, got: {result}"
                
            return True, "Link extraction test passed"
            
    except Exception as e:
        return False, f"Exception: {str(e)}" 