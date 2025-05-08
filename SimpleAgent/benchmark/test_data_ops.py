"""
Tests for data operation commands.

This module contains benchmark tests for all data operation commands.
"""

import os
from typing import Tuple, Dict, Any

from benchmark.test_framework import TEST_OUTPUT_DIR

# Import data operation functions
try:
    from commands.data_ops.text_analysis import text_analysis
    
    # Flag to track if imports succeeded
    DATA_OPS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import data_ops modules: {e}")
    DATA_OPS_AVAILABLE = False

# Test data
TEST_TEXT = """
SimpleAgent is a minimalist AI agent framework. It can help you perform various 
tasks through function calling. The agent uses the OpenAI API to generate responses 
and execute functions based on user instructions.

Key features include:
1. File operations for reading, writing, and editing files
2. Web operations for searching, scraping, and API requests
3. GitHub operations for repo and issue management
4. Data analysis for text processing
"""

def test_text_analysis() -> Tuple[bool, str]:
    """Test the text_analysis command."""
    if not DATA_OPS_AVAILABLE:
        return False, "data_ops modules not available"
    
    try:
        # Call the text_analysis function
        result = text_analysis(TEST_TEXT)
        
        # Verify result structure
        if not isinstance(result, dict):
            return False, f"Expected dictionary result, got: {type(result)}"
        
        # Check for expected keys
        expected_keys = ["summary", "entities", "keywords", "sentiment"]
        for key in expected_keys:
            if key not in result:
                return False, f"Missing expected key '{key}' in result: {result.keys()}"
        
        # Check that summary is not empty
        if not result["summary"] or len(result["summary"]) < 10:
            return False, f"Expected non-empty summary, got: {result['summary']}"
        
        # Check that keywords are a list
        if not isinstance(result["keywords"], list) or not result["keywords"]:
            return False, f"Expected non-empty keywords list, got: {result['keywords']}"
        
        return True, "Text analysis test passed"
    
    except Exception as e:
        return False, f"Exception: {str(e)}" 