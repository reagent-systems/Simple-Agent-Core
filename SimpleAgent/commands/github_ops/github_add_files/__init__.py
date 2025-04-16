"""GitHub file addition command for SimpleAgent.

This module provides functionality to add or update files in GitHub repositories using PyGithub.
"""

from typing import Dict, Any, Optional, List, Union
from github import Github, GithubException, InputGitTreeElement
import os
import base64
from commands import register_command

def github_add_files(
    repo_url: str,
    files: List[Dict[str, str]],
    branch: Optional[str] = None,
    commit_message: str = "Added files via SimpleAgent",
    base64_encoded: bool = False
) -> Dict[str, Any]:
    """Add or update files in a GitHub repository.
    
    Args:
        repo_url: The URL of the GitHub repository
        files: List of dictionaries containing file info:
              [{"path": "path/to/file.txt", "content": "file content"}]
        branch: Branch to commit to (defaults to repository's default branch)
        commit_message: Commit message for the changes
        base64_encoded: Whether the file contents are base64 encoded
        
    Returns:
        Dictionary containing the commit information
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
        
        # Get the branch to commit to
        if not branch:
            branch = repo.default_branch
            
        # Get the latest commit of the branch
        ref = repo.get_git_ref(f"heads/{branch}")
        latest_commit = repo.get_git_commit(ref.object.sha)
        base_tree = latest_commit.tree
        
        # Create blobs for each file
        element_list = []
        for file_info in files:
            try:
                content = file_info["content"]
                if not base64_encoded:
                    # If content is not base64 encoded, encode it
                    content = base64.b64encode(content.encode()).decode()
                
                # Create blob
                blob = repo.create_git_blob(content, "base64")
                
                # Create tree element
                element = InputGitTreeElement(
                    path=file_info["path"],
                    mode='100644',  # file mode (100644 for regular file)
                    type='blob',
                    sha=blob.sha
                )
                element_list.append(element)
                
            except Exception as e:
                return {
                    "error": f"Failed to process file {file_info.get('path')}: {str(e)}",
                    "url": repo_url
                }
        
        # Create tree with all files
        tree = repo.create_git_tree(element_list, base_tree)
        
        # Create commit
        commit = repo.create_git_commit(
            message=commit_message,
            tree=tree,
            parents=[latest_commit]
        )
        
        # Update branch reference
        ref.edit(commit.sha)
        
        return {
            "success": True,
            "commit_sha": commit.sha,
            "commit_url": commit.html_url,
            "commit_message": commit_message,
            "branch": branch,
            "files_added": len(files),
            "repo_url": repo_url
        }
            
    except GithubException as e:
        return {
            "error": f"GitHub API error: {str(e)}",
            "url": repo_url
        }
    except Exception as e:
        return {
            "error": f"Failed to add files: {str(e)}",
            "url": repo_url
        }
    finally:
        if 'g' in locals():
            g.close()

# Schema for the github_add_files command
GITHUB_ADD_FILES_SCHEMA = {
    "type": "function",
    "function": {
        "name": "github_add_files",
        "description": "Add or update files in a GitHub repository",
        "parameters": {
            "type": "object",
            "properties": {
                "repo_url": {
                    "type": "string",
                    "description": "The URL of the GitHub repository"
                },
                "files": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path where the file should be created/updated"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content of the file (can be base64 encoded if base64_encoded is true)"
                            }
                        },
                        "required": ["path", "content"]
                    },
                    "description": "List of files to add/update"
                },
                "branch": {
                    "type": "string",
                    "description": "Branch to commit to (defaults to repository's default branch)",
                    "default": None
                },
                "commit_message": {
                    "type": "string",
                    "description": "Commit message for the changes",
                    "default": "Added files via SimpleAgent"
                },
                "base64_encoded": {
                    "type": "boolean",
                    "description": "Whether the file contents are base64 encoded",
                    "default": False
                }
            },
            "required": ["repo_url", "files"]
        }
    }
}

register_command("github_add_files", github_add_files, GITHUB_ADD_FILES_SCHEMA) 