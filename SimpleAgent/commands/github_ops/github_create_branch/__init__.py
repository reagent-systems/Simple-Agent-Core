"""GitHub branch creation command for SimpleAgent.

This module provides functionality to create new branches in GitHub repositories using PyGithub.
"""

from typing import Dict, Any, Optional
from github import Github, GithubException
import os
from commands import register_command

def github_create_branch(
    repo_url: str,
    branch_name: str,
    base_branch: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new branch in a GitHub repository.
    
    Args:
        repo_url: The URL of the GitHub repository
        branch_name: The name of the new branch
        base_branch: The name of the branch to base from (defaults to repository's default branch)
        
    Returns:
        Dictionary containing the created branch information
    """
    try:
        # Initialize GitHub client with token if available
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return {
                "error": "GitHub token not found. Please set GITHUB_TOKEN environment variable.",
                "url": repo_url
            }
            
        g = Github(token)
        
        # Extract owner and repo from URL
        parts = repo_url.rstrip('/').split('/')
        owner = parts[-2]
        repo_name = parts[-1]
        
        # Get repository
        repo = g.get_repo(f"{owner}/{repo_name}")
        
        # Get the base branch to create from
        if not base_branch:
            base_branch = repo.default_branch
            
        # Get the latest commit of the base branch
        base_ref = repo.get_git_ref(f"heads/{base_branch}")
        
        try:
            # Create the new branch
            repo.create_git_ref(f"refs/heads/{branch_name}", base_ref.object.sha)
            
            return {
                "success": True,
                "branch_name": branch_name,
                "base_branch": base_branch,
                "sha": base_ref.object.sha,
                "repo_url": repo_url
            }
                
        except GithubException as e:
            return {
                "error": f"Failed to create branch: {str(e)}",
                "branch_name": branch_name,
                "base_branch": base_branch,
                "repo_url": repo_url
            }
            
    except GithubException as e:
        return {
            "error": f"GitHub API error: {str(e)}",
            "url": repo_url
        }
    except Exception as e:
        return {
            "error": f"Failed to create branch: {str(e)}",
            "url": repo_url
        }
    finally:
        if 'g' in locals():
            g.close()

# Schema for the github_create_branch command
GITHUB_CREATE_BRANCH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "github_create_branch",
        "description": "Create a new branch in a GitHub repository",
        "parameters": {
            "type": "object",
            "properties": {
                "repo_url": {
                    "type": "string",
                    "description": "The URL of the GitHub repository"
                },
                "branch_name": {
                    "type": "string",
                    "description": "The name of the new branch"
                },
                "base_branch": {
                    "type": "string",
                    "description": "The name of the branch to base from (defaults to repository's default branch)",
                    "default": None
                }
            },
            "required": ["repo_url", "branch_name"]
        }
    }
}

register_command("github_create_branch", github_create_branch, GITHUB_CREATE_BRANCH_SCHEMA) 