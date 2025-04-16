"""GitHub pull request closing command for SimpleAgent.

This module provides functionality to close pull requests in GitHub repositories using PyGithub.
"""

from typing import Dict, Any, Optional
from github import Github, GithubException
import os
from commands import register_command

def github_close_pr(
    repo_url: str,
    pr_number: int,
    comment: Optional[str] = None,
) -> Dict[str, Any]:
    """Close a pull request in a GitHub repository with an optional comment.
    
    Args:
        repo_url: The URL of the GitHub repository
        pr_number: The number of the pull request to close
        comment: Optional comment to leave before closing the pull request
        
    Returns:
        Dictionary containing the result of the closing operation
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
        
        # Get the pull request
        pr = repo.get_pull(pr_number)
        
        commented = False
        
        # Process the comment to handle newlines properly
        if comment:
            comment = comment.replace('\\n', '\n').strip()
            
            try:
                # Add the comment
                pr.create_issue_comment(comment)
                commented = True
            except GithubException as e:
                return {
                    "error": f"Failed to add comment to pull request: {str(e)}",
                    "pr_number": pr_number,
                    "repo_url": repo_url
                }
        
        try:
            # Close the pull request
            pr.edit(state="closed")
            
            return {
                "success": True,
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "closed_at": pr.closed_at.isoformat() if pr.closed_at else None,
                "commented": commented,
                "state": "closed",
                "repo_url": repo_url
            }
                
        except GithubException as e:
            return {
                "error": f"Failed to close pull request: {str(e)}",
                "pr_number": pr_number,
                "repo_url": repo_url,
                "commented": commented
            }
            
    except GithubException as e:
        return {
            "error": f"GitHub API error: {str(e)}",
            "url": repo_url,
            "pr_number": pr_number
        }
    except Exception as e:
        return {
            "error": f"Failed to close pull request: {str(e)}",
            "url": repo_url,
            "pr_number": pr_number
        }
    finally:
        if 'g' in locals():
            g.close()

# Schema for the github_close_pr command
GITHUB_CLOSE_PR_SCHEMA = {
    "type": "function",
    "function": {
        "name": "github_close_pr",
        "description": "Close a pull request in a GitHub repository with an optional comment",
        "parameters": {
            "type": "object",
            "properties": {
                "repo_url": {
                    "type": "string",
                    "description": "The URL of the GitHub repository"
                },
                "pr_number": {
                    "type": "integer",
                    "description": "The number of the pull request to close"
                },
                "comment": {
                    "type": "string",
                    "description": "Optional comment to leave before closing the pull request",
                    "default": None
                }
            },
            "required": ["repo_url", "pr_number"]
        }
    }
}

register_command("github_close_pr", github_close_pr, GITHUB_CLOSE_PR_SCHEMA) 