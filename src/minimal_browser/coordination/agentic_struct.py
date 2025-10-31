
"""Agent structures and registry for the Agent Communication Bus (ACB).

This module provides the foundational agent infrastructure including:
- Base Agent class with communication capabilities
- AgentRegistry for managing active agents
- Message types and routing protocols
- Agent lifecycle management
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field


# Configure logging
logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Enumeration of possible agent states."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    SUSPENDED = "suspended"
    TERMINATING = "terminating"
    TERMINATED = "terminated"


class MessagePriority(IntEnum):
    """Priority levels for agent messages."""
    LOWEST = 0
    LOW = 25
    NORMAL = 50
    HIGH = 75
    HIGHEST = 100


class MessageType(Enum):
    """Types of messages that can be exchanged between agents."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    BROADCAST = "broadcast"
    HEARTBEAT = "heartbeat"
    TASK_DELEGATION = "task_delegation"
    TASK_COMPLETION = "task_completion"
    CONTEXT_REQUEST = "context_request"
    CONTEXT_SHARE = "context_share"

    # System
    ERROR = "error"
    SHUTDOWN = "shutdown"


class AgentMessage(BaseModel):
    """Structured message exchanged between agents."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str
    recipient_id: Optional[str] = None  # None for broadcast
    message_type: MessageType
    priority: MessagePriority = MessagePriority.NORMAL
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None  # For request-response correlation
    expires_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        """Check if the message has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def is_broadcast(self) -> bool:
        """Check if this is a broadcast message."""
        return self.recipient_id is None


class AgentCapabilities(BaseModel):
    """Defines the capabilities of an agent."""

    name: str
    version: str = "1.0.0"
    supported_actions: List[str] = Field(default_factory=list)
    supported_message_types: List[MessageType] = Field(default_factory=list)
    max_concurrent_tasks: int = 1
    requires_context: bool = False
    provides_context: bool = False


class Agent:
    """Base class for all agents in the OACS system.

    This class provides the core functionality for agent communication,
    lifecycle management, and basic operations. Specific agent implementations
    should inherit from this class and implement the abstract methods.
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        name: str = "BaseAgent",
        capabilities: Optional[AgentCapabilities] = None,
    ) -> None:
        self.id = agent_id or str(uuid.uuid4())
        self.name = name
        self.capabilities = capabilities or AgentCapabilities(name=name)
        self.status = AgentStatus.INITIALIZING
        self.created_at = datetime.utcnow()
        self.last_heartbeat = datetime.utcnow()

        # Communication
        self._message_queue: asyncio.Queue[AgentMessage] = asyncio.Queue()
        self._message_handlers: Dict[MessageType, callable] = {}
        self._pending_responses: Dict[str, asyncio.Future] = {}

        # Task management
        self._active_tasks: Set[asyncio.Task] = set()
