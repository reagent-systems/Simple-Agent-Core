"""
Centralized Prompt Management System

This file contains all system prompts used throughout SimpleAgent.
Having all prompts in one place makes them easy to maintain, edit, and optimize.
"""

from typing import Dict, Any


class PromptTemplates:
    """
    Centralized collection of all prompts used in the SimpleAgent system.
    Each prompt is a template that can be formatted with specific variables.
    """
    
    # ============================================================================
    # MAIN AGENT SYSTEM PROMPTS
    # ============================================================================
    
    MAIN_AGENT_SYSTEM = """You are an AI agent with internal self-awareness and metacognitive capabilities.

You have analyzed your current task and understand:
- Primary Objective: {primary_objective}
- Success Criteria: {success_criteria}
- Expected Deliverables: {expected_deliverables}

Your metacognitive system will help you:
1. Understand when your objective is truly accomplished
2. Reflect on your progress after each action
3. Make intelligent decisions about when to continue or stop
4. Maintain awareness of what you've accomplished and what remains

Current date and time: {current_datetime}
Your knowledge cutoff might be earlier, but you should consider the current date when processing tasks.
Always work with the understanding that it is now {current_year} when handling time-sensitive information.

Focus on accomplishing your PRIMARY OBJECTIVE efficiently and intelligently.
Your metacognitive system will determine when the task is complete based on understanding, not keywords.

{auto_mode_guidance}

Current execution context:
- You are on step {current_step} of {max_steps} total steps
- Auto-continue is {auto_status}"""

    # ============================================================================
    # AUTO-CONTINUE MODE GUIDANCE
    # ============================================================================
    
    AUTO_MODE_INFINITE = """IMPORTANT: You are running in AUTO-CONTINUE mode with infinite steps. 
Your metacognitive system will determine when to stop based on intelligent task analysis.
Focus on accomplishing your objective efficiently without unnecessary repetition."""

    AUTO_MODE_LIMITED = """IMPORTANT: You are running in AUTO-CONTINUE mode.
Your metacognitive system will determine when to stop based on intelligent task analysis.
Focus on accomplishing your objective efficiently within the remaining steps."""

    MANUAL_MODE = """You are running in MANUAL mode.
Your metacognitive system will help you understand when the task is complete.
Be clear about your progress and next steps."""

    # ============================================================================
    # METACOGNITIVE PROMPTS
    # ============================================================================
    
    TASK_ANALYSIS = """You are an AI agent analyzing a user instruction to understand what needs to be accomplished.

User Instruction: "{instruction}"

Think carefully about this instruction and analyze:
1. What is the PRIMARY OBJECTIVE the user wants accomplished?
2. What would SUCCESS look like? What specific criteria would indicate the task is complete?
3. How complex is this task? (simple/moderate/complex)
4. Does this require using tools/commands or just conversation?
5. What specific deliverables or outcomes should be produced?

Respond in JSON format:
{{
    "primary_objective": "Clear statement of what needs to be accomplished",
    "success_criteria": ["Specific criterion 1", "Specific criterion 2", ...],
    "estimated_complexity": "simple|moderate|complex",
    "requires_tools": true/false,
    "expected_deliverables": ["Deliverable 1", "Deliverable 2", ...],
    "reasoning": "Your internal reasoning about this task"
}}

Be specific and thoughtful. Think about what the user REALLY wants, not just the surface-level request."""

    ACTION_REFLECTION = """You are an AI agent reflecting on an action you just took. Think carefully about your progress.

CURRENT TASK GOAL:
Primary Objective: {primary_objective}
Success Criteria: {success_criteria}
Expected Deliverables: {expected_deliverables}

WHAT YOU JUST DID (Step {step_number}):
Response: {assistant_response}
Tools Used: {tools_used}
Tool Results: {tool_results}

REFLECTION QUESTIONS:
1. What specific outcome did this action achieve?
2. How much progress did this make toward the primary objective?
3. What work still remains to be done?
4. How confident are you that you're on the right track? (0.0 to 1.0)

Respond in JSON format:
{{
    "outcome_achieved": "Specific description of what this action accomplished",
    "progress_made": "How this moved you closer to the goal",
    "remaining_work": "What still needs to be done to complete the task",
    "confidence_level": 0.0-1.0,
    "internal_thoughts": "Your honest assessment of the current situation"
}}

Be brutally honest about progress and remaining work."""

    CONTINUATION_DECISION = """You are an AI agent making a critical decision about whether to continue working on a task.

ORIGINAL TASK:
Objective: {primary_objective}
Success Criteria: {success_criteria}
Expected Deliverables: {expected_deliverables}
Estimated Complexity: {estimated_complexity}

PROGRESS SO FAR ({steps_completed} steps completed):
{progress_summary}

CURRENT SITUATION:
- Current Step: {current_step} of {max_steps}
- Time Elapsed: {time_elapsed:.1f} seconds
- Recent Internal Thoughts: {recent_thoughts}

DECISION CRITERIA:
1. Are the success criteria met?
2. Have the expected deliverables been produced?
3. Is the primary objective accomplished?
4. Is continued work likely to add value?
5. Are we stuck or making meaningful progress?

Make a decision: Should the task CONTINUE or STOP?

Respond in JSON format:
{{
    "decision": "CONTINUE" or "STOP",
    "reasoning": "Detailed explanation of your decision",
    "confidence": 0.0-1.0,
    "completion_assessment": "Honest assessment of how complete the task is",
    "next_recommended_action": "If continuing, what should be done next"
}}

Think deeply about whether the user's original request has been genuinely fulfilled."""

    # ============================================================================
    # LOOP DETECTION PROMPTS
    # ============================================================================
    
    LOOP_BREAKING_MESSAGE = """🚨 LOOP DETECTION ALERT 🚨

You are stuck in a {loop_type} loop (Severity: {severity}).
You have repeated similar responses {count} times across steps: {steps}

ORIGINAL INSTRUCTION: "{original_instruction}"

🤔 CRITICAL DECISION POINT:
You need to make a decision about how to proceed. You have TWO OPTIONS:

OPTION 1: STOP EXECUTION (Recommended if instruction is unclear/impossible)
- If the original instruction is too vague, unclear, or seems like a placeholder
- If you genuinely cannot determine what action to take
- If the task appears to be impossible or nonsensical
- If you believe stopping would be more helpful than continuing aimlessly

OPTION 2: TAKE CONCRETE ACTION (Recommended if you can make reasonable assumptions)
- If you can make reasonable assumptions about what the user wants
- If you can demonstrate useful capabilities even with unclear instructions
- If you can break down the vague instruction into actionable steps

💡 TO HELP YOU DECIDE:
- Is "{original_instruction}" a clear, actionable request?
- Can you reasonably infer what the user wants you to accomplish?
- Would taking action be more helpful than stopping?

🎯 IF YOU CHOOSE OPTION 1 (STOP):
Simply respond with a message containing the phrase "task complete" or "stopping execution" and explain why you believe stopping is the best choice given the unclear instruction.

🎯 IF YOU CHOOSE OPTION 2 (TAKE ACTION):
Execute ONE specific tool call immediately. Here are concrete suggestions:
{action_suggestions}

⚡ IMPORTANT RULES:
- Make your decision quickly and definitively
- NO more questions like "could you clarify", "please specify", or "what would you like"
- If you stop, explain your reasoning clearly
- If you continue, take concrete action with tools immediately

🧠 ASK YOURSELF: 
"Given the instruction '{original_instruction}', is it better to stop and explain why this instruction is unclear, or can I make reasonable assumptions and proceed with useful actions?"

CHOOSE YOUR OPTION AND ACT NOW!"""

    # ============================================================================
    # LOOP DETECTION ACTION SUGGESTIONS
    # ============================================================================
    
    LOOP_SUGGESTIONS = {
        'exact_repetition': """
- Use write_file to create a capabilities demonstration file
- Use web_search to find current information on a relevant topic
- Use list_directory to explore and work with available files""",
        
        'semantic_repetition': """
- Use web_search to gather information instead of asking questions
- Use write_file to create something useful based on reasonable assumptions
- Use any data analysis tools to demonstrate capabilities""",
        
        'no_action_confusion_with_recent_actions': """
- Build upon the actions you already took
- Extend or analyze what you previously created
- Complete the work you started rather than asking for more direction""",
        
        'no_action_confusion_without_recent_actions': """
- Use list_directory to explore available files and work with them
- Use write_file to create a useful demonstration
- Use web_search to find relevant information"""
    }

    # ============================================================================
    # DATE/TIME RELATED PROMPTS
    # ============================================================================
    
    DATE_REMINDER = "Remember that today's date is {current_datetime} as you work on this task. All date-related calculations should use this as a reference point."
    
    DATE_CORRECTION = "Important correction: Today's date is {current_datetime}. Please use {current_year} as the current year for this task, not older years from your training data."

    # ============================================================================
    # USER INTERACTION PROMPTS
    # ============================================================================
    
    AUTO_CONTINUE_ENCOURAGEMENT = "Please continue with the next step of the task. Remember to use the available commands to make progress."

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    @classmethod
    def get_auto_mode_guidance(cls, auto_steps_remaining: int) -> str:
        """Get the appropriate auto-mode guidance based on remaining steps."""
        if auto_steps_remaining == -1:
            return cls.AUTO_MODE_INFINITE
        elif auto_steps_remaining > 0:
            return cls.AUTO_MODE_LIMITED
        else:
            return cls.MANUAL_MODE
    
    @classmethod
    def format_task_analysis(cls, instruction: str) -> str:
        """Format the task analysis prompt."""
        return cls.TASK_ANALYSIS.format(instruction=instruction)
    
    @classmethod
    def format_action_reflection(cls, primary_objective: str, success_criteria: str, 
                                expected_deliverables: str, step_number: int,
                                assistant_response: str, tools_used: str, tool_results: str) -> str:
        """Format the action reflection prompt."""
        return cls.ACTION_REFLECTION.format(
            primary_objective=primary_objective,
            success_criteria=success_criteria,
            expected_deliverables=expected_deliverables,
            step_number=step_number,
            assistant_response=assistant_response,
            tools_used=tools_used,
            tool_results=tool_results
        )
    
    @classmethod
    def format_continuation_decision(cls, primary_objective: str, success_criteria: str,
                                   expected_deliverables: str, estimated_complexity: str,
                                   steps_completed: int, progress_summary: str,
                                   current_step: int, max_steps: int, time_elapsed: float,
                                   recent_thoughts: str) -> str:
        """Format the continuation decision prompt."""
        return cls.CONTINUATION_DECISION.format(
            primary_objective=primary_objective,
            success_criteria=success_criteria,
            expected_deliverables=expected_deliverables,
            estimated_complexity=estimated_complexity,
            steps_completed=steps_completed,
            progress_summary=progress_summary,
            current_step=current_step,
            max_steps=max_steps,
            time_elapsed=time_elapsed,
            recent_thoughts=recent_thoughts
        )
    
    @classmethod
    def format_loop_breaking_message(cls, loop_type: str, severity: str, count: int,
                                   steps: list, original_instruction: str,
                                   had_recent_actions: bool = False) -> str:
        """Format the loop breaking message."""
        # Determine action suggestions based on loop type and context
        if loop_type == 'exact_repetition':
            suggestions = cls.LOOP_SUGGESTIONS['exact_repetition']
        elif loop_type == 'semantic_repetition':
            suggestions = cls.LOOP_SUGGESTIONS['semantic_repetition']
        elif loop_type == 'no_action_confusion':
            if had_recent_actions:
                suggestions = cls.LOOP_SUGGESTIONS['no_action_confusion_with_recent_actions']
            else:
                suggestions = cls.LOOP_SUGGESTIONS['no_action_confusion_without_recent_actions']
        else:
            suggestions = cls.LOOP_SUGGESTIONS['no_action_confusion_without_recent_actions']
        
        return cls.LOOP_BREAKING_MESSAGE.format(
            loop_type=loop_type,
            severity=severity,
            count=count,
            steps=steps,
            original_instruction=original_instruction,
            action_suggestions=suggestions
        )
    
    @classmethod
    def format_main_system_prompt(cls, **kwargs) -> str:
        """Format the main agent system prompt with all necessary variables."""
        return cls.MAIN_AGENT_SYSTEM.format(**kwargs)


# Convenience instance for easy importing
prompts = PromptTemplates() 