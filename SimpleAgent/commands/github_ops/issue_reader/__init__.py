"""GitHub issue reader command for SimpleAgent.

This module provides functionality to read GitHub issues using PyGithub.
"""

from typing import Dict, Any, Optional
from github import Github, GithubException
import os
from commands import register_command

def issue_reader(repo_url: str, issue_number: Optional[int] = None, state: str = "open", limit: int = 10, include_comments: bool = False) -> Dict[str, Any]:
    """Read GitHub issues from a repository using PyGithub.
    
    Args:
        repo_url: The URL of the GitHub repository
        issue_number: Specific issue number to fetch (optional)
        state: Issue state to fetch ('open', 'closed', or 'all')
        limit: Maximum number of issues to fetch when not specifying an issue number
        include_comments: Whether to include all comments for the issue(s)
        
    Returns:
        Dictionary containing issue information
    """
    try:
        # Initialize GitHub client with token if available
        token = os.getenv("GITHUB_TOKEN")
        g = Github(token) if token else Github()
        
        # Extract owner and repo from URL
        parts = repo_url.rstrip('/').split('/')
        owner = parts[-2]
        repo_name = parts[-1]
        
        # Get repository
        repo = g.get_repo(f"{owner}/{repo_name}")
        
        if issue_number is not None:
            # Fetch specific issue
            issue = repo.get_issue(issue_number)
            issue_data = {
                "number": issue.number,
                "title": issue.title,
                "state": issue.state,
                "created_at": issue.created_at.isoformat(),
                "updated_at": issue.updated_at.isoformat(),
                "body": issue.body,
                "comments_count": issue.comments,
                "labels": [label.name for label in issue.labels],
                "assignees": [assignee.login for assignee in issue.assignees],
                "url": issue.html_url,
                "milestone": issue.milestone.title if issue.milestone else None,
                "locked": issue.locked,
                "author": issue.user.login
            }
            
            # Include comments if requested
            if include_comments and issue.comments > 0:
                comments_list = []
                for comment in issue.get_comments():
                    comments_list.append({
                        "id": comment.id,
                        "author": comment.user.login,
                        "created_at": comment.created_at.isoformat(),
                        "updated_at": comment.updated_at.isoformat(),
                        "body": comment.body,
                        "url": comment.html_url
                    })
                issue_data["comments"] = comments_list
            
            return {
                "issue": issue_data
            }
        else:
            # Fetch multiple issues
            issues = repo.get_issues(state=state)
            issue_list = []
            for i, issue in enumerate(issues):
                if i >= limit:
                    break
                    
                issue_data = {
                    "number": issue.number,
                    "title": issue.title,
                    "state": issue.state,
                    "created_at": issue.created_at.isoformat(),
                    "updated_at": issue.updated_at.isoformat(),
                    "comments_count": issue.comments,
                    "labels": [label.name for label in issue.labels],
                    "url": issue.html_url,
                    "author": issue.user.login
                }
                
                # Include comments if requested and there are comments
                if include_comments and issue.comments > 0:
                    comments_list = []
                    for comment in issue.get_comments():
                        comments_list.append({
                            "id": comment.id,
                            "author": comment.user.login,
                            "created_at": comment.created_at.isoformat(),
                            "updated_at": comment.updated_at.isoformat(),
                            "body": comment.body,
                            "url": comment.html_url
                        })
                    issue_data["comments"] = comments_list
                
                issue_list.append(issue_data)
            
            return {
                "total_count": len(issue_list),
                "state": state,
                "issues": issue_list
            }
            
    except GithubException as e:
        return {
            "error": f"GitHub API error: {str(e)}",
            "url": repo_url
        }
    except Exception as e:
        return {
            "error": f"Failed to read issues: {str(e)}",
            "url": repo_url
        }
    finally:
        if 'g' in locals():
            g.close()

# Define the schema for the issue_reader command
ISSUE_READER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "github_issue_reader",
        "description": "Read GitHub issues from a repository using PyGithub",
        "parameters": {
            "type": "object",
            "properties": {
                "repo_url": {
                    "type": "string",
                    "description": "The URL of the GitHub repository"
                },
                "issue_number": {
                    "type": "integer",
                    "description": "Specific issue number to fetch (optional)",
                    "default": None
                },
                "state": {
                    "type": "string",
                    "description": "Issue state to fetch ('open', 'closed', or 'all')",
                    "enum": ["open", "closed", "all"],
                    "default": "open"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of issues to fetch when not specifying an issue number",
                    "default": 10
                },
                "include_comments": {
                    "type": "boolean",
                    "description": "Whether to include all comments for the issue(s)",
                    "default": False
                }
            },
            "required": ["repo_url"]
        }
    }
}

# Register the command
register_command("github_issue_reader", issue_reader, ISSUE_READER_SCHEMA) 