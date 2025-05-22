"""
Browse web command for SimpleAgent.

This module provides the browse_web command for interactive web browsing using lynx.
"""

import subprocess
import shlex
from typing import Dict, Any
from commands import register_command


def browse_web(url: str) -> Dict[str, Any]:
    """
    Launch an interactive lynx browser session to browse a webpage.
    
    Args:
        url: The URL to browse
        
    Returns:
        Dictionary indicating success or failure
    """
    try:
        # Check if lynx is available
        which_process = subprocess.run(["which", "lynx"], capture_output=True, text=True)
        if which_process.returncode != 0:
            return {
                "success": False,
                "error": "Lynx browser is not installed. Please install lynx using 'sudo apt-get install lynx'."
            }
        
        # Print instructions for the user
        print("\n=== Lynx Browser Instructions ===")
        print("Arrow keys: Navigate")
        print("Enter: Follow link")
        print("q: Quit browser")
        print("g: Go to URL")
        print("h: Help")
        print("================================\n")
        
        # Launch lynx in interactive mode
        print(f"Opening {url} in lynx browser...")
        
        # We use subprocess.call to allow direct terminal interaction
        subprocess.call(["lynx", url])
        
        return {
            "success": True,
            "message": "Lynx browser session completed."
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to launch lynx browser: {str(e)}"
        }


# Define the schema for the browse_web command
BROWSE_WEB_SCHEMA = {
    "type": "function",
    "function": {
        "name": "browse_web",
        "description": "Launch an interactive lynx browser session to browse a webpage",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to browse"
                }
            },
            "required": ["url"]
        }
    }
}

# Register the command
register_command("browse_web", browse_web, BROWSE_WEB_SCHEMA) 