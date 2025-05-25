"""
Configuration Module

This module provides configuration settings for the SimpleAgent system.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI API settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o")
SUMMARIZER_MODEL = os.getenv("SUMMARIZER_MODEL", "gpt-3.5-turbo")

# LMStudio/Local API settings
API_BASE_URL = os.getenv("API_BASE_URL")  # Set to http://localhost:1234/v1 for LMStudio
LOCAL_MODEL = os.getenv("LOCAL_MODEL")  # Model name for local inference

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