"""
Terminal Manager for SimpleAgent - Simplified Version

Provides basic terminal control capabilities:
- Simple command execution
- Basic interactive session support
- Working directory management
- Clean, reliable I/O
"""

import subprocess
import time
import os
import signal
import psutil
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import platform
import threading


@dataclass
class TerminalResult:
    """Result of a terminal command execution."""
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    pid: Optional[int] = None
    background: bool = False


class SimpleInteractiveSession:
    """
    Simplified interactive terminal session - focuses on what actually works.
    """
    
    def __init__(self, session_id: str, working_dir: str = None):
        """Initialize a simple interactive session."""
        self.session_id = session_id
        self.working_dir = working_dir or os.getcwd()
        self.environment = dict(os.environ)
        
        self.process: Optional[subprocess.Popen] = None
        self.is_running = False
        self.command_history: List[str] = []
        
        # Simple output collection
        self.output_lines = []
        self.output_lock = threading.Lock()
        self.output_thread = None
    
    def start_process(self, command: str) -> bool:
        """Start a process with clean, simple settings."""
        if self.is_running:
            return False
        
        try:
            self.command_history.append(command)
            
            if platform.system() == "Windows":
                if command.strip().lower() == 'wsl':
                    # WSL with binary mode to have complete control over line endings
                    self.process = subprocess.Popen(
                        ['wsl.exe', '--exec', 'bash', '--norc', '--noprofile'],  # Minimal bash setup
                        cwd=self.working_dir,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=False,  # Binary mode
                        bufsize=0,  # Unbuffered
                        env=dict(os.environ, TERM='dumb', LANG='C.UTF-8')  # Clean environment
                    )
                else:
                    # Simple Windows command
                    self.process = subprocess.Popen(
                        command,
                        shell=True,
                        cwd=self.working_dir,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=0
                    )
            else:
                # Simple Unix command
                self.process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=self.working_dir,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=0
                )
            
            self.is_running = True
            
            # Start simple output collection
            self.output_thread = threading.Thread(target=self._collect_output, daemon=True)
            self.output_thread.start()
            
            # Wait for startup and send initial command to test
            time.sleep(2)
            
            # Send a test command to see if we get any response
            if command.strip().lower() == 'wsl':
                # Send with explicit UTF-8 encoding and Unix line ending only
                test_cmd = 'echo "WSL_READY"\n'.encode('utf-8')
                self.process.stdin.write(test_cmd)
                self.process.stdin.flush()
                time.sleep(1)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start: {e}")
            return False
    
    def _collect_output(self):
        """Simple output collection in background."""
        
        # Check if this is a WSL process (binary mode)
        is_wsl_binary = (hasattr(self.process, 'stdin') and 
                        hasattr(self.process.stdin, 'mode') and 
                        'b' in str(type(self.process.stdin)))
        
        if not is_wsl_binary:
            # Detect binary mode by checking if stdout has a mode attribute
            try:
                is_wsl_binary = not hasattr(self.process.stdout, 'encoding')
            except:
                is_wsl_binary = False
        
        while self.is_running and self.process:
            try:
                # Check if process is still alive
                poll_result = self.process.poll()
                if poll_result is not None:
                    break
                
                # Try to read with a timeout approach
                try:
                    if is_wsl_binary:
                        # Binary mode - read bytes and decode as UTF-8
                        line_bytes = self.process.stdout.readline()
                        if line_bytes:
                            line = line_bytes.decode('utf-8', errors='replace')
                            with self.output_lock:
                                self.output_lines.append(line.rstrip('\n\r'))
                        else:
                            time.sleep(0.1)
                    else:
                        # Text mode - read normally
                        line = self.process.stdout.readline()
                        if line:
                            with self.output_lock:
                                self.output_lines.append(line.rstrip('\n\r'))
                        else:
                            time.sleep(0.1)
                        
                except Exception as e:
                    time.sleep(0.1)
                    
            except Exception as e:
                break
    
    def send_command(self, command: str) -> bool:
        """Send a command with proper line ending."""
        if not self.is_running or not self.process:
            return False
        
        try:
            # Clean command completely
            clean_command = command.strip()
            # Remove ALL carriage returns and normalize line endings
            clean_command = clean_command.replace('\r\n', '').replace('\r', '').replace('\n', '')
            
            # Check if this is binary mode (WSL)
            is_wsl_binary = False
            try:
                is_wsl_binary = not hasattr(self.process.stdout, 'encoding')
            except:
                is_wsl_binary = False
            
            if is_wsl_binary:
                # Binary mode - encode as UTF-8 with only Unix newline
                command_bytes = (clean_command + '\n').encode('utf-8')
                self.process.stdin.write(command_bytes)
            else:
                # Text mode - add only Unix newline
                clean_command = clean_command + '\n'
                self.process.stdin.write(clean_command)
            
            self.process.stdin.flush()
            return True
            
        except Exception as e:
            print(f"❌ Send error: {e}")
            return False
    
    def send_key(self, key: str) -> bool:
        """Send special keyboard keys like arrow keys, Enter, etc."""
        if not self.is_running or not self.process:
            return False
        
        try:
            # Check if this is binary mode (WSL)
            is_wsl_binary = False
            try:
                is_wsl_binary = not hasattr(self.process.stdout, 'encoding')
            except:
                is_wsl_binary = False
            
            # Map special keys to their ANSI escape sequences
            key_mappings = {
                'up': '\x1b[A',        # Up arrow
                'down': '\x1b[B',      # Down arrow  
                'right': '\x1b[C',     # Right arrow
                'left': '\x1b[D',      # Left arrow
                'enter': '\r',         # Enter key
                'tab': '\t',           # Tab key
                'escape': '\x1b',      # Escape key
                'space': ' ',          # Space key
                'ctrl+c': '\x03',      # Ctrl+C
            }
            
            # Get the key sequence
            key_sequence = key_mappings.get(key.lower(), key)
            
            if is_wsl_binary:
                # Binary mode - encode as UTF-8
                key_bytes = key_sequence.encode('utf-8')
                self.process.stdin.write(key_bytes)
            else:
                # Text mode
                self.process.stdin.write(key_sequence)
            
            self.process.stdin.flush()
            return True
            
        except Exception as e:
            print(f"❌ Key send error: {e}")
            return False
    
    def send_arrow_key(self, direction: str) -> bool:
        """Send arrow key in specified direction."""
        return self.send_key(direction)
    
    def send_enter(self) -> bool:
        """Send Enter key."""
        return self.send_key('enter')
    
    def navigate_menu(self, option_index: int, total_options: int = None) -> bool:
        """Navigate to a specific menu option by index (0-based)."""
        if not self.is_running or not self.process:
            return False
        
        # Send arrow keys to navigate to the desired option
        # Assuming we start at option 0, navigate down to reach the target
        for i in range(option_index):
            if not self.send_arrow_key('down'):
                return False
            time.sleep(0.1)  # Small delay between key presses
        
        return True
    
    def select_menu_option(self, option_index: int, total_options: int = None) -> bool:
        """Navigate to and select a menu option."""
        if self.navigate_menu(option_index, total_options):
            time.sleep(0.2)  # Brief pause before selecting
            return self.send_enter()
        return False
    
    def get_output(self, clear: bool = True) -> str:
        """Get collected output."""
        with self.output_lock:
            output = '\n'.join(self.output_lines)
            if clear:
                self.output_lines.clear()
        return output
    
    def get_recent_output(self, lines: int = 10) -> str:
        """Get recent output lines."""
        with self.output_lock:
            recent = self.output_lines[-lines:] if self.output_lines else []
        return '\n'.join(recent)
    
    def wait_for_output(self, timeout: float = 5.0) -> str:
        """Wait for new output to appear."""
        start_time = time.time()
        initial_count = len(self.output_lines)
        
        while time.time() - start_time < timeout:
            with self.output_lock:
                if len(self.output_lines) > initial_count:
                    break
            time.sleep(0.1)
        
        return self.get_output(clear=False)
    
    def is_alive(self) -> bool:
        """Check if process is alive."""
        return self.is_running and self.process and self.process.poll() is None
    
    def terminate(self) -> bool:
        """Terminate the session."""
        if not self.is_running:
            return True
        
        self.is_running = False
        
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except:
                try:
                    self.process.kill()
                    self.process.wait()
                except:
                    pass
        
        return True


class SimpleTerminalSession:
    """
    Simplified terminal session management.
    """
    
    def __init__(self, session_id: str, working_dir: str = None):
        """Initialize terminal session."""
        self.session_id = session_id
        self.working_dir = working_dir or os.getcwd()
        self.environment = dict(os.environ)
        self.interactive_sessions: Dict[str, SimpleInteractiveSession] = {}
        self.is_active = True
    
    def execute_command(
        self, 
        command: str, 
        timeout: Optional[float] = 30,
        background: bool = False
    ) -> TerminalResult:
        """Execute a simple command."""
        start_time = time.time()
        
        try:
            if background:
                # Background process
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=self.working_dir,
                    env=self.environment
                )
                
                return TerminalResult(
                    stdout=f"Background process started (PID: {process.pid})",
                    stderr="",
                    exit_code=0,
                    execution_time=time.time() - start_time,
                    pid=process.pid,
                    background=True
                )
            else:
                # Foreground process
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=self.working_dir,
                    env=self.environment,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                return TerminalResult(
                    stdout=result.stdout or "",
                    stderr=result.stderr or "",
                    exit_code=result.returncode,
                    execution_time=time.time() - start_time
                )
        
        except subprocess.TimeoutExpired as e:
            return TerminalResult(
                stdout=e.stdout or "",
                stderr=f"Command timed out after {timeout}s",
                exit_code=-1,
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return TerminalResult(
                stdout="",
                stderr=f"Error: {str(e)}",
                exit_code=-1,
                execution_time=time.time() - start_time
            )
    
    def start_interactive_session(self, command: str, session_name: str = "default") -> bool:
        """Start an interactive session."""
        if session_name in self.interactive_sessions:
            self.interactive_sessions[session_name].terminate()
        
        session = SimpleInteractiveSession(session_name, self.working_dir)
        session.environment = self.environment.copy()
        
        if session.start_process(command):
            self.interactive_sessions[session_name] = session
            return True
        
        return False
    
    def send_to_session(self, input_text: str, session_name: str = "default") -> str:
        """Send input to interactive session."""
        if session_name not in self.interactive_sessions:
            return "❌ No session found"
        
        session = self.interactive_sessions[session_name]
        if not session.is_alive():
            return "❌ Session not active"
        
        # AGGRESSIVE input cleaning - remove ALL carriage returns and line endings
        clean_input = input_text.strip()
        # Remove all possible line ending variations
        clean_input = clean_input.replace('\r\n', '').replace('\r', '').replace('\n', '')
        
        # Clear old output first
        session.get_output(clear=True)
        
        # Send command
        success = session.send_command(clean_input)
        if not success:
            return "❌ Failed to send input"
        
        # Wait for output
        time.sleep(1.5)
        
        # Get new output
        output = session.get_output(clear=False)
        return output
    
    def send_key_to_session(self, key: str, session_name: str = "default") -> str:
        """Send special key to interactive session."""
        if session_name not in self.interactive_sessions:
            return "❌ No session found"
        
        session = self.interactive_sessions[session_name]
        if not session.is_alive():
            return "❌ Session not active"
        
        # Clear old output first
        session.get_output(clear=True)
        
        # Send key
        success = session.send_key(key)
        if not success:
            return "❌ Failed to send key"
        
        # Wait for output
        time.sleep(1.0)
        
        # Get new output
        output = session.get_output(clear=False)
        return output
    
    def send_arrow_to_session(self, direction: str, session_name: str = "default") -> str:
        """Send arrow key to interactive session."""
        return self.send_key_to_session(direction, session_name)
    
    def send_enter_to_session(self, session_name: str = "default") -> str:
        """Send Enter key to interactive session."""
        return self.send_key_to_session('enter', session_name)
    
    def navigate_session_menu(self, option_index: int, session_name: str = "default") -> str:
        """Navigate to specific menu option in interactive session."""
        if session_name not in self.interactive_sessions:
            return "❌ No session found"
        
        session = self.interactive_sessions[session_name]
        if not session.is_alive():
            return "❌ Session not active"
        
        # Clear old output first
        session.get_output(clear=True)
        
        # Navigate to option
        success = session.navigate_menu(option_index)
        if not success:
            return "❌ Failed to navigate menu"
        
        # Wait for output
        time.sleep(1.0)
        
        # Get new output
        output = session.get_output(clear=False)
        return output
    
    def select_session_menu_option(self, option_index: int, session_name: str = "default") -> str:
        """Navigate to and select menu option in interactive session."""
        if session_name not in self.interactive_sessions:
            return "❌ No session found"
        
        session = self.interactive_sessions[session_name]
        if not session.is_alive():
            return "❌ Session not active"
        
        # Clear old output first
        session.get_output(clear=True)
        
        # Navigate and select option
        success = session.select_menu_option(option_index)
        if not success:
            return "❌ Failed to select menu option"
        
        # Wait for output
        time.sleep(1.5)
        
        # Get new output
        output = session.get_output(clear=False)
        return output
    
    def get_session_output(self, session_name: str = "default") -> str:
        """Get current session output."""
        if session_name not in self.interactive_sessions:
            return "❌ No session found"
        
        session = self.interactive_sessions[session_name]
        return session.get_output(clear=False)
    
    def terminate_interactive_session(self, session_name: str = "default") -> str:
        """Terminate interactive session."""
        if session_name not in self.interactive_sessions:
            return "❌ No session found"
        
        session = self.interactive_sessions[session_name]
        session.terminate()
        del self.interactive_sessions[session_name]
        return f"✅ Session '{session_name}' terminated"
    
    def list_interactive_sessions(self) -> List[Dict[str, Any]]:
        """List interactive sessions."""
        sessions = []
        for name, session in self.interactive_sessions.items():
            sessions.append({
                "name": name,
                "alive": session.is_alive(),
                "commands": len(session.command_history)
            })
        return sessions


class SimpleTerminalManager:
    """
    Simplified terminal manager - focuses on core functionality.
    """
    
    def __init__(self):
        """Initialize the manager."""
        self.sessions: Dict[str, SimpleTerminalSession] = {}
        self.default_session_id = "main"
        
        # Create default session
        self.create_session(self.default_session_id)
    
    def create_session(self, session_id: str, working_dir: str = None) -> SimpleTerminalSession:
        """Create a new session."""
        if session_id in self.sessions:
            raise ValueError(f"Session {session_id} already exists")
        
        session = SimpleTerminalSession(session_id, working_dir)
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str = None) -> SimpleTerminalSession:
        """Get a session."""
        session_id = session_id or self.default_session_id
        if session_id not in self.sessions:
            return self.create_session(session_id)
        return self.sessions[session_id]
    
    def execute_command(
        self,
        command: str,
        session_id: str = None,
        timeout: Optional[float] = 30,
        background: bool = False
    ) -> TerminalResult:
        """Execute a command."""
        session = self.get_session(session_id)
        return session.execute_command(command, timeout, background)
    
    def start_interactive_session(
        self,
        command: str,
        session_id: str = None,
        interactive_session_name: str = "default"
    ) -> bool:
        """Start interactive session."""
        session = self.get_session(session_id)
        return session.start_interactive_session(command, interactive_session_name)
    
    def send_to_interactive_session(
        self,
        input_text: str,
        session_id: str = None,
        interactive_session_name: str = "default"
    ) -> str:
        """Send to interactive session."""
        session = self.get_session(session_id)
        return session.send_to_session(input_text, interactive_session_name)
    
    def send_key_to_interactive_session(
        self,
        key: str,
        session_id: str = None,
        interactive_session_name: str = "default"
    ) -> str:
        """Send special key to interactive session."""
        session = self.get_session(session_id)
        return session.send_key_to_session(key, interactive_session_name)
    
    def send_arrow_to_interactive_session(
        self,
        direction: str,
        session_id: str = None,
        interactive_session_name: str = "default"
    ) -> str:
        """Send arrow key to interactive session."""
        session = self.get_session(session_id)
        return session.send_arrow_to_session(direction, interactive_session_name)
    
    def send_enter_to_interactive_session(
        self,
        session_id: str = None,
        interactive_session_name: str = "default"
    ) -> str:
        """Send Enter key to interactive session."""
        session = self.get_session(session_id)
        return session.send_enter_to_session(interactive_session_name)
    
    def navigate_interactive_session_menu(
        self,
        option_index: int,
        session_id: str = None,
        interactive_session_name: str = "default"
    ) -> str:
        """Navigate to specific menu option in interactive session."""
        session = self.get_session(session_id)
        return session.navigate_session_menu(option_index, interactive_session_name)
    
    def select_interactive_session_menu_option(
        self,
        option_index: int,
        session_id: str = None,
        interactive_session_name: str = "default"
    ) -> str:
        """Navigate to and select menu option in interactive session."""
        session = self.get_session(session_id)
        return session.select_session_menu_option(option_index, interactive_session_name)
    
    def get_interactive_session_output(
        self,
        session_id: str = None,
        interactive_session_name: str = "default"
    ) -> str:
        """Get session output."""
        session = self.get_session(session_id)
        return session.get_session_output(interactive_session_name)
    
    def terminate_interactive_session(
        self,
        session_id: str = None,
        interactive_session_name: str = "default"
    ) -> str:
        """Terminate session."""
        session = self.get_session(session_id)
        return session.terminate_interactive_session(interactive_session_name)
    
    def list_sessions(self) -> List[str]:
        """List all sessions."""
        return list(self.sessions.keys())
    
    def cleanup_all(self):
        """Clean up all sessions."""
        for session_id in list(self.sessions.keys()):
            session = self.sessions[session_id]
            for interactive_session in list(session.interactive_sessions.values()):
                interactive_session.terminate()
            del self.sessions[session_id]


# Global instance
_terminal_manager = None


def get_terminal_manager() -> SimpleTerminalManager:
    """Get the global terminal manager instance."""
    global _terminal_manager
    if _terminal_manager is None:
        _terminal_manager = SimpleTerminalManager()
    return _terminal_manager 