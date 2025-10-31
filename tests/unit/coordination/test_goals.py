"""Unit tests for goal management.

These tests validate the goal and task management system including:
- Goal and Task model validation
- GoalManager CRUD operations
- Task dependency resolution
- Progress tracking
- Goal hierarchies
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

# Import the goals module directly
def import_module_direct(name: str, filepath: str):
    """Import a module directly from file path."""
    spec = importlib.util.spec_from_file_location(name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# Import goals module
try:
    src_dir = Path(__file__).parent.parent.parent.parent / "src" / "minimal_browser"
    goals_module = import_module_direct(
        'minimal_browser.coordination.goals',
        str(src_dir / 'coordination' / 'goals.py')
    )
    
    # Extract the classes we need
    Goal = goals_module.Goal
    Task = goals_module.Task
    GoalStatus = goals_module.GoalStatus
    GoalPriority = goals_module.GoalPriority
    ProgressInfo = goals_module.ProgressInfo
    GoalManager = goals_module.GoalManager
    
    GOALS_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    GOALS_AVAILABLE = False
    skip_reason = f"Cannot import goals: {e}"

pytestmark = pytest.mark.skipif(
    not GOALS_AVAILABLE,
    reason="Goals module not available"
)


class TestGoalModel:
    """Test Goal Pydantic model."""
    
    def test_create_minimal_goal(self):
        """Test creating a goal with minimal required fields."""
        goal = Goal(title="Test Goal")
        assert goal.title == "Test Goal"
        assert goal.status == GoalStatus.PENDING
        assert goal.priority == GoalPriority.NORMAL.value
        assert goal.id is not None
        assert isinstance(goal.created_at, datetime)
    
    def test_create_full_goal(self):
        """Test creating a goal with all fields."""
        goal = Goal(
            title="Research Task",
            description="Research Python frameworks",
            status=GoalStatus.IN_PROGRESS,
            priority=GoalPriority.HIGH.value,
            success_criteria=["Criterion 1", "Criterion 2"],
            assigned_agent_id="agent-123",
            metadata={"key": "value"}
        )
        assert goal.title == "Research Task"
        assert goal.description == "Research Python frameworks"
        assert goal.status == GoalStatus.IN_PROGRESS
        assert goal.priority == GoalPriority.HIGH.value
        assert len(goal.success_criteria) == 2
        assert goal.assigned_agent_id == "agent-123"
        assert goal.metadata["key"] == "value"
    
    def test_goal_empty_title_fails(self):
        """Test that empty title is rejected."""
        with pytest.raises(ValidationError):
            Goal(title="")
    
    def test_goal_priority_validation(self):
        """Test that priority is validated to be between 0 and 100."""
        # Valid priorities
        Goal(title="Test", priority=0)
        Goal(title="Test", priority=50)
        Goal(title="Test", priority=100)
        
        # Invalid priorities
        with pytest.raises(ValidationError):
            Goal(title="Test", priority=-1)
        with pytest.raises(ValidationError):
            Goal(title="Test", priority=101)
    
    def test_goal_id_auto_generated(self):
        """Test that goal ID is automatically generated."""
        goal1 = Goal(title="Goal 1")
        goal2 = Goal(title="Goal 2")
        assert goal1.id != goal2.id
        assert len(goal1.id) > 0
        assert len(goal2.id) > 0


class TestTaskModel:
    """Test Task Pydantic model."""
    
    def test_create_minimal_task(self):
        """Test creating a task with minimal required fields."""
        task = Task(goal_id="goal-123", title="Test Task")
        assert task.title == "Test Task"
        assert task.goal_id == "goal-123"
        assert task.status == GoalStatus.PENDING
        assert task.id is not None
        assert isinstance(task.created_at, datetime)
    
    def test_create_full_task(self):
        """Test creating a task with all fields."""
        task = Task(
            goal_id="goal-123",
            title="Research Flask",
            description="Study Flask documentation",
            status=GoalStatus.IN_PROGRESS,
            assigned_agent_id="agent-456",
            dependencies=["task-1", "task-2"],
            estimated_effort=60,
            actual_effort=45,
            metadata={"priority": "high"}
        )
        assert task.title == "Research Flask"
        assert task.description == "Study Flask documentation"
        assert task.status == GoalStatus.IN_PROGRESS
        assert task.assigned_agent_id == "agent-456"
        assert len(task.dependencies) == 2
        assert task.estimated_effort == 60
        assert task.actual_effort == 45
    
    def test_task_empty_title_fails(self):
        """Test that empty title is rejected."""
        with pytest.raises(ValidationError):
            Task(goal_id="goal-123", title="")
    
    def test_task_effort_validation(self):
        """Test that effort fields must be non-negative."""
        # Valid efforts
        Task(goal_id="goal-123", title="Test", estimated_effort=0)
        Task(goal_id="goal-123", title="Test", estimated_effort=100)
        
        # Invalid efforts
        with pytest.raises(ValidationError):
            Task(goal_id="goal-123", title="Test", estimated_effort=-1)
        with pytest.raises(ValidationError):
            Task(goal_id="goal-123", title="Test", actual_effort=-1)


class TestProgressInfo:
    """Test ProgressInfo model."""
    
    def test_create_progress_info(self):
        """Test creating progress info."""
        progress = ProgressInfo(
            goal_id="goal-123",
            total_tasks=10,
            completed_tasks=5,
            in_progress_tasks=2,
            blocked_tasks=1,
            percent_complete=50.0,
            completed_task_ids=["t1", "t2"],
            blocked_task_ids=["t3"]
        )
        assert progress.goal_id == "goal-123"
        assert progress.total_tasks == 10
        assert progress.completed_tasks == 5
        assert progress.percent_complete == 50.0
    
    def test_progress_validation(self):
        """Test that progress fields are validated."""
        # Valid progress
        ProgressInfo(
            goal_id="goal-123",
            total_tasks=0,
            completed_tasks=0,
            in_progress_tasks=0,
            blocked_tasks=0,
            percent_complete=0.0
        )
        
        # Invalid values
        with pytest.raises(ValidationError):
            ProgressInfo(
                goal_id="goal-123",
                total_tasks=-1,
                completed_tasks=0,
                in_progress_tasks=0,
                blocked_tasks=0,
                percent_complete=0.0
            )
        
        with pytest.raises(ValidationError):
            ProgressInfo(
                goal_id="goal-123",
                total_tasks=10,
                completed_tasks=5,
                in_progress_tasks=2,
                blocked_tasks=1,
                percent_complete=150.0  # Invalid: > 100
            )


class TestGoalManagerCRUD:
    """Test GoalManager CRUD operations."""
    
    def test_create_and_get_goal(self):
        """Test creating and retrieving a goal."""
        manager = GoalManager()
        goal = Goal(title="Test Goal")
        goal_id = manager.create_goal(goal)
        
        retrieved = manager.get_goal(goal_id)
        assert retrieved.id == goal_id
        assert retrieved.title == "Test Goal"
    
    def test_create_duplicate_goal_fails(self):
        """Test that creating a goal with duplicate ID fails."""
        manager = GoalManager()
        goal = Goal(id="test-id", title="Test Goal")
        manager.create_goal(goal)
        
        # Try to create another goal with same ID
        duplicate = Goal(id="test-id", title="Another Goal")
        with pytest.raises(ValueError, match="already exists"):
            manager.create_goal(duplicate)
    
    def test_get_nonexistent_goal_fails(self):
        """Test that getting a nonexistent goal raises KeyError."""
        manager = GoalManager()
        with pytest.raises(KeyError):
            manager.get_goal("nonexistent-id")
    
    def test_update_goal(self):
        """Test updating goal attributes."""
        manager = GoalManager()
        goal = Goal(title="Original Title")
        goal_id = manager.create_goal(goal)
        
        manager.update_goal(goal_id, {"title": "Updated Title", "status": GoalStatus.IN_PROGRESS})
        
        updated = manager.get_goal(goal_id)
        assert updated.title == "Updated Title"
        assert updated.status == GoalStatus.IN_PROGRESS
    
    def test_update_invalid_field_fails(self):
        """Test that updating invalid field raises ValueError."""
        manager = GoalManager()
        goal = Goal(title="Test Goal")
        goal_id = manager.create_goal(goal)
        
        with pytest.raises(ValueError, match="Invalid field"):
            manager.update_goal(goal_id, {"nonexistent_field": "value"})
    
    def test_delete_goal(self):
        """Test deleting a goal."""
        manager = GoalManager()
        goal = Goal(title="Test Goal")
        goal_id = manager.create_goal(goal)
        
        manager.delete_goal(goal_id)
        
        with pytest.raises(KeyError):
            manager.get_goal(goal_id)
    
    def test_delete_goal_deletes_tasks(self):
        """Test that deleting a goal also deletes its tasks."""
        manager = GoalManager()
        goal = Goal(title="Test Goal")
        goal_id = manager.create_goal(goal)
        
        task = Task(goal_id=goal_id, title="Test Task")
        task_id = manager.create_task(task)
        
        manager.delete_goal(goal_id)
        
        with pytest.raises(KeyError):
            manager.get_task(task_id)


class TestGoalManagerTasks:
    """Test GoalManager task operations."""
    
    def test_create_and_get_task(self):
        """Test creating and retrieving a task."""
        manager = GoalManager()
        goal = Goal(title="Test Goal")
        goal_id = manager.create_goal(goal)
        
        task = Task(goal_id=goal_id, title="Test Task")
        task_id = manager.create_task(task)
        
        retrieved = manager.get_task(task_id)
        assert retrieved.id == task_id
        assert retrieved.title == "Test Task"
        assert retrieved.goal_id == goal_id
    
    def test_create_task_nonexistent_goal_fails(self):
        """Test that creating a task for nonexistent goal fails."""
        manager = GoalManager()
        task = Task(goal_id="nonexistent-goal", title="Test Task")
        
        with pytest.raises(ValueError, match="does not exist"):
            manager.create_task(task)
    
    def test_create_task_invalid_dependency_fails(self):
        """Test that creating a task with invalid dependency fails."""
        manager = GoalManager()
        goal = Goal(title="Test Goal")
        goal_id = manager.create_goal(goal)
        
        task = Task(
            goal_id=goal_id,
            title="Test Task",
            dependencies=["nonexistent-task"]
        )
        
        with pytest.raises(ValueError, match="does not exist"):
            manager.create_task(task)
    
    def test_update_task(self):
        """Test updating task attributes."""
        manager = GoalManager()
        goal = Goal(title="Test Goal")
        goal_id = manager.create_goal(goal)
        
        task = Task(goal_id=goal_id, title="Original Title")
        task_id = manager.create_task(task)
        
        manager.update_task(task_id, {"title": "Updated Title", "status": GoalStatus.COMPLETED})
        
        updated = manager.get_task(task_id)
        assert updated.title == "Updated Title"
        assert updated.status == GoalStatus.COMPLETED
    
    def test_assign_task(self):
        """Test assigning a task to an agent."""
        manager = GoalManager()
        goal = Goal(title="Test Goal")
        goal_id = manager.create_goal(goal)
        
        task = Task(goal_id=goal_id, title="Test Task")
        task_id = manager.create_task(task)
        
        manager.assign_task(task_id, "agent-123")
        
        updated = manager.get_task(task_id)
        assert updated.assigned_agent_id == "agent-123"
    
    def test_get_goal_tasks(self):
        """Test retrieving all tasks for a goal."""
        manager = GoalManager()
        goal = Goal(title="Test Goal")
        goal_id = manager.create_goal(goal)
        
        task1 = Task(goal_id=goal_id, title="Task 1")
        task2 = Task(goal_id=goal_id, title="Task 2")
        manager.create_task(task1)
        manager.create_task(task2)
        
        tasks = manager.get_goal_tasks(goal_id)
        assert len(tasks) == 2
        assert {t.title for t in tasks} == {"Task 1", "Task 2"}
    
    def test_get_agent_tasks(self):
        """Test retrieving all tasks for an agent."""
        manager = GoalManager()
        goal = Goal(title="Test Goal")
        goal_id = manager.create_goal(goal)
        
        task1 = Task(goal_id=goal_id, title="Task 1", assigned_agent_id="agent-123")
        task2 = Task(goal_id=goal_id, title="Task 2", assigned_agent_id="agent-123")
        task3 = Task(goal_id=goal_id, title="Task 3", assigned_agent_id="agent-456")
        manager.create_task(task1)
        manager.create_task(task2)
        manager.create_task(task3)
        
        agent_tasks = manager.get_agent_tasks("agent-123")
        assert len(agent_tasks) == 2
        assert {t.title for t in agent_tasks} == {"Task 1", "Task 2"}


class TestGoalHierarchy:
    """Test goal hierarchy and parent/child relationships."""
    
    def test_create_goal_with_parent(self):
        """Test creating a goal with a parent goal."""
        manager = GoalManager()
        parent = Goal(title="Parent Goal")
        parent_id = manager.create_goal(parent)
        
        child = Goal(title="Child Goal", parent_goal_id=parent_id)
        child_id = manager.create_goal(child)
        
        retrieved = manager.get_goal(child_id)
        assert retrieved.parent_goal_id == parent_id
    
    def test_create_goal_invalid_parent_fails(self):
        """Test that creating a goal with invalid parent fails."""
        manager = GoalManager()
        child = Goal(title="Child Goal", parent_goal_id="nonexistent-parent")
        
        with pytest.raises(ValueError, match="does not exist"):
            manager.create_goal(child)
    
    def test_get_child_goals(self):
        """Test retrieving child goals."""
        manager = GoalManager()
        parent = Goal(title="Parent Goal")
        parent_id = manager.create_goal(parent)
        
        child1 = Goal(title="Child 1", parent_goal_id=parent_id)
        child2 = Goal(title="Child 2", parent_goal_id=parent_id)
        manager.create_goal(child1)
        manager.create_goal(child2)
        
        children = manager.get_child_goals(parent_id)
        assert len(children) == 2
        assert {c.title for c in children} == {"Child 1", "Child 2"}
    
    def test_get_active_goals(self):
        """Test retrieving active goals."""
        manager = GoalManager()
        goal1 = Goal(title="Active 1", status=GoalStatus.IN_PROGRESS)
        goal2 = Goal(title="Active 2", status=GoalStatus.PENDING)
        goal3 = Goal(title="Completed", status=GoalStatus.COMPLETED)
        goal4 = Goal(title="Failed", status=GoalStatus.FAILED)
        
        manager.create_goal(goal1)
        manager.create_goal(goal2)
        manager.create_goal(goal3)
        manager.create_goal(goal4)
        
        active = manager.get_active_goals()
        assert len(active) == 2
        assert {g.title for g in active} == {"Active 1", "Active 2"}


class TestTaskDependencies:
    """Test task dependency resolution."""
    
    def test_resolve_simple_dependency(self):
        """Test resolving a simple dependency chain."""
        manager = GoalManager()
        goal = Goal(title="Test Goal")
        goal_id = manager.create_goal(goal)
        
        task1 = Task(goal_id=goal_id, title="Task 1")
        task1_id = manager.create_task(task1)
        
        task2 = Task(goal_id=goal_id, title="Task 2", dependencies=[task1_id])
        task2_id = manager.create_task(task2)
        
        order = manager.resolve_task_dependencies(task2_id)
        assert order == [task1_id, task2_id]
    
    def test_resolve_complex_dependencies(self):
        """Test resolving complex dependency graph."""
        manager = GoalManager()
        goal = Goal(title="Test Goal")
        goal_id = manager.create_goal(goal)
        
        # Create dependency graph: task1 -> task2 -> task4
        #                          task3 -> task4
        task1 = Task(goal_id=goal_id, title="Task 1")
        task1_id = manager.create_task(task1)
        
        task2 = Task(goal_id=goal_id, title="Task 2", dependencies=[task1_id])
        task2_id = manager.create_task(task2)
        
        task3 = Task(goal_id=goal_id, title="Task 3")
        task3_id = manager.create_task(task3)
        
        task4 = Task(goal_id=goal_id, title="Task 4", dependencies=[task2_id, task3_id])
        task4_id = manager.create_task(task4)
        
        order = manager.resolve_task_dependencies(task4_id)
        
        # Task 1 must come before Task 2
        assert order.index(task1_id) < order.index(task2_id)
        # Task 2 must come before Task 4
        assert order.index(task2_id) < order.index(task4_id)
        # Task 3 must come before Task 4
        assert order.index(task3_id) < order.index(task4_id)
        # Task 4 must be last
        assert order[-1] == task4_id
    
    def test_circular_dependency_detected(self):
        """Test that circular dependencies are detected."""
        manager = GoalManager()
        goal = Goal(title="Test Goal")
        goal_id = manager.create_goal(goal)
        
        task1 = Task(goal_id=goal_id, title="Task 1")
        task1_id = manager.create_task(task1)
        
        task2 = Task(goal_id=goal_id, title="Task 2", dependencies=[task1_id])
        task2_id = manager.create_task(task2)
        
        # Manually create circular dependency (task1 -> task2 -> task1)
        manager._tasks[task1_id].dependencies = [task2_id]
        
        with pytest.raises(ValueError, match="Circular dependency"):
            manager.resolve_task_dependencies(task1_id)


class TestProgressTracking:
    """Test progress tracking functionality."""
    
    def test_calculate_progress_no_tasks(self):
        """Test progress calculation for goal with no tasks."""
        manager = GoalManager()
        goal = Goal(title="Test Goal")
        goal_id = manager.create_goal(goal)
        
        progress = manager.calculate_progress(goal_id)
        assert progress.total_tasks == 0
        assert progress.completed_tasks == 0
        assert progress.percent_complete == 0.0
    
    def test_calculate_progress_with_tasks(self):
        """Test progress calculation with various task states."""
        manager = GoalManager()
        goal = Goal(title="Test Goal")
        goal_id = manager.create_goal(goal)
        
        # Create tasks in different states
        task1 = Task(goal_id=goal_id, title="Task 1", status=GoalStatus.COMPLETED)
        task2 = Task(goal_id=goal_id, title="Task 2", status=GoalStatus.COMPLETED)
        task3 = Task(goal_id=goal_id, title="Task 3", status=GoalStatus.IN_PROGRESS)
        task4 = Task(goal_id=goal_id, title="Task 4", status=GoalStatus.BLOCKED)
        task5 = Task(goal_id=goal_id, title="Task 5", status=GoalStatus.PENDING)
        
        manager.create_task(task1)
        manager.create_task(task2)
        manager.create_task(task3)
        manager.create_task(task4)
        manager.create_task(task5)
        
        progress = manager.calculate_progress(goal_id)
        assert progress.total_tasks == 5
        assert progress.completed_tasks == 2
        assert progress.in_progress_tasks == 1
        assert progress.blocked_tasks == 1
        assert progress.percent_complete == 40.0
        assert len(progress.completed_task_ids) == 2
        assert len(progress.blocked_task_ids) == 1
    
    def test_update_progress_transitions(self):
        """Test that update_progress transitions goal status appropriately."""
        manager = GoalManager()
        goal = Goal(title="Test Goal", status=GoalStatus.PENDING)
        goal_id = manager.create_goal(goal)
        
        # 0% progress - stays PENDING
        manager.update_progress(goal_id, 0)
        assert manager.get_goal(goal_id).status == GoalStatus.PENDING
        
        # Partial progress - transitions to IN_PROGRESS
        manager.update_progress(goal_id, 50)
        updated = manager.get_goal(goal_id)
        assert updated.status == GoalStatus.IN_PROGRESS
        assert updated.started_at is not None
        
        # 100% progress - transitions to COMPLETED
        manager.update_progress(goal_id, 100)
        completed = manager.get_goal(goal_id)
        assert completed.status == GoalStatus.COMPLETED
        assert completed.completed_at is not None
    
    def test_update_progress_invalid_range(self):
        """Test that invalid progress values are rejected."""
        manager = GoalManager()
        goal = Goal(title="Test Goal")
        goal_id = manager.create_goal(goal)
        
        with pytest.raises(ValueError, match="between 0 and 100"):
            manager.update_progress(goal_id, -1)
        
        with pytest.raises(ValueError, match="between 0 and 100"):
            manager.update_progress(goal_id, 101)


class TestGoalDecomposition:
    """Test goal decomposition functionality."""
    
    def test_decompose_goal(self):
        """Test basic goal decomposition."""
        manager = GoalManager()
        goal = Goal(title="Research Web Frameworks")
        goal_id = manager.create_goal(goal)
        
        task_titles = [
            "Research Flask",
            "Research Django",
            "Research FastAPI",
            "Create comparison table"
        ]
        
        task_ids = manager.decompose_goal(goal_id, task_titles)
        
        assert len(task_ids) == 4
        tasks = manager.get_goal_tasks(goal_id)
        assert len(tasks) == 4
        assert {t.title for t in tasks} == set(task_titles)
    
    def test_decompose_nonexistent_goal_fails(self):
        """Test that decomposing nonexistent goal fails."""
        manager = GoalManager()
        
        with pytest.raises(KeyError):
            manager.decompose_goal("nonexistent-goal", ["Task 1"])
