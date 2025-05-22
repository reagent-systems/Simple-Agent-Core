"""GitHub fork and clone command for SimpleAgent.

This module provides functionality to fork a GitHub repository under your account,
clone it locally, and set up the remote to target the original repository for PRs.
"""

import os
import subprocess
from typing import Dict, Any, Optional, List
from github import Github, GithubException
import re
from commands import register_command

def github_fork_clone(
    repo_url: str,
    target_dir: str = "",
    description: str = "",
    branch: str = ""
) -> Dict[str, Any]:
    """Fork a GitHub repository, clone it locally, and set up remotes to target the original repo.
    
    Args:
        repo_url: The URL of the GitHub repository to fork (e.g., 'https://github.com/owner/repo')
        target_dir: Optional target directory for cloning (defaults to repo name)
        description: Optional description for the forked repository
        branch: Optional branch to checkout after cloning
        
    Returns:
        Dictionary containing the operation result information
    """
    g = None
    try:
        # Check for GitHub token
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return {
                "success": False,
                "error": "GitHub token not found. Please set GITHUB_TOKEN environment variable."
            }
            
        # Initialize GitHub client
        g = Github(token)
        
        # Extract owner and repo from URL
        parts = extract_repo_parts(repo_url)
        if not parts:
            return {
                "success": False,
                "error": f"Invalid GitHub repository URL: {repo_url}",
                "message": "URL must be in format: https://github.com/owner/repo"
            }
            
        owner, repo_name = parts
        
        try:
            # Get the repository to fork
            source_repo = g.get_repo(f"{owner}/{repo_name}")
            
            # Fork the repository
            fork = source_repo.create_fork()
            
            # Update description if provided
            if description:
                fork.edit(description=description)
                
            # Get the clone URL
            clone_url = fork.clone_url
            
            # If target_dir is not specified, use the repo name
            if not target_dir:
                target_dir = repo_name
                
            # Clone the forked repository
            current_dir = os.path.abspath(os.getcwd())
            target_path = os.path.join(current_dir, target_dir)
            
            # Clone the fork
            clone_cmd = ["git", "clone", clone_url]
            if target_dir:
                clone_cmd.append(target_dir)
                
            process = subprocess.run(
                clone_cmd,
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
                    "fork_url": fork.html_url
                }
                
            # Set up the upstream remote to point to the original repository
            upstream_cmd = [
                "git", 
                "-C", 
                target_path, 
                "remote", 
                "add", 
                "upstream", 
                source_repo.clone_url
            ]
            
            upstream_process = subprocess.run(
                upstream_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            if upstream_process.returncode != 0:
                return {
                    "success": True,
                    "warning": "Repository forked and cloned, but failed to set upstream remote",
                    "fork_url": fork.html_url,
                    "upstream_error": upstream_process.stderr,
                    "repo_path": target_path
                }
                
            # Checkout specific branch if specified
            if branch:
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
                        "warning": f"Repository forked and cloned, but failed to checkout branch '{branch}'",
                        "fork_url": fork.html_url,
                        "checkout_error": checkout_process.stderr,
                        "repo_path": target_path
                    }
            
            # Get repository info - list files in root directory
            files = []
            if os.path.exists(target_path):
                files = os.listdir(target_path)
                
            return {
                "success": True,
                "message": "Repository forked and cloned successfully",
                "fork_url": fork.html_url,
                "original_url": source_repo.html_url,
                "clone_path": target_path,
                "origin_remote": fork.clone_url,
                "upstream_remote": source_repo.clone_url,
                "branch": branch if branch else source_repo.default_branch,
                "files": files
            }
                
        except GithubException as e:
            error_detail = f"Status {e.status}: {e.data.get('message', str(e))}" if hasattr(e, 'status') and hasattr(e, 'data') else str(e)
            return {
                "success": False,
                "error": f"GitHub API Error: {error_detail}",
                "repo_url": repo_url
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to fork and clone repository: {str(e)}",
            "repo_url": repo_url
        }
    finally:
        if g is not None:
            g.close()


def extract_repo_parts(repo_url: str) -> Optional[tuple]:
    """Extract owner and repository name from a GitHub URL.
    
    Args:
        repo_url: The GitHub repository URL
        
    Returns:
        Tuple of (owner, repo_name) or None if invalid URL
    """
    # Handle different URL formats
    # https://github.com/owner/repo
    # https://github.com/owner/repo.git
    # git@github.com:owner/repo.git
    
    # For HTTPS URLs
    https_match = re.match(r'https?://github\.com/([^/]+)/([^/\.]+)', repo_url)
    if https_match:
        return https_match.groups()
        
    # For SSH URLs
    ssh_match = re.match(r'git@github\.com:([^/]+)/([^/\.]+)', repo_url)
    if ssh_match:
        return ssh_match.groups()
        
    return None


# Schema for the github_fork_clone command
GITHUB_FORK_CLONE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "github_fork_clone",
        "description": "Fork a GitHub repository, clone it locally, and set up remotes to target the original repo for PRs",
        "parameters": {
            "type": "object",
            "properties": {
                "repo_url": {
                    "type": "string",
                    "description": "The URL of the GitHub repository to fork (e.g., 'https://github.com/owner/repo')"
                },
                "target_dir": {
                    "type": "string",
                    "description": "Optional target directory for cloning (defaults to repo name)",
                    "default": ""
                },
                "description": {
                    "type": "string",
                    "description": "Optional description for the forked repository",
                    "default": ""
                },
                "branch": {
                    "type": "string",
                    "description": "Optional branch to checkout after cloning",
                    "default": ""
                }
            },
            "required": ["repo_url"]
        }
    }
}

# Register the command
register_command("github_fork_clone", github_fork_clone, GITHUB_FORK_CLONE_SCHEMA) 