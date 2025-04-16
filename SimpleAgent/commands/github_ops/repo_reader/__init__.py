"""GitHub repository reader command for SimpleAgent.

This module provides functionality to read and analyze GitHub repositories using PyGithub.
"""

from typing import Dict, Any
from github import Github, GithubException
import os
from commands import register_command

def repo_reader(repo_url: str, include_readme: bool = True, include_files: bool = False) -> Dict[str, Any]:
    """Read and analyze a GitHub repository using PyGithub.
    
    Args:
        repo_url: The URL of the GitHub repository (e.g., 'https://github.com/owner/repo')
        include_readme: Whether to include the README content
        include_files: Whether to include the file structure
        
    Returns:
        Dictionary containing repository information
    """
    try:
        # Initialize GitHub client with token if available
        token = os.getenv("GITHUB_TOKEN")
        g = Github(token) if token else Github()
        
        # Extract owner and repo from URL
        parts = repo_url.rstrip('/').split('/')
        owner = parts[-2]
        repo = parts[-1]
        
        # Get repository
        repo = g.get_repo(f"{owner}/{repo}")
        
        result = {
            "name": repo.name,
            "description": repo.description,
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "open_issues": repo.open_issues_count,
            "default_branch": repo.default_branch,
            "created_at": repo.created_at.isoformat(),
            "updated_at": repo.updated_at.isoformat(),
            "language": repo.language,
            "license": repo.license.name if repo.license else None,
            "topics": repo.get_topics(),
            "visibility": repo.visibility,
            "size": repo.size,
            "homepage": repo.homepage,
            "has_wiki": repo.has_wiki,
            "has_pages": repo.has_pages,
            "archived": repo.archived
        }
        
        # Get README if requested
        if include_readme:
            try:
                readme = repo.get_readme()
                result["readme"] = readme.decoded_content.decode('utf-8')
            except GithubException as e:
                result["readme_error"] = str(e)
        
        # Get file structure if requested
        if include_files:
            try:
                contents = repo.get_contents("")
                result["files"] = []
                while contents:
                    file_content = contents.pop(0)
                    if file_content.type == "dir":
                        contents.extend(repo.get_contents(file_content.path))
                    result["files"].append({
                        "name": file_content.name,
                        "type": file_content.type,
                        "size": file_content.size,
                        "path": file_content.path,
                        "sha": file_content.sha
                    })
            except GithubException as e:
                result["files_error"] = str(e)
        
        return result
        
    except GithubException as e:
        return {
            "error": f"GitHub API error: {str(e)}",
            "url": repo_url
        }
    except Exception as e:
        return {
            "error": f"Failed to read repository: {str(e)}",
            "url": repo_url
        }
    finally:
        if 'g' in locals():
            g.close()

# Define the schema for the repo_reader command
REPO_READER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "github_repo_reader",
        "description": "Read and analyze a GitHub repository using PyGithub",
        "parameters": {
            "type": "object",
            "properties": {
                "repo_url": {
                    "type": "string",
                    "description": "The URL of the GitHub repository (e.g., 'https://github.com/owner/repo')"
                },
                "include_readme": {
                    "type": "boolean",
                    "description": "Whether to include the README content",
                    "default": True
                },
                "include_files": {
                    "type": "boolean",
                    "description": "Whether to include the file structure",
                    "default": False
                }
            },
            "required": ["repo_url"]
        }
    }
}

# Register the command
register_command("github_repo_reader", repo_reader, REPO_READER_SCHEMA) 