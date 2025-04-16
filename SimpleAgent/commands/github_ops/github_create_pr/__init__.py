"""GitHub pull request creation command for SimpleAgent.

This module provides functionality to create pull requests in GitHub repositories using PyGithub.
"""

from typing import Dict, Any, Optional, List
from github import Github, GithubException
import os
from commands import register_command

def github_create_pr(
    repo_url: str,
    title: str,
    body: str,
    head_branch: str,
    base_branch: Optional[str] = None,
    draft: bool = False,
    labels: Optional[List[str]] = None,
    assignees: Optional[List[str]] = None,
    reviewers: Optional[List[str]] = None,
    team_reviewers: Optional[List[str]] = None,
    maintainer_can_modify: bool = True
) -> Dict[str, Any]:
    """Create a new pull request in a GitHub repository.
    
    Args:
        repo_url: The URL of the GitHub repository
        title: The title of the pull request
        body: The body text of the pull request (supports markdown)
        head_branch: The name of the branch containing the changes
        base_branch: The name of the branch to merge into (defaults to repository's default branch)
        draft: Whether to create the PR as a draft
        labels: Optional list of label names to add to the PR
        assignees: Optional list of GitHub usernames to assign
        reviewers: Optional list of individual reviewers to request
        team_reviewers: Optional list of team names to request review from
        maintainer_can_modify: Whether maintainers can modify the PR's head branch
        
    Returns:
        Dictionary containing the created pull request information
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
        
        # Get the base branch to merge into
        if not base_branch:
            base_branch = repo.default_branch
            
        # Process the body text to handle newlines properly
        body = body.replace('\\n', '\n').strip()
        
        try:
            # Create the pull request
            pr = repo.create_pull(
                title=title,
                body=body,
                head=head_branch,
                base=base_branch,
                draft=draft,
                maintainer_can_modify=maintainer_can_modify
            )
            
            # Add labels if provided
            if labels:
                pr.add_to_labels(*labels)
                
            # Add assignees if provided
            if assignees:
                pr.add_to_assignees(*assignees)
                
            # Request reviewers if provided
            if reviewers or team_reviewers:
                pr.create_review_request(reviewers=reviewers or [], team_reviewers=team_reviewers or [])
            
            return {
                "success": True,
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "created_at": pr.created_at.isoformat(),
                "author": pr.user.login,
                "title": pr.title,
                "labels": [label.name for label in pr.labels],
                "assignees": [assignee.login for assignee in pr.assignees],
                "reviewers": [reviewer.login for reviewer in pr.requested_reviewers],
                "team_reviewers": [team.name for team in pr.requested_teams],
                "draft": pr.draft,
                "head_branch": head_branch,
                "base_branch": base_branch,
                "repo_url": repo_url
            }
                
        except GithubException as e:
            return {
                "error": f"Failed to create pull request: {str(e)}",
                "head_branch": head_branch,
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
            "error": f"Failed to create pull request: {str(e)}",
            "url": repo_url
        }
    finally:
        if 'g' in locals():
            g.close()

# Schema for the github_create_pr command
GITHUB_CREATE_PR_SCHEMA = {
    "type": "function",
    "function": {
        "name": "github_create_pr",
        "description": "Create a new pull request in a GitHub repository",
        "parameters": {
            "type": "object",
            "properties": {
                "repo_url": {
                    "type": "string",
                    "description": "The URL of the GitHub repository"
                },
                "title": {
                    "type": "string",
                    "description": "The title of the pull request"
                },
                "body": {
                    "type": "string",
                    "description": "The body text of the pull request (supports markdown)"
                },
                "head_branch": {
                    "type": "string",
                    "description": "The name of the branch containing the changes"
                },
                "base_branch": {
                    "type": "string",
                    "description": "The name of the branch to merge into (defaults to repository's default branch)",
                    "default": None
                },
                "draft": {
                    "type": "boolean",
                    "description": "Whether to create the PR as a draft",
                    "default": False
                },
                "labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of label names to add to the PR",
                    "default": None
                },
                "assignees": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of GitHub usernames to assign",
                    "default": None
                },
                "reviewers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of individual reviewers to request",
                    "default": None
                },
                "team_reviewers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of team names to request review from",
                    "default": None
                },
                "maintainer_can_modify": {
                    "type": "boolean",
                    "description": "Whether maintainers can modify the PR's head branch",
                    "default": True
                }
            },
            "required": ["repo_url", "title", "body", "head_branch"]
        }
    }
}

register_command("github_create_pr", github_create_pr, GITHUB_CREATE_PR_SCHEMA) 