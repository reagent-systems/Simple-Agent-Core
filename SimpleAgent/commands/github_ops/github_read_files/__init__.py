"""GitHub PR file reader command for SimpleAgent.

This module provides functionality to read file contents from GitHub pull requests using PyGithub.
"""

from typing import Dict, Any, Optional, List
from github import Github, GithubException
import os
from commands import register_command

def github_read_files(repo_url: str, pr_number: int, file_filter: Optional[str] = None, max_files: int = 10) -> Dict[str, Any]:
    """Read file contents from a GitHub pull request.
    
    Args:
        repo_url: The URL of the GitHub repository
        pr_number: The PR number to fetch files from
        file_filter: Optional regex pattern to filter files (e.g. "*.py" for Python files)
        max_files: Maximum number of files to fetch (default 10)
        
    Returns:
        Dictionary containing file contents and metadata
    """
    try:
        # Initialize GitHub client with token if available
        token = os.getenv("GITHUB_TOKEN")
        g = Github(token) if token else Github()
        
        # Extract owner and repo from URL
        parts = repo_url.rstrip('/').split('/')
        owner = parts[-2]
        repo_name = parts[-1]
        
        # Get repository and PR
        repo = g.get_repo(f"{owner}/{repo_name}")
        pr = repo.get_pull(pr_number)
        
        # Get files from PR
        files = pr.get_files()
        
        result = {
            "pr_number": pr_number,
            "pr_title": pr.title,
            "total_files": pr.changed_files,
            "files": []
        }
        
        import re
        file_pattern = re.compile(file_filter) if file_filter else None
        
        file_count = 0
        for file in files:
            # Skip if we've reached max files
            if file_count >= max_files:
                break
                
            # Apply file filter if specified
            if file_pattern and not file_pattern.match(file.filename):
                continue
            
            file_data = {
                "filename": file.filename,
                "status": file.status,
                "sha": file.sha,
                "additions": file.additions,
                "deletions": file.deletions,
                "changes": file.changes,
                "raw_url": file.raw_url,
                "blob_url": file.blob_url,
                "contents_url": file.contents_url if hasattr(file, 'contents_url') else None,
            }
            
            # Get the actual file contents if available
            try:
                if file.status != "removed":
                    # Get file content from the PR's head branch
                    content = repo.get_contents(file.filename, ref=pr.head.sha)
                    if content:
                        file_data["content"] = content.decoded_content.decode('utf-8')
                    else:
                        file_data["content"] = None
            except Exception as e:
                file_data["content"] = None
                file_data["content_error"] = str(e)
            
            # Include patch if available (shows actual changes)
            if hasattr(file, 'patch'):
                file_data["patch"] = file.patch
            
            # For renamed files, include the previous name
            if hasattr(file, 'previous_filename'):
                file_data["previous_filename"] = file.previous_filename
            
            result["files"].append(file_data)
            file_count += 1
        
        # Add summary information
        result["summary"] = {
            "files_included": len(result["files"]),
            "files_by_status": {},
            "total_additions": sum(f["additions"] for f in result["files"]),
            "total_deletions": sum(f["deletions"] for f in result["files"]),
            "total_changes": sum(f["changes"] for f in result["files"])
        }
        
        # Count files by status
        for file in result["files"]:
            status = file["status"]
            result["summary"]["files_by_status"][status] = \
                result["summary"]["files_by_status"].get(status, 0) + 1
        
        return result
            
    except GithubException as e:
        return {
            "error": f"GitHub API error: {str(e)}",
            "url": repo_url,
            "pr_number": pr_number
        }
    except Exception as e:
        return {
            "error": f"Failed to read PR files: {str(e)}",
            "url": repo_url,
            "pr_number": pr_number
        }
    finally:
        if 'g' in locals():
            g.close()

# Schema for the github_read_files command
GITHUB_READ_FILES_SCHEMA = {
    "type": "function",
    "function": {
        "name": "github_read_files",
        "description": "Read file contents from a GitHub pull request",
        "parameters": {
            "type": "object",
            "properties": {
                "repo_url": {
                    "type": "string",
                    "description": "The URL of the GitHub repository"
                },
                "pr_number": {
                    "type": "integer",
                    "description": "The PR number to fetch files from"
                },
                "file_filter": {
                    "type": "string",
                    "description": "Optional regex pattern to filter files (e.g. '*.py' for Python files)",
                    "default": None
                },
                "max_files": {
                    "type": "integer",
                    "description": "Maximum number of files to fetch",
                    "default": 10
                }
            },
            "required": ["repo_url", "pr_number"]
        }
    }
}

register_command("github_read_files", github_read_files, GITHUB_READ_FILES_SCHEMA) 