"""Extract links command for SimpleAgent.

This module provides the extract_links command for fetching and categorizing links from a webpage.
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List
from urllib.parse import urljoin, urlparse
from commands import register_command
from ..user_agents import user_agent_manager


def extract_links(url: str, categorize: bool = True, follow_redirects: bool = False) -> Dict[str, Any]:
    """
    Extract all links from a webpage with optional categorization.
    
    Args:
        url: The URL to extract links from
        categorize: Whether to categorize links by type (default: True)
        follow_redirects: Whether to follow redirects when categorizing external links (default: False)
        
    Returns:
        Dictionary containing the extracted links
    """
    try:
        # Get random headers for this request
        headers = user_agent_manager.get_headers()
        
        # Fetch the page
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse the content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract base URL components for relative link resolution
        parsed_url = urlparse(url)
        base_domain = parsed_url.netloc
        base_scheme = parsed_url.scheme
        base_url = f"{base_scheme}://{base_domain}"
        
        # Find all links in the page
        all_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and not href.startswith(('javascript:', 'mailto:', 'tel:')):
                # Create the full URL if it's a relative link
                full_url = urljoin(url, href)
                
                # Get link text and title
                link_text = link.get_text(strip=True) or "[No Text]"
                link_title = link.get('title', '')
                
                all_links.append({
                    "url": full_url,
                    "text": link_text[:100] + ("..." if len(link_text) > 100 else ""),
                    "title": link_title,
                    "is_relative": not bool(urlparse(href).netloc)
                })
        
        result = {
            "url": url,
            "title": soup.title.string if soup.title else None,
            "total_links": len(all_links),
            "links": all_links
        }
        
        # Categorize links if requested
        if categorize:
            internal_links = []
            external_links = []
            media_links = []
            document_links = []
            
            # Media and document extensions
            media_exts = ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.mp4', '.webm', '.avi', '.mov']
            doc_exts = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.csv', '.zip', '.rar']
            
            for link in all_links:
                link_url = link["url"]
                parsed_link = urlparse(link_url)
                
                # Check if link is internal or external
                if parsed_link.netloc == base_domain or not parsed_link.netloc:
                    internal_links.append(link)
                else:
                    # If we need to follow redirects to check final URL
                    if follow_redirects:
                        try:
                            head_response = requests.head(link_url, headers=headers, timeout=5, allow_redirects=True)
                            link["final_url"] = head_response.url
                            link["status_code"] = head_response.status_code
                        except Exception:
                            # If we can't follow the redirect, just use the original URL
                            link["final_url"] = link_url
                            link["status_code"] = None
                    
                    external_links.append(link)
                
                # Check if it's a media link
                if any(link_url.lower().endswith(ext) for ext in media_exts):
                    media_links.append(link)
                
                # Check if it's a document link
                if any(link_url.lower().endswith(ext) for ext in doc_exts):
                    document_links.append(link)
            
            result["categories"] = {
                "internal_links": {
                    "count": len(internal_links),
                    "links": internal_links
                },
                "external_links": {
                    "count": len(external_links),
                    "links": external_links
                },
                "media_links": {
                    "count": len(media_links),
                    "links": media_links
                },
                "document_links": {
                    "count": len(document_links),
                    "links": document_links
                }
            }
        
        return result
        
    except Exception as e:
        return {
            "error": f"Failed to extract links: {str(e)}",
            "url": url
        }


# Define the schema for the extract_links command
EXTRACT_LINKS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "extract_links",
        "description": "Extract and optionally categorize all links from a webpage",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to extract links from"
                },
                "categorize": {
                    "type": "boolean",
                    "description": "Whether to categorize links by type (default: true)",
                    "default": True
                },
                "follow_redirects": {
                    "type": "boolean",
                    "description": "Whether to follow redirects when categorizing external links (default: false)",
                    "default": False
                }
            },
            "required": ["url"]
        }
    }
}

# Register the command
register_command("extract_links", extract_links, EXTRACT_LINKS_SCHEMA) 