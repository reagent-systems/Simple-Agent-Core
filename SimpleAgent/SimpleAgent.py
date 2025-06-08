"""
SimpleAgent - A minimalist AI agent framework

This script implements a simple AI agent that can perform basic operations
through function calling. It supports both OpenAI API and LM-Studio for local models.
"""

import os
import sys
import json
import time
import argparse
import logging
import uuid
from typing import List, Dict, Any, Optional, Callable

# Set up basic logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Suppress httpx INFO messages (like HTTP request logs)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Import commands package
import commands
from commands import REGISTERED_COMMANDS, COMMAND_SCHEMAS

# Import core modules
from core.agent.agent import SimpleAgent
from core.utils.config import OPENAI_API_KEY, MAX_STEPS, API_PROVIDER, API_BASE_URL, GEMINI_API_KEY, create_client
from core.utils.version import AGENT_VERSION

# Commands will be initialized in main() based on user preference

# Check for proper configuration based on API provider
if API_PROVIDER == "lmstudio":
    if not API_BASE_URL:
        logging.error("Error: API_BASE_URL environment variable not set for LM-Studio provider.")
        logging.info("Please set API_BASE_URL to your LM-Studio endpoint (e.g., http://192.168.0.2:1234/v1)")
        logging.info("You can set it in a .env file or in your environment variables.")
        sys.exit(1)
    logging.info(f"Using LM-Studio provider at: {API_BASE_URL}")
elif API_PROVIDER == "openai":
    if not OPENAI_API_KEY:
        logging.error("Error: OPENAI_API_KEY environment variable not set for OpenAI provider.")
        logging.info("Please set it in a .env file or in your environment variables.")
        sys.exit(1)
    logging.info("Using OpenAI provider")
elif API_PROVIDER == "gemini":
    if not GEMINI_API_KEY:
        logging.error("Error: GEMINI_API_KEY environment variable not set for Gemini provider.")
        logging.info("Please set it in a .env file or in your environment variables.")
        sys.exit(1)
    logging.info("Using Gemini provider")
else:
    logging.error(f"Error: Unknown API_PROVIDER '{API_PROVIDER}'. Supported providers: 'openai', 'lmstudio', 'gemini'")
    sys.exit(1)


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='SimpleAgent - An AI agent that can perform tasks')
    # Add flags first to prevent instruction from being consumed as a flag value
    parser.add_argument('-a', '--auto', type=int, nargs='?', const=10, default=0,
                      help='Auto-continue for N steps (default: 10 if no number provided)')
    parser.add_argument('-m', '--max-steps', type=int, default=10,
                      help='Maximum number of steps to run (default: 10)')
    parser.add_argument('--eager-loading', action='store_true',
                      help='Use eager loading (load all tools at startup) instead of dynamic loading')
    parser.add_argument('instruction', nargs='+', help='The instruction for the AI agent')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Join the instruction parts back together
    instruction = ' '.join(args.instruction)
    
    # Initialize commands based on user preference
    dynamic_loading = not args.eager_loading
    print(f"🔧 Initializing tools with {'dynamic' if dynamic_loading else 'eager'} loading...")
    commands.init(dynamic=dynamic_loading)
    
    # Ensure max_steps is at least as large as auto_continue
    max_steps = max(args.max_steps, args.auto) if args.auto > 0 else args.max_steps

    # Create a unique output directory for this run
    base_output_dir = os.path.abspath('output')
    if not os.path.exists(base_output_dir):
        os.makedirs(base_output_dir)
    run_id = str(uuid.uuid4())[:8]
    version_folder = 'v' + '_'.join(AGENT_VERSION.lstrip('v').split('.'))
    run_output_dir = os.path.join(base_output_dir, f"{version_folder}_{run_id}")
    os.makedirs(run_output_dir, exist_ok=True)

    try:
        # Initialize and run the agent with the unique output directory
        agent = SimpleAgent(output_dir=run_output_dir)
        agent.run(instruction, max_steps=max_steps, auto_continue=args.auto)
    finally:
        # Clean up tool manager resources
        commands.cleanup()


if __name__ == "__main__":
    main() 