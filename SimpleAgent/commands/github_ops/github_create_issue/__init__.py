"""GitHub issue creation command for SimpleAgent.

This module provides functionality to create GitHub issues using PyGithub.
"""

from typing import Dict, Any, Optional, List
from github import Github, GithubException
import os
from commands import register_command

def github_create_issue(
    repo_url: str,
    title: str,
    body: str,
    labels: Optional[List[str]] = None,
    assignees: Optional[List[str]] = None,
    milestone: Optional[int] = None
) -> Dict[str, Any]:
    """Create a new GitHub issue.
    
    Args:
        repo_url: The URL of the GitHub repository
        title: The title of the issue
        body: The body text of the issue (supports markdown)
        labels: Optional list of label names to add to the issue
        assignees: Optional list of GitHub usernames to assign
        milestone: Optional milestone number to associate with the issue
        
    Returns:
        Dictionary containing the created issue information
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
        
        # Process the body text to handle newlines properly
        body = body.replace('\\n', '\n').strip()
        
        # Create the issue
        issue = repo.create_issue(
            title=title,
            body=body,
            labels=labels or [],
            assignees=assignees or []
        )
        
        # Set milestone if provided
        if milestone is not None:
            try:
                milestone_obj = repo.get_milestone(milestone)
                issue.edit(milestone=milestone_obj)
            except GithubException as e:
                return {
                    "error": f"Could not set milestone {milestone}: {str(e)}",
                    "issue_url": issue.html_url,
                    "issue_number": issue.number
                }
        
        return {
            "success": True,
            "issue_number": issue.number,
            "issue_url": issue.html_url,
            "created_at": issue.created_at.isoformat(),
            "author": issue.user.login,
            "title": issue.title,
            "labels": [label.name for label in issue.labels],
            "assignees": [assignee.login for assignee in issue.assignees],
            "milestone": issue.milestone.title if issue.milestone else None,
            "repo_url": repo_url
        }
            
    except GithubException as e:
        return {
            "error": f"GitHub API error: {str(e)}",
            "url": repo_url
        }
    except Exception as e:
        return {
            "error": f"Failed to create issue: {str(e)}",
            "url": repo_url
        }
    finally:
        if 'g' in locals():
            g.close()

# Schema for the github_create_issue command
GITHUB_CREATE_ISSUE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "github_create_issue",
        "description": "Create a new GitHub issue",
        "parameters": {
            "type": "object",
            "properties": {
                "repo_url": {
                    "type": "string",
                    "description": "The URL of the GitHub repository"
                },
                "title": {
                    "type": "string",
                    "description": "The title of the issue"
                },
                "body": {
                    "type": "string",
                    "description": "The body text of the issue (supports markdown). Use \\n for newlines."
                },
                "labels": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Optional list of label names to add to the issue",
                    "default": None
                },
                "assignees": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Optional list of GitHub usernames to assign",
                    "default": None
                },
                "milestone": {
                    "type": "integer",
                    "description": "Optional milestone number to associate with the issue",
                    "default": None
                }
            },
            "required": ["repo_url", "title", "body"]
        }
    }
}

register_command("github_create_issue", github_create_issue, GITHUB_CREATE_ISSUE_SCHEMA) 