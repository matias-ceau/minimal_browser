"""Unit tests for Agent-to-Agent Communication System (a2a.py).

Tests cover MessageBroker, EventBus, and AgentRegistry functionality
including message passing, event routing, and agent discovery.
"""

from __future__ import annotations

import asyncio
import importlib.util
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import pytest

# Import modules directly to avoid PySide6 dependency
def import_module_direct(name: str, filepath: str):
    """Import a module directly from file path, bypassing package __init__.py"""
    spec = importlib.util.spec_from_file_location(name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# Get the source directory
src_dir = Path(__file__).parent.parent.parent.parent / "src" / "minimal_browser" / "coordination"

# Import required modules
agentic_struct_module = import_module_direct(
    'minimal_browser.coordination.agentic_struct',
    str(src_dir / 'agentic_struct.py')
)
a2a_module = import_module_direct(
    'minimal_browser.coordination.a2a',
    str(src_dir / 'a2a.py')
)

# Extract classes we need
Agent = agentic_struct_module.Agent
AgentCapabilities = agentic_struct_module.AgentCapabilities
AgentMessage = agentic_struct_module.AgentMessage
AgentStatus = agentic_struct_module.AgentStatus
MessagePriority = agentic_struct_module.MessagePriority
MessageType = agentic_struct_module.MessageType

MessageBroker = a2a_module.MessageBroker
EventBus = a2a_module.EventBus
AgentRegistry = a2a_module.AgentRegistry


class TestMessageBroker:
    """Test MessageBroker functionality."""

    @pytest.mark.asyncio
    async def test_create_broker(self):
        """Test creating a message broker."""
        broker = MessageBroker()
        assert broker is not None
        assert len(broker.get_dead_letter_queue()) == 0

    @pytest.mark.asyncio
    async def test_send_message_direct(self):
        """Test sending a direct message to a specific agent."""
        broker = MessageBroker()
        
        message = AgentMessage(
            sender_id="agent_a",
            recipient_id="agent_b",
            message_type=MessageType.REQUEST,
            payload={"action": "search", "query": "test"}
        )
        
        await broker.send_message(message)
        
        # Retrieve messages for agent_b
        messages = await broker.get_pending_messages("agent_b")
        assert len(messages) == 1
        assert messages[0].sender_id == "agent_a"
        assert messages[0].payload["action"] == "search"

    @pytest.mark.asyncio
    async def test_send_message_without_recipient_raises_error(self):
        """Test that sending a message without recipient raises ValueError."""
        broker = MessageBroker()
        
        message = AgentMessage(
            sender_id="agent_a",
            recipient_id=None,  # Broadcast message
            message_type=MessageType.REQUEST,
            payload={"test": "data"}
        )
        
        with pytest.raises(ValueError, match="recipient_id cannot be None"):
            await broker.send_message(message)

    @pytest.mark.asyncio
    async def test_message_priority_ordering(self):
        """Test that messages are delivered in priority order."""
        broker = MessageBroker()
        
        # Send messages with different priorities
        low_msg = AgentMessage(
            sender_id="sender",
            recipient_id="receiver",
            message_type=MessageType.NOTIFICATION,
            priority=MessagePriority.LOW,
            payload={"priority": "low"}
        )
        
        high_msg = AgentMessage(
            sender_id="sender",
            recipient_id="receiver",
            message_type=MessageType.NOTIFICATION,
            priority=MessagePriority.HIGH,
            payload={"priority": "high"}
        )
        
        normal_msg = AgentMessage(
            sender_id="sender",
            recipient_id="receiver",
            message_type=MessageType.NOTIFICATION,
            priority=MessagePriority.NORMAL,
            payload={"priority": "normal"}
        )
        
        # Send in random order
        await broker.send_message(low_msg)
        await broker.send_message(high_msg)
        await broker.send_message(normal_msg)
        
        # Retrieve messages - should be in priority order
        messages = await broker.get_pending_messages("receiver")
        assert len(messages) == 3
        assert messages[0].payload["priority"] == "high"
        assert messages[1].payload["priority"] == "normal"
        assert messages[2].payload["priority"] == "low"

    @pytest.mark.asyncio
    async def test_broadcast_message(self):
        """Test broadcasting a message to multiple agents."""
        broker = MessageBroker()
        
        # Subscribe agents to message type
        await broker.subscribe("agent_1", [MessageType.BROADCAST])
        await broker.subscribe("agent_2", [MessageType.BROADCAST])
        await broker.subscribe("agent_3", [MessageType.NOTIFICATION])  # Different type
        
        # Broadcast message
        message = AgentMessage(
            sender_id="broadcaster",
            recipient_id=None,
            message_type=MessageType.BROADCAST,
            payload={"announcement": "System update"}
        )
        
        await broker.broadcast(message)
        
        # Check that subscribed agents received the message
        agent1_messages = await broker.get_pending_messages("agent_1")
        agent2_messages = await broker.get_pending_messages("agent_2")
        agent3_messages = await broker.get_pending_messages("agent_3")
        
        assert len(agent1_messages) == 1
        assert len(agent2_messages) == 1
        assert len(agent3_messages) == 0  # Not subscribed to BROADCAST

    @pytest.mark.asyncio
    async def test_publish_routes_correctly(self):
        """Test that publish() routes to send_message or broadcast correctly."""
        broker = MessageBroker()
        
        # Direct message
        direct_msg = AgentMessage(
            sender_id="sender",
            recipient_id="receiver",
            message_type=MessageType.REQUEST,
            payload={}
        )
        await broker.publish(direct_msg)
        
        # Broadcast message
        await broker.subscribe("agent_1", [MessageType.BROADCAST])
        broadcast_msg = AgentMessage(
            sender_id="sender",
            recipient_id=None,
            message_type=MessageType.BROADCAST,
            payload={}
        )
        await broker.publish(broadcast_msg)
        
        # Verify routing
        receiver_messages = await broker.get_pending_messages("receiver")
        agent1_messages = await broker.get_pending_messages("agent_1")
        
        assert len(receiver_messages) == 1
        assert len(agent1_messages) == 1

    @pytest.mark.asyncio
    async def test_expired_message_goes_to_dead_letter_queue(self):
        """Test that expired messages are moved to dead letter queue."""
        broker = MessageBroker()
        
        # Create an already-expired message
        past_time = datetime.utcnow() - timedelta(hours=1)
        expired_msg = AgentMessage(
            sender_id="sender",
            recipient_id="receiver",
            message_type=MessageType.REQUEST,
            expires_at=past_time,
            payload={}
        )
        
        await broker.send_message(expired_msg)
        
        # Check dead letter queue
        dlq = broker.get_dead_letter_queue()
        assert len(dlq) == 1
        assert dlq[0][0].id == expired_msg.id
        assert dlq[0][1] == "expired"
        
        # Message should not be in regular queue
        messages = await broker.get_pending_messages("receiver")
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_subscribe_and_unsubscribe(self):
        """Test agent subscription and unsubscription."""
        broker = MessageBroker()
        
        # Subscribe agent
        await broker.subscribe("agent_1", [MessageType.REQUEST, MessageType.RESPONSE])
        
        # Send broadcast
        message = AgentMessage(
            sender_id="sender",
            recipient_id=None,
            message_type=MessageType.REQUEST,
            payload={}
        )
        await broker.broadcast(message)
        
        # Agent should receive message
        messages = await broker.get_pending_messages("agent_1")
        assert len(messages) == 1
        
        # Unsubscribe
        await broker.unsubscribe("agent_1")
        
        # Send another broadcast
        message2 = AgentMessage(
            sender_id="sender",
            recipient_id=None,
            message_type=MessageType.REQUEST,
            payload={}
        )
        await broker.broadcast(message2)
        
        # Agent should not receive new message
        messages = await broker.get_pending_messages("agent_1")
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_max_messages_limit(self):
        """Test retrieving limited number of messages."""
        broker = MessageBroker()
        
        # Send multiple messages
        for i in range(10):
            message = AgentMessage(
                sender_id="sender",
                recipient_id="receiver",
                message_type=MessageType.NOTIFICATION,
                payload={"index": i}
            )
            await broker.send_message(message)
        
        # Retrieve only 3 messages
        messages = await broker.get_pending_messages("receiver", max_messages=3)
        assert len(messages) == 3

    @pytest.mark.asyncio
    async def test_clear_dead_letter_queue(self):
        """Test clearing the dead letter queue."""
        broker = MessageBroker()
        
        # Create expired message
        past_time = datetime.utcnow() - timedelta(hours=1)
        expired_msg = AgentMessage(
            sender_id="sender",
            recipient_id="receiver",
            message_type=MessageType.REQUEST,
            expires_at=past_time,
            payload={}
        )
        
        await broker.send_message(expired_msg)
        assert len(broker.get_dead_letter_queue()) == 1
        
        # Clear DLQ
        broker.clear_dead_letter_queue()
        assert len(broker.get_dead_letter_queue()) == 0


class TestEventBus:
    """Test EventBus functionality."""

    @pytest.mark.asyncio
    async def test_create_event_bus(self):
        """Test creating an event bus."""
        bus = EventBus()
        assert bus is not None

    @pytest.mark.asyncio
    async def test_publish_and_subscribe(self):
        """Test basic publish-subscribe functionality."""
        bus = EventBus()
        received_events = []
        
        def handler(event: Dict[str, Any]):
            received_events.append(event)
        
        # Subscribe to topic
        sub_id = await bus.subscribe("browser.navigation", handler)
        assert sub_id.startswith("sub_")
        
        # Publish event
        await bus.publish("browser.navigation", {"url": "https://example.com"})
        
        # Check handler was called
        assert len(received_events) == 1
        assert received_events[0]["url"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_async_event_handler(self):
        """Test that async event handlers work correctly."""
        bus = EventBus()
        received_events = []
        
        async def async_handler(event: Dict[str, Any]):
            await asyncio.sleep(0.01)  # Simulate async work
            received_events.append(event)
        
        await bus.subscribe("test.async", async_handler)
        await bus.publish("test.async", {"data": "test"})
        
        assert len(received_events) == 1
        assert received_events[0]["data"] == "test"

    @pytest.mark.asyncio
    async def test_wildcard_topic_matching(self):
        """Test wildcard pattern matching for topics."""
        bus = EventBus()
        received_events = []
        
        def handler(event: Dict[str, Any]):
            received_events.append(event)
        
        # Subscribe with wildcard
        await bus.subscribe("browser.*", handler)
        
        # Publish to different sub-topics
        await bus.publish("browser.navigation", {"action": "nav"})
        await bus.publish("browser.reload", {"action": "reload"})
        await bus.publish("window.close", {"action": "close"})  # Different topic
        
        # Handler should receive browser.* events only
        assert len(received_events) == 2
        assert received_events[0]["action"] == "nav"
        assert received_events[1]["action"] == "reload"

    @pytest.mark.asyncio
    async def test_double_wildcard_matching(self):
        """Test ** wildcard matching for multiple segments."""
        bus = EventBus()
        received_events = []
        
        def handler(event: Dict[str, Any]):
            received_events.append(event)
        
        # Subscribe with double wildcard
        await bus.subscribe("browser.**", handler)
        
        # Publish to nested topics
        await bus.publish("browser.tab.open", {"tab": 1})
        await bus.publish("browser.tab.close", {"tab": 2})
        await bus.publish("browser.window.resize", {"size": 100})
        await bus.publish("system.shutdown", {"now": True})  # Different root
        
        # Handler should receive all browser.** events
        assert len(received_events) == 3

    @pytest.mark.asyncio
    async def test_multiple_subscribers_same_topic(self):
        """Test multiple subscribers to the same topic."""
        bus = EventBus()
        handler1_calls = []
        handler2_calls = []
        
        def handler1(event: Dict[str, Any]):
            handler1_calls.append(event)
        
        def handler2(event: Dict[str, Any]):
            handler2_calls.append(event)
        
        # Multiple subscriptions to same topic
        await bus.subscribe("test.topic", handler1)
        await bus.subscribe("test.topic", handler2)
        
        # Publish event
        await bus.publish("test.topic", {"data": "test"})
        
        # Both handlers should be called
        assert len(handler1_calls) == 1
        assert len(handler2_calls) == 1

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        """Test unsubscribing from topics."""
        bus = EventBus()
        received_events = []
        
        def handler(event: Dict[str, Any]):
            received_events.append(event)
        
        # Subscribe and publish
        sub_id = await bus.subscribe("test.topic", handler)
        await bus.publish("test.topic", {"count": 1})
        
        # Unsubscribe
        await bus.unsubscribe(sub_id)
        
        # Publish again
        await bus.publish("test.topic", {"count": 2})
        
        # Should only have received first event
        assert len(received_events) == 1
        assert received_events[0]["count"] == 1

    @pytest.mark.asyncio
    async def test_publish_pattern(self):
        """Test publishing to a pattern of topics."""
        bus = EventBus()
        nav_events = []
        tab_events = []
        
        def nav_handler(event: Dict[str, Any]):
            nav_events.append(event)
        
        def tab_handler(event: Dict[str, Any]):
            tab_events.append(event)
        
        # Subscribe to specific topics
        await bus.subscribe("browser.navigation", nav_handler)
        await bus.subscribe("browser.tab", tab_handler)
        
        # Publish to pattern
        await bus.publish_pattern("browser.*", {"source": "pattern"})
        
        # Both handlers should receive the event
        assert len(nav_events) == 1
        assert len(tab_events) == 1

    @pytest.mark.asyncio
    async def test_handler_exception_handling(self):
        """Test that exceptions in handlers don't break the event bus."""
        bus = EventBus()
        good_handler_calls = []
        
        def bad_handler(event: Dict[str, Any]):
            raise RuntimeError("Handler error")
        
        def good_handler(event: Dict[str, Any]):
            good_handler_calls.append(event)
        
        # Subscribe both handlers
        await bus.subscribe("test.topic", bad_handler)
        await bus.subscribe("test.topic", good_handler)
        
        # Publish event - should not raise exception
        await bus.publish("test.topic", {"data": "test"})
        
        # Good handler should still be called
        assert len(good_handler_calls) == 1

    @pytest.mark.asyncio
    async def test_exact_topic_matching(self):
        """Test exact topic matching without wildcards."""
        bus = EventBus()
        received_events = []
        
        def handler(event: Dict[str, Any]):
            received_events.append(event)
        
        await bus.subscribe("exact.topic.name", handler)
        
        # Exact match should work
        await bus.publish("exact.topic.name", {"exact": True})
        
        # Similar but different topics should not match
        await bus.publish("exact.topic", {"exact": False})
        await bus.publish("exact.topic.name.extra", {"exact": False})
        
        assert len(received_events) == 1
        assert received_events[0]["exact"] is True


class TestAgentRegistry:
    """Test AgentRegistry functionality."""

    @pytest.mark.asyncio
    async def test_create_registry(self):
        """Test creating an agent registry."""
        registry = AgentRegistry()
        assert registry is not None

    @pytest.mark.asyncio
    async def test_register_agent(self):
        """Test registering an agent."""
        registry = AgentRegistry()
        
        agent = Agent(
            agent_id="test_agent",
            name="TestAgent",
            capabilities=AgentCapabilities(
                name="search",
                supported_actions=["web_search", "query"]
            )
        )
        
        await registry.register(agent)
        
        # Verify agent was registered
        retrieved = await registry.get_agent("test_agent")
        assert retrieved is not None
        assert retrieved.name == "TestAgent"

    @pytest.mark.asyncio
    async def test_unregister_agent(self):
        """Test unregistering an agent."""
        registry = AgentRegistry()
        
        agent = Agent(agent_id="test_agent", name="TestAgent")
        await registry.register(agent)
        
        # Unregister
        await registry.unregister("test_agent")
        
        # Agent should be gone
        retrieved = await registry.get_agent("test_agent")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_find_by_capability(self):
        """Test finding agents by capability."""
        registry = AgentRegistry()
        
        # Register agents with different capabilities
        agent1 = Agent(
            agent_id="search_agent",
            name="SearchAgent",
            capabilities=AgentCapabilities(
                name="search",
                supported_actions=["web_search", "query"]
            )
        )
        
        agent2 = Agent(
            agent_id="render_agent",
            name="RenderAgent",
            capabilities=AgentCapabilities(
                name="renderer",
                supported_actions=["render_html", "generate_ui"]
            )
        )
        
        agent3 = Agent(
            agent_id="multi_agent",
            name="MultiAgent",
            capabilities=AgentCapabilities(
                name="multi",
                supported_actions=["web_search", "render_html"]
            )
        )
        
        await registry.register(agent1)
        await registry.register(agent2)
        await registry.register(agent3)
        
        # Find by capability
        search_agents = await registry.find_by_capability("web_search")
        render_agents = await registry.find_by_capability("render_html")
        
        assert len(search_agents) == 2
        assert len(render_agents) == 2
        assert any(a.id == "search_agent" for a in search_agents)
        assert any(a.id == "multi_agent" for a in search_agents)

    @pytest.mark.asyncio
    async def test_get_all_agents(self):
        """Test getting all registered agents."""
        registry = AgentRegistry()
        
        # Register multiple agents
        for i in range(3):
            agent = Agent(agent_id=f"agent_{i}", name=f"Agent{i}")
            await registry.register(agent)
        
        # Get all agents
        all_agents = await registry.get_all_agents()
        assert len(all_agents) == 3

    @pytest.mark.asyncio
    async def test_update_agent_status(self):
        """Test updating agent status."""
        registry = AgentRegistry()
        
        agent = Agent(agent_id="test_agent", name="TestAgent")
        await registry.register(agent)
        
        # Update status
        await registry.update_status("test_agent", AgentStatus.BUSY)
        
        # Verify status changed
        retrieved = await registry.get_agent("test_agent")
        assert retrieved.status == AgentStatus.BUSY

    @pytest.mark.asyncio
    async def test_heartbeat(self):
        """Test recording agent heartbeats."""
        registry = AgentRegistry()
        
        agent = Agent(agent_id="test_agent", name="TestAgent")
        await registry.register(agent)
        
        # Get initial heartbeat time
        retrieved = await registry.get_agent("test_agent")
        initial_heartbeat = retrieved.last_heartbeat
        
        # Wait a bit and send heartbeat
        await asyncio.sleep(0.1)
        await registry.heartbeat("test_agent")
        
        # Verify heartbeat updated
        retrieved = await registry.get_agent("test_agent")
        assert retrieved.last_heartbeat > initial_heartbeat

    @pytest.mark.asyncio
    async def test_get_stale_agents(self):
        """Test detecting stale agents."""
        # Use very short timeout for testing
        registry = AgentRegistry(heartbeat_timeout=0.2)
        
        agent = Agent(agent_id="test_agent", name="TestAgent")
        await registry.register(agent)
        
        # Agent should not be stale immediately
        stale = await registry.get_stale_agents()
        assert len(stale) == 0
        
        # Wait for agent to become stale
        await asyncio.sleep(0.3)
        
        # Agent should now be stale
        stale = await registry.get_stale_agents()
        assert len(stale) == 1
        assert stale[0].id == "test_agent"

    @pytest.mark.asyncio
    async def test_register_updates_heartbeat(self):
        """Test that registering an agent updates its heartbeat."""
        registry = AgentRegistry()
        
        agent = Agent(agent_id="test_agent", name="TestAgent")
        old_heartbeat = agent.last_heartbeat
        
        await asyncio.sleep(0.1)
        await registry.register(agent)
        
        # Heartbeat should be updated during registration
        retrieved = await registry.get_agent("test_agent")
        assert retrieved.last_heartbeat > old_heartbeat


class TestIntegration:
    """Integration tests combining multiple components."""

    @pytest.mark.asyncio
    async def test_agent_communication_workflow(self):
        """Test complete agent-to-agent communication workflow."""
        broker = MessageBroker()
        registry = AgentRegistry()
        
        # Register agents
        agent_a = Agent(
            agent_id="agent_a",
            name="AgentA",
            capabilities=AgentCapabilities(
                name="requester",
                supported_actions=["request"]
            )
        )
        agent_b = Agent(
            agent_id="agent_b",
            name="AgentB",
            capabilities=AgentCapabilities(
                name="responder",
                supported_actions=["respond"]
            )
        )
        
        await registry.register(agent_a)
        await registry.register(agent_b)
        
        # Agent A sends request to Agent B
        request = AgentMessage(
            sender_id="agent_a",
            recipient_id="agent_b",
            message_type=MessageType.REQUEST,
            payload={"action": "search", "query": "test"}
        )
        await broker.send_message(request)
        
        # Agent B retrieves request
        messages = await broker.get_pending_messages("agent_b")
        assert len(messages) == 1
        
        # Agent B sends response
        response = AgentMessage(
            sender_id="agent_b",
            recipient_id="agent_a",
            message_type=MessageType.RESPONSE,
            correlation_id=messages[0].id,
            payload={"results": ["result1", "result2"]}
        )
        await broker.send_message(response)
        
        # Agent A retrieves response
        responses = await broker.get_pending_messages("agent_a")
        assert len(responses) == 1
        assert responses[0].correlation_id == request.id

    @pytest.mark.asyncio
    async def test_event_bus_with_multiple_agents(self):
        """Test event bus coordination with multiple agents."""
        bus = EventBus()
        registry = AgentRegistry()
        
        # Track events received by each agent
        agent_events = {"agent_1": [], "agent_2": [], "agent_3": []}
        
        def make_handler(agent_id: str):
            def handler(event: Dict[str, Any]):
                agent_events[agent_id].append(event)
            return handler
        
        # Register agents and subscribe to events
        for agent_id in agent_events.keys():
            agent = Agent(agent_id=agent_id, name=f"Agent{agent_id[-1]}")
            await registry.register(agent)
            await bus.subscribe("browser.*", make_handler(agent_id))
        
        # Publish event
        await bus.publish("browser.navigation", {"url": "https://example.com"})
        
        # All agents should receive the event
        for agent_id, events in agent_events.items():
            assert len(events) == 1
            assert events[0]["url"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_capability_based_task_routing(self):
        """Test routing tasks based on agent capabilities."""
        broker = MessageBroker()
        registry = AgentRegistry()
        
        # Register specialized agents
        search_agent = Agent(
            agent_id="search_agent",
            name="SearchAgent",
            capabilities=AgentCapabilities(
                name="search",
                supported_actions=["web_search"]
            )
        )
        render_agent = Agent(
            agent_id="render_agent",
            name="RenderAgent",
            capabilities=AgentCapabilities(
                name="render",
                supported_actions=["render_html"]
            )
        )
        
        await registry.register(search_agent)
        await registry.register(render_agent)
        
        # Find agent for web search
        capable_agents = await registry.find_by_capability("web_search")
        assert len(capable_agents) == 1
        
        # Send task to capable agent
        task = AgentMessage(
            sender_id="coordinator",
            recipient_id=capable_agents[0].id,
            message_type=MessageType.TASK_DELEGATION,
            payload={"query": "Python tutorials"}
        )
        await broker.send_message(task)
        
        # Search agent should have the task
        messages = await broker.get_pending_messages("search_agent")
        assert len(messages) == 1
        assert messages[0].message_type == MessageType.TASK_DELEGATION
