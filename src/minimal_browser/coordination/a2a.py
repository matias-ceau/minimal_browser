"""Agent-to-Agent Communication System.

This module implements the core communication infrastructure for the multi-agent
system (OACS), providing:
- Message passing between agents
- Event bus for agent coordination
- Agent registry and discovery
"""

from __future__ import annotations

import asyncio
import logging
import re
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from .agentic_struct import Agent, AgentMessage, AgentStatus, MessageType

# Configure logging
logger = logging.getLogger(__name__)


class MessageBroker:
    """Central message routing and delivery system.
    
    Provides reliable message delivery with at-least-once semantics,
    message queuing, priority handling, and TTL support.
    """
    
    def __init__(self) -> None:
        """Initialize the message broker."""
        # Message queues for each agent (agent_id -> priority queue)
        self._queues: Dict[str, asyncio.PriorityQueue] = {}
        
        # Subscriptions: agent_id -> set of MessageTypes they're interested in
        self._subscriptions: Dict[str, Set[MessageType]] = defaultdict(set)
        
        # Dead letter queue for messages that couldn't be delivered
        self._dead_letter_queue: List[tuple[AgentMessage, str]] = []
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        
        # Message counter for tie-breaking in priority queue
        self._message_counter = 0
        
        logger.info("MessageBroker initialized")
    
    async def subscribe(
        self,
        agent_id: str,
        message_types: List[MessageType]
    ) -> None:
        """Subscribe an agent to specific message types.
        
        Args:
            agent_id: ID of the agent subscribing
            message_types: List of message types to subscribe to
        """
        async with self._lock:
            if agent_id not in self._queues:
                self._queues[agent_id] = asyncio.PriorityQueue()
            
            self._subscriptions[agent_id].update(message_types)
            logger.debug(
                f"Agent {agent_id} subscribed to {len(message_types)} message types"
            )
    
    async def unsubscribe(self, agent_id: str) -> None:
        """Unsubscribe an agent from all message types.
        
        Args:
            agent_id: ID of the agent to unsubscribe
        """
        async with self._lock:
            if agent_id in self._subscriptions:
                del self._subscriptions[agent_id]
            
            # Clear the queue but don't delete it (agent might reconnect)
            if agent_id in self._queues:
                # Drain the queue
                while not self._queues[agent_id].empty():
                    try:
                        self._queues[agent_id].get_nowait()
                    except asyncio.QueueEmpty:
                        break
            
            logger.debug(f"Agent {agent_id} unsubscribed from all message types")
    
    async def send_message(self, message: AgentMessage) -> None:
        """Send a message to a specific agent.
        
        Args:
            message: The message to send
            
        Raises:
            ValueError: If recipient_id is None (use broadcast instead)
        """
        if message.recipient_id is None:
            raise ValueError("recipient_id cannot be None for send_message. Use broadcast() instead.")
        
        # Check if message has expired
        if message.is_expired():
            logger.warning(f"Message {message.id} has expired, not delivering")
            await self._add_to_dead_letter_queue(message, "expired")
            return
        
        async with self._lock:
            recipient_id = message.recipient_id
            
            # Create queue if it doesn't exist
            if recipient_id not in self._queues:
                self._queues[recipient_id] = asyncio.PriorityQueue()
            
            # Priority is negated because PriorityQueue is a min-heap
            # Higher priority values should be processed first
            # Use counter as tie-breaker to ensure FIFO for same priority
            priority = -message.priority.value
            self._message_counter += 1
            await self._queues[recipient_id].put((priority, self._message_counter, message))
            
            logger.debug(
                f"Message {message.id} queued for {recipient_id} "
                f"(type: {message.message_type}, priority: {message.priority})"
            )
    
    async def broadcast(self, message: AgentMessage) -> None:
        """Broadcast a message to all subscribed agents.
        
        Args:
            message: The message to broadcast (recipient_id will be ignored)
        """
        if message.is_expired():
            logger.warning(f"Broadcast message {message.id} has expired, not delivering")
            await self._add_to_dead_letter_queue(message, "expired")
            return
        
        async with self._lock:
            # Find all agents interested in this message type
            interested_agents = [
                agent_id
                for agent_id, subscribed_types in self._subscriptions.items()
                if message.message_type in subscribed_types or not subscribed_types
            ]
            
            if not interested_agents:
                logger.warning(
                    f"No agents subscribed to message type {message.message_type} "
                    f"for broadcast message {message.id}"
                )
                return
            
            # Queue message for each interested agent
            for agent_id in interested_agents:
                if agent_id not in self._queues:
                    self._queues[agent_id] = asyncio.PriorityQueue()
                
                priority = -message.priority.value
                self._message_counter += 1
                await self._queues[agent_id].put((priority, self._message_counter, message))
            
            logger.debug(
                f"Broadcast message {message.id} queued for {len(interested_agents)} agents"
            )
    
    async def publish(self, message: AgentMessage) -> None:
        """Publish a message (automatically routes to send_message or broadcast).
        
        Args:
            message: The message to publish
        """
        if message.is_broadcast():
            await self.broadcast(message)
        else:
            await self.send_message(message)
    
    async def get_pending_messages(
        self,
        agent_id: str,
        max_messages: Optional[int] = None
    ) -> List[AgentMessage]:
        """Get pending messages for an agent.
        
        Args:
            agent_id: ID of the agent
            max_messages: Maximum number of messages to retrieve (None for all)
            
        Returns:
            List of messages in priority order
        """
        async with self._lock:
            if agent_id not in self._queues:
                return []
            
            messages = []
            queue = self._queues[agent_id]
            count = 0
            
            while not queue.empty():
                if max_messages is not None and count >= max_messages:
                    break
                
                try:
                    priority, counter, message = queue.get_nowait()
                    
                    # Check if message has expired
                    if message.is_expired():
                        logger.debug(f"Message {message.id} expired, moving to dead letter queue")
                        await self._add_to_dead_letter_queue(message, "expired")
                        continue
                    
                    messages.append(message)
                    count += 1
                except asyncio.QueueEmpty:
                    break
            
            logger.debug(f"Retrieved {len(messages)} pending messages for {agent_id}")
            return messages
    
    async def _add_to_dead_letter_queue(
        self,
        message: AgentMessage,
        reason: str
    ) -> None:
        """Add a message to the dead letter queue.
        
        Args:
            message: The failed message
            reason: Reason for failure
        """
        self._dead_letter_queue.append((message, reason))
        logger.debug(f"Message {message.id} added to dead letter queue: {reason}")
    
    def get_dead_letter_queue(self) -> List[tuple[AgentMessage, str]]:
        """Get all messages in the dead letter queue.
        
        Returns:
            List of (message, reason) tuples
        """
        return list(self._dead_letter_queue)
    
    def clear_dead_letter_queue(self) -> None:
        """Clear the dead letter queue."""
        self._dead_letter_queue.clear()
        logger.debug("Dead letter queue cleared")


class EventBus:
    """Topic-based event system for agent coordination.
    
    Provides publish-subscribe event system with pattern matching
    and event filtering capabilities.
    """
    
    def __init__(self) -> None:
        """Initialize the event bus."""
        # Topic subscriptions: subscription_id -> (topic/pattern, handler)
        self._subscriptions: Dict[str, tuple[str, Callable]] = {}
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        
        # Subscription counter for generating unique IDs
        self._subscription_counter = 0
        
        logger.info("EventBus initialized")
    
    async def publish(self, topic: str, event: Dict[str, Any]) -> None:
        """Publish an event to a specific topic.
        
        Args:
            topic: The topic to publish to
            event: The event data
        """
        async with self._lock:
            handlers_to_call = []
            
            # Find matching subscriptions
            for sub_id, (sub_topic, handler) in self._subscriptions.items():
                if self._topic_matches(topic, sub_topic):
                    handlers_to_call.append((sub_id, handler))
            
            if not handlers_to_call:
                logger.debug(f"No handlers for topic: {topic}")
                return
            
            logger.debug(
                f"Publishing event to topic '{topic}' "
                f"({len(handlers_to_call)} handlers)"
            )
        
        # Call handlers outside the lock to avoid deadlocks
        for sub_id, handler in handlers_to_call:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(
                    f"Error in event handler (subscription {sub_id}): {e}",
                    exc_info=True
                )
    
    async def subscribe(
        self,
        topic: str,
        handler: Callable[[Dict[str, Any]], None]
    ) -> str:
        """Subscribe to a topic or pattern.
        
        Args:
            topic: Topic name or pattern (supports wildcards: * and **)
            handler: Callback function to handle events
            
        Returns:
            Subscription ID for later unsubscribe
        """
        async with self._lock:
            self._subscription_counter += 1
            subscription_id = f"sub_{self._subscription_counter}"
            
            self._subscriptions[subscription_id] = (topic, handler)
            
            logger.debug(f"Subscription {subscription_id} created for topic: {topic}")
            return subscription_id
    
    async def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from a topic.
        
        Args:
            subscription_id: The subscription ID returned by subscribe()
        """
        async with self._lock:
            if subscription_id in self._subscriptions:
                topic, _ = self._subscriptions[subscription_id]
                del self._subscriptions[subscription_id]
                logger.debug(
                    f"Subscription {subscription_id} removed (topic: {topic})"
                )
            else:
                logger.warning(f"Subscription {subscription_id} not found")
    
    async def publish_pattern(self, pattern: str, event: Dict[str, Any]) -> None:
        """Publish an event to all topics matching a pattern.
        
        Args:
            pattern: Topic pattern with wildcards
            event: The event data
        """
        async with self._lock:
            handlers_to_call = []
            
            # Find subscriptions where the pattern matches their topic
            for sub_id, (sub_topic, handler) in self._subscriptions.items():
                if self._topic_matches(sub_topic, pattern):
                    handlers_to_call.append((sub_id, handler))
            
            if not handlers_to_call:
                logger.debug(f"No handlers matching pattern: {pattern}")
                return
            
            logger.debug(
                f"Publishing event to pattern '{pattern}' "
                f"({len(handlers_to_call)} handlers)"
            )
        
        # Call handlers outside the lock
        for sub_id, handler in handlers_to_call:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(
                    f"Error in event handler (subscription {sub_id}): {e}",
                    exc_info=True
                )
    
    def _topic_matches(self, topic: str, pattern: str) -> bool:
        """Check if a topic matches a pattern.
        
        Pattern syntax:
        - * matches any single segment
        - ** matches any number of segments
        - Exact matches are supported
        
        Args:
            topic: The topic to check
            pattern: The pattern to match against
            
        Returns:
            True if topic matches pattern
        """
        # Exact match
        if topic == pattern:
            return True
        
        # Convert pattern to regex
        # Escape special regex characters except * and .
        pattern_escaped = re.escape(pattern)
        
        # Replace ** with regex for any segments
        pattern_escaped = pattern_escaped.replace(r"\*\*", ".*")
        
        # Replace * with regex for single segment
        pattern_escaped = pattern_escaped.replace(r"\*", "[^.]+")
        
        # Match full string
        pattern_regex = f"^{pattern_escaped}$"
        
        return re.match(pattern_regex, topic) is not None


class AgentRegistry:
    """Agent discovery and capability matching system.
    
    Manages agent registration, discovery, and health monitoring.
    """
    
    def __init__(self, heartbeat_timeout: float = 60.0) -> None:
        """Initialize the agent registry.
        
        Args:
            heartbeat_timeout: Seconds before an agent is considered stale
        """
        # Registered agents: agent_id -> Agent
        self._agents: Dict[str, Agent] = {}
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        
        # Heartbeat timeout
        self._heartbeat_timeout = heartbeat_timeout
        
        logger.info(f"AgentRegistry initialized (heartbeat timeout: {heartbeat_timeout}s)")
    
    async def register(self, agent: Agent) -> None:
        """Register an agent in the registry.
        
        Args:
            agent: The agent to register
        """
        async with self._lock:
            agent.last_heartbeat = datetime.utcnow()
            self._agents[agent.id] = agent
            
            logger.info(
                f"Agent registered: {agent.id} (name: {agent.name}, "
                f"capabilities: {agent.capabilities.name})"
            )
    
    async def unregister(self, agent_id: str) -> None:
        """Unregister an agent from the registry.
        
        Args:
            agent_id: ID of the agent to unregister
        """
        async with self._lock:
            if agent_id in self._agents:
                agent = self._agents[agent_id]
                del self._agents[agent_id]
                logger.info(f"Agent unregistered: {agent_id} (name: {agent.name})")
            else:
                logger.warning(f"Attempted to unregister unknown agent: {agent_id}")
    
    async def find_by_capability(self, capability: str) -> List[Agent]:
        """Find agents that support a specific capability.
        
        Args:
            capability: The capability to search for
            
        Returns:
            List of agents with the capability
        """
        async with self._lock:
            matching_agents = [
                agent
                for agent in self._agents.values()
                if capability in agent.capabilities.supported_actions
            ]
            
            logger.debug(
                f"Found {len(matching_agents)} agents with capability: {capability}"
            )
            return matching_agents
    
    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID.
        
        Args:
            agent_id: The agent ID
            
        Returns:
            The agent or None if not found
        """
        async with self._lock:
            return self._agents.get(agent_id)
    
    async def get_all_agents(self) -> List[Agent]:
        """Get all registered agents.
        
        Returns:
            List of all registered agents
        """
        async with self._lock:
            return list(self._agents.values())
    
    async def update_status(self, agent_id: str, status: AgentStatus) -> None:
        """Update an agent's status.
        
        Args:
            agent_id: The agent ID
            status: The new status
        """
        async with self._lock:
            if agent_id in self._agents:
                self._agents[agent_id].status = status
                logger.debug(f"Agent {agent_id} status updated to {status.value}")
            else:
                logger.warning(f"Attempted to update status of unknown agent: {agent_id}")
    
    async def heartbeat(self, agent_id: str) -> None:
        """Record a heartbeat from an agent.
        
        Args:
            agent_id: The agent ID
        """
        async with self._lock:
            if agent_id in self._agents:
                self._agents[agent_id].last_heartbeat = datetime.utcnow()
                logger.debug(f"Heartbeat received from agent: {agent_id}")
            else:
                logger.warning(f"Heartbeat from unknown agent: {agent_id}")
    
    async def get_stale_agents(self) -> List[Agent]:
        """Get agents that haven't sent a heartbeat recently.
        
        Returns:
            List of stale agents
        """
        async with self._lock:
            now = datetime.utcnow()
            stale_agents = [
                agent
                for agent in self._agents.values()
                if (now - agent.last_heartbeat).total_seconds() > self._heartbeat_timeout
            ]
            
            if stale_agents:
                logger.warning(f"Found {len(stale_agents)} stale agents")
            
            return stale_agents
