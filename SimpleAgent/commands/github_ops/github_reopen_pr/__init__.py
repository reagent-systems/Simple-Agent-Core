"""GitHub pull request reopen command for SimpleAgent.

This module provides functionality to reopen closed pull requests in GitHub repositories using PyGithub.
"""

from typing import Dict, Any, Optional
from github import Github, GithubException
import os
import traceback
from commands import register_command

def github_reopen_pr(
    repo_url: str,
    pr_number: int,
    comment: Optional[str] = None
) -> Dict[str, Any]:
    """Reopen a closed pull request in a GitHub repository.
    
    Args:
        repo_url: The URL of the GitHub repository
        pr_number: The number of the pull request to reopen
        comment: Optional comment to leave when reopening the pull request
        
    Returns:
        Dictionary containing the result of the reopen operation
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
        
        # Add diagnostic info
        pr_info = {
            "pr_number": pr.number,
            "pr_url": pr.html_url,
            "pr_state": pr.state,
            "pr_title": pr.title,
            "head_branch": pr.head.ref,
            "base_branch": pr.base.ref,
            "is_merged": pr.merged,
            "repo_url": repo_url
        }
        
        # Check if PR is already merged
        if pr.merged:
            return {
                "error": "Pull request is already merged and cannot be reopened.",
                **pr_info
            }
            
        # Check if PR is already open
        if pr.state == "open":
            return {
                "error": "Pull request is already open.",
                **pr_info
            }
            
        commented = False
            
        # Add a comment if provided
        if comment:
            try:
                # Process the comment to handle newlines properly
                processed_comment = comment.replace('\\n', '\n').strip()
                
                # Add the comment
                pr.create_issue_comment(processed_comment)
                commented = True
            except GithubException as e:
                return {
                    "error": f"Failed to add comment to pull request: {str(e)}",
                    "error_details": {
                        "status": e.status if hasattr(e, 'status') else None,
                        "data": e.data if hasattr(e, 'data') else None,
                        "stack": traceback.format_exc()
                    },
                    **pr_info
                }
        
        try:
            # Reopen the pull request
            pr.edit(state="open")
            
            # Refresh the PR state
            pr = repo.get_pull(pr_number)
            
            return {
                "success": True,
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "pr_state": pr.state,
                "commented": commented,
                "reopened_at": pr.updated_at.isoformat() if hasattr(pr, 'updated_at') else None,
                "head_branch": pr.head.ref,
                "base_branch": pr.base.ref,
                "repo_url": repo_url
            }
                
        except GithubException as e:
            error_data = {
                "status": e.status,
                "data": e.data,
                "stack": traceback.format_exc()
            } if hasattr(e, 'status') and hasattr(e, 'data') else {"message": str(e)}
            
            return {
                "error": f"Failed to reopen pull request: {str(e)}",
                "error_details": error_data,
                "commented": commented,
                **pr_info
            }
            
    except GithubException as e:
        error_data = {
            "status": e.status,
            "data": e.data,
            "stack": traceback.format_exc()
        } if hasattr(e, 'status') and hasattr(e, 'data') else {"message": str(e)}
        
        return {
            "error": f"GitHub API error: {str(e)}",
            "error_details": error_data,
            "url": repo_url,
            "pr_number": pr_number
        }
    except Exception as e:
        return {
            "error": f"Failed to reopen pull request: {str(e)}",
            "error_details": traceback.format_exc(),
            "url": repo_url,
            "pr_number": pr_number
        }
    finally:
        if 'g' in locals():
            g.close()

# Schema for the github_reopen_pr command
GITHUB_REOPEN_PR_SCHEMA = {
    "type": "function",
    "function": {
        "name": "github_reopen_pr",
        "description": "Reopen a closed pull request in a GitHub repository",
        "parameters": {
            "type": "object",
            "properties": {
                "repo_url": {
                    "type": "string",
                    "description": "The URL of the GitHub repository"
                },
                "pr_number": {
                    "type": "integer",
                    "description": "The number of the pull request to reopen"
                },
                "comment": {
                    "type": "string",
                    "description": "Optional comment to leave when reopening the pull request",
                    "default": None
                }
            },
            "required": ["repo_url", "pr_number"]
        }
    }
}

register_command("github_reopen_pr", github_reopen_pr, GITHUB_REOPEN_PR_SCHEMA) 