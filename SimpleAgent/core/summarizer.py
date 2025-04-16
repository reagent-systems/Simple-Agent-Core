"""
Change Summarizer Module

This module provides functionality to summarize changes made by the SimpleAgent agent
using a cheaper GPT model.
"""

import os
from typing import List, Dict, Any
from openai import OpenAI
from core.config import OPENAI_API_KEY, SUMMARIZER_MODEL


class ChangeSummarizer:
    def __init__(self, model: str = None):
        """
        Initialize the ChangeSummarizer.
        
        Args:
            model: The OpenAI model to use for summarization (defaults to config value)
        """
        self.model = model or SUMMARIZER_MODEL
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        
    def summarize_changes(self, changes: List[Dict[str, Any]], is_step_summary: bool = False) -> str:
        """
        Summarize the changes made by the agent.
        
        Args:
            changes: List of changes made by the agent
            is_step_summary: Whether this is a summary for a single step
            
        Returns:
            A summary of the changes
        """
        if not changes:
            return None
            
        # Prepare the prompt for the summarization
        prompt = """Provide a clear and concise summary of the changes made. Focus on:

1. What was actually changed or created
2. Any new functionality or capabilities added
3. The impact or result of the changes

Be direct and avoid filler words or redundant information.
Use bullet points for clarity.

Changes to analyze:

"""
        
        # Group changes by file for better context
        changes_by_file = {}
        for change in changes:
            file = change.get("file", "unknown")
            if file not in changes_by_file:
                changes_by_file[file] = []
            changes_by_file[file].append(change)
            
        # Add each file's changes to the prompt
        for file, file_changes in changes_by_file.items():
            prompt += f"\nFile: {file}\n"
            for change in file_changes:
                operation = change.get("operation", "unknown")
                content = change.get("content", "")
                result = change.get("result", "")
                
                prompt += f"- Operation: {operation}\n"
                if content:
                    # Truncate content if it's too long
                    content_preview = content[:500] + "..." if len(content) > 500 else content
                    prompt += f"  Content:\n{content_preview}\n"
                if result:
                    prompt += f"  Result: {result}\n"
        
        # Call the model to generate the summary
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a technical summarizer that explains code changes clearly and concisely.
Focus on concrete changes and their impact. Avoid filler words and redundant information.

Examples of good summaries:
✓ "Added /time endpoint that returns current time in ISO format"
✓ "Created error handling for 404 responses in user routes"
✓ "Set up project with Flask 2.0.3 and basic config"

Examples of bad summaries:
✗ "Made changes to the file"
✗ "Added some new code"
✗ "The changes were successful"

Use bullet points and be specific but brief."""
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.2
            )
            
            if response.choices and response.choices[0].message and response.choices[0].message.content:
                summary = response.choices[0].message.content.strip()
                
                # For step summaries, make it immediate and brief
                if is_step_summary:
                    return f"📍 Step Result:\n{summary}"
                # For overall summaries, provide more context
                else:
                    return f"📋 Project Status:\n{summary}"
            else:
                return None
                
        except Exception as e:
            return f"Error generating summary: {str(e)}" 