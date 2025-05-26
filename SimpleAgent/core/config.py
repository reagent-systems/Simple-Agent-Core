"""
Configuration Module

This module provides configuration settings for the SimpleAgent system.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# API Provider settings
API_PROVIDER = os.getenv("API_PROVIDER", "openai").lower()  # "openai" or "lmstudio"
API_BASE_URL = os.getenv("API_BASE_URL", None)  # For LM-Studio: http://192.168.0.2:1234/v1
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Model settings
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o")
SUMMARIZER_MODEL = os.getenv("SUMMARIZER_MODEL", "gpt-3.5-turbo")

# For LM-Studio, we might want to use the same model for both
if API_PROVIDER == "lmstudio":
    # Override models if LM-Studio specific models are set
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "deepseek-r1-distill-llama-8b")
    SUMMARIZER_MODEL = os.getenv("SUMMARIZER_MODEL", "deepseek-r1-distill-llama-8b")

# Output directory - All file operations MUST happen within this directory
# Can be customized through environment variable
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Memory settings
MEMORY_FILE = os.path.join(OUTPUT_DIR, os.getenv("MEMORY_FILE", "memory.json"))

# Application settings
MAX_STEPS = int(os.getenv("MAX_STEPS", "10"))
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"


def create_openai_client():
    """
    Create an OpenAI client based on the configured API provider.
    
    Returns:
        OpenAI client configured for either OpenAI API or LM-Studio
    """
    if API_PROVIDER == "lmstudio":
        if not API_BASE_URL:
            raise ValueError("API_BASE_URL must be set when using LM-Studio provider")
        
        # For LM-Studio, we don't need a real API key, but the client requires one
        # LM-Studio typically doesn't validate the API key
        api_key = OPENAI_API_KEY or "lm-studio-local"
        
        return OpenAI(
            base_url=API_BASE_URL,
            api_key=api_key
        )
    else:
        # Default to OpenAI
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be set when using OpenAI provider")
        
        return OpenAI(api_key=OPENAI_API_KEY) 