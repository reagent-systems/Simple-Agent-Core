"""Discord bot integration for SimpleAgent.

This module provides a Discord bot that allows users to interact with SimpleAgent through Discord slash commands.
"""

import os
import discord
from discord import app_commands
from typing import Optional, List
from core.agent import SimpleAgent
from dotenv import load_dotenv
import commands
import glob
import re
import shutil
import time
import traceback
import sys
import asyncio
import builtins
import threading
import queue
from commands import COMMAND_SCHEMAS
import zipfile

# Load environment variables
load_dotenv()

commands.init()

# Get Discord token from environment
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable not set")

# Initialize Discord client with all intents
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Store active SimpleAgent instances and their output directories per thread
agent_instances = {}
output_dirs = {}

# Thread-safe queues for communication
input_queues = {}  # For sending inputs from Discord to SimpleAgent
output_queues = {}  # For sending outputs from SimpleAgent to Discord
current_threads = {}  # Store current thread objects
waiting_for_input = {}  # Track threads that are waiting for input

# Direct flag to process a specific message
direct_process_input = {}  # For sending direct inputs to SimpleAgent

# Constants for Discord limits
EMBED_DESCRIPTION_LIMIT = 4096

def truncate_title(title: str, max_length: int = 100) -> str:
    """Truncate a title to fit Discord's thread name limits."""
    if len(title) <= max_length:
        return title
    
    # Try to truncate at a word boundary
    truncated = title[:max_length-3].rsplit(' ', 1)[0]
    return truncated + "..."

def create_output_dir(thread_id: str) -> str:
    """Create and return a unique output directory for the thread."""
    base_output_dir = os.path.abspath("output")
    if not os.path.exists(base_output_dir):
        os.makedirs(base_output_dir)
        
    output_dir = os.path.join(base_output_dir, f"thread_{thread_id}_{int(time.time())}")
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    print(f"Created output directory: {output_dir}")  # Debug print
    return output_dir

async def send_debug_info(thread: discord.Thread, agent: SimpleAgent):
    """Send debugging information to the thread."""
    debug_embed = discord.Embed(
        title="🔍 Debug Information",
        color=discord.Color.blue()
    )
    
    # Add output directory info
    output_dir = agent.output_dir if hasattr(agent, 'output_dir') else 'Not set'
    output_dir_path = shorten_path(output_dir)
    
    # Handle long paths by truncating if needed - embed fields have a 1024 character limit
    if len(output_dir_path) > 1000:  # Leave some buffer
        output_dir_path = output_dir_path[:997] + "..."
        
    debug_embed.add_field(
        name="Output Directory",
        value=f"```{output_dir_path}```",
        inline=False
    )
    
    # Add directory contents if it exists
    if output_dir and os.path.exists(output_dir):
        contents = os.listdir(output_dir)
        contents_str = ', '.join(contents) if contents else 'Empty'
        
        # Handle long content lists by truncating if needed
        if len(contents_str) > 1000:
            contents_str = contents_str[:997] + "..."
            
        debug_embed.add_field(
            name="Directory Contents",
            value=f"```{contents_str}```",
            inline=False
        )
    else:
        debug_embed.add_field(
            name="Directory Status",
            value="Output directory does not exist",
            inline=False
        )
    
    # Add current working directory
    cwd_path = shorten_path(os.getcwd())
    if len(cwd_path) > 1000:
        cwd_path = cwd_path[:997] + "..."
        
    debug_embed.add_field(
        name="Current Working Directory",
        value=f"```{cwd_path}```",
        inline=False
    )
    
    await thread.send(embed=debug_embed)

async def send_output_files(thread: discord.Thread, output_dir: str):
    """Send all files from the output directory to the thread."""
    if not os.path.exists(output_dir):
        return
        
    # Get all files in the output directory and subdirectories
    files = []
    for filepath in glob.glob(os.path.join(output_dir, "**/*"), recursive=True):
        # Skip memory.json files
        if os.path.isfile(filepath) and not os.path.basename(filepath) == "memory.json":
            files.append(filepath)
    
    if not files:
        # Check if we need to explicitly look for thread-specific files
        thread_id = str(thread.id)
        if not output_dir.endswith(thread_id) and "thread_" not in output_dir:
            # This might be a case where we need to search for thread-specific folder
            thread_specific_dirs = glob.glob(os.path.join(os.path.dirname(output_dir), f"thread_{thread_id}*"))
            for thread_dir in thread_specific_dirs:
                if os.path.exists(thread_dir):
                    # Found a thread-specific directory, search for files there
                    for filepath in glob.glob(os.path.join(thread_dir, "**/*"), recursive=True):
                        # Skip memory.json files
                        if os.path.isfile(filepath) and not os.path.basename(filepath) == "memory.json":
                            files.append(filepath)
        
        # Still no files found
        if not files:
            await thread.send(embed=discord.Embed(
                title="📁 No Files Generated",
                description="No files were created during this session.",
                color=discord.Color.blue()
            ))
            return
    
    # Create an embed for the files overview
    embed = discord.Embed(
        title="📁 Generated Files",
        description=f"Found {len(files)} file(s)",
        color=discord.Color.blue()
    )
    
    # Group files by type/directory for the embed
    file_groups = {}
    for filepath in files:
        dir_name = os.path.dirname(filepath).replace(output_dir, "").lstrip(os.sep) or "root"
        if dir_name not in file_groups:
            file_groups[dir_name] = []
        file_groups[dir_name].append(os.path.basename(filepath))
    
    for dir_name, filenames in file_groups.items():
        # Embed field values are limited to 1024 characters
        files_value = "\n".join(f"📄 {fname}" for fname in filenames)
        
        # If the field value is too long, truncate it
        if len(files_value) > 1000:  # Leave some buffer
            # Count how many files we're showing vs total
            shown_files = 0
            truncated_value = ""
            
            for fname in filenames:
                file_entry = f"📄 {fname}\n"
                if len(truncated_value) + len(file_entry) <= 950:  # Leave room for the message
                    truncated_value += file_entry
                    shown_files += 1
                else:
                    break
            
            # Add a note about truncated files
            truncated_value += f"\n... and {len(filenames) - shown_files} more files"
            files_value = truncated_value
        
        embed.add_field(
            name=f"📂 {dir_name}",
            value=files_value,
            inline=False
        )
    
    await thread.send(embed=embed)

    # If more than 5 files, zip and send the zip
    if len(files) > 5:
        zip_path = os.path.join(output_dir, "all_files.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in files:
                arcname = os.path.relpath(file, output_dir)
                zipf.write(file, arcname=arcname)
        await thread.send(files=[discord.File(zip_path)])
        return

    # Otherwise, send files in batches of up to 10
    batch = []
    for i, file in enumerate(files):
        batch.append(discord.File(file))
        if len(batch) == 10:
            await thread.send(files=batch)
            batch = []
    if batch:
        await thread.send(files=batch)

def split_long_message(message: str, max_length: int = EMBED_DESCRIPTION_LIMIT) -> List[str]:
    """Split a long message into chunks that fit within Discord's embed limits."""
    if len(message) <= max_length:
        return [message]
    
    chunks = []
    # Try to split on paragraph boundaries first
    paragraphs = message.split('\n\n')
    current_chunk = ""
    
    for paragraph in paragraphs:
        # If a single paragraph is too long, we'll need to split it further
        if len(paragraph) > max_length:
            # If current chunk isn't empty, add it to chunks first
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            
            # Split the long paragraph
            for i in range(0, len(paragraph), max_length):
                chunk = paragraph[i:i + max_length]
                chunks.append(chunk)
        else:
            # Check if adding this paragraph would exceed the limit
            if len(current_chunk) + len(paragraph) + 2 > max_length:  # +2 for the newlines
                chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

async def handle_output_queue(thread_id):
    """Process messages from the SimpleAgent output queue and send to Discord."""
    thread = current_threads.get(thread_id)
    if not thread:
        return
    
    while True:
        try:
            # Check if we have a queue and if there's a message
            if thread_id not in output_queues:
                break
                
            try:
                # Use a shorter timeout to prevent blocking the event loop for too long
                # This helps avoid "heartbeat blocked" warnings
                message = output_queues[thread_id].get(block=True, timeout=0.1)
            except queue.Empty:
                # Instead of continuing immediately, yield control back to the event loop
                # This prevents the heartbeat from being blocked
                await asyncio.sleep(0.1)
                continue
                
            if message == "DONE":
                break
                
            # Filter out most debug and heartbeat messages
            if message.startswith("Loop thread traceback") or "heartbeat blocked" in message:
                # Skip these messages entirely - they're just noise
                continue
                
            # Format and send message to Discord
            if message.startswith(("🤖", "📍", "📋", "✅", "❌", "📊", "⚠️", "🏁")):
                # Special formatted message
                emoji = message[0]
                content = message[1:].strip()
                
                title_map = {
                    "🤖": "Assistant Response",
                    "📍": "Status Update",
                    "📋": "Task Progress",
                    "✅": "Success",
                    "❌": "Error",
                    "📊": "Function Details",
                    "⚠️": "Warning",
                    "🏁": "Execution Complete"
                }
                
                title = title_map.get(emoji, "Status Update")
                
                # Set color based on message type
                color = discord.Color.blue()
                if emoji in ["❌", "⚠️"]:
                    color = discord.Color.red()
                elif emoji == "✅":
                    color = discord.Color.green()
                
                # Split long messages
                content_chunks = split_long_message(content)
                
                # Send the first chunk with the title
                embed = discord.Embed(title=title, description=content_chunks[0], color=color)
                await thread.send(embed=embed)
                
                # Send any additional chunks as continuations
                for i, chunk in enumerate(content_chunks[1:], 1):
                    continuation_embed = discord.Embed(
                        title=f"{title} (Part {i+1} of {len(content_chunks)})",
                        description=chunk,
                        color=color
                    )
                    await thread.send(embed=continuation_embed)
                    # Add a small delay between sending multiple chunks to avoid rate limits
                    await asyncio.sleep(0.1)
                
            elif message.startswith("🧑 Enter your next instruction"):
                # Handle input request message
                auto_mode = False
                
                # Check if we have an auto_mode setting (not None and positive)
                if thread_id in agent_instances:
                    agent = agent_instances[thread_id]
                    if hasattr(agent, 'auto_mode') and agent.auto_mode is not None and agent.auto_mode != 0:
                        auto_mode = True
                
                embed = discord.Embed(
                    title="🤔 Input Required",
                    description="Type your response in this thread:\n- Type 'y' to continue with the current task\n- Type 'n' to stop\n- Type anything else as a new instruction",
                    color=discord.Color.yellow()
                )
                await thread.send(embed=embed)
                
                if auto_mode:
                    # Auto-mode: just continue
                    await thread.send(embed=discord.Embed(
                        title="🔄 Auto-Continuing",
                        description="Auto-continue mode is enabled. Continuing automatically.",
                        color=discord.Color.blue()
                    ))
                    input_queues[thread_id].put('y')
                else:
                    # Set flag that we're waiting for input in this thread
                    waiting_for_input[thread_id] = True
                    
                    # Manual mode: wait for user response
                    def check(msg):
                        return msg.channel.id == int(thread_id) and not msg.author.bot
                        
                    try:
                        # Wait for response in the thread - increased timeout to 10 minutes
                        # This helps prevent timeouts when the user takes a bit longer to respond
                        user_msg = await client.wait_for('message', check=check, timeout=600)
                        
                        # Process the message only if we're still waiting for input
                        if thread_id in waiting_for_input and waiting_for_input[thread_id]:
                            # Get the user's response
                            user_response = user_msg.content.strip()
                            
                            # Log the input for debugging
                            print(f"[DEBUG] Got Discord input from wait_for: '{user_response}' - Sending to SimpleAgent")
                            
                            # Mark that we're no longer waiting for input
                            waiting_for_input[thread_id] = False
                            
                            # Confirm receipt with appropriate message based on input
                            if user_response.lower() == 'y':
                                await thread.send(embed=discord.Embed(
                                    title="✅ Continuing",
                                    description="Continuing with the current task...",
                                    color=discord.Color.green()
                                ))
                                # For "y" responses, we set a flag to ensure it's treated as a continue
                                input_queues[thread_id].put('y')
                            elif user_response.lower() == 'n':
                                await thread.send(embed=discord.Embed(
                                    title="🛑 Stopping",
                                    description="Stopping as requested.",
                                    color=discord.Color.red()
                                ))
                                input_queues[thread_id].put('n')
                            else:
                                await thread.send(embed=discord.Embed(
                                    title="✅ Input Received",
                                    description=f"Processing new instruction: `{user_response}`",
                                    color=discord.Color.green()
                                ))
                                input_queues[thread_id].put(user_response)
                        
                    except asyncio.TimeoutError:
                        # Timeout - stop execution
                        await thread.send(embed=discord.Embed(
                            title="⚠️ Timeout",
                            description="No response received within 5 minutes. Stopping execution.",
                            color=discord.Color.red()
                        ))
                        waiting_for_input[thread_id] = False
                        input_queues[thread_id].put('n')
            elif message == "[DEBUG] User input received: 'y'":
                # This is a special debug message that we can silently ignore in the Discord output
                pass
            elif message.startswith("[DEBUG]"):
                # Filter out most debug messages related to user input responses
                # Only show critical debug messages, filter out common verbose ones
                if any(skip_phrase in message for skip_phrase in [
                    "[DEBUG] Waiting for input",
                    "[DEBUG] Set waiting_for_input flag",
                    "[DEBUG] Reset waiting_for_input flag",
                    "[DEBUG] Received input:",
                    "[DEBUG] Normalized response:",
                    "[DEBUG] Continuing with current task based on 'y' input",
                    "[DEBUG] Waiting for new input in queue",
                    "[DEBUG] Got Discord input from wait_for:",
                    "[DEBUG] User input received:",
                    "[DEBUG] Processing thread message:"
                ]) or "thread" in message.lower() or "shard" in message.lower() or "discord.gateway" in message:
                    # Silently ignore these debug messages
                    pass
                else:
                    # Show other debug messages with a special format
                    debug_message_chunks = split_long_message(message)
                    
                    # Send the first chunk with the main title
                    debug_embed = discord.Embed(
                        title="🔍 Debug Info",
                        description=debug_message_chunks[0],
                        color=discord.Color.light_grey()
                    )
                    await thread.send(embed=debug_embed)
                    
                    # Send any additional chunks as continuations
                    for i, chunk in enumerate(debug_message_chunks[1:], 1):
                        continuation_embed = discord.Embed(
                            title=f"🔍 Debug Info (Part {i+1} of {len(debug_message_chunks)})",
                            description=chunk,
                            color=discord.Color.light_grey()
                        )
                        await thread.send(embed=continuation_embed)
                        # Add a small delay between chunks
                        await asyncio.sleep(0.1)
            else:
                # Regular message - split if needed
                message_chunks = split_long_message(message)
                
                # Send the first chunk with the main title
                embed = discord.Embed(
                    title="Output", 
                    description=message_chunks[0],
                    color=discord.Color.blue()
                )
                await thread.send(embed=embed)
                
                # Send any additional chunks as continuations
                for i, chunk in enumerate(message_chunks[1:], 1):
                    continuation_embed = discord.Embed(
                        title=f"Output (Part {i+1} of {len(message_chunks)})",
                        description=chunk,
                        color=discord.Color.blue()
                    )
                    await thread.send(embed=continuation_embed)
                
        except Exception as e:
            print(f"Error in output handler: {str(e)}")
            traceback.print_exc()

def run_SimpleAgent(thread_id, agent, prompt, max_steps, auto_continue):
    """Run SimpleAgent in a separate thread."""
    
    # Store original functions
    original_print = print
    original_input = input
    
    # Custom print function that sends to the output queue
    def custom_print(*args, **kwargs):
        message = " ".join(str(arg) for arg in args)
        if thread_id in output_queues:
            output_queues[thread_id].put(message)
        # Also print to console for debugging
        original_print(*args, **kwargs)
    
    # Custom input function that gets input from the input queue
    def custom_input(prompt_text):
        # Send the prompt to the output queue
        if thread_id in output_queues:
            output_queues[thread_id].put(prompt_text)
            
        # Set the waiting flag to indicate we're expecting input (no debug message)
        if thread_id in waiting_for_input:
            waiting_for_input[thread_id] = True
        
        # Wait for input from Discord
        if thread_id in input_queues:
            try:
                # Empty the queue first to avoid any stale inputs - do this silently
                while not input_queues[thread_id].empty():
                    try:
                        input_queues[thread_id].get_nowait()
                    except queue.Empty:
                        break
                
                # Block until we get a response from the Discord thread - no debug needed here
                # Increase timeout from 10 minutes to 30 minutes to prevent heartbeat timeouts
                user_response = input_queues[thread_id].get(block=True, timeout=1800)  # 30 minute timeout
                
                # Normalize response - no need to log the details
                normalized_response = user_response.strip().lower() if user_response else ''
                
                # Reset waiting flag as we've received input
                if thread_id in waiting_for_input:
                    waiting_for_input[thread_id] = False
                
                # Make sure 'y' and 'n' responses are handled correctly - EXPLICIT COMPARISON
                if normalized_response == 'y':
                    # No logging for 'y' response - this is what we're trying to clean up
                    return 'y'
                elif normalized_response == 'n':
                    # Minimal logging for 'n' - just to console, not to discord
                    return 'n'
                else:
                    # Minimal logging for new instructions - just to console, not to discord
                    return user_response
                
            except queue.Empty:
                # Reset waiting flag as we're no longer waiting
                if thread_id in waiting_for_input:
                    waiting_for_input[thread_id] = False
                return "n"  # Default to stopping if timeout
        
        # Check for direct input processing
        if thread_id in direct_process_input and direct_process_input[thread_id]:
            user_input = direct_process_input[thread_id]
            # Clear the direct input flag
            direct_process_input[thread_id] = None
            
            # Normalize the input without logging
            normalized_input = user_input.strip().lower()
            
            # Handle different input types with minimal logging
            if normalized_input == 'y':
                # No debug for 'y' input - this is the common case
                return 'y'
            elif normalized_input == 'n':
                original_print("[DEBUG] Using direct 'n' input")
                return 'n'
            else:
                original_print(f"[DEBUG] Using direct input as instruction: '{user_input}'")
                return user_input
        
        original_print("[DEBUG] No input queue for thread - defaulting to 'n'")
        # Reset waiting flag
        if thread_id in waiting_for_input:
            waiting_for_input[thread_id] = False
        return "n"  # Default to stopping if something is wrong
    
    try:
        # Replace functions
        builtins.print = custom_print
        builtins.input = custom_input
        
        # Run the agent - ensure auto_continue is None or an integer
        if auto_continue == '':
            auto_continue = None
            
        # Additional debug info
        custom_print(f"Starting SimpleAgent with auto_continue={auto_continue}, max_steps={max_steps}")
        
        # Run the agent
        agent.run(prompt, max_steps=max_steps, auto_continue=auto_continue)
        
    except Exception as e:
        custom_print(f"❌ Error in SimpleAgent execution: {str(e)}")
        traceback.print_exc()
    finally:
        # Reset waiting flag at the end
        if thread_id in waiting_for_input:
            waiting_for_input[thread_id] = False
            
        # Restore original functions
        builtins.print = original_print
        builtins.input = original_input
        
        # Signal completion to output handler
        if thread_id in output_queues:
            output_queues[thread_id].put("DONE")

@tree.command(
    name="simpleagent",
    description="Run a SimpleAgent command (use without auto parameter for manual mode with user interaction)"
)
async def simpleagent(
    interaction: discord.Interaction,
    prompt: str,
    auto: Optional[int] = None,  # Optional auto-continue steps
    max_steps: Optional[int] = 10
):
    """Execute a SimpleAgent command."""
    # Defer the response since it might take a while
    await interaction.response.defer()
    
    try:
        # Create thread for this execution
        thread_name = truncate_title(prompt)
        thread = await interaction.channel.create_thread(
            name=thread_name,
            type=discord.ChannelType.public_thread,
            reason="SimpleAgent execution"
        )
        
        # Add the user to the thread
        await thread.add_user(interaction.user)
        
        # Create initial embed
        start_embed = discord.Embed(
            title="🤖 SimpleAgent Execution Started",
            description=prompt,
            color=discord.Color.blue()
        )
        
        # Update auto-continue field based on mode
        if auto is not None:
            start_embed.add_field(name="Auto-continue", value=f"{auto} steps")
        else:
            start_embed.add_field(name="Mode", value="Manual (interactive)")
            
        start_embed.add_field(name="Max Steps", value=str(max_steps))
        start_embed.set_footer(text=f"Thread ID: {thread.id}")
        
        # Send initial message to thread
        await thread.send(f"{interaction.user.mention}", embed=start_embed)
        
        # Create output directory for this thread
        thread_id = str(thread.id)
        output_dir = create_output_dir(thread_id)
        output_dirs[thread_id] = output_dir
        
        # Send status message about directory creation
        dir_embed = discord.Embed(
            title="📁 Output Directory Created",
            description=f"Created directory for outputs at:\n```{shorten_path(output_dir)}```",
            color=discord.Color.blue()
        )
        await thread.send(embed=dir_embed)
        
        # Create or get SimpleAgent instance for this thread
        if thread_id not in agent_instances:
            agent_instances[thread_id] = SimpleAgent(output_dir=output_dir)
            setup_embed = discord.Embed(
                title="🔧 SimpleAgent Instance Created",
                description="Created new SimpleAgent instance for this thread",
                color=discord.Color.blue()
            )
            await thread.send(embed=setup_embed)
        else:
            setup_embed = discord.Embed(
                title="🔄 SimpleAgent Instance Reused",
                description="Using existing SimpleAgent instance for this thread",
                color=discord.Color.blue()
            )
            await thread.send(embed=setup_embed)
        
        agent = agent_instances[thread_id]
        # Set the output directory for this instance - IMPORTANT: This ensures all file operations
        # happen in the thread-specific directory
        agent.output_dir = output_dir
        # Store the original output directory in case we need to send files later
        output_dirs[thread_id] = output_dir
        
        # Log that we're using a thread-specific directory
        dir_info_embed = discord.Embed(
            title="🔄 Thread Directory Set",
            description=f"All files will be saved in thread-specific directory: \n```{shorten_path(output_dir)}```",
            color=discord.Color.blue()
        )
        await thread.send(embed=dir_info_embed)
        
        # Store auto mode setting with the agent - use exactly the value provided
        agent.auto_mode = auto
        
        # Send debug info before running
        await send_debug_info(thread, agent)
        
        # Set up communication queues
        input_queues[thread_id] = queue.Queue()
        output_queues[thread_id] = queue.Queue()
        current_threads[thread_id] = thread
        waiting_for_input[thread_id] = False  # Initialize waiting state
        
        # Check and clear any existing queues to prevent stale data
        while not input_queues[thread_id].empty():
            try:
                input_queues[thread_id].get_nowait()
            except queue.Empty:
                break
        
        while not output_queues[thread_id].empty():
            try:
                output_queues[thread_id].get_nowait()
            except queue.Empty:
                break
        
        # Start output handler
        output_handler_task = asyncio.create_task(handle_output_queue(thread_id))
        
        # Start SimpleAgent in a separate thread
        agent_thread = threading.Thread(
            target=run_SimpleAgent,
            args=(thread_id, agent, prompt, max_steps, auto)  # Pass auto as is (None or integer)
        )
        agent_thread.daemon = True  # Allow the thread to be terminated when main program exits
        agent_thread.start()
        
        # Wait for SimpleAgent to finish
        while agent_thread.is_alive():
            await asyncio.sleep(1)
            
        # Wait for output handler to finish
        await output_handler_task
        
        # Clean up
        if thread_id in input_queues:
            del input_queues[thread_id]
        if thread_id in output_queues:
            del output_queues[thread_id]
        
        # Send debug info after running
        await send_debug_info(thread, agent)
        
        # Send any generated files - make sure we're using the correct directory
        if thread_id in output_dirs:
            # Use the stored output directory for this thread
            thread_output_dir = output_dirs[thread_id]
            print(f"Sending files from thread output directory: {thread_output_dir}")
            await send_output_files(thread, thread_output_dir)
        else:
            # Fallback to the agent's output directory
            print(f"Sending files from agent output directory: {agent.output_dir}")
            await send_output_files(thread, agent.output_dir)
        
        # Create completion embed
        complete_embed = discord.Embed(
            title="✅ SimpleAgent Execution Completed",
            color=discord.Color.green()
        )
        await thread.send(embed=complete_embed)
        
        # Send completion message in original channel
        await interaction.followup.send(
            embed=discord.Embed(
                title="✅ Execution Completed",
                description=f"Check the thread: {thread.jump_url}",
                color=discord.Color.green()
            )
        )
        
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ Error Occurred",
            description=str(e),
            color=discord.Color.red()
        )
        
        # Add traceback information
        tb = traceback.format_exception(type(e), e, e.__traceback__)
        # Clean up paths in traceback
        cleaned_tb = []
        for line in tb[-3:]:
            if ":\\" in line or "/" in line:
                parts = line.split('"')
                for i, part in enumerate(parts):
                    if ":\\" in part or "/" in part:
                        parts[i] = shorten_path(part)
                line = '"'.join(parts)
            cleaned_tb.append(line)
            
        error_details = ''.join(cleaned_tb)
        
        # Check if error details are too long for a single field
        if len(error_details) > 1000:
            # Split the traceback into chunks
            error_chunks = split_long_message(error_details, 1000)
            
            # Add first chunk to the error embed
            error_embed.add_field(
                name="Error Details",
                value=f"```python\n{error_chunks[0]}\n```",
                inline=False
            )
            
            # Add additional chunks as separate fields
            for i, chunk in enumerate(error_chunks[1:], 1):
                error_embed.add_field(
                    name=f"Error Details (continued {i})",
                    value=f"```python\n{chunk}\n```",
                    inline=False
                )
        else:
            error_embed.add_field(
                name="Error Details",
                value=f"```python\n{error_details}\n```",
                inline=False
            )
        
        if 'thread' in locals():
            if 'agent' in locals():
                await send_debug_info(thread, agent)
            await thread.send(embed=error_embed)
        await interaction.followup.send(embed=error_embed)

@tree.command(
    name="reset_agent",
    description="Reset the SimpleAgent instance for this thread"
)
async def reset_agent(interaction: discord.Interaction):
    """Reset the SimpleAgent instance for the current thread."""
    # Check if we're in a thread
    if not isinstance(interaction.channel, discord.Thread):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Invalid Channel",
                description="This command can only be used in a SimpleAgent thread.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
        return
        
    thread_id = str(interaction.channel.id)
    if thread_id in agent_instances:
        # Clean up instance and output directory
        del agent_instances[thread_id]
        if thread_id in output_dirs:
            output_dir = output_dirs[thread_id]
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
            del output_dirs[thread_id]
            
        # Clean up queues
        if thread_id in input_queues:
            del input_queues[thread_id]
        if thread_id in output_queues:
            del output_queues[thread_id]
        if thread_id in current_threads:
            del current_threads[thread_id]
            
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🔄 Reset Complete",
                description="SimpleAgent instance has been reset for this thread.",
                color=discord.Color.blue()
            )
        )
    else:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="ℹ️ No Instance Found",
                description="No SimpleAgent instance exists for this thread.",
                color=discord.Color.orange()
            )
        )

async def handle_thread_message(thread_id, user_message):
    """Process a user message from a thread and send it to SimpleAgent."""
    try:
        if thread_id not in input_queues or thread_id not in current_threads:
            return False
            
        user_response = user_message.content.strip()
        thread = current_threads[thread_id]
        
        # Normalize the response for comparison
        normalized_response = user_response.strip().lower()
        
        # Mark that we're no longer waiting for input
        if thread_id in waiting_for_input:
            waiting_for_input[thread_id] = False
        
        # Process the response with minimal logging
        if thread_id in input_queues:
            # IMPORTANT: Do direct string comparison to ensure exact matching
            if normalized_response == "y":
                # Don't log for 'y' input
                await thread.send(embed=discord.Embed(
                    title="✅ Continuing",
                    description="Continuing with the current task...",
                    color=discord.Color.green()
                ))
                
                # Make sure to clear the queue first to prevent stale inputs
                while not input_queues[thread_id].empty():
                    try:
                        input_queues[thread_id].get_nowait()
                    except queue.Empty:
                        break
                        
                # Now add our 'y' input with priority
                input_queues[thread_id].put('y')
                return True
            elif normalized_response == "n":
                await thread.send(embed=discord.Embed(
                    title="🛑 Stopping",
                    description="Stopping as requested.",
                    color=discord.Color.red()
                ))
                input_queues[thread_id].put('n')
                return True
            else:
                await thread.send(embed=discord.Embed(
                    title="✅ Input Received",
                    description=f"Processing new instruction: `{user_response}`",
                    color=discord.Color.green()
                ))
                input_queues[thread_id].put(user_response)
                return True
    except Exception as e:
        # Log any errors but don't crash
        print(f"Error in handle_thread_message: {e}")
        traceback.print_exc()
    
    return False

@client.event
async def on_message(message):
    """Handle messages sent in threads to pass to SimpleAgent."""
    # Don't process messages from bots (including self)
    if message.author.bot:
        return
        
    # Check if the message is in a thread
    if isinstance(message.channel, discord.Thread):
        thread_id = str(message.channel.id)
        
        # Check if this is an active thread with a SimpleAgent instance
        if thread_id not in agent_instances:
            return
        
        # For y/n responses, create a temporary typing indicator to show the bot is processing
        # This helps with the perception of responsiveness
        user_input = message.content.strip().lower()
        if user_input == 'y' or user_input == 'n':
            async with message.channel.typing():
                # Set flag to force processing this input
                direct_process_input[thread_id] = message.content.strip()
                
                # Add the input directly to the input queue as well, with priority
                # First clear the queue to avoid any synchronization issues
                if thread_id in input_queues:
                    # Clear existing items to prevent out-of-sync responses
                    while not input_queues[thread_id].empty():
                        try:
                            input_queues[thread_id].get_nowait()
                        except queue.Empty:
                            break
                    
                    # Now add our input, ensuring it's lowercase for y/n
                    input_queues[thread_id].put(user_input)
                
                # Process the message immediately for these simple responses
                await handle_thread_message(thread_id, message)
        else:
            # For other responses, normal processing
            # Set flag to force processing this input
            direct_process_input[thread_id] = message.content.strip()
            
            # Add the input directly to the input queue as well
            if thread_id in input_queues:
                # Make sure we're using lowercase for 'y' and 'n' comparison
                if user_input == 'y' or user_input == 'n':
                    # Force consistent format for y/n responses
                    input_queues[thread_id].put(user_input)
                else:
                    input_queues[thread_id].put(message.content.strip())
            
            # Process the message
            processed = await handle_thread_message(thread_id, message)
            
            # If we didn't process it but we're waiting for input, try again
            # This is for backward compatibility with the waiting_for_input flag
            if not processed and thread_id in waiting_for_input and waiting_for_input[thread_id]:
                await handle_thread_message(thread_id, message)

@client.event
async def on_ready():
    """Called when the bot is ready."""
    print(f"Logged in as {client.user}")
    # Sync commands with Discord
    await tree.sync()
    print("Commands synced!")

def shorten_path(path: str, max_length: int = 50) -> str:
    """Shorten a file path for display while keeping important parts."""
    if len(path) <= max_length:
        return path
        
    parts = path.split(os.sep)
    if len(parts) <= 2:
        return path
        
    # Keep the first and last two parts
    shortened = os.path.join(parts[0], "...", *parts[-2:])
    return shortened

def cleanup_old_thread_dirs(max_age_days=7):
    """Clean up thread directories older than the specified age."""
    try:
        base_output_dir = os.path.abspath("output")
        if not os.path.exists(base_output_dir):
            return
            
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        # Find all thread directories
        thread_dirs = []
        for item in os.listdir(base_output_dir):
            if item.startswith("thread_") and os.path.isdir(os.path.join(base_output_dir, item)):
                thread_dirs.append(os.path.join(base_output_dir, item))
        
        # Check age and remove old directories
        for thread_dir in thread_dirs:
            # Try to extract timestamp from directory name
            try:
                # Format: thread_ID_TIMESTAMP
                dir_name = os.path.basename(thread_dir)
                timestamp_str = dir_name.split("_")[-1]
                timestamp = int(timestamp_str)
                
                # Check if directory is older than max age
                if current_time - timestamp > max_age_seconds:
                    print(f"Cleaning up old thread directory: {thread_dir}")
                    shutil.rmtree(thread_dir, ignore_errors=True)
            except (IndexError, ValueError):
                # If we can't parse the timestamp, check file modification time
                try:
                    dir_mtime = os.path.getmtime(thread_dir)
                    if current_time - dir_mtime > max_age_seconds:
                        print(f"Cleaning up old thread directory (by mtime): {thread_dir}")
                        shutil.rmtree(thread_dir, ignore_errors=True)
                except Exception as e:
                    print(f"Error checking directory age: {e}")
    except Exception as e:
        print(f"Error in cleanup_old_thread_dirs: {e}")

def run_bot():
    """Run the Discord bot."""
    cleanup_old_thread_dirs()  # Clean up old directories on startup
    client.run(DISCORD_TOKEN)

@tree.command(
    name="process_message",
    description="Force the bot to process a message in a thread"
)
async def process_message(
    interaction: discord.Interaction,
    message: str,
    as_y: bool = False
):
    """Force the bot to process a specific message."""
    # Check if we're in a thread
    if not isinstance(interaction.channel, discord.Thread):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Invalid Channel",
                description="This command can only be used in a SimpleAgent thread.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
        return
        
    thread_id = str(interaction.channel.id)
    
    # Check if this thread has a SimpleAgent instance
    if thread_id not in input_queues or thread_id not in current_threads:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ No Active Instance",
                description="There is no active SimpleAgent instance for this thread.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
        return
    
    # Process the message
    if as_y:
        input_message = 'y'
        description = "Sending 'y' to continue with current task"
    else:
        input_message = message
        description = f"Processing message: `{message}`"
    
    # Add to input queue
    input_queues[thread_id].put(input_message)
    
    # Set direct processing flag
    direct_process_input[thread_id] = input_message
    
    # Mark that we're no longer waiting for input
    if thread_id in waiting_for_input:
        waiting_for_input[thread_id] = False
    
    # Send confirmation
    await interaction.response.send_message(
        embed=discord.Embed(
            title="✅ Message Processed",
            description=description,
            color=discord.Color.green()
        ),
        ephemeral=True
    )

@tree.command(
    name="stop_agent",
    description="Stop the currently running SimpleAgent agent in this thread"
)
async def stop_agent(interaction: discord.Interaction):
    """Stop the running SimpleAgent agent in the current thread."""
    # Check if we're in a thread
    if not isinstance(interaction.channel, discord.Thread):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Invalid Channel",
                description="This command can only be used in a SimpleAgent thread.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
        return
        
    thread_id = str(interaction.channel.id)
    if thread_id in agent_instances:
        agent = agent_instances[thread_id]
        
        # Request the agent to stop
        if hasattr(agent, 'request_stop'):
            agent.request_stop()
            
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="🛑 Stop Requested",
                    description="SimpleAgent agent has been requested to stop. It will halt at the next convenient point.",
                    color=discord.Color.orange()
                )
            )
            
            # Also send a message to the thread for better visibility
            await interaction.channel.send(
                embed=discord.Embed(
                    title="🛑 Agent Stopping",
                    description=f"Stop requested by {interaction.user.mention}. The agent will stop at the next step.",
                    color=discord.Color.orange()
                )
            )
            
            # If there's a waiting input queue, add an 'n' response to break out
            if thread_id in waiting_for_input and waiting_for_input[thread_id]:
                if thread_id in input_queues:
                    input_queues[thread_id].put('n')
                waiting_for_input[thread_id] = False
                
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="⚠️ Unable to Stop",
                    description="This agent doesn't support the stop command. Try using /reset_agent instead.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
    else:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="ℹ️ No Agent Running",
                description="No SimpleAgent agent is currently running in this thread.",
                color=discord.Color.blue()
            ),
            ephemeral=True
        )

@tree.command(
    name="list_tools",
    description="List all available tools (commands) with their descriptions"
)
async def list_tools(interaction: discord.Interaction):
    """List all registered tools/commands as a pretty, readable embed with one field per tool."""
    await interaction.response.defer(ephemeral=True)  # Defer, so Discord doesn't show 'Failed to reply'
    await interaction.followup.send("Tools sent to channel!", ephemeral=True)  # Quick ephemeral confirmation

    if not COMMAND_SCHEMAS:
        await interaction.channel.send(
            embed=discord.Embed(
                title="No Tools Registered",
                description="No tools (commands) are currently registered.",
                color=discord.Color.red()
            )
        )
        return
    
    # Discord embed field limit is 25 fields per embed
    MAX_FIELDS = 25
    embeds = []
    part = 1
    current_embed = discord.Embed(
        title=f"🛠️ Available Tools (Part {part})",
        color=discord.Color.blurple()
    )
    field_count = 0
    for i, schema in enumerate(COMMAND_SCHEMAS):
        func = schema.get("function", {})
        name = func.get("name", "<unknown>")
        desc = func.get("description", "No description available.")
        # Truncate description if too long for a field
        if len(desc) > 1000:
            desc = desc[:997] + "..."
        current_embed.add_field(name=f"`{name}`", value=desc, inline=False)
        field_count += 1
        if field_count == MAX_FIELDS:
            current_embed.set_footer(text=f"Use these tool names in your instructions! | Part {part}")
            embeds.append(current_embed)
            part += 1
            current_embed = discord.Embed(
                title=f"🛠️ Available Tools (Part {part})",
                color=discord.Color.blurple()
            )
            field_count = 0
    if field_count > 0:
        current_embed.set_footer(text="Use these tool names in your instructions!" + (f" | Part {part}" if part > 1 else ""))
        embeds.append(current_embed)
    for embed in embeds:
        await interaction.channel.send(embed=embed)

if __name__ == "__main__":
    run_bot() 