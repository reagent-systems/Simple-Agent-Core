"""GitHub comment command for SimpleAgent.

This module provides functionality to add comments to GitHub PRs using PyGithub.
"""

from typing import Dict, Any, Optional
from github import Github, GithubException
import os
from commands import register_command

def github_comment(repo_url: str, pr_number: int, comment_text: str, reply_to_comment_id: Optional[int] = None) -> Dict[str, Any]:
    """Add a comment to a GitHub pull request.
    
    Args:
        repo_url: The URL of the GitHub repository
        pr_number: The PR number to comment on
        comment_text: The text content of the comment
        reply_to_comment_id: Optional ID of a comment to reply to
        
    Returns:
        Dictionary containing the comment information
    """
    try:
        # Initialize GitHub client with token if available
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return {
                "error": "GitHub token not found. Please set GITHUB_TOKEN environment variable.",
                "url": repo_url,
                "pr_number": pr_number
            }
            
        g = Github(token)
        
        # Extract owner and repo from URL
        parts = repo_url.rstrip('/').split('/')
        owner = parts[-2]
        repo_name = parts[-1]
        
        # Get repository and PR
        repo = g.get_repo(f"{owner}/{repo_name}")
        pr = repo.get_pull(pr_number)
        
        # Process the comment text to handle newlines properly
        comment_text = comment_text.replace('\\n', '\n').strip()
        
        if reply_to_comment_id:
            # Get the comment to reply to
            try:
                original_comment = pr.get_issue_comment(reply_to_comment_id)
                # Format the reply with a quote of the original comment
                quoted_text = '\n'.join([f'> {line}' for line in original_comment.body.split('\n')])
                comment_text = f"**In reply to [{original_comment.user.login}'s comment]({original_comment.html_url}):**\n\n{quoted_text}\n\n---\n\n{comment_text}"
            except GithubException:
                return {
                    "error": f"Could not find comment with ID {reply_to_comment_id}",
                    "url": repo_url,
                    "pr_number": pr_number
                }
        
        # Create the comment
        comment = pr.create_issue_comment(comment_text)
        
        return {
            "success": True,
            "comment_id": comment.id,
            "comment_url": comment.html_url,
            "created_at": comment.created_at.isoformat(),
            "author": comment.user.login,
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
            "error": f"Failed to add comment: {str(e)}",
            "url": repo_url,
            "pr_number": pr_number
        }
    finally:
        if 'g' in locals():
            g.close()

# Schema for the github_comment command
GITHUB_COMMENT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "github_comment",
        "description": "Add a comment to a GitHub pull request",
        "parameters": {
            "type": "object",
            "properties": {
                "repo_url": {
                    "type": "string",
                    "description": "The URL of the GitHub repository"
                },
                "pr_number": {
                    "type": "integer",
                    "description": "The PR number to comment on"
                },
                "comment_text": {
                    "type": "string",
                    "description": "The text content of the comment (supports markdown). Use \\n for newlines."
                },
                "reply_to_comment_id": {
                    "type": "integer",
                    "description": "Optional ID of a comment to reply to",
                    "default": None
                }
            },
            "required": ["repo_url", "pr_number", "comment_text"]
        }
    }
}

register_command("github_comment", github_comment, GITHUB_COMMENT_SCHEMA) 