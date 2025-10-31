# Issue: Implement Agent-to-Agent Communication System

## Priority
**P2 - Medium Priority** (Experimental/Future Enhancement)

## Component
`src/minimal_browser/coordination/a2a.py`

## Current State
Complete placeholder module with only a docstring:
```python
"""
Placeholder for agent-to-agent communication.

Future implementation will include:
- Message passing between agents
- Event bus for agent coordination
- Agent registry and discovery
"""
```

## Description
This module implements the core communication infrastructure for the multi-agent system (OACS). It provides message passing, event routing, and agent discovery capabilities. This is the communication backbone that enables agents to coordinate and collaborate.

## Required Features

### 1. Message Passing Between Agents
- Reliable message delivery (at-least-once semantics)
- Message queuing and buffering
- Request-response patterns
- One-to-one and broadcast messaging
- Message priority handling
- Message expiration and TTL

### 2. Event Bus for Agent Coordination
- Publish-subscribe event system
- Topic-based message routing
- Pattern matching for subscriptions
- Event filtering and transformation
- Event replay for new subscribers
- Dead letter queue for failed messages

### 3. Agent Registry and Discovery
- Central agent registry
- Agent capability advertisement
- Service discovery by capability
- Agent health monitoring
- Dynamic agent registration/deregistration
- Agent metadata and versioning

## Technical Considerations

### Architecture
- Build on existing `coordination/agentic_struct.py` (Agent, AgentMessage classes)
- Use asyncio for async message handling
- Consider message broker patterns (in-memory vs external like RabbitMQ/Redis)
- Support both local and distributed deployments

### Data Model
```python
class MessageBroker:
    """Central message routing and delivery system"""
    def publish(message: AgentMessage) -> None
    def subscribe(agent_id: str, message_types: List[MessageType]) -> None
    def unsubscribe(agent_id: str) -> None
    def send_message(message: AgentMessage) -> None
    def broadcast(message: AgentMessage) -> None
    def get_pending_messages(agent_id: str) -> List[AgentMessage]

class EventBus:
    """Topic-based event system"""
    def publish(topic: str, event: Dict[str, Any]) -> None
    def subscribe(topic: str, handler: Callable) -> str  # Returns subscription ID
    def unsubscribe(subscription_id: str) -> None
    def publish_pattern(pattern: str, event: Dict[str, Any]) -> None
    
class AgentRegistry:
    """Agent discovery and capability matching"""
    def register(agent: Agent) -> None
    def unregister(agent_id: str) -> None
    def find_by_capability(capability: str) -> List[Agent]
    def get_agent(agent_id: str) -> Agent
    def get_all_agents() -> List[Agent]
    def update_status(agent_id: str, status: AgentStatus) -> None
    def heartbeat(agent_id: str) -> None
```

### Integration Points
- `coordination/agentic_struct.py`: Agent, AgentMessage, MessageType
- `coordination/context.py`: Shared state for message routing
- `coordination/goals.py`: Task assignment messages
- Python asyncio for async operations

### Performance & Scalability
- Async message processing
- Message batching for efficiency
- Connection pooling
- Rate limiting and backpressure
- Message queue size limits
- Monitoring and metrics

### Reliability
- Message persistence (optional)
- Retry logic with exponential backoff
- Circuit breaker pattern for failing agents
- Message acknowledgment system
- Error handling and dead letter queue

## Acceptance Criteria
- [ ] MessageBroker with publish/subscribe
- [ ] Direct messaging (agent-to-agent)
- [ ] Broadcast messaging
- [ ] EventBus with topic-based routing
- [ ] Pattern matching for subscriptions
- [ ] AgentRegistry with registration/discovery
- [ ] Capability-based agent lookup
- [ ] Health monitoring and heartbeats
- [ ] Message priority handling
- [ ] Message expiration and TTL
- [ ] Dead letter queue
- [ ] Unit tests with >80% coverage
- [ ] Integration tests with multiple agents
- [ ] Performance benchmarks
- [ ] API documentation

## Example Use Cases

### 1. Direct Agent Communication
```python
# Agent A sends request to Agent B
message = AgentMessage(
    sender_id="agent_a",
    recipient_id="agent_b",
    message_type=MessageType.REQUEST,
    payload={"action": "search", "query": "Python tutorials"}
)
broker.send_message(message)

# Agent B receives and responds
response = AgentMessage(
    sender_id="agent_b",
    recipient_id="agent_a",
    message_type=MessageType.RESPONSE,
    correlation_id=message.id,
    payload={"results": [...]}
)
broker.send_message(response)
```

### 2. Event Bus Coordination
```python
# Agent subscribes to browser events
def on_navigation(event):
    print(f"Page changed to: {event['url']}")

event_bus.subscribe("browser.navigation", on_navigation)

# Browser publishes navigation event
event_bus.publish("browser.navigation", {"url": "https://example.com"})
```

### 3. Agent Discovery
```python
# Find agents capable of web search
search_agents = registry.find_by_capability("web_search")
if search_agents:
    # Send task to first available agent
    message = AgentMessage(
        sender_id="coordinator",
        recipient_id=search_agents[0].id,
        message_type=MessageType.TASK_DELEGATION,
        payload={"query": "Python tutorials"}
    )
    broker.send_message(message)
```

### 4. Broadcast Notifications
```python
# Notify all agents of system shutdown
message = AgentMessage(
    sender_id="system",
    recipient_id=None,  # Broadcast
    message_type=MessageType.SHUTDOWN,
    payload={"reason": "maintenance", "graceful": True}
)
broker.broadcast(message)
```

## Related Issues/Features
- Depends on `coordination/agentic_struct.py` (Agent infrastructure)
- Related to `coordination/context.py` (State sharing)
- Related to `coordination/goals.py` (Task distribution)
- Foundation for all multi-agent coordination

## Suggested Implementation Approach
1. Implement MessageBroker with in-memory queues
2. Add direct messaging (point-to-point)
3. Add broadcast messaging
4. Implement EventBus with topic-based routing
5. Add pattern matching for subscriptions
6. Implement AgentRegistry with CRUD operations
7. Add capability-based discovery
8. Add health monitoring and heartbeats
9. Implement message priority and expiration
10. Add dead letter queue for failed messages
11. Write comprehensive tests
12. Add performance benchmarks
13. Document API and usage patterns
14. Create example multi-agent scenarios

## Assignment
**Suggested for Copilot Agent**: Systems/Distributed Systems specialist agent
**Estimated Effort**: 6-8 days for complete implementation
**Dependencies**:
- `coordination/agentic_struct.py` must be functional
- Understanding of message broker patterns
- Familiarity with asyncio and concurrent programming
- Knowledge of pub/sub architectures

## Future Enhancements
- [ ] External message broker support (RabbitMQ, Redis, NATS)
- [ ] Message persistence for durability
- [ ] Distributed agent deployment
- [ ] Load balancing across agent instances
- [ ] Message routing policies
- [ ] Monitoring dashboard for message flows
- [ ] GraphQL/REST API for external agent integration

## Notes
- This is the core infrastructure for multi-agent coordination
- Start with simple in-memory implementation
- Design for future distributed deployment
- Consider existing message broker libraries (aio-pika, redis-py)
- Low priority until agent use cases are defined
- May need protocol versioning for backward compatibility
