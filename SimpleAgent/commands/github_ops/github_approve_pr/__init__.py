"""GitHub pull request approval command for SimpleAgent.

This module provides functionality to approve pull requests in GitHub repositories using PyGithub.
"""

from typing import Dict, Any, Optional
from github import Github, GithubException
import os
from commands import register_command

def github_approve_pr(
    repo_url: str,
    pr_number: int,
    review_comment: Optional[str] = None,
) -> Dict[str, Any]:
    """Approve a pull request in a GitHub repository.
    
    Args:
        repo_url: The URL of the GitHub repository
        pr_number: The number of the pull request to approve
        review_comment: Optional comment to include with the approval
        
    Returns:
        Dictionary containing the result of the approval operation
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
        
        # Process the review comment to handle newlines properly
        if review_comment:
            review_comment = review_comment.replace('\\n', '\n').strip()
        
        try:
            # Create the review with approval
            review = pr.create_review(
                body=review_comment or "Looks good! Approving this pull request.",
                event="APPROVE"
            )
            
            return {
                "success": True,
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "approved_at": review.submitted_at.isoformat() if hasattr(review, 'submitted_at') else None,
                "reviewer": review.user.login if hasattr(review, 'user') else None,
                "review_id": review.id,
                "review_state": "APPROVED",
                "repo_url": repo_url
            }
                
        except GithubException as e:
            return {
                "error": f"Failed to approve pull request: {str(e)}",
                "pr_number": pr_number,
                "repo_url": repo_url
            }
            
    except GithubException as e:
        return {
            "error": f"GitHub API error: {str(e)}",
            "url": repo_url,
            "pr_number": pr_number
        }
    except Exception as e:
        return {
            "error": f"Failed to approve pull request: {str(e)}",
            "url": repo_url,
            "pr_number": pr_number
        }
    finally:
        if 'g' in locals():
            g.close()

# Schema for the github_approve_pr command
GITHUB_APPROVE_PR_SCHEMA = {
    "type": "function",
    "function": {
        "name": "github_approve_pr",
        "description": "Approve a pull request in a GitHub repository",
        "parameters": {
            "type": "object",
            "properties": {
                "repo_url": {
                    "type": "string",
                    "description": "The URL of the GitHub repository"
                },
                "pr_number": {
                    "type": "integer",
                    "description": "The number of the pull request to approve"
                },
                "review_comment": {
                    "type": "string",
                    "description": "Optional comment to include with the approval",
                    "default": None
                }
            },
            "required": ["repo_url", "pr_number"]
        }
    }
}

register_command("github_approve_pr", github_approve_pr, GITHUB_APPROVE_PR_SCHEMA) 