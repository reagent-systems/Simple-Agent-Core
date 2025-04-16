"""Fetch JSON API command for SimpleAgent.

This module provides the fetch_json_api command for retrieving JSON data from APIs.
"""

import json
import requests
from typing import Dict, Any, Optional, Union, List
from commands import register_command
from ..user_agents import user_agent_manager


def fetch_json_api(
    url: str, 
    method: str = "GET", 
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    auth_type: Optional[str] = None,
    auth_token: Optional[str] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Fetch JSON data from an API endpoint.
    
    Args:
        url: The API endpoint URL
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        params: Query parameters for the request
        headers: Custom headers for the request
        data: Data to send in the request body (for POST, PUT, etc.)
        auth_type: Authentication type (basic, bearer, api_key)
        auth_token: Authentication token or API key
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary containing the API response
    """
    try:
        # Set up default headers with user agent
        request_headers = user_agent_manager.get_headers()
        request_headers["Accept"] = "application/json"
        
        # Add custom headers if provided
        if headers:
            request_headers.update(headers)
            
        # Handle authentication
        if auth_type and auth_token:
            if auth_type.lower() == "bearer":
                request_headers["Authorization"] = f"Bearer {auth_token}"
            elif auth_type.lower() == "basic":
                request_headers["Authorization"] = f"Basic {auth_token}"
            elif auth_type.lower() == "api_key":
                # Default to using auth_token as an API key in header
                # If the API requires it as a param, use the params argument instead
                request_headers["X-API-Key"] = auth_token
                
        # Prepare request arguments
        request_args = {
            "url": url,
            "headers": request_headers,
            "timeout": timeout
        }
        
        # Add query parameters if provided
        if params:
            request_args["params"] = params
            
        # Add request body if provided for appropriate methods
        if data and method.upper() in ["POST", "PUT", "PATCH"]:
            # Check if data should be JSON or form data
            if isinstance(data, dict):
                if request_headers.get("Content-Type") == "application/x-www-form-urlencoded":
                    request_args["data"] = data
                else:
                    request_args["json"] = data
            else:
                request_args["data"] = data
        
        # Make the request
        response = requests.request(method.upper(), **request_args)
        
        # Attempt to parse JSON response
        try:
            json_response = response.json()
        except json.JSONDecodeError:
            # Return text response if not JSON
            return {
                "success": response.ok,
                "status_code": response.status_code,
                "url": url,
                "method": method.upper(),
                "is_json": False,
                "text_content": response.text[:10000] if len(response.text) > 10000 else response.text,
                "headers": dict(response.headers)
            }
        
        # Return successful JSON response
        result = {
            "success": response.ok,
            "status_code": response.status_code,
            "url": url,
            "method": method.upper(),
            "is_json": True,
            "data": json_response,
            "headers": dict(response.headers)
        }
        
        return result
        
    except requests.exceptions.Timeout:
        return {
            "error": "Request timed out",
            "success": False,
            "url": url,
            "method": method.upper()
        }
    except requests.exceptions.ConnectionError:
        return {
            "error": "Connection error - could not connect to the API",
            "success": False,
            "url": url,
            "method": method.upper()
        }
    except Exception as e:
        return {
            "error": f"Failed to fetch API data: {str(e)}",
            "success": False,
            "url": url,
            "method": method.upper()
        }


# Define the schema for the fetch_json_api command
FETCH_JSON_API_SCHEMA = {
    "type": "function",
    "function": {
        "name": "fetch_json_api",
        "description": "Fetch JSON data from an API endpoint with various options",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The API endpoint URL"
                },
                "method": {
                    "type": "string",
                    "description": "HTTP method (GET, POST, PUT, DELETE, etc.)",
                    "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"],
                    "default": "GET"
                },
                "params": {
                    "type": "object",
                    "description": "Query parameters for the request",
                    "additionalProperties": {"type": "string"}
                },
                "headers": {
                    "type": "object",
                    "description": "Custom headers for the request",
                    "additionalProperties": {"type": "string"}
                },
                "data": {
                    "type": "object",
                    "description": "Data to send in the request body (for POST, PUT, etc.)",
                    "additionalProperties": {"type": "string"}
                },
                "auth_type": {
                    "type": "string",
                    "description": "Authentication type (basic, bearer, api_key)",
                    "enum": ["basic", "bearer", "api_key"]
                },
                "auth_token": {
                    "type": "string",
                    "description": "Authentication token or API key"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds",
                    "default": 30
                }
            },
            "required": ["url"]
        }
    }
}

# Register the command
register_command("fetch_json_api", fetch_json_api, FETCH_JSON_API_SCHEMA) 