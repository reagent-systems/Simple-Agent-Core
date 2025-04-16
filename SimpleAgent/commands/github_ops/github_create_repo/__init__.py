"""GitHub repository creation command for SimpleAgent.

This module provides functionality to create new GitHub repositories using PyGithub.
"""

from typing import Dict, Any, Optional, List
from github import Github, GithubException
import os
import traceback
from commands import register_command

def github_create_repo(
    name: str,
    description: str = "",
    private: bool = False,
    has_wiki: bool = True,
    has_issues: bool = True,
    has_projects: bool = True,
    auto_init: bool = True,
    gitignore_template: Optional[str] = None,
    license_template: Optional[str] = None,
    organization: Optional[str] = None,
    team_id: Optional[int] = None
) -> Dict[str, Any]:
    """Create a new GitHub repository.
    
    Args:
        name: The name of the repository
        description: A description of the repository
        private: Whether the repository should be private
        has_wiki: Enable/disable wiki
        has_issues: Enable/disable issues
        has_projects: Enable/disable projects
        auto_init: Auto-initialize with README
        gitignore_template: Name of gitignore template (e.g., 'Python', 'Node')
        license_template: Name of license template (e.g., 'mit', 'apache-2.0')
        organization: Optional organization name to create repo under
        team_id: Optional team ID to grant access to
        
    Returns:
        Dictionary containing the created repository information
    """
    g = None
    try:
        # Initialize GitHub client with token if available
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return {
                "success": False,
                "error": "GitHub token not found. Please set GITHUB_TOKEN environment variable."
            }
            
        g = Github(token)
        
        try:
            
            # Build the repo creation kwargs dictionary to avoid None parameters
            repo_kwargs = {
                "name": name,
                "description": description,
                "private": private,
                "has_wiki": has_wiki,
                "has_issues": has_issues,
                "has_projects": has_projects,
                "auto_init": True
            }
            
            # Only add non-None optional parameters
            if gitignore_template is not None:
                repo_kwargs["gitignore_template"] = gitignore_template
                
            if license_template is not None:
                repo_kwargs["license_template"] = license_template
            
            # Create repository either under organization or user account
            if organization:
                org = g.get_organization(organization)
                repo = org.create_repo(**repo_kwargs)
                
                # Add team to repository if specified
                if team_id:
                    team = org.get_team(team_id)
                    team.add_to_repos(repo)
            else:
                # Create under authenticated user's account
                repo = g.get_user().create_repo(**repo_kwargs)
            
            return {
                "success": True,
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "private": repo.private,
                "html_url": repo.html_url,
                "clone_url": repo.clone_url,
                "ssh_url": repo.ssh_url,
                "created_at": repo.created_at.isoformat(),
                "owner": repo.owner.login,
                "default_branch": repo.default_branch,
                "organization": organization if organization else None
            }
                
        except GithubException as e:
            error_detail = f"Status {e.status}: {e.data.get('message', str(e))}" if hasattr(e, 'status') and hasattr(e, 'data') else str(e)
            return {
                "success": False,
                "error": f"GitHub API Error: {error_detail}",
                "name": name
            }
            
    except Exception as e:
        error_message = str(e) if e else "Unknown error occurred"
        stack_trace = traceback.format_exc()
        return {
            "success": False,
            "error": f"Unexpected error: {error_message}",
            "stack_trace": stack_trace,
            "name": name
        }
    finally:
        if g is not None:
            g.close()

# Schema for the github_create_repo command
GITHUB_CREATE_REPO_SCHEMA = {
    "type": "function",
    "function": {
        "name": "github_create_repo",
        "description": "Create a new GitHub repository",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the repository"
                },
                "description": {
                    "type": "string",
                    "description": "A description of the repository",
                    "default": ""
                },
                "private": {
                    "type": "boolean",
                    "description": "Whether the repository should be private",
                    "default": False
                },
                "has_wiki": {
                    "type": "boolean",
                    "description": "Enable/disable wiki",
                    "default": True
                },
                "has_issues": {
                    "type": "boolean",
                    "description": "Enable/disable issues",
                    "default": True
                },
                "has_projects": {
                    "type": "boolean",
                    "description": "Enable/disable projects",
                    "default": True
                },
                "auto_init": {
                    "type": "boolean",
                    "description": "Auto-initialize with README",
                    "default": True
                },
                "gitignore_template": {
                    "type": "string",
                    "description": "Name of gitignore template (e.g., 'Python', 'Node')",
                    "default": None
                },
                "license_template": {
                    "type": "string",
                    "description": "Name of license template (e.g., 'mit', 'apache-2.0')",
                    "default": None
                },
                "organization": {
                    "type": "string",
                    "description": "Optional organization name to create repo under",
                    "default": None
                },
                "team_id": {
                    "type": "integer",
                    "description": "Optional team ID to grant access to",
                    "default": None
                }
            },
            "required": ["name"]
        }
    }
}

register_command("github_create_repo", github_create_repo, GITHUB_CREATE_REPO_SCHEMA) 