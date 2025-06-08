"""
Metacognition Module

This module provides the agent with internal monologue
capabilities to intelligently understand task progress and completion.
The agent can reflect on its own actions and reasoning to make smart decisions.
"""

import json
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from core.metacognition.prompts import prompts
from core.utils.config import METACOGNITION_MODEL


@dataclass
class TaskGoal:
    """Represents what the agent is trying to accomplish"""
    primary_objective: str
    success_criteria: List[str]
    estimated_complexity: str  # 'simple', 'moderate', 'complex'
    requires_tools: bool
    expected_deliverables: List[str]


@dataclass
class ActionReflection:
    """Represents the agent's reflection on an action it took"""
    step_number: int
    action_taken: str
    tools_used: List[str]
    outcome_achieved: str
    progress_made: str
    remaining_work: str
    confidence_level: float  # 0.0 to 1.0


class MetaCognition:
    """
    Provides the agent with internal monologue and self-awareness capabilities.
    The agent can think about its own progress and make intelligent decisions.
    """
    
    def __init__(self, model_client):
        self.model_client = model_client
        self.current_goal: Optional[TaskGoal] = None
        self.action_reflections: List[ActionReflection] = []
        self.internal_thoughts: List[str] = []
        self.task_started_at = None
        
    def analyze_user_instruction(self, instruction: str) -> TaskGoal:
        """
        Have the agent think deeply about what the user is asking for
        and what success would look like.
        """
        analysis_prompt = prompts.format_task_analysis(instruction)

        try:
            response = self.model_client.chat.completions.create(
                model=METACOGNITION_MODEL,
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.1
            )
            
            analysis = json.loads(response.choices[0].message.content)
            
            self.current_goal = TaskGoal(
                primary_objective=analysis["primary_objective"],
                success_criteria=analysis["success_criteria"],
                estimated_complexity=analysis["estimated_complexity"],
                requires_tools=analysis["requires_tools"],
                expected_deliverables=analysis["expected_deliverables"]
            )
            
            self.internal_thoughts.append(f"TASK ANALYSIS: {analysis['reasoning']}")
            self.task_started_at = time.time()
            
            return self.current_goal
            
        except Exception as e:
            # Fallback if analysis fails
            self.current_goal = TaskGoal(
                primary_objective=instruction,
                success_criteria=["Complete the requested task"],
                estimated_complexity="moderate",
                requires_tools=True,
                expected_deliverables=["Task completion"]
            )
            return self.current_goal
    
    def reflect_on_action(self, step_number: int, assistant_response: str, 
                         tools_used: List[str], tool_results: List[str]) -> ActionReflection:
        """
        Have the agent reflect on what it just did and assess progress.
        """
        if not self.current_goal:
            return None
            
        reflection_prompt = prompts.format_action_reflection(
            primary_objective=self.current_goal.primary_objective,
            success_criteria=', '.join(self.current_goal.success_criteria),
            expected_deliverables=', '.join(self.current_goal.expected_deliverables),
            step_number=step_number,
            assistant_response=assistant_response,
            tools_used=', '.join(tools_used) if tools_used else 'None',
            tool_results=str(tool_results) if tool_results else 'None'
        )

        try:
            response = self.model_client.chat.completions.create(
                model=METACOGNITION_MODEL,
                messages=[{"role": "user", "content": reflection_prompt}],
                temperature=0.2
            )
            
            reflection_data = json.loads(response.choices[0].message.content)
            
            reflection = ActionReflection(
                step_number=step_number,
                action_taken=assistant_response,
                tools_used=tools_used,
                outcome_achieved=reflection_data["outcome_achieved"],
                progress_made=reflection_data["progress_made"],
                remaining_work=reflection_data["remaining_work"],
                confidence_level=float(reflection_data["confidence_level"])
            )
            
            self.action_reflections.append(reflection)
            self.internal_thoughts.append(f"STEP {step_number} REFLECTION: {reflection_data['internal_thoughts']}")
            
            return reflection
            
        except Exception as e:
            # Fallback reflection
            return ActionReflection(
                step_number=step_number,
                action_taken=assistant_response,
                tools_used=tools_used,
                outcome_achieved="Action completed",
                progress_made="Made progress",
                remaining_work="Continuing task",
                confidence_level=0.5
            )
    
    def should_task_continue(self, current_step: int, max_steps: int) -> Tuple[bool, str, float]:
        """
        Intelligently determine if the task should continue based on deep understanding.
        
        Returns:
            (should_continue, reasoning, confidence)
        """
        if not self.current_goal or not self.action_reflections:
            return True, "Task just started, continuing", 0.5

        # Build progress summary
        progress_summary = ""
        for reflection in self.action_reflections[-3:]:  # Last 3 steps
            progress_summary += f"""
Step {reflection.step_number}:
- Action: {reflection.action_taken[:100]}...
- Outcome: {reflection.outcome_achieved}
- Progress: {reflection.progress_made}
- Remaining: {reflection.remaining_work}
- Confidence: {reflection.confidence_level}
"""
            
        decision_prompt = prompts.format_continuation_decision(
            primary_objective=self.current_goal.primary_objective,
            success_criteria=', '.join(self.current_goal.success_criteria),
            expected_deliverables=', '.join(self.current_goal.expected_deliverables),
            estimated_complexity=self.current_goal.estimated_complexity,
            steps_completed=len(self.action_reflections),
            progress_summary=progress_summary,
            current_step=current_step,
            max_steps=max_steps,
            time_elapsed=time.time() - self.task_started_at,
            recent_thoughts=str(self.internal_thoughts[-2:] if len(self.internal_thoughts) >= 2 else self.internal_thoughts)
        )

        try:
            response = self.model_client.chat.completions.create(
                model=METACOGNITION_MODEL,
                messages=[{"role": "user", "content": decision_prompt}],
                temperature=0.1
            )
            
            decision = json.loads(response.choices[0].message.content)
            
            should_continue = decision["decision"] == "CONTINUE"
            reasoning = decision["reasoning"]
            confidence = float(decision["confidence"])
            
            # Add to internal thoughts
            self.internal_thoughts.append(f"CONTINUATION DECISION: {decision['decision']} - {reasoning}")
            
            return should_continue, reasoning, confidence
            
        except Exception as e:
            # Fallback to conservative continuation
            return True, f"Error in decision making: {str(e)}", 0.3
    
    def get_internal_monologue(self) -> List[str]:
        """Return the agent's internal thoughts for debugging/transparency"""
        return self.internal_thoughts.copy()
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get a summary of task progress"""
        if not self.current_goal:
            return {"status": "No active task"}
            
        return {
            "goal": self.current_goal.primary_objective,
            "steps_completed": len(self.action_reflections),
            "average_confidence": sum(r.confidence_level for r in self.action_reflections) / len(self.action_reflections) if self.action_reflections else 0,
            "recent_progress": self.action_reflections[-1].progress_made if self.action_reflections else "No progress yet",
            "remaining_work": self.action_reflections[-1].remaining_work if self.action_reflections else "Unknown",
            "time_elapsed": time.time() - self.task_started_at if self.task_started_at else 0
        }
    
    def reset(self):
        """Reset the metacognition state for a new task"""
        self.current_goal = None
        self.action_reflections.clear()
        self.internal_thoughts.clear()
        self.task_started_at = None 