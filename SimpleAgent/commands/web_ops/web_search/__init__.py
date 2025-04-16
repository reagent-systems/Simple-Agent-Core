"""
Web search command for SimpleAgent.

This module provides the web_search command for searching the web and retrieving information.
"""

import json
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