# Agent-to-Agent Communication System (a2a.py)

## Overview

The Agent-to-Agent Communication System provides the core communication infrastructure for the multi-agent OACS (Open Agent Communication System). It implements three main components:

1. **MessageBroker** - Message routing and delivery
2. **EventBus** - Topic-based event system  
3. **AgentRegistry** - Agent discovery and health monitoring

## Quick Start

```python
import asyncio
from minimal_browser.coordination.a2a import MessageBroker, EventBus, AgentRegistry
from minimal_browser.coordination.agentic_struct import (
    Agent, AgentMessage, AgentCapabilities, MessageType
)

async def main():
    # Create infrastructure
    broker = MessageBroker()
    bus = EventBus()
    registry = AgentRegistry()
    
    # Register an agent
    agent = Agent(
        agent_id="search_agent",
        name="SearchAgent",
        capabilities=AgentCapabilities(
            name="search",
            supported_actions=["web_search"]
        )
    )
    await registry.register(agent)
    
    # Send a message
    message = AgentMessage(
        sender_id="coordinator",
        recipient_id="search_agent",
        message_type=MessageType.REQUEST,
        payload={"query": "Python tutorials"}
    )
    await broker.send_message(message)

asyncio.run(main())
```

## MessageBroker API

### send_message(message: AgentMessage)
Send a message to a specific agent with priority handling.

### broadcast(message: AgentMessage)
Broadcast to all agents subscribed to that message type.

### get_pending_messages(agent_id: str, max_messages: Optional[int])
Retrieve pending messages in priority order.

### subscribe/unsubscribe
Manage agent subscriptions to message types.

## EventBus API

### publish(topic: str, event: Dict)
Publish event to a specific topic.

### subscribe(topic: str, handler: Callable) -> str
Subscribe to topics with wildcard support (* and **).

### Pattern Matching
- `exact.topic` - Exact match only
- `topic.*` - Single segment wildcard
- `topic.**` - Multi-segment wildcard

## AgentRegistry API

### register/unregister(agent: Agent)
Manage agent lifecycle.

### find_by_capability(capability: str) -> List[Agent]
Discover agents by supported capabilities.

### heartbeat(agent_id: str)
Record agent health status.

### get_stale_agents()
Find agents that haven't sent heartbeats.

## Testing

```bash
pytest tests/unit/coordination/test_a2a.py -v
```

32 comprehensive tests covering all functionality.

## See Also

- `coordination/agentic_struct.py` - Base Agent and Message classes
- Test file: `tests/unit/coordination/test_a2a.py`
