"""
SimpleAgent Run Manager Module

This module handles the run loop from agent.py

Args:
    model: The OpenAI model to use
    output_dir: The output directory for file operations
"""

import os
import time
import json
from typing import List, Dict, Any, Optional
import sentry_sdk
import uuid

from core.conversation.conversation import ConversationManager
from core.execution.execution import ExecutionManager
from core.conversation.memory import MemoryManager
from core.execution.summarizer import ChangeSummarizer
from core.metacognition.loop_detector import LoopDetector
from core.metacognition.metacognition import MetaCognition
from core.metacognition.prompts import prompts
from core.utils.config import OUTPUT_DIR
from core.utils import sentry_integration


class RunManager:
    """
    Manages the run loop for SimpleAgent, coordinating the conversation,
    execution, and memory components with intelligent metacognition.
    """
    
    def __init__(self, model: str, output_dir: str = OUTPUT_DIR):
        """
        Initialize the run manager.
        
        Args:
            model: The OpenAI model to use
            output_dir: The output directory for file operations
        """
        self.output_dir = output_dir
        self.conversation_manager = ConversationManager()
        self.execution_manager = ExecutionManager(model=model, output_dir=output_dir)
        self.memory_manager = MemoryManager()
        self.summarizer = ChangeSummarizer()
        self.loop_detector = LoopDetector(window_size=5, similarity_threshold=0.7)
        
        # Initialize the metacognition system with the same model client
        self.metacognition = MetaCognition(self.execution_manager.client)
        
    def run(self, user_instruction: str, max_steps: int = 10, auto_continue: int = 0):
        """
        Run the SimpleAgent with the given instruction.
        
        Args:
            user_instruction: The instruction from the user
            max_steps: Maximum number of steps to run
            auto_continue: Number of steps to auto-continue (0 = disabled, -1 = infinite)
        """
        # Reset stop flag and intelligent systems
        self.execution_manager.stop_requested = False
        self.metacognition.reset()
        
        # Setup initial console output
        print(f"\n🤖 SimpleAgent initialized with instruction: {user_instruction}")
        print(f"📁 Using output directory: {self.output_dir}")
        
        # Have the agent deeply analyze the task using metacognition
        print("\n🧠 Agent analyzing task requirements...")
        task_goal = self.metacognition.analyze_user_instruction(user_instruction)
        print(f"🎯 Primary Objective: {task_goal.primary_objective}")
        print(f"📋 Success Criteria: {', '.join(task_goal.success_criteria)}")
        print(f"🔧 Complexity: {task_goal.estimated_complexity}")
        print(f"🛠️ Requires Tools: {task_goal.requires_tools}")
        if task_goal.expected_deliverables:
            print(f"📦 Expected Deliverables: {', '.join(task_goal.expected_deliverables)}")
        
        # Get current date and time information for the system message
        current_datetime = time.strftime("%Y-%m-%d %H:%M:%S")
        current_year = time.strftime("%Y")
        print(f"📅 Current date: {current_datetime}")
        
        # Only print auto-continue message if it's enabled (non-zero and not None)
        if auto_continue and auto_continue != 0:
            print(f"📌 Auto-continue enabled for {auto_continue if auto_continue > 0 else 'all'} steps")
            print("💡 Press Ctrl+C at any time to interrupt and stop execution")
        else:
            print("📌 Manual mode (auto-continue disabled)")
        print()
        
        # Save and change to the output directory
        original_cwd = os.getcwd()
        
        try:
            # Change to the output directory so all operations happen there
            if os.path.exists(self.output_dir):
                os.chdir(self.output_dir)
                # Get relative path from output directory onwards
                current_dir = os.getcwd()
                # Find the last occurrence of 'output' to get the relative path
                if 'output' in current_dir:
                    output_index = current_dir.rfind('output')
                    relative_path = current_dir[output_index:]
                    # Convert to forward slashes for consistent display
                    relative_path = relative_path.replace('\\', '/')
                    print(f"🔄 Changed working directory to: {relative_path}")
                else:
                    # Fallback to full path if 'output' not found
                    print(f"🔄 Changed working directory to: {current_dir}")
            
            # Clear the conversation history and start fresh
            self.conversation_manager.clear()
            
            # Reset loop detector for a fresh start
            self.loop_detector.reset()
            
            # Add the user instruction to the conversation
            self.conversation_manager.add_message("user", user_instruction)
            
            # Check if the instruction is potentially date/time related
            date_keywords = ["today", "current date", "this year", "this month", "schedule", "calendar", 
                           "deadline", "upcoming", "recently", "last year", "next week", "time", 
                           "date", "year", "month", "day", "2023", "2024", "2025", "future", "past"]
            
            instruction_lower = user_instruction.lower()
            is_date_related = any(keyword in instruction_lower for keyword in date_keywords)
            
            # If date-related, add a reminder about the current date
            if is_date_related:
                date_reminder = prompts.DATE_REMINDER.format(current_datetime=current_datetime)
                print(f"📅 Adding date reminder: {date_reminder}")
                self.conversation_manager.add_message("user", date_reminder)
            
            # Track changes for summarization
            changes_made = []
            step_changes = []  # Track changes for each step
            
            # Run the agent loop with metacognitive awareness
            step = 0
            # Ensure auto_steps_remaining is an integer (0 if auto_continue is None)
            auto_steps_remaining = 0 if auto_continue is None else auto_continue
            
            run_id = str(uuid.uuid4())[:8]
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            extra_data = {
                "expected_deliverables": task_goal.expected_deliverables,
                "success_criteria": task_goal.success_criteria,
                "complexity": task_goal.estimated_complexity,
                "requires_tools": task_goal.requires_tools,
            }
            sentry_integration.log_run_start(
                user_instruction=user_instruction,
                output_dir=self.output_dir,
                max_steps=max_steps,
                auto_continue=auto_continue,
                timestamp=timestamp,
                extra_data=extra_data,
                run_id=run_id,
                task_type="ai_news_summary" if "ai news" in user_instruction.lower() else None
            )
            
            with sentry_integration.start_agent_run_transaction():
                while step < max_steps and not self.execution_manager.stop_requested:
                    try:
                        with sentry_integration.start_agent_step_span(step):
                            step += 1
                            should_continue = self._run_step(
                                step, user_instruction, max_steps, auto_steps_remaining, task_goal, changes_made
                            )
                            if not should_continue:
                                break
                            if auto_steps_remaining == -1 or auto_steps_remaining > 0:
                                if auto_steps_remaining > 0:
                                    auto_steps_remaining -= 1
                                    
                                # Check if a stop was requested
                                if self.execution_manager.stop_requested:
                                    print("\n🛑 Stop requested. Halting auto-continue execution.")
                                    break
                                print("\n🔄 Auto-continuing...")
                                continue
                            
                            # Manual mode - ask for user input
                            user_input = input("\n🧑 Enter your next instruction, 'y' to continue with current task, or 'n' to stop: ")
                            
                            # Normalize the input
                            normalized_input = user_input.strip().lower()
                            
                            if normalized_input == 'n':
                                print("Stopping the agent")
                                break
                            elif normalized_input == 'y':
                                # Simply continue
                                continue
                            else:
                                # Add the custom message to the conversation
                                print(f"\n🧑 User: {user_input}")
                                self.conversation_manager.add_message("user", user_input)
                    except Exception as e:
                        sentry_integration.capture_exception(e)
                        print(f"Error in step execution: {str(e)}")
                        break
            
            # Generate a final summary of all changes
            if changes_made:
                final_summary = self.summarizer.summarize_changes(changes_made)
                print(f"\n📝 Final Summary of All Changes:\n{final_summary}")
            
            # Show the agent's final internal thoughts and progress
            internal_thoughts = self.metacognition.get_internal_monologue()
            if internal_thoughts:
                print(f"\n🧠 Agent's Internal Monologue:")
                for thought in internal_thoughts[-3:]:  # Show last 3 thoughts
                    print(f"   💭 {thought}")
            
            progress_summary = self.metacognition.get_progress_summary()
            if progress_summary.get("status") != "No active task":
                print(f"\n📊 Final Task Analysis:")
                print(f"   🎯 Goal: {progress_summary['goal']}")
                print(f"   📋 Steps Completed: {progress_summary['steps_completed']}")
                print(f"    Average Confidence: {progress_summary['average_confidence']:.2f}")
                print(f"   ⏱️ Time Elapsed: {progress_summary['time_elapsed']:.1f} seconds")
            
            # Save the memory
            self.memory_manager.add_conversation(self.conversation_manager.get_history())
            self.memory_manager.save_memory()
            
            print("\n🏁 SimpleAgent execution completed")
            sentry_integration.capture_message("Agent run completed")
        except Exception as e:
            sentry_integration.capture_exception(e)
            raise
        finally:
            # Always restore the original working directory
            if os.getcwd() != original_cwd:
                os.chdir(original_cwd)

    def _run_step(self, step, user_instruction, max_steps, auto_steps_remaining, task_goal, changes_made):
        current_datetime = time.strftime("%Y-%m-%d %H:%M:%S")
        current_year = time.strftime("%Y")
        auto_mode_guidance = prompts.get_auto_mode_guidance(auto_steps_remaining)
        if auto_steps_remaining == -1:
            auto_status = "enabled (infinite)"
        elif auto_steps_remaining > 0:
            auto_status = f"enabled ({auto_steps_remaining} steps remaining)"
        else:
            auto_status = "disabled"
        system_content = prompts.format_main_system_prompt(
            primary_objective=task_goal.primary_objective,
            success_criteria=', '.join(task_goal.success_criteria),
            expected_deliverables=', '.join(task_goal.expected_deliverables),
            current_datetime=current_datetime,
            current_year=current_year,
            auto_mode_guidance=auto_mode_guidance,
            current_step=step,
            max_steps=max_steps,
            auto_status=auto_status
        )
        self.conversation_manager.update_system_message(system_content)
        print(f"\n--- Step {step}/{max_steps} ---")
        assistant_message = self.execution_manager.get_next_action(
            self.conversation_manager.get_history()
        )
        if not assistant_message:
            print("Error: Failed to get a response from the model.")
            return False
        content = None
        if hasattr(assistant_message, 'content'):
            content = assistant_message.content
        elif isinstance(assistant_message, dict) and 'content' in assistant_message:
            content = assistant_message['content']
        if content:
            print(f"\n🤖 Assistant: {content}")
        message_dict = {"role": "assistant"}
        if content:
            message_dict["content"] = content
        has_tool_calls = hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls
        tools_used = []
        tool_results = []
        if has_tool_calls:
            message_dict["tool_calls"] = [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                } for tool_call in assistant_message.tool_calls
            ]
        self.conversation_manager.conversation_history.append(message_dict)
        step_changes = []
        if has_tool_calls:
            for tool_call in assistant_message.tool_calls:
                change, function_name = self._execute_tool_call(tool_call, tools_used, step_changes, changes_made)
        if content:
            print("\n🧠 Agent reflecting on action...")
            reflection = self.metacognition.reflect_on_action(
                step, content, tools_used, tool_results
            )
            if reflection:
                print(f"💭 Outcome: {reflection.outcome_achieved}")
                print(f"📈 Progress: {reflection.progress_made}")
                print(f"📋 Remaining: {reflection.remaining_work}")
                print(f"🎯 Confidence: {reflection.confidence_level:.2f}")
        should_continue, reasoning, confidence = self.metacognition.should_task_continue(step, max_steps)
        sentry_integration.log_breadcrumb(
            message=f"Metacognitive decision: {'CONTINUE' if should_continue else 'STOP'}",
            category="agent.decision",
            level="info",
            data={"reasoning": reasoning, "confidence": confidence}
        )
        if not should_continue:
            print(f"\n🧠 METACOGNITIVE DECISION: STOP")
            print(f"💡 Reasoning: {reasoning}")
            print(f"🎯 Confidence: {confidence:.2f}")
            print("\n✅ Task completed based on intelligent analysis")
            return False
        else:
            print(f"\n🧠 METACOGNITIVE DECISION: CONTINUE")
            print(f"💡 Reasoning: {reasoning}")
            print(f"🎯 Confidence: {confidence:.2f}")
        if content:
            self.loop_detector.add_response(content, step, has_tool_calls)
            loop_info = self.loop_detector.detect_loop(step)
            if loop_info and loop_info['loop_severity'] == 'high':
                print(f"\n🔄 HIGH-SEVERITY LOOP DETECTED: {loop_info['type']}")
                print(f"   Repeated {loop_info['count']} times across steps: {loop_info['steps_involved']}")
                print("🧠 Metacognitive system reconsidering due to loop detection...")
                should_continue, reasoning, confidence = self.metacognition.should_task_continue(step, max_steps)
                if not should_continue:
                    print(f"🛑 Metacognitive decision: STOP due to loop + task analysis")
                    print(f"💡 Reasoning: {reasoning}")
                    return False
                else:
                    loop_breaking_message = prompts.format_loop_breaking_message(
                        loop_type=loop_info['type'],
                        severity=loop_info['loop_severity'], 
                        count=loop_info['count'],
                        steps=loop_info['steps_involved'],
                        original_instruction=user_instruction,
                        had_recent_actions=loop_info.get('recent_actions', False)
                    )
                    print(f"\n⚡ Injecting loop-breaking guidance...")
                    self.conversation_manager.add_message("user", loop_breaking_message)
                    return True
        if step_changes:
            step_summary = self.summarizer.summarize_changes(step_changes, is_step_summary=True)
            if step_summary:
                print(f"\n{step_summary}")
        if changes_made:
            overall_summary = self.summarizer.summarize_changes(changes_made)
            if overall_summary:
                print(f"\n{overall_summary}")
        return True

    def _execute_tool_call(self, tool_call, tools_used, step_changes, changes_made):
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        with sentry_integration.start_tool_call_span(function_name):
            sentry_integration.log_breadcrumb(
                message=f"Executing tool: {function_name}",
                category="tool.execution",
                level="info",
                data={"function_name": function_name, "args": function_args}
            )
            function_response, change = self.execution_manager.execute_function(
                function_name, function_args
            )
            sentry_integration.log_breadcrumb(
                message=f"Tool executed successfully: {function_name}",
                category="tool.execution",
                level="info",
                data={"function_name": function_name, "result": function_response}
            )
            if function_name == "write_file" and "file_path" in function_args:
                sentry_integration.log_breadcrumb(
                    message=f"File written: {function_args['file_path']}",
                    category="file.operation",
                    level="info",
                    data={"file_path": function_args['file_path'], "content_length": len(function_args.get('content', ''))}
                )
        tools_used.append(function_name)
        if change:
            changes_made.append(change)
            step_changes.append(change)
        self.conversation_manager.add_message(
            "tool", 
            str(function_response), 
            tool_call_id=tool_call.id,
            name=function_name
        )
        return change, function_name

