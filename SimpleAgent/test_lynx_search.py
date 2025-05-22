#!/usr/bin/env python3
"""
Test script for lynx-based web search.

This script demonstrates the web search functionality using lynx.
"""

import sys
import json
from commands.web_ops.web_search import web_search
from commands.web_ops.browse_web import browse_web

def main():
    """Run a test of the lynx web search."""
    # Check if query is provided as argument
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter search query: ")
    
    print(f"\nSearching for: {query}\n")
    
    # Perform search
    results = web_search(query, num_results=5, include_snippets=True)
    
    # Print results
    print(f"Found {results.get('total_results', 0)} results:\n")
    
    for i, result in enumerate(results.get('results', []), 1):
        print(f"{i}. {result.get('title', 'No title')}")
        print(f"   URL: {result.get('url', 'No URL')}")
        if 'snippet' in result:
            print(f"   Snippet: {result.get('snippet')[:150]}...")
        print()
    
    # Ask if user wants to browse one of the results
    if results.get('results'):
        try:
            choice = input("Enter result number to browse (or press Enter to exit): ")
            if choice and choice.isdigit():
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(results.get('results', [])):
                    url = results['results'][choice_idx].get('url')
                    if url:
                        print(f"\nOpening {url} in lynx browser...")
                        browse_web(url)
        except KeyboardInterrupt:
            print("\nBrowsing cancelled.")
    
    print("Test completed.")

if __name__ == "__main__":
    main() 