# Agent Goal Management

The Agent Goal Management module provides goal-oriented planning and task management for the OACS (Open Agent Coordination System) multi-agent infrastructure.

## Features

### Goal Management
- **Goal CRUD operations**: Create, read, update, and delete goals
- **Goal hierarchies**: Support for parent/child goal relationships
- **Status tracking**: Comprehensive state management (pending, in_progress, completed, etc.)
- **Priority levels**: Prioritize goals from 0 (lowest) to 100 (highest)
- **Success criteria**: Define measurable completion criteria for goals

### Task Management
- **Task decomposition**: Break down goals into actionable tasks
- **Dependency management**: Define task dependencies with topological sorting
- **Effort estimation**: Track estimated and actual effort in minutes
- **Agent assignment**: Assign tasks to specific agents
- **Task queries**: Retrieve tasks by goal, agent, or status

### Progress Tracking
- **Real-time progress**: Calculate completion percentages automatically
- **Task state monitoring**: Track completed, in-progress, and blocked tasks
- **Automatic status updates**: Goals transition states based on progress
- **Progress metrics**: Detailed metrics including task counts and percentages

## Data Models

### Goal
Represents a high-level objective with success criteria:
- `id`: Unique identifier (auto-generated UUID)
- `title`: Short descriptive title (required)
- `description`: Detailed description
- `status`: Current state (GoalStatus enum)
- `priority`: Importance level (0-100)
- `parent_goal_id`: Optional parent goal for hierarchies
- `success_criteria`: List of completion criteria
- `assigned_agent_id`: Optional agent assignment
- `created_at`, `started_at`, `completed_at`: Timestamps
- `metadata`: Additional arbitrary data

### Task
Represents an actionable unit of work within a goal:
- `id`: Unique identifier (auto-generated UUID)
- `goal_id`: Parent goal ID (required)
- `title`: Short descriptive title (required)
- `description`: Detailed description
- `status`: Current state (GoalStatus enum)
- `assigned_agent_id`: Agent responsible for execution
- `dependencies`: List of task IDs that must complete first
- `estimated_effort`: Estimated time in minutes
- `actual_effort`: Actual time spent in minutes
- `created_at`, `completed_at`: Timestamps
- `metadata`: Additional arbitrary data

### GoalStatus
Enumeration of possible goal/task states:
- `PENDING`: Not yet started
- `PLANNED`: Planning phase complete
- `IN_PROGRESS`: Currently being worked on
- `BLOCKED`: Waiting on dependencies or external factors
- `COMPLETED`: Successfully finished
- `FAILED`: Failed to complete
- `CANCELLED`: Cancelled before completion

### ProgressInfo
Progress metrics for a goal:
- `goal_id`: Goal being tracked
- `total_tasks`: Total number of tasks
- `completed_tasks`: Number of completed tasks
- `in_progress_tasks`: Number of in-progress tasks
- `blocked_tasks`: Number of blocked tasks
- `percent_complete`: Completion percentage (0-100)
- `completed_task_ids`: List of completed task IDs
- `blocked_task_ids`: List of blocked task IDs

## API Reference

### GoalManager

#### Goal Operations
```python
# Create a goal
goal = Goal(title="Research frameworks", priority=75)
goal_id = manager.create_goal(goal)

# Retrieve a goal
goal = manager.get_goal(goal_id)

# Update a goal
manager.update_goal(goal_id, {"status": GoalStatus.IN_PROGRESS})

# Delete a goal (also deletes associated tasks)
manager.delete_goal(goal_id)

# Get active goals (not completed, failed, or cancelled)
active_goals = manager.get_active_goals()

# Get child goals
children = manager.get_child_goals(parent_goal_id)
```

#### Task Operations
```python
# Create a task
task = Task(goal_id=goal_id, title="Research Flask")
task_id = manager.create_task(task)

# Create task with dependencies
task = Task(
    goal_id=goal_id,
    title="Create comparison table",
    dependencies=[task1_id, task2_id]
)
task_id = manager.create_task(task)

# Retrieve a task
task = manager.get_task(task_id)

# Update a task
manager.update_task(task_id, {"status": GoalStatus.COMPLETED})

# Assign task to agent
manager.assign_task(task_id, "agent-123")

# Get tasks for a goal
tasks = manager.get_goal_tasks(goal_id)

# Get tasks for an agent
agent_tasks = manager.get_agent_tasks("agent-123")
```

#### Task Dependencies
```python
# Resolve task dependencies (topological sort)
execution_order = manager.resolve_task_dependencies(task_id)
# Returns: [dependency1_id, dependency2_id, ..., task_id]
```

#### Progress Tracking
```python
# Calculate progress
progress = manager.calculate_progress(goal_id)
print(f"Progress: {progress.percent_complete}%")
print(f"Completed: {progress.completed_tasks}/{progress.total_tasks}")

# Update goal status based on progress
manager.update_progress(goal_id, 50.0)  # 50% complete
```

#### Goal Decomposition
```python
# Decompose a goal into tasks
task_titles = [
    "Research Flask",
    "Research Django",
    "Create comparison table"
]
task_ids = manager.decompose_goal(goal_id, task_titles)
```

## Usage Examples

See `examples/goal_management_examples.py` for comprehensive examples including:

1. **Simple Goal Management**: Creating and managing a basic goal
2. **Goal Decomposition**: Breaking down a goal into tasks
3. **Agent Assignment**: Assigning tasks to different agents
4. **Progress Tracking**: Monitoring goal completion
5. **Task Dependencies**: Managing task execution order
6. **Goal Hierarchy**: Creating parent/child goal relationships
7. **Multi-Agent Workflow**: Coordinating parallel task execution
8. **Active Goals Query**: Retrieving goals by status

### Quick Example

```python
from minimal_browser.coordination.goals import Goal, GoalManager, Task

# Create manager
manager = GoalManager()

# Create a goal
goal = Goal(
    title="Research Python web frameworks",
    success_criteria=["Document differences", "Recommend framework"]
)
goal_id = manager.create_goal(goal)

# Decompose into tasks
task_ids = manager.decompose_goal(goal_id, [
    "Research Flask",
    "Research Django",
    "Create comparison table"
])

# Assign tasks to agents
for i, task_id in enumerate(task_ids):
    manager.assign_task(task_id, f"research_agent_{i+1}")

# Track progress
progress = manager.calculate_progress(goal_id)
print(f"Progress: {progress.percent_complete}%")
```

## Testing

Run the comprehensive test suite:

```bash
# Run all goal management tests
pytest tests/unit/coordination/test_goals.py -v

# Run specific test class
pytest tests/unit/coordination/test_goals.py::TestGoalManagerCRUD -v

# Run with coverage
pytest tests/unit/coordination/test_goals.py --cov=src/minimal_browser/coordination/goals
```

The test suite includes 38 tests covering:
- Goal and Task model validation
- CRUD operations
- Goal hierarchies
- Task dependencies and circular dependency detection
- Progress tracking
- Agent task assignment
- Goal decomposition

## Integration

### With Agent Infrastructure
The goal management system integrates with `coordination/agentic_struct.py`:

```python
from minimal_browser.coordination.agentic_struct import Agent
from minimal_browser.coordination.goals import GoalManager, Task

class ResearchAgent(Agent):
    def __init__(self, goal_manager: GoalManager):
        super().__init__(name="ResearchAgent")
        self.goal_manager = goal_manager
    
    async def execute_task(self, task_id: str):
        task = self.goal_manager.get_task(task_id)
        # Execute task logic
        self.goal_manager.update_task(task_id, {"status": GoalStatus.COMPLETED})
```

### With Context Sharing
Goals can be shared via `coordination/context.py`:

```python
# Share goal state between agents
context = AgentContext()
context.set("current_goal_id", goal_id)
context.set("goal_progress", manager.calculate_progress(goal_id))
```

### With Agent-to-Agent Communication
Goal/task notifications via `coordination/a2a.py`:

```python
# Notify agents of task assignments
message = AgentMessage(
    sender_id="manager",
    recipient_id="agent-123",
    message_type=MessageType.TASK_DELEGATION,
    payload={"task_id": task_id, "goal_id": goal_id}
)
```

## Future Enhancements

Planned features for future releases:
- **Persistence layer**: SQLite or JSON file-based storage
- **AI-assisted planning**: Use AI for automatic task decomposition
- **Effort estimation**: AI-powered task complexity analysis
- **Bottleneck detection**: Identify tasks blocking progress
- **Goal visualization**: UI dashboard for goal/task graphs
- **Temporal integration**: Integration with temporal workflow engines
- **Event streaming**: Real-time goal/task event notifications
- **Query optimization**: Indexed queries for large goal sets

## Architecture Notes

### Design Principles
- **Pydantic validation**: All models use Pydantic for type safety
- **Immutable IDs**: UUIDs generated at creation, never modified
- **Explicit state transitions**: Status changes are explicit and validated
- **Topological sorting**: Dependencies resolved using DFS-based algorithm
- **In-memory first**: Simple in-memory storage, persistence layer separate

### Performance Considerations
- Current implementation is in-memory only (suitable for <10K goals/tasks)
- For larger scale, implement persistence layer with indexing
- Task dependency resolution is O(V + E) for V tasks and E dependencies
- Progress calculation is O(n) for n tasks per goal

### Error Handling
All operations raise appropriate exceptions:
- `ValueError`: Invalid inputs or constraint violations
- `KeyError`: Attempting to access non-existent goals/tasks
- `ValidationError`: Pydantic validation failures

## License

Part of the Minimal Browser project - see main repository LICENSE.
