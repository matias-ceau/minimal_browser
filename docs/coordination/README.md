# Coordination Module

This module contains the infrastructure for the Open Agent Coordination System (OACS), enabling multi-agent collaboration in the minimal browser.

## Components

### Agent Infrastructure (`agentic_struct.py`)

Provides the foundational agent infrastructure including:
- Base `Agent` class with communication capabilities
- `AgentRegistry` for managing active agents
- Message types and routing protocols (`AgentMessage`, `MessageType`)
- Agent lifecycle management (`AgentStatus`)

### Context Management (`context.py`) ✅

**Status: Implemented**

A robust context management system for sharing state between agents:

- **Context Scoping**: GLOBAL, AGENT, and TASK scopes
- **Versioning**: Track changes with version numbers and history
- **Subscriptions**: Pattern-based notifications for context changes
- **Conflict Resolution**: Multiple strategies (LAST_WRITE_WINS, VERSION_CHECK, MERGE)
- **Thread Safety**: Full thread-safe operations with RLock
- **TTL Support**: Automatic expiration for temporary data

**Key Classes:**
- `ContextEntry`: Pydantic model for context data
- `ContextStore`: Low-level storage with CRUD operations
- `ContextManager`: High-level API for agents
- `ContextScope`: Enum for scoping levels

**Documentation**: See [`CONTEXT_API.md`](./CONTEXT_API.md) for complete API documentation and examples.

**Tests**: 45 comprehensive unit tests in `tests/unit/coordination/test_context.py`

### Agent-to-Agent Communication (`a2a.py`)

**Status: Placeholder**

Future implementation will include:
- Message passing between agents
- Event bus for agent coordination
- Agent registry and discovery

### Goal Management (`goals.py`)

**Status: Placeholder**

Future implementation will include:
- Goal tracking and planning
- Task decomposition
- Progress monitoring

## Usage Example

```python
from minimal_browser.coordination.context import ContextStore, ContextManager

# Create shared context store
store = ContextStore()

# Create agents with context managers
browser_agent = ContextManager(store=store, agent_id="browser")
ai_agent = ContextManager(store=store, agent_id="ai_assistant")

# Browser agent shares current state
browser_agent.set_global("browser.current_url", "https://example.com")
browser_agent.set_global("browser.title", "Example Domain")

# AI agent reads browser state to provide context-aware responses
url = ai_agent.get_global("browser.current_url")
print(f"AI sees browser at: {url.value}")

# Subscribe to changes
def on_url_change(entry):
    print(f"URL changed to: {entry.value}")

ai_agent.subscribe("browser.current_url", on_url_change)
```

## Development Status

| Component | Status | Test Coverage | Documentation |
|-----------|--------|---------------|---------------|
| `agentic_struct.py` | ✅ Implemented | Partial | Inline |
| `context.py` | ✅ Implemented | 45 tests (100%) | ✅ Complete |
| `a2a.py` | 🚧 Placeholder | - | - |
| `goals.py` | 🚧 Placeholder | - | - |

## Architecture

The coordination system follows a layered architecture:

1. **Foundation Layer**: `agentic_struct.py` provides base agent infrastructure
2. **Context Layer**: `context.py` enables state sharing between agents
3. **Communication Layer**: `a2a.py` (planned) will handle message passing
4. **Goal Layer**: `goals.py` (planned) will manage agent goals and tasks

## Design Principles

1. **Thread Safety**: All components are thread-safe for concurrent agent operations
2. **Pydantic Models**: Use Pydantic for data validation and serialization
3. **Minimal Dependencies**: Core functionality uses only Python stdlib + Pydantic
4. **Extensibility**: Easy to add new context scopes, message types, etc.
5. **Testing**: Comprehensive test coverage for all components

## Contributing

When adding new coordination features:

1. Follow existing patterns (Pydantic models, thread safety)
2. Add comprehensive unit tests
3. Update documentation
4. Ensure compatibility with existing components

## References

- [OACS Design Document](../../ARCHITECTURE.md)
- [Context Management API](./CONTEXT_API.md)
- [Agent Message Types](../../../src/minimal_browser/coordination/agentic_struct.py)
