"""Example usage scenarios for the Agent Goal Management system.

This module demonstrates how to use the goal management features including:
- Creating and managing goals
- Task decomposition
- Agent task assignment
- Progress tracking
- Goal hierarchies
"""

import importlib.util
import sys
from pathlib import Path


# Import goals module directly to avoid PySide6 dependency
def import_module_direct(name: str, filepath: str):
    """Import a module directly from file path."""
    spec = importlib.util.spec_from_file_location(name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Import goals module
src_dir = Path(__file__).parent.parent / "src" / "minimal_browser"
goals_module = import_module_direct(
    'minimal_browser.coordination.goals',
    str(src_dir / 'coordination' / 'goals.py')
)

# Extract the classes we need
Goal = goals_module.Goal
GoalManager = goals_module.GoalManager
GoalPriority = goals_module.GoalPriority
GoalStatus = goals_module.GoalStatus
Task = goals_module.Task


def example_simple_goal():
    """Example 1: Creating and managing a simple goal."""
    print("=== Example 1: Simple Goal Management ===\n")
    
    # Create a goal manager
    manager = GoalManager()
    
    # Create a simple goal
    goal = Goal(
        title="Research Python web frameworks",
        description="Compare Flask, Django, and FastAPI for the new project",
        priority=GoalPriority.HIGH.value,
        success_criteria=[
            "Document key differences",
            "Create comparison table",
            "Recommend framework for project"
        ]
    )
    
    goal_id = manager.create_goal(goal)
    print(f"Created goal: {goal.title}")
    print(f"Goal ID: {goal_id}")
    print(f"Status: {goal.status.value}\n")
    
    return manager, goal_id


def example_task_decomposition():
    """Example 2: Decomposing a goal into tasks."""
    print("=== Example 2: Goal Decomposition ===\n")
    
    manager = GoalManager()
    
    # Create a goal
    goal = Goal(
        title="Research Python web frameworks",
        description="Compare Flask, Django, and FastAPI"
    )
    goal_id = manager.create_goal(goal)
    
    # Decompose into tasks
    task_titles = [
        "Search for Flask documentation",
        "Search for Django documentation",
        "Search for FastAPI documentation",
        "Create comparison table",
        "Write recommendation summary"
    ]
    
    task_ids = manager.decompose_goal(goal_id, task_titles)
    
    print(f"Decomposed goal '{goal.title}' into {len(task_ids)} tasks:")
    for i, task_id in enumerate(task_ids, 1):
        task = manager.get_task(task_id)
        print(f"  {i}. {task.title}")
    print()
    
    return manager, goal_id, task_ids


def example_agent_assignment():
    """Example 3: Assigning tasks to agents."""
    print("=== Example 3: Agent Task Assignment ===\n")
    
    manager, goal_id, task_ids = example_task_decomposition()
    
    # Assign tasks to different agents
    manager.assign_task(task_ids[0], "research_agent_1")
    manager.assign_task(task_ids[1], "research_agent_2")
    manager.assign_task(task_ids[2], "research_agent_3")
    manager.assign_task(task_ids[3], "analysis_agent")
    manager.assign_task(task_ids[4], "writing_agent")
    
    print("Task assignments:")
    for task_id in task_ids:
        task = manager.get_task(task_id)
        print(f"  - {task.title} -> {task.assigned_agent_id}")
    
    # Get tasks for a specific agent
    agent_tasks = manager.get_agent_tasks("research_agent_1")
    print(f"\nTasks for 'research_agent_1': {len(agent_tasks)}")
    for task in agent_tasks:
        print(f"  - {task.title}")
    print()
    
    return manager, goal_id, task_ids


def example_progress_tracking():
    """Example 4: Tracking goal progress."""
    print("=== Example 4: Progress Tracking ===\n")
    
    manager, goal_id, task_ids = example_agent_assignment()
    
    # Simulate task completion
    manager.update_task(task_ids[0], {"status": GoalStatus.COMPLETED})
    manager.update_task(task_ids[1], {"status": GoalStatus.COMPLETED})
    manager.update_task(task_ids[2], {"status": GoalStatus.IN_PROGRESS})
    manager.update_task(task_ids[3], {"status": GoalStatus.BLOCKED})
    
    # Calculate progress
    progress = manager.calculate_progress(goal_id)
    
    print("Goal Progress:")
    print(f"  Total tasks: {progress.total_tasks}")
    print(f"  Completed: {progress.completed_tasks}")
    print(f"  In progress: {progress.in_progress_tasks}")
    print(f"  Blocked: {progress.blocked_tasks}")
    print(f"  Completion: {progress.percent_complete}%")
    
    # Update goal status based on progress
    manager.update_progress(goal_id, progress.percent_complete)
    updated_goal = manager.get_goal(goal_id)
    print(f"  Goal status: {updated_goal.status.value}\n")
    
    return manager, goal_id


def example_task_dependencies():
    """Example 5: Managing task dependencies."""
    print("=== Example 5: Task Dependencies ===\n")
    
    manager = GoalManager()
    
    # Create a goal
    goal = Goal(title="Build web application")
    goal_id = manager.create_goal(goal)
    
    # Create tasks with dependencies
    task1 = Task(goal_id=goal_id, title="Design database schema")
    task1_id = manager.create_task(task1)
    
    task2 = Task(
        goal_id=goal_id,
        title="Create database tables",
        dependencies=[task1_id]
    )
    task2_id = manager.create_task(task2)
    
    task3 = Task(
        goal_id=goal_id,
        title="Implement API endpoints",
        dependencies=[task2_id]
    )
    task3_id = manager.create_task(task3)
    
    task4 = Task(
        goal_id=goal_id,
        title="Write unit tests",
        dependencies=[task3_id]
    )
    task4_id = manager.create_task(task4)
    
    # Resolve dependencies
    execution_order = manager.resolve_task_dependencies(task4_id)
    
    print("Task execution order (with dependencies):")
    for i, task_id in enumerate(execution_order, 1):
        task = manager.get_task(task_id)
        print(f"  {i}. {task.title}")
    print()
    
    return manager, goal_id


def example_goal_hierarchy():
    """Example 6: Creating goal hierarchies."""
    print("=== Example 6: Goal Hierarchy ===\n")
    
    manager = GoalManager()
    
    # Create parent goal
    parent_goal = Goal(
        title="Launch new product",
        description="Complete product launch by Q2",
        priority=GoalPriority.HIGHEST.value
    )
    parent_id = manager.create_goal(parent_goal)
    
    # Create child goals
    child1 = Goal(
        title="Complete product development",
        parent_goal_id=parent_id,
        priority=GoalPriority.HIGH.value
    )
    child1_id = manager.create_goal(child1)
    
    child2 = Goal(
        title="Prepare marketing materials",
        parent_goal_id=parent_id,
        priority=GoalPriority.NORMAL.value
    )
    child2_id = manager.create_goal(child2)
    
    child3 = Goal(
        title="Set up customer support",
        parent_goal_id=parent_id,
        priority=GoalPriority.NORMAL.value
    )
    child3_id = manager.create_goal(child3)
    
    # Display hierarchy
    print(f"Parent Goal: {parent_goal.title}")
    children = manager.get_child_goals(parent_id)
    print(f"Child Goals ({len(children)}):")
    for child in children:
        print(f"  - {child.title} (Priority: {child.priority})")
    print()
    
    return manager, parent_id


def example_multi_agent_workflow():
    """Example 7: Multi-agent workflow coordination."""
    print("=== Example 7: Multi-Agent Workflow ===\n")
    
    manager = GoalManager()
    
    # Create goal for website performance analysis
    goal = Goal(
        title="Analyze website performance",
        description="Comprehensive performance analysis",
        success_criteria=[
            "Load time < 2s",
            "Lighthouse score > 90",
            "No accessibility issues"
        ]
    )
    goal_id = manager.create_goal(goal)
    
    # Create parallel tasks for different agents
    fetch_task = Task(
        goal_id=goal_id,
        title="Fetch webpage",
        assigned_agent_id="fetch_agent",
        estimated_effort=5
    )
    fetch_id = manager.create_task(fetch_task)
    
    lighthouse_task = Task(
        goal_id=goal_id,
        title="Run Lighthouse audit",
        assigned_agent_id="lighthouse_agent",
        dependencies=[fetch_id],
        estimated_effort=30
    )
    lighthouse_id = manager.create_task(lighthouse_task)
    
    accessibility_task = Task(
        goal_id=goal_id,
        title="Check accessibility",
        assigned_agent_id="accessibility_agent",
        dependencies=[fetch_id],
        estimated_effort=20
    )
    accessibility_id = manager.create_task(accessibility_task)
    
    analysis_task = Task(
        goal_id=goal_id,
        title="Analyze results",
        assigned_agent_id="analysis_agent",
        dependencies=[lighthouse_id, accessibility_id],
        estimated_effort=15
    )
    analysis_id = manager.create_task(analysis_task)
    
    print(f"Goal: {goal.title}")
    print("\nTask workflow:")
    tasks = manager.get_goal_tasks(goal_id)
    for task in tasks:
        deps = ", ".join([manager.get_task(d).title for d in task.dependencies]) if task.dependencies else "None"
        print(f"  - {task.title}")
        print(f"    Agent: {task.assigned_agent_id}")
        print(f"    Depends on: {deps}")
        print(f"    Estimated effort: {task.estimated_effort} min")
    print()
    
    return manager, goal_id


def example_active_goals():
    """Example 8: Querying active goals."""
    print("=== Example 8: Active Goals Query ===\n")
    
    manager = GoalManager()
    
    # Create goals in different states
    goal1 = Goal(title="Active Goal 1", status=GoalStatus.IN_PROGRESS)
    goal2 = Goal(title="Active Goal 2", status=GoalStatus.PENDING)
    goal3 = Goal(title="Completed Goal", status=GoalStatus.COMPLETED)
    goal4 = Goal(title="Failed Goal", status=GoalStatus.FAILED)
    goal5 = Goal(title="Active Goal 3", status=GoalStatus.BLOCKED)
    
    manager.create_goal(goal1)
    manager.create_goal(goal2)
    manager.create_goal(goal3)
    manager.create_goal(goal4)
    manager.create_goal(goal5)
    
    # Query active goals
    active_goals = manager.get_active_goals()
    
    print(f"Total goals: 5")
    print(f"Active goals: {len(active_goals)}")
    print("\nActive goals:")
    for goal in active_goals:
        print(f"  - {goal.title} (Status: {goal.status.value})")
    print()


def main():
    """Run all examples."""
    print("=" * 60)
    print("Agent Goal Management System - Usage Examples")
    print("=" * 60)
    print()
    
    try:
        example_simple_goal()
        example_task_decomposition()
        example_agent_assignment()
        example_progress_tracking()
        example_task_dependencies()
        example_goal_hierarchy()
        example_multi_agent_workflow()
        example_active_goals()
        
        print("=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
