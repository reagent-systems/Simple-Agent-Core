"""
Configuration Module

This module provides configuration settings for the SimpleAgent system.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# AI Provider settings
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")  # openai, gemini, lmstudio

# OpenAI API settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o")
SUMMARIZER_MODEL = os.getenv("SUMMARIZER_MODEL", "gpt-3.5-turbo")

# Gemini API settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# LMStudio settings
LMSTUDIO_BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234")
LMSTUDIO_API_KEY = os.getenv("LMSTUDIO_API_KEY")  # Optional

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