"""Git clone command for SimpleAgent.

This module provides functionality to safely clone git repositories into the agent's output directory.
"""

import os
import subprocess
import shutil
import re
from typing import Dict, Any, Union
from commands import register_command
from core.agent import get_secure_path

def git_clone(repo_url: str, target_dir: str = "", branch: str = "") -> Dict[str, Any]:
    """Clone a git repository into the agent's output directory.
    
    Args:
        repo_url: The URL of the git repository to clone (e.g., 'https://github.com/owner/repo')
        target_dir: The target directory name within the output directory (defaults to repo name)
        branch: Optional branch to checkout after cloning
        
    Returns:
        Dictionary containing cloning result information
    """
    try:
        # Validate the git repo URL (basic check for safety)
        if not is_valid_git_url(repo_url):
            return {
                "success": False,
                "error": f"Invalid git repository URL: {repo_url}",
                "message": "URL must be a valid git URL (https://, git://, or ssh://)"
            }
            
        # Get the repository name from URL
        repo_name = get_repo_name_from_url(repo_url)
        
        # If target_dir is not specified, use the repo name
        if not target_dir:
            target_dir = repo_name
            
        # Make sure the target directory is within the output directory
        # This uses the current working directory, which should already be set to output_dir
        # by the agent's run method when commands are executed
        target_path = os.path.abspath(target_dir)
        current_dir = os.path.abspath(os.getcwd())
        
        # Safety check - ensure we're cloning inside our current directory
        if not target_path.startswith(current_dir):
            # Force the target to be within current directory
            target_path = os.path.join(current_dir, target_dir)
            
        # Create a clean target directory
        if os.path.exists(target_path):
            # Only remove if it's within our output directory (extra safety check)
            if target_path.startswith(current_dir):
                # Rename rather than delete for safety
                backup_dir = f"{target_path}_old_{int(os.path.getmtime(target_path))}"
                shutil.move(target_path, backup_dir)
                
        # Prepare command with proper arguments
        git_cmd = ["git", "clone", repo_url]
        
        # Add target directory if specified
        if target_dir:
            git_cmd.append(target_dir)
            
        # Execute git clone command
        process = subprocess.run(
            git_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        if process.returncode != 0:
            return {
                "success": False,
                "error": f"Git clone failed with exit code {process.returncode}",
                "message": process.stderr,
                "command": " ".join(git_cmd)
            }
            
        # Checkout specific branch if specified
        if branch and os.path.exists(target_path):
            checkout_cmd = ["git", "-C", target_path, "checkout", branch]
            checkout_process = subprocess.run(
                checkout_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            if checkout_process.returncode != 0:
                return {
                    "success": True,
                    "warning": f"Repository cloned successfully, but failed to checkout branch '{branch}'",
                    "clone_message": process.stdout,
                    "checkout_error": checkout_process.stderr,
                    "repo_path": target_path,
                    "repo_url": repo_url
                }
        
        # Get repository info - list files in root directory
        files = []
        if os.path.exists(target_path):
            files = os.listdir(target_path)
            
        return {
            "success": True,
            "message": "Repository cloned successfully",
            "output": process.stdout,
            "repo_name": repo_name,
            "repo_path": target_path,
            "repo_url": repo_url,
            "branch": branch if branch else "default",
            "files": files
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to clone repository: {str(e)}",
            "repo_url": repo_url
        }


def is_valid_git_url(url: str) -> bool:
    """Validate if a URL is a valid git repository URL.
    
    Args:
        url: The URL to validate
        
    Returns:
        True if the URL is valid, False otherwise
    """
    # Basic pattern for git URLs (https, git, ssh)
    patterns = [
        r'^https?://[a-zA-Z0-9_.-]+\.[a-zA-Z]{2,}(/[a-zA-Z0-9_./-]+)+$',  # HTTPS URLs
        r'^git@[a-zA-Z0-9_.-]+\.[a-zA-Z]{2,}:[a-zA-Z0-9_.-/]+\.git$',     # SSH URLs
        r'^git://[a-zA-Z0-9_.-]+\.[a-zA-Z]{2,}(/[a-zA-Z0-9_./-]+)+$'      # Git protocol
    ]
    
    return any(re.match(pattern, url) for pattern in patterns)


def get_repo_name_from_url(url: str) -> str:
    """Extract repository name from a git URL.
    
    Args:
        url: The git repository URL
        
    Returns:
        The repository name
    """
    # Remove .git extension if present
    if url.endswith('.git'):
        url = url[:-4]
        
    # Get the last part of the URL (the repo name)
    parts = url.rstrip('/').split('/')
    repo_name = parts[-1] if parts else "repo"
    
    # Clean up the name for use as a directory name
    repo_name = re.sub(r'[^\w\-\.]', '_', repo_name)
    
    return repo_name


# Define the schema for the git_clone command
GIT_CLONE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "git_clone",
        "description": "Clone a git repository into the agent's output directory",
        "parameters": {
            "type": "object",
            "properties": {
                "repo_url": {
                    "type": "string",
                    "description": "The URL of the git repository to clone (e.g., 'https://github.com/owner/repo')"
                },
                "target_dir": {
                    "type": "string",
                    "description": "Optional target directory name within the output directory (defaults to repo name)"
                },
                "branch": {
                    "type": "string",
                    "description": "Optional branch name to checkout after cloning"
                }
            },
            "required": ["repo_url"]
        }
    }
}

# Register the command
register_command("git_clone", git_clone, GIT_CLONE_SCHEMA) 