# Issue: Implement Agent Goal Management

## Priority
**P2 - Medium Priority** (Experimental/Future Enhancement)

## Component
`src/minimal_browser/coordination/goals.py`

## Current State
Complete placeholder module with only a docstring:
```python
"""
Placeholder for agent goal management.

Future implementation will include:
- Goal tracking and planning
- Task decomposition
- Progress monitoring
"""
```

## Description
This module provides goal-oriented planning and task management for the multi-agent system. It enables agents to define high-level goals, decompose them into actionable tasks, and track progress toward completion. This is part of the experimental OACS (Open Agent Coordination System).

## Required Features

### 1. Goal Tracking and Planning
- Goal definition with success criteria
- Goal hierarchies (parent/child relationships)
- Goal prioritization
- Goal state management (pending, active, completed, failed)
- Goal history and audit trail

### 2. Task Decomposition
- Break down high-level goals into subtasks
- Task dependencies and ordering
- Task assignment to agents
- Task estimation (effort, duration)
- Automatic vs manual decomposition

### 3. Progress Monitoring
- Real-time progress tracking
- Completion percentage calculation
- Milestone detection
- Bottleneck identification
- Progress reporting and visualization

## Technical Considerations

### Data Model
```python
class GoalStatus(Enum):
    PENDING = "pending"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Goal:
    id: str
    title: str
    description: str
    status: GoalStatus
    priority: int
    parent_goal_id: Optional[str]
    success_criteria: List[str]
    assigned_agent_id: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    metadata: Dict[str, Any]
    
class Task:
    id: str
    goal_id: str
    title: str
    description: str
    status: GoalStatus
    assigned_agent_id: str
    dependencies: List[str]  # Task IDs
    estimated_effort: Optional[int]  # minutes
    actual_effort: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]

class GoalManager:
    def create_goal(goal: Goal) -> str
    def update_goal(goal_id: str, updates: Dict) -> None
    def get_goal(goal_id: str) -> Goal
    def decompose_goal(goal_id: str) -> List[Task]
    def assign_task(task_id: str, agent_id: str) -> None
    def update_progress(goal_id: str, progress: float) -> None
    def get_active_goals() -> List[Goal]
    def get_agent_tasks(agent_id: str) -> List[Task]
```

### Architecture
- Build on `coordination/agentic_struct.py` (Agent infrastructure)
- Use `coordination/context.py` for shared goal state
- Use `coordination/a2a.py` for goal/task notifications
- Persist goals and tasks (SQLite or JSON)

### Integration Points
- `coordination/agentic_struct.py`: Agent task execution
- `coordination/context.py`: Shared goal state
- `coordination/a2a.py`: Goal status notifications
- `ai/`: AI-assisted goal decomposition
- UI: Goal/task visualization dashboard

### AI-Assisted Planning
- Use AI to suggest task decomposition
- Estimate task complexity/duration
- Recommend task ordering
- Identify potential blockers

## Acceptance Criteria
- [ ] Goal and Task data models with full CRUD
- [ ] Goal hierarchy support (parent/child)
- [ ] Task dependency resolution
- [ ] Progress calculation algorithms
- [ ] Goal state machine with valid transitions
- [ ] Agent task assignment and tracking
- [ ] Persistence layer (SQLite or files)
- [ ] Unit tests with >80% coverage
- [ ] Integration with Agent infrastructure
- [ ] API documentation
- [ ] Example goal planning scenarios

## Example Use Cases

### 1. User Research Goal
```python
# Create high-level goal
goal = Goal(
    title="Research Python web frameworks",
    description="Compare Flask, Django, and FastAPI",
    success_criteria=[
        "Document key differences",
        "Create comparison table",
        "Recommend framework for project"
    ]
)
goal_id = goal_manager.create_goal(goal)

# Decompose into tasks
tasks = goal_manager.decompose_goal(goal_id)
# Tasks: [
#   "Search for Flask documentation",
#   "Search for Django documentation", 
#   "Search for FastAPI documentation",
#   "Create comparison table",
#   "Write recommendation summary"
# ]

# Assign tasks to agents
for task in tasks[:3]:
    goal_manager.assign_task(task.id, "research_agent")
```

### 2. Multi-Agent Workflow
```python
# Parallel task execution
goal_manager.create_goal(Goal(
    title="Analyze website performance",
    success_criteria=["Load time < 2s", "Lighthouse score > 90"]
))

# Agent A: Fetch page
# Agent B: Run Lighthouse audit
# Agent C: Analyze results
# All tasks coordinated through goal manager
```

### 3. Progress Monitoring
```python
# Track goal progress
progress = goal_manager.get_progress(goal_id)
print(f"Goal progress: {progress.percent_complete}%")
print(f"Completed tasks: {progress.completed_tasks}/{progress.total_tasks}")
print(f"Blocked tasks: {len(progress.blocked_tasks)}")
```

## Related Issues/Features
- Depends on `coordination/agentic_struct.py` (Agent infrastructure)
- Related to `coordination/context.py` (State sharing)
- Related to `coordination/a2a.py` (Task notifications)
- Could integrate with AI for automated planning

## Suggested Implementation Approach
1. Define Goal and Task data models with Pydantic
2. Implement in-memory GoalManager with CRUD operations
3. Add goal hierarchy and parent/child relationships
4. Implement task decomposition logic
5. Add task dependency resolution (topological sort)
6. Implement progress calculation algorithms
7. Add persistence layer (SQLite)
8. Integrate with Agent infrastructure for task execution
9. Add AI-assisted planning (optional)
10. Write comprehensive tests and documentation
11. Create example workflows

## Assignment
**Suggested for Copilot Agent**: Systems/Planning specialist agent
**Estimated Effort**: 5-7 days for complete implementation
**Dependencies**:
- `coordination/agentic_struct.py` must be functional
- `coordination/context.py` for state sharing
- Understanding of planning algorithms (STRIPS, HTN)
- Optional: AI integration for decomposition

## Notes
- This is an experimental feature for advanced multi-agent workflows
- Consider existing planning frameworks (Temporal, Celery)
- Start simple, add complexity incrementally
- Low priority until core agent features are stable
- May benefit from visualization UI for goal/task graphs
