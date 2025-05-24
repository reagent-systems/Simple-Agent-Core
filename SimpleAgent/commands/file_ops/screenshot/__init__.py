"""
Screenshot command for SimpleAgent.

This module provides the take_screenshot command for capturing a screenshot and saving it to the output directory.
"""

import os
import pyautogui
from commands import register_command
from core.security import get_secure_path
from core.config import OUTPUT_DIR

def take_screenshot(filename: str = "screenshot.png") -> str:
    """
    Take a screenshot and save it to the output directory.
    Args:
        filename: The name of the screenshot file (default: screenshot.png)
    Returns:
        The path to the saved screenshot or an error message
    """
    try:
        secure_path = get_secure_path(filename, OUTPUT_DIR)
        os.makedirs(os.path.dirname(secure_path), exist_ok=True)  # Ensure directory exists
        screenshot = pyautogui.screenshot()
        screenshot.save(secure_path)
        return f"Screenshot saved to {secure_path}"
    except Exception as e:
        return f"Error taking screenshot: {str(e)}"

TAKE_SCREENSHOT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "take_screenshot",
        "description": "Take a screenshot and save it to the output directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The name of the screenshot file (default: screenshot.png)"
                }
            },
            "required": []
        }
    }
}

register_command("take_screenshot", take_screenshot, TAKE_SCREENSHOT_SCHEMA) 