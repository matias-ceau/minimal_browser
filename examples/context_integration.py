"""Integration example: Context Management with AgentMessage System

This example demonstrates how the context management system integrates with
the AgentMessage infrastructure for agent-to-agent communication.
"""

import sys
import importlib.util
from pathlib import Path

# Import modules directly to avoid PySide6 dependency
def import_module_direct(name: str, filepath: str):
    """Import a module directly from file path."""
    spec = importlib.util.spec_from_file_location(name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# Import coordination modules
src_path = Path(__file__).parent.parent / "src" / "minimal_browser"
context_module = import_module_direct(
    "coordination.context",
    str(src_path / "coordination" / "context.py")
)
agentic_module = import_module_direct(
    "coordination.agentic_struct",
    str(src_path / "coordination" / "agentic_struct.py")
)

# Extract classes
ContextStore = context_module.ContextStore
ContextManager = context_module.ContextManager
ContextScope = context_module.ContextScope
AgentMessage = agentic_module.AgentMessage
MessageType = agentic_module.MessageType
MessagePriority = agentic_module.MessagePriority
ConflictResolutionStrategy = context_module.ConflictResolutionStrategy


def example_context_sharing_via_messages():
    """Example 1: Share context updates via agent messages."""
    
    # Create shared context store
    store = ContextStore()
    
    # Create agents
    browser_agent = ContextManager(store=store, agent_id="browser_agent")
    ai_agent = ContextManager(store=store, agent_id="ai_agent")
    
    # Browser agent updates context
    browser_agent.set_global("browser.current_url", "https://example.com")
    
    # Browser agent notifies other agents via message
    message = AgentMessage(
        sender_id="browser_agent",
        recipient_id="ai_agent",
        message_type=MessageType.CONTEXT_SHARE,
        payload={
            "context_key": "browser.current_url",
            "context_scope": ContextScope.GLOBAL.value,
            "context_value": "https://example.com"
        }
    )
    
    print(f"Message sent: {message.message_type} from {message.sender_id}")
    
    # AI agent receives message and reads context
    url_entry = ai_agent.get_global("browser.current_url")
    print(f"AI agent sees URL: {url_entry.value}")
    
    return message


def example_context_request():
    """Example 2: Request context from another agent."""
    
    store = ContextStore()
    ContextManager(store=store, agent_id="requester")  # Will request context
    provider = ContextManager(store=store, agent_id="provider")
    
    # Provider has some context
    provider.set_agent("status", "processing")
    provider.set_agent("progress", 75)
    
    # Requester sends context request
    request = AgentMessage(
        sender_id="requester",
        recipient_id="provider",
        message_type=MessageType.CONTEXT_REQUEST,
        payload={
            "requested_keys": ["status", "progress"],
            "scope": ContextScope.AGENT.value
        }
    )
    
    print(f"\nContext request sent for: {request.payload['requested_keys']}")
    
    # Provider responds with context (in real implementation)
    # For demo, requester reads directly from shared store
    status = store.get("status", ContextScope.AGENT, "provider")
    progress = store.get("progress", ContextScope.AGENT, "provider")
    
    response = AgentMessage(
        sender_id="provider",
        recipient_id="requester",
        message_type=MessageType.RESPONSE,
        correlation_id=request.id,
        payload={
            "status": status.value if status else None,
            "progress": progress.value if progress else None
        }
    )
    
    print(f"Response: status={response.payload['status']}, progress={response.payload['progress']}")
    
    return request, response


def example_broadcast_context_update():
    """Example 3: Broadcast context updates to all agents."""
    
    store = ContextStore()
    
    # Create multiple agents
    coordinator = ContextManager(store=store, agent_id="coordinator")
    agents = [
        ContextManager(store=store, agent_id=f"agent_{i}")
        for i in range(3)
    ]
    
    # Coordinator broadcasts a system-wide update
    coordinator.set_global("system.mode", "maintenance")
    
    broadcast = AgentMessage(
        sender_id="coordinator",
        recipient_id=None,  # Broadcast to all
        message_type=MessageType.BROADCAST,
        priority=MessagePriority.HIGH,
        payload={
            "context_key": "system.mode",
            "context_value": "maintenance",
            "message": "System entering maintenance mode"
        }
    )
    
    print(f"\nBroadcast sent: {broadcast.payload['message']}")
    
    # All agents can read the context
    for agent in agents:
        mode = agent.get_global("system.mode")
        print(f"  {agent.agent_id} sees mode: {mode.value}")
    
    return broadcast


def example_subscription_with_notifications():
    """Example 4: Use subscriptions to trigger agent notifications."""
    
    store = ContextStore()
    monitor = ContextManager(store=store, agent_id="monitor")
    worker = ContextManager(store=store, agent_id="worker")
    
    messages_sent = []
    
    def on_task_complete(entry):
        """Callback when task context changes."""
        if entry.key == "task.status" and entry.value == "completed":
            # Send notification message
            notification = AgentMessage(
                sender_id="monitor",
                recipient_id=None,  # Broadcast
                message_type=MessageType.NOTIFICATION,
                payload={
                    "event": "task_completed",
                    "task_id": entry.metadata.get("task_id"),
                    "completed_by": entry.agent_id
                }
            )
            messages_sent.append(notification)
            print(f"\nNotification sent: Task {entry.metadata.get('task_id')} completed")
    
    # Monitor subscribes to task status changes
    monitor.subscribe("task.status", on_task_complete)
    
    # Worker completes a task
    worker.set_global(
        "task.status",
        "completed",
        metadata={"task_id": "task_123"}
    )
    
    # Note: In real async environment, callback would fire automatically
    # Here we're demonstrating the pattern
    
    return messages_sent


def example_versioned_coordination():
    """Example 5: Use version checking for coordinated updates."""
    
    store = ContextStore(conflict_strategy=ConflictResolutionStrategy.VERSION_CHECK)
    
    agent1 = ContextManager(store=store, agent_id="agent1")
    ContextManager(store=store, agent_id="agent2")  # Will attempt updates
    
    # Agent1 initializes shared counter
    entry = agent1.set_global("shared.counter", 0)
    print(f"\nInitialized counter at version {entry.version}")
    
    # Agent1 increments (version check)
    try:
        entry = store.set(
            key="shared.counter",
            value=1,
            agent_id="agent1",
            expected_version=1
        )
        print(f"Agent1 incremented to {entry.value} (version {entry.version})")
    except ValueError as e:
        print(f"Agent1 conflict: {e}")
    
    # Agent2 tries to update with stale version
    try:
        entry = store.set(
            key="shared.counter",
            value=5,
            agent_id="agent2",
            expected_version=1  # Stale!
        )
        print(f"Agent2 updated to {entry.value}")
    except ValueError as e:
        print(f"Agent2 conflict detected: {e}")
        
        # Agent2 reads current version and retries
        current = store.get("shared.counter")
        entry = store.set(
            key="shared.counter",
            value=current.value + 1,
            agent_id="agent2",
            expected_version=current.version
        )
        print(f"Agent2 retry succeeded: {entry.value} (version {entry.version})")
    
    # Both agents can send TASK_COMPLETION messages
    completion1 = AgentMessage(
        sender_id="agent1",
        recipient_id="coordinator",
        message_type=MessageType.TASK_COMPLETION,
        payload={
            "task": "increment",
            "result": "success"
        }
    )
    
    completion2 = AgentMessage(
        sender_id="agent2",
        recipient_id="coordinator",
        message_type=MessageType.TASK_COMPLETION,
        payload={
            "task": "increment",
            "result": "success (after retry)"
        }
    )
    
    return [completion1, completion2]


def example_task_delegation_with_context():
    """Example 6: Delegate tasks with context sharing."""
    
    store = ContextStore()
    coordinator = ContextManager(store=store, agent_id="coordinator")
    worker = ContextManager(store=store, agent_id="worker")
    
    # Coordinator sets up task context
    coordinator.set_task("task.type", "data_processing")
    coordinator.set_task("task.input_data", {"records": [1, 2, 3, 4, 5]})
    coordinator.set_task("task.parameters", {"batch_size": 2})
    
    # Coordinator delegates task
    delegation = AgentMessage(
        sender_id="coordinator",
        recipient_id="worker",
        message_type=MessageType.TASK_DELEGATION,
        payload={
            "task_id": "task_001",
            "context_keys": [
                "task.type",
                "task.input_data",
                "task.parameters"
            ]
        }
    )
    
    print(f"\nTask delegated: {delegation.payload['task_id']}")
    
    # Worker reads task context
    task_type = worker.get_task("task.type")
    input_data = worker.get_task("task.input_data")
    params = worker.get_task("task.parameters")
    
    print(f"Worker received: {task_type.value}")
    print(f"  Input: {input_data.value}")
    print(f"  Params: {params.value}")
    
    # Worker updates progress in context
    worker.set_task("task.progress", 50)
    worker.set_task("task.status", "processing")
    
    # Worker completes and reports back
    worker.set_task("task.result", {"processed": 5, "success": True})
    worker.set_task("task.status", "completed")
    
    completion = AgentMessage(
        sender_id="worker",
        recipient_id="coordinator",
        message_type=MessageType.TASK_COMPLETION,
        correlation_id=delegation.id,
        payload={
            "task_id": "task_001",
            "status": "completed",
            "result_context_key": "task.result"
        }
    )
    
    print(f"Task completed: {completion.payload['status']}")
    
    # Coordinator reads result
    result = coordinator.get_task("task.result")
    print(f"  Result: {result.value}")
    
    return delegation, completion


def main():
    """Run all integration examples."""
    print("=" * 60)
    print("Context Management + AgentMessage Integration Examples")
    print("=" * 60)
    
    print("\n1. Context Sharing via Messages")
    print("-" * 60)
    example_context_sharing_via_messages()
    
    print("\n2. Context Request/Response")
    print("-" * 60)
    example_context_request()
    
    print("\n3. Broadcast Context Updates")
    print("-" * 60)
    example_broadcast_context_update()
    
    print("\n4. Subscription-based Notifications")
    print("-" * 60)
    example_subscription_with_notifications()
    
    print("\n5. Versioned Coordination")
    print("-" * 60)
    example_versioned_coordination()
    
    print("\n6. Task Delegation with Context")
    print("-" * 60)
    example_task_delegation_with_context()
    
    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
