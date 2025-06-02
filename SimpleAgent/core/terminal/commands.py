"""
Terminal Commands for SimpleAgent - Simplified Version

This module provides command schemas and implementations for terminal operations.
These commands are integrated into the tool system and provide a clean interface
for terminal control, including interactive session management.
"""

from typing import Dict, Any, Optional
from .terminal_manager import get_terminal_manager, TerminalResult
import time


def execute_command(
    command: str,
    timeout: Optional[float] = 30,
    background: bool = False,
    session_id: Optional[str] = None
) -> str:
    """
    Execute a terminal command.
    
    Args:
        command: The command to execute
        timeout: Maximum execution time in seconds (default: 30)
        background: Whether to run in background (default: False)
        session_id: Terminal session to use (optional, uses default if not specified)
    
    Returns:
        Formatted result of the command execution
    """
    terminal_manager = get_terminal_manager()
    
    try:
        result = terminal_manager.execute_command(
            command=command,
            timeout=timeout,
            background=background,
            session_id=session_id
        )
        
        # Format the result for the agent
        output_parts = []
        
        if result.background:
            output_parts.append(f"✅ Command started in background (PID: {result.pid})")
            output_parts.append(f"Command: {command}")
        else:
            output_parts.append(f"✅ Command executed (Exit code: {result.exit_code})")
            output_parts.append(f"Command: {command}")
            output_parts.append(f"Execution time: {result.execution_time:.2f}s")
        
        if result.stdout:
            output_parts.append("\n📤 Output:")
            output_parts.append(result.stdout)
        
        if result.stderr and result.exit_code != 0:
            output_parts.append("\n❌ Error:")
            output_parts.append(result.stderr)
        elif result.stderr:
            output_parts.append("\n⚠️ Warning:")
            output_parts.append(result.stderr)
        
        return "\n".join(output_parts)
    
    except Exception as e:
        return f"❌ Error executing command: {str(e)}"


def start_interactive_session(
    command: str,
    session_id: Optional[str] = None,
    interactive_session_name: str = "default"
) -> str:
    """
    Start an interactive terminal session for commands with menus or prompts.
    
    Args:
        command: The interactive command to start (e.g., 'wsl', 'firebase init')
        session_id: Terminal session to use (optional)
        interactive_session_name: Name for the interactive session (default: 'default')
    
    Returns:
        Status message about starting the interactive session
    """
    terminal_manager = get_terminal_manager()
    
    try:
        success = terminal_manager.start_interactive_session(
            command=command,
            session_id=session_id,
            interactive_session_name=interactive_session_name
        )
        
        if success:
            return f"✅ Started interactive session '{interactive_session_name}' with command: {command}\n" \
                   f"Use 'send_to_interactive_session' to send commands and 'get_interactive_session_output' to check output."
        else:
            return f"❌ Failed to start interactive session with command: {command}"
    
    except Exception as e:
        return f"❌ Error starting interactive session: {str(e)}"


def send_to_interactive_session(
    input_text: str,
    session_id: Optional[str] = None,
    interactive_session_name: str = "default"
) -> str:
    """
    Send specific input to an interactive session.
    
    Args:
        input_text: Text to send to the interactive session
        session_id: Terminal session to use (optional)
        interactive_session_name: Name of the interactive session (default: 'default')
    
    Returns:
        Output received after sending the input
    """
    terminal_manager = get_terminal_manager()
    
    try:
        output = terminal_manager.send_to_interactive_session(
            input_text=input_text,
            session_id=session_id,
            interactive_session_name=interactive_session_name
        )
        
        return f"📤 Sent: {input_text.strip()}\n📥 Output:\n{output}"
    
    except Exception as e:
        return f"❌ Error sending input: {str(e)}"


def get_interactive_session_output(
    session_id: Optional[str] = None,
    interactive_session_name: str = "default"
) -> str:
    """
    Get current output from an interactive session without sending input.
    
    Args:
        session_id: Terminal session to use (optional)
        interactive_session_name: Name of the interactive session (default: 'default')
    
    Returns:
        Current output from the interactive session
    """
    terminal_manager = get_terminal_manager()
    
    try:
        output = terminal_manager.get_interactive_session_output(
            session_id=session_id,
            interactive_session_name=interactive_session_name
        )
        
        return f"📺 Current output:\n{output}"
    
    except Exception as e:
        return f"❌ Error getting session output: {str(e)}"


def terminate_interactive_session(
    session_id: Optional[str] = None,
    interactive_session_name: str = "default"
) -> str:
    """
    Terminate an interactive session.
    
    Args:
        session_id: Terminal session to use (optional)
        interactive_session_name: Name of the interactive session (default: 'default')
    
    Returns:
        Status message about termination
    """
    terminal_manager = get_terminal_manager()
    
    try:
        result = terminal_manager.terminate_interactive_session(
            session_id=session_id,
            interactive_session_name=interactive_session_name
        )
        
        return result
    
    except Exception as e:
        return f"❌ Error terminating interactive session: {str(e)}"


def list_interactive_sessions(session_id: Optional[str] = None) -> str:
    """
    List all interactive sessions in a terminal session.
    
    Args:
        session_id: Terminal session to check (optional)
    
    Returns:
        List of interactive sessions
    """
    terminal_manager = get_terminal_manager()
    
    try:
        session = terminal_manager.get_session(session_id)
        sessions = session.list_interactive_sessions()
        
        if not sessions:
            return "📋 No active interactive sessions"
        
        output_parts = ["📋 Active interactive sessions:"]
        for sess in sessions:
            status = "🟢 Active" if sess['alive'] else "🔴 Inactive"
            output_parts.append(
                f"  • {sess['name']}: {status} "
                f"({sess['commands']} commands executed)"
            )
        
        return "\n".join(output_parts)
    
    except Exception as e:
        return f"❌ Error listing interactive sessions: {str(e)}"


def list_sessions() -> str:
    """
    List all active terminal sessions.
    
    Returns:
        List of active terminal sessions
    """
    terminal_manager = get_terminal_manager()
    
    try:
        sessions = terminal_manager.list_sessions()
        
        if not sessions:
            return "📋 No active terminal sessions"
        
        output_parts = ["📋 Active terminal sessions:"]
        for session_id in sessions:
            session = terminal_manager.get_session(session_id)
            interactive_count = len(session.interactive_sessions)
            output_parts.append(
                f"  • {session_id} (Working dir: {session.working_dir}, "
                f"Interactive sessions: {interactive_count})"
            )
        
        return "\n".join(output_parts)
    
    except Exception as e:
        return f"❌ Error listing sessions: {str(e)}"


def send_key_to_interactive_session(
    key: str,
    session_id: Optional[str] = None,
    interactive_session_name: str = "default"
) -> str:
    """
    Send special keys like arrow keys, Enter, etc. to an interactive session.
    
    Args:
        key: Special key to send ('up', 'down', 'left', 'right', 'enter', 'tab', 'escape', 'space', 'ctrl+c')
        session_id: Terminal session to use (optional)
        interactive_session_name: Name of the interactive session (default: 'default')
    
    Returns:
        Output received after sending the key
    """
    terminal_manager = get_terminal_manager()
    
    try:
        output = terminal_manager.send_key_to_interactive_session(
            key=key,
            session_id=session_id,
            interactive_session_name=interactive_session_name
        )
        
        return f"🔑 Sent key: {key}\n📥 Output:\n{output}"
    
    except Exception as e:
        return f"❌ Error sending key: {str(e)}"


def send_arrow_to_interactive_session(
    direction: str,
    session_id: Optional[str] = None,
    interactive_session_name: str = "default"
) -> str:
    """
    Send arrow key to navigate menus in interactive session.
    
    Args:
        direction: Arrow direction ('up', 'down', 'left', 'right')
        session_id: Terminal session to use (optional)
        interactive_session_name: Name of the interactive session (default: 'default')
    
    Returns:
        Output received after sending the arrow key
    """
    terminal_manager = get_terminal_manager()
    
    try:
        output = terminal_manager.send_arrow_to_interactive_session(
            direction=direction,
            session_id=session_id,
            interactive_session_name=interactive_session_name
        )
        
        return f"⬆️⬇️⬅️➡️ Sent arrow: {direction}\n📥 Output:\n{output}"
    
    except Exception as e:
        return f"❌ Error sending arrow key: {str(e)}"


def send_enter_to_interactive_session(
    session_id: Optional[str] = None,
    interactive_session_name: str = "default"
) -> str:
    """
    Send Enter key to confirm selection in interactive session.
    
    Args:
        session_id: Terminal session to use (optional)
        interactive_session_name: Name of the interactive session (default: 'default')
    
    Returns:
        Output received after sending Enter
    """
    terminal_manager = get_terminal_manager()
    
    try:
        output = terminal_manager.send_enter_to_interactive_session(
            session_id=session_id,
            interactive_session_name=interactive_session_name
        )
        
        return f"↩️ Sent Enter key\n📥 Output:\n{output}"
    
    except Exception as e:
        return f"❌ Error sending Enter key: {str(e)}"


def navigate_interactive_session_menu(
    option_index: int,
    session_id: Optional[str] = None,
    interactive_session_name: str = "default"
) -> str:
    """
    Navigate to a specific menu option by index (0-based) in interactive session.
    
    Args:
        option_index: Index of the menu option to navigate to (0-based)
        session_id: Terminal session to use (optional)
        interactive_session_name: Name of the interactive session (default: 'default')
    
    Returns:
        Output received after navigation
    """
    terminal_manager = get_terminal_manager()
    
    try:
        output = terminal_manager.navigate_interactive_session_menu(
            option_index=option_index,
            session_id=session_id,
            interactive_session_name=interactive_session_name
        )
        
        return f"🧭 Navigated to menu option {option_index}\n📥 Output:\n{output}"
    
    except Exception as e:
        return f"❌ Error navigating menu: {str(e)}"


def select_interactive_session_menu_option(
    option_index: int,
    session_id: Optional[str] = None,
    interactive_session_name: str = "default"
) -> str:
    """
    Navigate to and select a specific menu option by index (0-based) in interactive session.
    
    Args:
        option_index: Index of the menu option to select (0-based)
        session_id: Terminal session to use (optional)
        interactive_session_name: Name of the interactive session (default: 'default')
    
    Returns:
        Output received after selection
    """
    terminal_manager = get_terminal_manager()
    
    try:
        output = terminal_manager.select_interactive_session_menu_option(
            option_index=option_index,
            session_id=session_id,
            interactive_session_name=interactive_session_name
        )
        
        return f"✅ Selected menu option {option_index}\n📥 Output:\n{output}"
    
    except Exception as e:
        return f"❌ Error selecting menu option: {str(e)}"


# Simplified command schemas for the tool system
EXECUTE_COMMAND_SCHEMA = {
    "type": "function",
    "function": {
        "name": "execute_command",
        "description": "Execute a terminal/shell command. Supports background processes and persistent sessions.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The command to execute (e.g., 'ls -la', 'git status', 'npm install')"
                },
                "timeout": {
                    "type": "number",
                    "description": "Maximum execution time in seconds (default: 30)",
                    "default": 30
                },
                "background": {
                    "type": "boolean", 
                    "description": "Whether to run the command in background (default: false)",
                    "default": False
                },
                "session_id": {
                    "type": "string",
                    "description": "Terminal session ID to use (optional, uses default session if not specified)"
                }
            },
            "required": ["command"]
        }
    }
}

START_INTERACTIVE_SESSION_SCHEMA = {
    "type": "function",
    "function": {
        "name": "start_interactive_session",
        "description": "Start an interactive terminal session for commands that need ongoing interaction.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The interactive command to start (e.g., 'wsl', 'firebase init', 'python')"
                },
                "session_id": {
                    "type": "string",
                    "description": "Terminal session ID to use (optional)"
                },
                "interactive_session_name": {
                    "type": "string",
                    "description": "Name for this interactive session (default: 'default')",
                    "default": "default"
                }
            },
            "required": ["command"]
        }
    }
}

SEND_TO_INTERACTIVE_SESSION_SCHEMA = {
    "type": "function",
    "function": {
        "name": "send_to_interactive_session",
        "description": "Send input to an active interactive session.",
        "parameters": {
            "type": "object",
            "properties": {
                "input_text": {
                    "type": "string",
                    "description": "Text to send to the interactive session"
                },
                "session_id": {
                    "type": "string",
                    "description": "Terminal session ID (optional)"
                },
                "interactive_session_name": {
                    "type": "string",
                    "description": "Name of the interactive session (default: 'default')",
                    "default": "default"
                }
            },
            "required": ["input_text"]
        }
    }
}

GET_INTERACTIVE_SESSION_OUTPUT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_interactive_session_output",
        "description": "Get current output from an interactive session without sending any input.",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Terminal session ID (optional)"
                },
                "interactive_session_name": {
                    "type": "string",
                    "description": "Name of the interactive session (default: 'default')",
                    "default": "default"
                }
            },
            "required": []
        }
    }
}

TERMINATE_INTERACTIVE_SESSION_SCHEMA = {
    "type": "function",
    "function": {
        "name": "terminate_interactive_session",
        "description": "Terminate an interactive session when you're done with it.",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Terminal session ID (optional)"
                },
                "interactive_session_name": {
                    "type": "string",
                    "description": "Name of the interactive session (default: 'default')",
                    "default": "default"
                }
            },
            "required": []
        }
    }
}

LIST_INTERACTIVE_SESSIONS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "list_interactive_sessions",
        "description": "List all active interactive sessions.",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Terminal session ID (optional)"
                }
            },
            "required": []
        }
    }
}

LIST_SESSIONS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "list_sessions",
        "description": "List all active terminal sessions",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}

SEND_KEY_TO_INTERACTIVE_SESSION_SCHEMA = {
    "type": "function",
    "function": {
        "name": "send_key_to_interactive_session",
        "description": "Send special keys like arrow keys, Enter, etc. to navigate interactive CLI menus.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Special key to send ('up', 'down', 'left', 'right', 'enter', 'tab', 'escape', 'space', 'ctrl+c')"
                },
                "session_id": {
                    "type": "string",
                    "description": "Terminal session ID (optional)"
                },
                "interactive_session_name": {
                    "type": "string",
                    "description": "Name of the interactive session (default: 'default')",
                    "default": "default"
                }
            },
            "required": ["key"]
        }
    }
}

SEND_ARROW_TO_INTERACTIVE_SESSION_SCHEMA = {
    "type": "function",
    "function": {
        "name": "send_arrow_to_interactive_session",
        "description": "Send arrow key to navigate menus in interactive CLI applications.",
        "parameters": {
            "type": "object",
            "properties": {
                "direction": {
                    "type": "string",
                    "description": "Arrow direction ('up', 'down', 'left', 'right')"
                },
                "session_id": {
                    "type": "string",
                    "description": "Terminal session ID (optional)"
                },
                "interactive_session_name": {
                    "type": "string",
                    "description": "Name of the interactive session (default: 'default')",
                    "default": "default"
                }
            },
            "required": ["direction"]
        }
    }
}

SEND_ENTER_TO_INTERACTIVE_SESSION_SCHEMA = {
    "type": "function",
    "function": {
        "name": "send_enter_to_interactive_session",
        "description": "Send Enter key to confirm selection in interactive CLI menu.",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Terminal session ID (optional)"
                },
                "interactive_session_name": {
                    "type": "string",
                    "description": "Name of the interactive session (default: 'default')",
                    "default": "default"
                }
            },
            "required": []
        }
    }
}

NAVIGATE_INTERACTIVE_SESSION_MENU_SCHEMA = {
    "type": "function",
    "function": {
        "name": "navigate_interactive_session_menu",
        "description": "Navigate to a specific menu option by index (0-based) without selecting it.",
        "parameters": {
            "type": "object",
            "properties": {
                "option_index": {
                    "type": "integer",
                    "description": "Index of the menu option to navigate to (0-based)"
                },
                "session_id": {
                    "type": "string",
                    "description": "Terminal session ID (optional)"
                },
                "interactive_session_name": {
                    "type": "string",
                    "description": "Name of the interactive session (default: 'default')",
                    "default": "default"
                }
            },
            "required": ["option_index"]
        }
    }
}

SELECT_INTERACTIVE_SESSION_MENU_OPTION_SCHEMA = {
    "type": "function",
    "function": {
        "name": "select_interactive_session_menu_option",
        "description": "Navigate to and select a specific menu option by index (0-based) in one operation.",
        "parameters": {
            "type": "object",
            "properties": {
                "option_index": {
                    "type": "integer",
                    "description": "Index of the menu option to select (0-based)"
                },
                "session_id": {
                    "type": "string",
                    "description": "Terminal session ID (optional)"
                },
                "interactive_session_name": {
                    "type": "string",
                    "description": "Name of the interactive session (default: 'default')",
                    "default": "default"
                }
            },
            "required": ["option_index"]
        }
    }
}


def register_terminal_commands():
    """Register core terminal commands with the tool system."""
    from core.tool_manager import register_command
    
    # Register simplified terminal commands
    register_command("execute_command", execute_command, EXECUTE_COMMAND_SCHEMA)
    register_command("start_interactive_session", start_interactive_session, START_INTERACTIVE_SESSION_SCHEMA)
    register_command("send_to_interactive_session", send_to_interactive_session, SEND_TO_INTERACTIVE_SESSION_SCHEMA)
    register_command("get_interactive_session_output", get_interactive_session_output, GET_INTERACTIVE_SESSION_OUTPUT_SCHEMA)
    register_command("terminate_interactive_session", terminate_interactive_session, TERMINATE_INTERACTIVE_SESSION_SCHEMA)
    register_command("list_interactive_sessions", list_interactive_sessions, LIST_INTERACTIVE_SESSIONS_SCHEMA)
    register_command("list_sessions", list_sessions, LIST_SESSIONS_SCHEMA)
    register_command("send_key_to_interactive_session", send_key_to_interactive_session, SEND_KEY_TO_INTERACTIVE_SESSION_SCHEMA)
    register_command("send_arrow_to_interactive_session", send_arrow_to_interactive_session, SEND_ARROW_TO_INTERACTIVE_SESSION_SCHEMA)
    register_command("send_enter_to_interactive_session", send_enter_to_interactive_session, SEND_ENTER_TO_INTERACTIVE_SESSION_SCHEMA)
    register_command("navigate_interactive_session_menu", navigate_interactive_session_menu, NAVIGATE_INTERACTIVE_SESSION_MENU_SCHEMA)
    register_command("select_interactive_session_menu_option", select_interactive_session_menu_option, SELECT_INTERACTIVE_SESSION_MENU_OPTION_SCHEMA) 