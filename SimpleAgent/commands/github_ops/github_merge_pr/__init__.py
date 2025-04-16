"""GitHub pull request merge command for SimpleAgent.

This module provides functionality to merge pull requests in GitHub repositories using PyGithub.
"""

from typing import Dict, Any, Optional, Literal
from github import Github, GithubException
import os
import traceback
from commands import register_command

def github_merge_pr(
    repo_url: str,
    pr_number: int,
    merge_method: Optional[Literal["merge", "squash", "rebase"]] = "merge",
    commit_title: Optional[str] = None,
    commit_message: Optional[str] = None,
    delete_branch: bool = False
) -> Dict[str, Any]:
    """Merge a pull request in a GitHub repository.
    
    Args:
        repo_url: The URL of the GitHub repository
        pr_number: The number of the pull request to merge
        merge_method: Method to use for the merge (merge, squash, or rebase)
        commit_title: Optional title for the merge commit (default: PR title)
        commit_message: Optional message for the merge commit (default: PR body)
        delete_branch: Whether to delete the head branch after merging
        
    Returns:
        Dictionary containing the result of the merge operation
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
        
        # Add more diagnostic info
        pr_info = {
            "pr_number": pr.number,
            "pr_url": pr.html_url,
            "pr_state": pr.state,
            "pr_title": pr.title,
            "head_branch": pr.head.ref,
            "base_branch": pr.base.ref,
            "is_merged": pr.merged,
            "mergeable_state": pr.mergeable_state if hasattr(pr, 'mergeable_state') else "unknown",
            "repo_url": repo_url
        }
        
        # Check if PR is already merged
        if pr.merged:
            return {
                "error": "Pull request is already merged.",
                **pr_info
            }
            
        # Check if PR is closed
        if pr.state == "closed":
            return {
                "error": "Pull request is closed but not merged.",
                **pr_info
            }
            
        # Force refresh the mergeable state
        pr = repo.get_pull(pr_number)
        
        # Wait for GitHub to compute mergeable (it might be null initially)
        # Unfortunately, we can't do a proper wait as that would block the request
        # We'll just check and provide more detailed diagnostics
        
        if pr.mergeable is None:
            return {
                "error": "GitHub is still computing whether this PR is mergeable. Please try again in a few seconds.",
                **pr_info
            }
            
        # Check if PR is mergeable
        if pr.mergeable is False:
            return {
                "error": f"Pull request is not mergeable. Mergeable state: {pr.mergeable_state if hasattr(pr, 'mergeable_state') else 'unknown'}",
                **pr_info
            }
            
        head_branch = pr.head.ref
        
        try:
            # Merge the pull request
            merge_args = {
                "merge_method": merge_method
            }
            if commit_title is not None:
                merge_args["commit_title"] = commit_title
            if commit_message is not None:
                merge_args["commit_message"] = commit_message

            merge_result = pr.merge(**merge_args)
            
            result = {
                "success": True,
                "merged": merge_result.merged,
                "message": merge_result.message,
                "merge_method": merge_method,
                "sha": merge_result.sha if hasattr(merge_result, 'sha') else None,
                "head_branch": head_branch,
                **pr_info
            }
            
            # Delete branch if requested
            if delete_branch and merge_result.merged:
                try:
                    # Check if branch exists
                    branch = repo.get_git_ref(f"heads/{head_branch}")
                    branch.delete()
                    result["branch_deleted"] = True
                except GithubException as e:
                    result["branch_deleted"] = False
                    result["branch_delete_error"] = str(e)
            
            return result
                
        except GithubException as e:
            error_data = {
                "status": e.status,
                "data": e.data,
                "stack": traceback.format_exc()
            } if hasattr(e, 'status') and hasattr(e, 'data') else {"message": str(e)}
            
            return {
                "error": f"Failed to merge pull request: {str(e)}",
                "error_details": error_data,
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
            "error": f"Failed to merge pull request: {str(e)}",
            "error_details": traceback.format_exc(),
            "url": repo_url,
            "pr_number": pr_number
        }
    finally:
        if 'g' in locals():
            g.close()

# Schema for the github_merge_pr command
GITHUB_MERGE_PR_SCHEMA = {
    "type": "function",
    "function": {
        "name": "github_merge_pr",
        "description": "Merge a pull request in a GitHub repository",
        "parameters": {
            "type": "object",
            "properties": {
                "repo_url": {
                    "type": "string",
                    "description": "The URL of the GitHub repository"
                },
                "pr_number": {
                    "type": "integer",
                    "description": "The number of the pull request to merge"
                },
                "merge_method": {
                    "type": "string",
                    "description": "Method to use for the merge (merge, squash, or rebase)",
                    "enum": ["merge", "squash", "rebase"],
                    "default": "merge"
                },
                "commit_title": {
                    "type": "string",
                    "description": "Optional title for the merge commit (default: PR title)",
                    "default": None
                },
                "commit_message": {
                    "type": "string",
                    "description": "Optional message for the merge commit (default: PR body)",
                    "default": None
                },
                "delete_branch": {
                    "type": "boolean",
                    "description": "Whether to delete the head branch after merging",
                    "default": False
                }
            },
            "required": ["repo_url", "pr_number"]
        }
    }
}

register_command("github_merge_pr", github_merge_pr, GITHUB_MERGE_PR_SCHEMA) 