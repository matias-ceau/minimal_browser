"""Agent goal management for the OACS multi-agent system.

This module provides goal-oriented planning and task management for agents.
It enables agents to define high-level goals, decompose them into actionable
tasks, and track progress toward completion.

Key Features:
- Goal tracking with hierarchical relationships
- Task decomposition and dependency management
- Progress monitoring and state management
- Agent task assignment
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field


class GoalStatus(Enum):
    """Enumeration of possible goal/task states."""

    PENDING = "pending"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GoalPriority(Enum):
    """Priority levels for goals."""

    LOWEST = 0
    LOW = 25
    NORMAL = 50
    HIGH = 75
    HIGHEST = 100


class Goal(BaseModel):
    """Represents a high-level goal with success criteria.

    Goals can have parent/child relationships to form hierarchies and
    can be assigned to specific agents for execution.

    Attributes:
        id: Unique identifier for the goal
        title: Short descriptive title
        description: Detailed description of the goal
        status: Current state of the goal
        priority: Importance level (0-100)
        parent_goal_id: Optional parent goal ID for hierarchies
        success_criteria: List of criteria for goal completion
        assigned_agent_id: Optional agent assigned to this goal
        created_at: Timestamp when goal was created
        started_at: Timestamp when goal execution began
        completed_at: Timestamp when goal was completed
        metadata: Additional arbitrary data
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(min_length=1)
    description: str = ""
    status: GoalStatus = GoalStatus.PENDING
    priority: int = Field(default=GoalPriority.NORMAL.value, ge=0, le=100)
    parent_goal_id: Optional[str] = None
    success_criteria: List[str] = Field(default_factory=list)
    assigned_agent_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Task(BaseModel):
    """Represents an actionable task within a goal.

    Tasks are the atomic units of work that compose a goal. They can
    have dependencies on other tasks and track effort estimation.

    Attributes:
        id: Unique identifier for the task
        goal_id: ID of the parent goal
        title: Short descriptive title
        description: Detailed description of the task
        status: Current state of the task
        assigned_agent_id: Agent responsible for this task
        dependencies: List of task IDs that must complete first
        estimated_effort: Estimated time in minutes
        actual_effort: Actual time spent in minutes
        created_at: Timestamp when task was created
        completed_at: Timestamp when task was completed
        metadata: Additional arbitrary data
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal_id: str
    title: str = Field(min_length=1)
    description: str = ""
    status: GoalStatus = GoalStatus.PENDING
    assigned_agent_id: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    estimated_effort: Optional[int] = Field(default=None, ge=0)
    actual_effort: Optional[int] = Field(default=None, ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProgressInfo(BaseModel):
    """Progress tracking information for a goal.

    Provides detailed metrics about goal completion including task counts,
    percentage complete, and lists of tasks in different states.

    Attributes:
        goal_id: ID of the goal being tracked
        total_tasks: Total number of tasks in the goal
        completed_tasks: Number of completed tasks
        in_progress_tasks: Number of tasks currently in progress
        blocked_tasks: Number of blocked tasks
        percent_complete: Completion percentage (0-100)
        completed_task_ids: List of completed task IDs
        blocked_task_ids: List of blocked task IDs
    """

    goal_id: str
    total_tasks: int = Field(ge=0)
    completed_tasks: int = Field(ge=0)
    in_progress_tasks: int = Field(ge=0)
    blocked_tasks: int = Field(ge=0)
    percent_complete: float = Field(ge=0.0, le=100.0)
    completed_task_ids: List[str] = Field(default_factory=list)
    blocked_task_ids: List[str] = Field(default_factory=list)


class GoalManager:
    """Manages goals and tasks for the multi-agent system.

    Provides CRUD operations, task decomposition, dependency resolution,
    and progress tracking for goal-oriented agent workflows.
    """

    def __init__(self) -> None:
        """Initialize the goal manager with empty storage."""
        self._goals: Dict[str, Goal] = {}
        self._tasks: Dict[str, Task] = {}

    def create_goal(self, goal: Goal) -> str:
        """Create a new goal.

        Args:
            goal: Goal instance to create

        Returns:
            The ID of the created goal

        Raises:
            ValueError: If goal with this ID already exists
        """
        if goal.id in self._goals:
            raise ValueError(f"Goal with id {goal.id} already exists")

        # Validate parent_goal_id if provided
        if goal.parent_goal_id and goal.parent_goal_id not in self._goals:
            raise ValueError(f"Parent goal {goal.parent_goal_id} does not exist")

        self._goals[goal.id] = goal
        return goal.id

    def get_goal(self, goal_id: str) -> Goal:
        """Retrieve a goal by ID.

        Args:
            goal_id: ID of the goal to retrieve

        Returns:
            The Goal instance

        Raises:
            KeyError: If goal does not exist
        """
        if goal_id not in self._goals:
            raise KeyError(f"Goal {goal_id} not found")
        return self._goals[goal_id]

    def update_goal(self, goal_id: str, updates: Dict[str, Any]) -> None:
        """Update goal attributes.

        Args:
            goal_id: ID of the goal to update
            updates: Dictionary of attributes to update

        Raises:
            KeyError: If goal does not exist
            ValueError: If trying to update invalid fields
        """
        goal = self.get_goal(goal_id)

        # Update allowed fields
        for key, value in updates.items():
            if hasattr(goal, key):
                setattr(goal, key, value)
            else:
                raise ValueError(f"Invalid field: {key}")

    def delete_goal(self, goal_id: str) -> None:
        """Delete a goal and its associated tasks.

        Args:
            goal_id: ID of the goal to delete

        Raises:
            KeyError: If goal does not exist
        """
        if goal_id not in self._goals:
            raise KeyError(f"Goal {goal_id} not found")

        # Delete associated tasks
        task_ids = [tid for tid, task in self._tasks.items() if task.goal_id == goal_id]
        for task_id in task_ids:
            del self._tasks[task_id]

        del self._goals[goal_id]

    def create_task(self, task: Task) -> str:
        """Create a new task.

        Args:
            task: Task instance to create

        Returns:
            The ID of the created task

        Raises:
            ValueError: If task with this ID already exists or goal doesn't exist
        """
        if task.id in self._tasks:
            raise ValueError(f"Task with id {task.id} already exists")

        # Validate goal exists
        if task.goal_id not in self._goals:
            raise ValueError(f"Goal {task.goal_id} does not exist")

        # Validate dependencies exist
        for dep_id in task.dependencies:
            if dep_id not in self._tasks:
                raise ValueError(f"Dependency task {dep_id} does not exist")

        self._tasks[task.id] = task
        return task.id

    def get_task(self, task_id: str) -> Task:
        """Retrieve a task by ID.

        Args:
            task_id: ID of the task to retrieve

        Returns:
            The Task instance

        Raises:
            KeyError: If task does not exist
        """
        if task_id not in self._tasks:
            raise KeyError(f"Task {task_id} not found")
        return self._tasks[task_id]

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> None:
        """Update task attributes.

        Args:
            task_id: ID of the task to update
            updates: Dictionary of attributes to update

        Raises:
            KeyError: If task does not exist
            ValueError: If trying to update invalid fields
        """
        task = self.get_task(task_id)

        # Update allowed fields
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
            else:
                raise ValueError(f"Invalid field: {key}")

    def assign_task(self, task_id: str, agent_id: str) -> None:
        """Assign a task to an agent.

        Args:
            task_id: ID of the task to assign
            agent_id: ID of the agent to assign the task to

        Raises:
            KeyError: If task does not exist
        """
        task = self.get_task(task_id)
        task.assigned_agent_id = agent_id

    def get_goal_tasks(self, goal_id: str) -> List[Task]:
        """Get all tasks for a goal.

        Args:
            goal_id: ID of the goal

        Returns:
            List of tasks belonging to the goal
        """
        return [task for task in self._tasks.values() if task.goal_id == goal_id]

    def get_agent_tasks(self, agent_id: str) -> List[Task]:
        """Get all tasks assigned to an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            List of tasks assigned to the agent
        """
        return [
            task for task in self._tasks.values() if task.assigned_agent_id == agent_id
        ]

    def get_active_goals(self) -> List[Goal]:
        """Get all goals that are not completed, failed, or cancelled.

        Returns:
            List of active goals
        """
        return [
            goal
            for goal in self._goals.values()
            if goal.status
            not in (GoalStatus.COMPLETED, GoalStatus.FAILED, GoalStatus.CANCELLED)
        ]

    def get_child_goals(self, parent_goal_id: str) -> List[Goal]:
        """Get all child goals of a parent goal.

        Args:
            parent_goal_id: ID of the parent goal

        Returns:
            List of child goals
        """
        return [
            goal
            for goal in self._goals.values()
            if goal.parent_goal_id == parent_goal_id
        ]

    def resolve_task_dependencies(self, task_id: str) -> List[str]:
        """Resolve task dependencies using topological sort.

        Returns tasks in the order they must be executed, with the given
        task_id appearing last in the list.

        Args:
            task_id: ID of the task to resolve dependencies for

        Returns:
            Ordered list of task IDs (dependencies first, task_id last)

        Raises:
            KeyError: If task does not exist
            ValueError: If circular dependency detected
        """
        task = self.get_task(task_id)
        visited: Set[str] = set()
        temp_visited: Set[str] = set()
        result: List[str] = []

        def visit(tid: str) -> None:
            if tid in temp_visited:
                raise ValueError(f"Circular dependency detected involving task {tid}")
            if tid in visited:
                return

            temp_visited.add(tid)

            # Visit dependencies first
            if tid in self._tasks:
                for dep_id in self._tasks[tid].dependencies:
                    visit(dep_id)

            temp_visited.remove(tid)
            visited.add(tid)
            result.append(tid)

        visit(task_id)
        return result

    def calculate_progress(self, goal_id: str) -> ProgressInfo:
        """Calculate progress for a goal based on its tasks.

        Args:
            goal_id: ID of the goal to calculate progress for

        Returns:
            ProgressInfo with completion metrics

        Raises:
            KeyError: If goal does not exist
        """
        # Ensure goal exists
        self.get_goal(goal_id)

        tasks = self.get_goal_tasks(goal_id)
        total = len(tasks)

        if total == 0:
            return ProgressInfo(
                goal_id=goal_id,
                total_tasks=0,
                completed_tasks=0,
                in_progress_tasks=0,
                blocked_tasks=0,
                percent_complete=0.0,
                completed_task_ids=[],
                blocked_task_ids=[],
            )

        completed = [t for t in tasks if t.status == GoalStatus.COMPLETED]
        in_progress = [t for t in tasks if t.status == GoalStatus.IN_PROGRESS]
        blocked = [t for t in tasks if t.status == GoalStatus.BLOCKED]

        percent = (len(completed) / total) * 100.0

        return ProgressInfo(
            goal_id=goal_id,
            total_tasks=total,
            completed_tasks=len(completed),
            in_progress_tasks=len(in_progress),
            blocked_tasks=len(blocked),
            percent_complete=round(percent, 2),
            completed_task_ids=[t.id for t in completed],
            blocked_task_ids=[t.id for t in blocked],
        )

    def update_progress(self, goal_id: str, progress: float) -> None:
        """Update goal status based on progress percentage.

        Automatically transitions goal status based on progress:
        - 0%: PENDING or PLANNED
        - 0-100%: IN_PROGRESS
        - 100%: COMPLETED

        Args:
            goal_id: ID of the goal to update
            progress: Progress percentage (0-100)

        Raises:
            KeyError: If goal does not exist
            ValueError: If progress is out of range
        """
        if not 0 <= progress <= 100:
            raise ValueError(f"Progress must be between 0 and 100, got {progress}")

        goal = self.get_goal(goal_id)

        if progress == 0:
            if goal.status == GoalStatus.PENDING:
                pass  # Stay in PENDING
        elif progress < 100:
            if goal.status in (GoalStatus.PENDING, GoalStatus.PLANNED):
                goal.status = GoalStatus.IN_PROGRESS
                goal.started_at = datetime.utcnow()
        else:  # progress == 100
            goal.status = GoalStatus.COMPLETED
            goal.completed_at = datetime.utcnow()

    def decompose_goal(self, goal_id: str, task_titles: List[str]) -> List[str]:
        """Decompose a goal into a list of tasks.

        Creates tasks for the goal based on provided titles. This is a simple
        decomposition; more advanced AI-assisted decomposition can be added later.

        Args:
            goal_id: ID of the goal to decompose
            task_titles: List of task titles to create

        Returns:
            List of created task IDs

        Raises:
            KeyError: If goal does not exist
        """
        # Ensure goal exists
        self.get_goal(goal_id)

        task_ids = []
        for title in task_titles:
            task = Task(goal_id=goal_id, title=title, status=GoalStatus.PENDING)
            task_id = self.create_task(task)
            task_ids.append(task_id)

        return task_ids
