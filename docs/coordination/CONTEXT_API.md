# Agent Context Management API Documentation

## Overview

The Agent Context Management system provides a robust, thread-safe mechanism for sharing state and information between agents in the OACS (Open Agent Coordination System). It supports context scoping, versioning, subscriptions, and conflict resolution.

## Core Concepts

### Context Scopes

Context entries can be scoped at three levels:

- **GLOBAL**: Shared across all agents in the system
- **AGENT**: Specific to a single agent instance
- **TASK**: Associated with a specific task or workflow

### Context Entry

A `ContextEntry` represents a single piece of context data with metadata:

```python
class ContextEntry:
    id: str                          # Unique identifier
    scope: ContextScope              # GLOBAL, AGENT, or TASK
    key: str                         # Context key (e.g., "browser.current_url")
    value: Any                       # The actual data
    agent_id: str                    # Owner agent ID
    version: int                     # Version number (starts at 1)
    timestamp: datetime              # When created/updated
    expires_at: Optional[datetime]   # Expiration time (optional)
    metadata: Dict[str, Any]         # Additional metadata
```

## Quick Start

### Basic Usage with ContextManager

The `ContextManager` provides a high-level API for working with context:

```python
from minimal_browser.coordination.context import ContextManager

# Create a manager for your agent
manager = ContextManager(agent_id="my_agent")

# Set global context
manager.set_global("browser.current_url", "https://example.com")

# Get global context
entry = manager.get_global("browser.current_url")
print(entry.value)  # "https://example.com"

# Set agent-specific context
manager.set_agent("status", "active")

# Set task-specific context
manager.set_task("task.search.query", "python documentation")
```

### Shared Context Between Agents

Multiple agents can share the same context store:

```python
from minimal_browser.coordination.context import ContextStore, ContextManager

# Create a shared store
store = ContextStore()

# Create managers for different agents
agent_a = ContextManager(store=store, agent_id="agent_a")
agent_b = ContextManager(store=store, agent_id="agent_b")

# Agent A stores data
agent_a.set_global("shared.data", {"key": "value"})

# Agent B retrieves it
entry = agent_b.get_global("shared.data")
print(entry.value)  # {"key": "value"}
```

## API Reference

See the full API documentation in the source code docstrings:
- `ContextManager`: High-level API for agent integration
- `ContextStore`: Low-level storage with CRUD operations
- `ContextEntry`: Data model for context entries
- `ContextScope`: Enum for context scoping levels

## Pattern Matching

Context keys support glob-style pattern matching for queries and subscriptions:

### Wildcards

- `*` - Matches any characters within a segment (between dots)
- `**` - Matches across segments (multiple levels)

### Examples

```python
# Single wildcard
"browser.*"          → Matches "browser.url", "browser.title"
                     → Does NOT match "browser.tab.url"

# Double wildcard
"browser.**"         → Matches "browser.url", "browser.tab.url", etc.

# Pattern in middle
"task.*.results"     → Matches "task.search.results", "task.query.results"

# Match everything
"**"                 → Matches all keys
```

## Real-World Examples

### Example 1: Browser State Sharing

```python
# Browser control agent
browser_agent.set_global("browser.current_url", "https://example.com")
browser_agent.set_global("browser.title", "Example Domain")

# AI agent reads browser state
url = ai_agent.get_global("browser.current_url")
print(f"Current page: {url.value}")
```

### Example 2: Task-Specific Context

```python
# Store search task context
manager.set_task("task.search.query", "python documentation")
manager.set_task("task.search.results", [
    {"title": "Python Docs", "url": "https://docs.python.org"}
])

# Retrieve task context
query = manager.get_task("task.search.query")
results = manager.get_task("task.search.results")
```

### Example 3: Context Change Notifications

```python
def on_browser_change(entry):
    print(f"Browser state changed: {entry.key} = {entry.value}")

# Subscribe to browser state changes
sub_id = manager.subscribe("browser.*", on_browser_change)

# Changes will trigger callback
manager.set_global("browser.url", "https://example.com")
```

### Example 4: Versioned Updates

```python
from minimal_browser.coordination.context import ConflictResolutionStrategy

store = ContextStore(conflict_strategy=ConflictResolutionStrategy.VERSION_CHECK)

# Update with version check
try:
    entry = store.set(
        key="counter",
        value=1,
        agent_id="agent1",
        expected_version=1
    )
except ValueError as e:
    print(f"Version conflict: {e}")
```

## Best Practices

### 1. Use Appropriate Scope

- Use `GLOBAL` for shared state (browser URL, system settings)
- Use `AGENT` for agent-specific data (agent status, preferences)
- Use `TASK` for workflow-specific data (search results, task progress)

### 2. Namespace Your Keys

Use hierarchical naming:
```python
# Good
"browser.current_url"
"task.search.query"
"agent.status"

# Avoid
"url", "query", "status"
```

### 3. Clean Up When Done

```python
# Clear task context after completion
manager.clear_agent_context()
```

### 4. Use TTL for Temporary Data

```python
# Cache data with expiration
manager.set_global("cache.data", data, ttl=3600)
```

### 5. Handle Version Conflicts

```python
try:
    entry = store.set(key, value, agent_id=id, expected_version=ver)
except ValueError:
    # Handle conflict - retry or refresh
    current = store.get(key)
```

## Thread Safety

The `ContextStore` is thread-safe and uses `threading.RLock` for synchronization. Multiple threads can safely access and modify context simultaneously.

## Integration with AgentMessage System

Context can be propagated through agent messages using the `CONTEXT_SHARE` message type:

```python
from minimal_browser.coordination.agentic_struct import AgentMessage, MessageType

message = AgentMessage(
    sender_id="agent_a",
    recipient_id="agent_b",
    message_type=MessageType.CONTEXT_SHARE,
    payload={
        "context_key": "browser.url",
        "context_value": "https://example.com"
    }
)
```

## Additional Resources

- Full implementation: `src/minimal_browser/coordination/context.py`
- Comprehensive tests: `tests/unit/coordination/test_context.py`
- Agent infrastructure: `src/minimal_browser/coordination/agentic_struct.py`
