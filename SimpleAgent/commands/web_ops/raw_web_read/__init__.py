"""Raw web read command for SimpleAgent.

This module provides the raw_web_read command for fetching the raw content of a webpage.
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Any
from commands import register_command
from ..user_agents import user_agent_manager


def raw_web_read(url: str, include_html: bool = False, max_length: int = 50000) -> Dict[str, Any]:
    """
    Fetch the raw content of a webpage with minimal processing.
    
    Args:
        url: The URL to read
        include_html: Whether to include the raw HTML in the response (default: False)
        max_length: Maximum length of text content to return (default: 50000)
        
    Returns:
        Dictionary containing the raw webpage content
    """
    try:
        # Get random headers for this request
        headers = user_agent_manager.get_headers()
        
        # Fetch the page
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse the content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Initialize result dictionary
        result = {
            "url": url,
            "title": soup.title.string if soup.title else None,
            "status_code": response.status_code,
            "content_type": response.headers.get('Content-Type', 'unknown')
        }
        
        # Extract all text content
        # Remove script, style, and other non-content elements
        for script in soup(["script", "style", "meta", "noscript", "svg"]):
            script.decompose()
            
        # Get the text content
        text_content = soup.get_text(separator="\n", strip=True)
        
        # Truncate if needed
        if len(text_content) > max_length:
            text_content = text_content[:max_length] + "... (content truncated)"
            result["truncated"] = True
        else:
            result["truncated"] = False
            
        result["text_content"] = text_content
        result["content_length"] = len(text_content)
        
        # Include raw HTML if requested
        if include_html:
            html_content = response.text
            if len(html_content) > max_length:
                html_content = html_content[:max_length] + "... (HTML truncated)"
                result["html_truncated"] = True
            else:
                result["html_truncated"] = False
                
            result["html_content"] = html_content
        
        return result
        
    except Exception as e:
        return {
            "error": f"Failed to read webpage: {str(e)}",
            "url": url
        }


# Define the schema for the raw_web_read command
RAW_WEB_READ_SCHEMA = {
    "type": "function",
    "function": {
        "name": "raw_web_read",
        "description": "Fetch the raw content of a webpage with minimal processing",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to read"
                },
                "include_html": {
                    "type": "boolean",
                    "description": "Whether to include the raw HTML in the response (default: false)",
                    "default": False
                },
                "max_length": {
                    "type": "integer",
                    "description": "Maximum length of text content to return (default: 50000)",
                    "default": 50000
                }
            },
            "required": ["url"]
        }
    }
}

# Register the command
register_command("raw_web_read", raw_web_read, RAW_WEB_READ_SCHEMA) 