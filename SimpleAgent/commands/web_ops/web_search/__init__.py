"""
Web search command for SimpleAgent.

This module provides the web_search command for searching the web and retrieving information.
"""

import json
import subprocess
import shlex
from typing import List, Dict, Any
from googlesearch import search
import requests
from bs4 import BeautifulSoup
from commands import register_command
from ..user_agents import user_agent_manager


def web_search(query: str, num_results: int = 5, include_snippets: bool = True) -> Dict[str, Any]:
    """
    Search the web for information.
    
    Args:
        query: The search query
        num_results: Number of results to return (default: 5)
        include_snippets: Whether to include text snippets from the pages (default: True)
        
    Returns:
        Dictionary containing search results and snippets
    """
    # Try to use lynx first if available
    try:
        # Check if lynx is available
        which_process = subprocess.run(["which", "lynx"], capture_output=True, text=True)
        lynx_available = which_process.returncode == 0

        if lynx_available:
            return _lynx_web_search(query, num_results, include_snippets)
        else:
            return _default_web_search(query, num_results, include_snippets)
    except Exception as e:
        # If any error occurs with lynx, fall back to default implementation
        print(f"Lynx search failed, falling back to default search: {str(e)}")
        return _default_web_search(query, num_results, include_snippets)


def _lynx_web_search(query: str, num_results: int = 5, include_snippets: bool = True) -> Dict[str, Any]:
    """
    Use lynx to search the web for information.
    
    Args:
        query: The search query
        num_results: Number of results to return
        include_snippets: Whether to include text snippets from the pages
        
    Returns:
        Dictionary containing search results and snippets
    """
    try:
        # Format query for a search engine URL (using DuckDuckGo which is more friendly to text browsers)
        search_url = f"https://lite.duckduckgo.com/lite/?q={query.replace(' ', '+')}"
        
        # Use lynx in dump mode to get the text content of the search results
        # -dump: output the rendered page content to stdout
        # -nolist: don't show the link list at the end
        # -width=800: wider output to avoid line wrapping
        cmd = ["lynx", "-dump", "-nolist", "-width=800", search_url]
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        if process.returncode != 0:
            raise Exception(f"Lynx command failed with code {process.returncode}: {process.stderr}")
        
        # Process the output to extract results
        output = process.stdout
        
        # Split output into lines and look for results
        lines = output.split('\n')
        results = []
        current_result = None
        url = None
        
        # Simple parsing of the DDG Lite output
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Extract links - they appear as numbers in brackets
            if line.startswith('[') and ']' in line and 'http' in line:
                url_part = line.split(']', 1)[1].strip()
                if 'http' in url_part:
                    url = url_part.split(' ', 1)[0].strip()
                    
            # Look for potential result titles (non-empty lines that aren't navigation)
            elif line and not line.startswith('[') and not line.startswith('DuckDuckGo'):
                # This might be a result title or description
                if url and len(line) > 10:  # Ensure it's substantial content
                    # Create a new result
                    current_result = {
                        "url": url,
                        "title": line,
                    }
                    if include_snippets:
                        # For snippet, we'll try to get the next non-empty line
                        current_result["snippet"] = line
                    
                    results.append(current_result)
                    current_result = None
                    url = None
                    
                    # Limit to requested number of results
                    if len(results) >= num_results:
                        break
        
        return {
            "query": query,
            "results": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        return {
            "error": f"Lynx search failed: {str(e)}",
            "query": query,
            "results": []
        }


def _default_web_search(query: str, num_results: int = 5, include_snippets: bool = True) -> Dict[str, Any]:
    """
    Default implementation of web search using googlesearch-python and requests.
    
    Args:
        query: The search query
        num_results: Number of results to return
        include_snippets: Whether to include text snippets from the pages
        
    Returns:
        Dictionary containing search results and snippets
    """
    try:
        # Get random headers for search requests
        headers = user_agent_manager.get_headers()
        
        # Perform the search (note: googlesearch-python doesn't accept user_agent directly)
        search_results = list(search(
            query, 
            num_results=num_results,
            lang="en"
        ))
        
        results = []
        for url in search_results:
            try:
                result = {"url": url}
                
                if include_snippets:
                    # Get new random headers for each page request
                    page_headers = user_agent_manager.get_headers()
                    
                    # Fetch the page content
                    response = requests.get(url, headers=page_headers, timeout=10)
                    response.raise_for_status()
                    
                    # Parse the content
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Get the title
                    title = soup.title.string if soup.title else "No title"
                    result["title"] = title
                    
                    # Get a relevant snippet (first paragraph or similar)
                    paragraphs = soup.find_all('p')
                    if paragraphs:
                        # Get the first non-empty paragraph
                        for p in paragraphs:
                            text = p.get_text().strip()
                            if text and len(text) > 50:  # Ensure it's a meaningful paragraph
                                result["snippet"] = text[:500] + "..." if len(text) > 500 else text
                                break
                
                results.append(result)
                
            except Exception as e:
                # If we can't fetch a particular result, just include the URL
                results.append({
                    "url": url,
                    "error": str(e)
                })
                
        return {
            "query": query,
            "results": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        return {
            "error": f"Search failed: {str(e)}",
            "query": query,
            "results": []
        }


# Define the schema for the web_search command
WEB_SEARCH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for information about a topic",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5)",
                    "default": 5
                },
                "include_snippets": {
                    "type": "boolean",
                    "description": "Whether to include text snippets from the pages (default: true)",
                    "default": True
                }
            },
            "required": ["query"]
        }
    }
}

# Register the command
register_command("web_search", web_search, WEB_SEARCH_SCHEMA) 