"""GitHub pull request reader command for SimpleAgent.

This module provides functionality to read GitHub pull requests using PyGithub.
"""

from typing import Dict, Any, Optional
from github import Github, GithubException
import os
from commands import register_command

def pr_reader(
    repo_url: str, 
    pr_number: Optional[int] = None, 
    state: str = "open", 
    limit: int = 10, 
    include_files: bool = False,
    include_comments: bool = False,
    include_review_comments: bool = False
) -> Dict[str, Any]:
    """Read GitHub pull requests from a repository using PyGithub.
    
    Args:
        repo_url: The URL of the GitHub repository
        pr_number: Specific PR number to fetch (optional)
        state: PR state to fetch ('open', 'closed', or 'all')
        limit: Maximum number of PRs to fetch when not specifying a PR number
        include_files: Whether to include file changes (only for specific PR)
        include_comments: Whether to include regular comments on the PR
        include_review_comments: Whether to include review comments on specific lines of code
        
    Returns:
        Dictionary containing pull request information
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
        
        if pr_number is not None:
            # Fetch specific PR
            pr = repo.get_pull(pr_number)
            pr_data = {
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
                "body": pr.body,
                "comments_count": pr.comments,
                "review_comments_count": pr.review_comments,
                "commits": pr.commits,
                "additions": pr.additions,
                "deletions": pr.deletions,
                "changed_files": pr.changed_files,
                "labels": [label.name for label in pr.labels],
                "assignees": [assignee.login for assignee in pr.assignees],
                "url": pr.html_url,
                "base": pr.base.ref,
                "head": pr.head.ref,
                "mergeable": pr.mergeable,
                "merged": pr.merged,
                "author": pr.user.login,
                "maintainer_can_modify": pr.maintainer_can_modify,
                "draft": pr.draft
            }

            # Include regular comments if requested
            if include_comments and pr.comments > 0:
                comment_list = []
                for comment in pr.get_issue_comments():
                    comment_list.append({
                        "id": comment.id,
                        "author": comment.user.login,
                        "created_at": comment.created_at.isoformat(),
                        "updated_at": comment.updated_at.isoformat(),
                        "body": comment.body,
                        "url": comment.html_url
                    })
                pr_data["comments"] = comment_list
                
            # Include review comments if requested
            if include_review_comments and pr.review_comments > 0:
                review_comment_list = []
                for comment in pr.get_review_comments():
                    review_comment_list.append({
                        "id": comment.id,
                        "author": comment.user.login,
                        "created_at": comment.created_at.isoformat(),
                        "updated_at": comment.updated_at.isoformat(),
                        "body": comment.body,
                        "path": comment.path,
                        "position": comment.position,
                        "original_position": comment.original_position if hasattr(comment, 'original_position') else None,
                        "commit_id": comment.commit_id,
                        "url": comment.html_url,
                        "diff_hunk": comment.diff_hunk if hasattr(comment, 'diff_hunk') else None
                    })
                pr_data["review_comments"] = review_comment_list

            # Include file changes if requested
            if include_files:
                files = pr.get_files()
                pr_data["file_changes"] = []
                for file in files:
                    file_data = {
                        "filename": file.filename,
                        "status": file.status,  # 'added', 'removed', 'modified', 'renamed', etc.
                        "additions": file.additions,
                        "deletions": file.deletions,
                        "changes": file.changes,
                        "raw_url": file.raw_url,
                        "blob_url": file.blob_url,
                        "sha": file.sha,
                        "previous_filename": file.previous_filename if hasattr(file, 'previous_filename') else None,
                    }
                    
                    # Include patch if available (shows actual changes)
                    if hasattr(file, 'patch'):
                        file_data["patch"] = file.patch
                    
                    pr_data["file_changes"].append(file_data)
                
                # Add summary of file changes
                pr_data["file_changes_summary"] = {
                    "total_files": len(pr_data["file_changes"]),
                    "files_by_status": {},
                    "total_additions": sum(f["additions"] for f in pr_data["file_changes"]),
                    "total_deletions": sum(f["deletions"] for f in pr_data["file_changes"]),
                    "total_changes": sum(f["changes"] for f in pr_data["file_changes"])
                }
                
                # Count files by status
                for file in pr_data["file_changes"]:
                    status = file["status"]
                    pr_data["file_changes_summary"]["files_by_status"][status] = \
                        pr_data["file_changes_summary"]["files_by_status"].get(status, 0) + 1

            return {"pull_request": pr_data}
        else:
            # Fetch multiple PRs
            pulls = repo.get_pulls(state=state, sort='updated', direction='desc')
            pr_list = []
            for i, pr in enumerate(pulls):
                if i >= limit:
                    break
                    
                pr_data = {
                    "number": pr.number,
                    "title": pr.title,
                    "state": pr.state,
                    "created_at": pr.created_at.isoformat(),
                    "updated_at": pr.updated_at.isoformat(),
                    "comments_count": pr.comments,
                    "review_comments_count": pr.review_comments,
                    "commits": pr.commits,
                    "changed_files": pr.changed_files,
                    "labels": [label.name for label in pr.labels],
                    "url": pr.html_url,
                    "base": pr.base.ref,
                    "head": pr.head.ref,
                    "author": pr.user.login,
                    "draft": pr.draft
                }
                
                # Include regular comments if requested
                if include_comments and pr.comments > 0:
                    comment_list = []
                    for comment in pr.get_issue_comments():
                        comment_list.append({
                            "id": comment.id,
                            "author": comment.user.login,
                            "created_at": comment.created_at.isoformat(),
                            "updated_at": comment.updated_at.isoformat(),
                            "body": comment.body,
                            "url": comment.html_url
                        })
                    pr_data["comments"] = comment_list
                    
                # Include review comments if requested
                if include_review_comments and pr.review_comments > 0:
                    review_comment_list = []
                    for comment in pr.get_review_comments():
                        review_comment_list.append({
                            "id": comment.id,
                            "author": comment.user.login,
                            "created_at": comment.created_at.isoformat(),
                            "updated_at": comment.updated_at.isoformat(),
                            "body": comment.body,
                            "path": comment.path,
                            "position": comment.position,
                            "commit_id": comment.commit_id,
                            "url": comment.html_url
                        })
                    pr_data["review_comments"] = review_comment_list
                    
                pr_list.append(pr_data)
            
            return {
                "total_count": len(pr_list),
                "state": state,
                "pull_requests": pr_list
            }
            
    except GithubException as e:
        return {
            "error": f"GitHub API error: {str(e)}",
            "url": repo_url
        }
    except Exception as e:
        return {
            "error": f"Failed to read pull requests: {str(e)}",
            "url": repo_url
        }
    finally:
        if 'g' in locals():
            g.close()

# Update schema to include the new parameters
PR_READER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "github_pr_reader",
        "description": "Read GitHub pull requests from a repository using PyGithub",
        "parameters": {
            "type": "object",
            "properties": {
                "repo_url": {
                    "type": "string",
                    "description": "The URL of the GitHub repository"
                },
                "pr_number": {
                    "type": "integer",
                    "description": "Specific PR number to fetch (optional)",
                    "default": None
                },
                "state": {
                    "type": "string",
                    "description": "PR state to fetch ('open', 'closed', or 'all')",
                    "enum": ["open", "closed", "all"],
                    "default": "open"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of PRs to fetch when not specifying a PR number",
                    "default": 10
                },
                "include_files": {
                    "type": "boolean",
                    "description": "Whether to include file changes (only for specific PR)",
                    "default": False
                },
                "include_comments": {
                    "type": "boolean",
                    "description": "Whether to include regular comments on the PR",
                    "default": False
                },
                "include_review_comments": {
                    "type": "boolean",
                    "description": "Whether to include review comments on specific lines of code",
                    "default": False
                }
            },
            "required": ["repo_url"]
        }
    }
}

register_command("github_pr_reader", pr_reader, PR_READER_SCHEMA) 