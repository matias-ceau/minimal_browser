"""Agent Context Management for OACS.

This module provides context management capabilities for agent-to-agent
communication and state sharing in the Open Agent Coordination System (OACS).

Features:
- Context sharing between agents with scoping (global, agent-specific, task-specific)
- Context versioning and history tracking
- Subscription/notification system for context changes
- Conflict resolution for concurrent updates
- Thread-safe operations with async support
"""

from __future__ import annotations

import asyncio
import logging
import threading
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import re

from pydantic import BaseModel, Field


# Configure logging
logger = logging.getLogger(__name__)


class ContextScope(Enum):
    """Scope levels for context entries."""
    GLOBAL = "global"      # Shared across all agents
    AGENT = "agent"        # Specific to an agent
    TASK = "task"          # Specific to a task


class ContextEntry(BaseModel):
    """Represents a single context entry with metadata and versioning.
    
    Attributes:
        id: Unique identifier for this context entry
        scope: Scope level (GLOBAL, AGENT, TASK)
        key: Context key (e.g., "browser.current_url")
        value: Actual context data (can be any type)
        agent_id: ID of the agent that owns/created this entry
        version: Version number for optimistic locking
        timestamp: When this entry was created/updated
        expires_at: Optional expiration time
        metadata: Additional metadata
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scope: ContextScope
    key: str
    value: Any
    agent_id: str
    version: int = 1
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if this context entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def matches_pattern(self, pattern: str) -> bool:
        """Check if the key matches a glob-style pattern.
        
        Supports wildcards:
        - * matches any characters within a segment
        - ** matches across segments (dots)
        
        Examples:
            "browser.*" matches "browser.url", "browser.title"
            "task.**.results" matches "task.search.results", "task.query.web.results"
        """
        # Convert glob pattern to regex
        # Important: Handle ** before * to avoid double substitution
        pattern_regex = pattern.replace(".", r"\.")
        pattern_regex = pattern_regex.replace("**", "<<DOUBLE_WILDCARD>>")
        pattern_regex = pattern_regex.replace("*", r"[^.]*")
        pattern_regex = pattern_regex.replace("<<DOUBLE_WILDCARD>>", ".*")
        pattern_regex = f"^{pattern_regex}$"
        
        try:
            return bool(re.match(pattern_regex, self.key))
        except re.error:
            logger.warning(f"Invalid pattern: {pattern}")
            return False


class ConflictResolutionStrategy(Enum):
    """Strategies for resolving context update conflicts."""
    LAST_WRITE_WINS = "last_write_wins"      # Latest update wins
    VERSION_CHECK = "version_check"          # Fail if version mismatch
    MERGE = "merge"                          # Attempt to merge values
    AGENT_PRIORITY = "agent_priority"        # Higher priority agent wins


class ContextStore:
    """Thread-safe storage for context entries with versioning and subscriptions.
    
    Provides CRUD operations, pattern-based subscriptions, and conflict resolution
    for managing shared context between agents.
    """

    def __init__(
        self,
        conflict_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.LAST_WRITE_WINS
    ):
        """Initialize the context store.
        
        Args:
            conflict_strategy: Strategy to use for resolving update conflicts
        """
        # Storage: scope -> key -> ContextEntry
        self._storage: Dict[ContextScope, Dict[str, ContextEntry]] = {
            scope: {} for scope in ContextScope
        }
        
        # History tracking: scope -> key -> List[ContextEntry]
        self._history: Dict[ContextScope, Dict[str, List[ContextEntry]]] = {
            scope: defaultdict(list) for scope in ContextScope
        }
        
        # Subscriptions: pattern -> List[(subscription_id, callback)]
        self._subscriptions: Dict[str, List[tuple[str, Callable[[ContextEntry], None]]]] = defaultdict(list)
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Configuration
        self.conflict_strategy = conflict_strategy
        self._max_history_size = 10  # Keep last 10 versions
        
        logger.info("ContextStore initialized with strategy: %s", conflict_strategy)

    def get(
        self,
        key: str,
        scope: ContextScope = ContextScope.GLOBAL,
        agent_id: Optional[str] = None
    ) -> Optional[ContextEntry]:
        """Retrieve a context entry by key and scope.
        
        Args:
            key: Context key to retrieve
            scope: Scope level to search in
            agent_id: For AGENT scope, the agent ID (required if scope is AGENT)
            
        Returns:
            The context entry if found and not expired, None otherwise
        """
        with self._lock:
            # For agent-specific context, include agent_id in the lookup key
            lookup_key = self._make_lookup_key(key, scope, agent_id)
            
            entry = self._storage[scope].get(lookup_key)
            
            if entry is None:
                return None
                
            if entry.is_expired():
                logger.debug("Context entry expired: %s", key)
                del self._storage[scope][lookup_key]
                return None
                
            return entry

    def set(
        self,
        key: str,
        value: Any,
        scope: ContextScope = ContextScope.GLOBAL,
        agent_id: Optional[str] = None,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        expected_version: Optional[int] = None
    ) -> ContextEntry:
        """Set or update a context entry.
        
        Args:
            key: Context key
            value: Value to store
            scope: Scope level
            agent_id: Agent ID (required if scope is AGENT or for ownership)
            ttl: Time to live in seconds (optional)
            metadata: Additional metadata
            expected_version: For optimistic locking, the expected current version
            
        Returns:
            The created or updated context entry
            
        Raises:
            ValueError: If version check fails or agent_id missing for AGENT scope
        """
        with self._lock:
            if scope == ContextScope.AGENT and agent_id is None:
                raise ValueError("agent_id is required for AGENT scope")
            
            if agent_id is None:
                agent_id = "system"
            
            lookup_key = self._make_lookup_key(key, scope, agent_id)
            existing = self._storage[scope].get(lookup_key)
            
            # Handle versioning and conflicts
            new_version = 1
            if existing is not None:
                # Check version if requested
                if (expected_version is not None and 
                    existing.version != expected_version and
                    self.conflict_strategy == ConflictResolutionStrategy.VERSION_CHECK):
                    raise ValueError(
                        f"Version conflict: expected {expected_version}, "
                        f"got {existing.version}"
                    )
                
                new_version = existing.version + 1
                
                # Store in history
                self._history[scope][lookup_key].append(existing)
                if len(self._history[scope][lookup_key]) > self._max_history_size:
                    self._history[scope][lookup_key].pop(0)
            
            # Calculate expiration
            expires_at = None
            if ttl is not None:
                expires_at = datetime.utcnow() + timedelta(seconds=ttl)
            
            # Create new entry
            entry = ContextEntry(
                scope=scope,
                key=key,
                value=value,
                agent_id=agent_id,
                version=new_version,
                expires_at=expires_at,
                metadata=metadata or {}
            )
            
            self._storage[scope][lookup_key] = entry
            logger.debug("Set context: %s = %s (scope=%s, version=%d)", 
                        key, value, scope, new_version)
            
            # Notify subscribers in a non-blocking way
            try:
                # Try to get or create event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._notify_subscribers(entry))
                else:
                    # If no loop is running, skip async notification
                    pass
            except RuntimeError:
                # No event loop, skip async notification
                pass
            
            return entry

    def delete(
        self,
        key: str,
        scope: ContextScope = ContextScope.GLOBAL,
        agent_id: Optional[str] = None
    ) -> bool:
        """Delete a context entry.
        
        Args:
            key: Context key to delete
            scope: Scope level
            agent_id: Agent ID (required if scope is AGENT)
            
        Returns:
            True if entry was deleted, False if not found
        """
        with self._lock:
            lookup_key = self._make_lookup_key(key, scope, agent_id)
            
            if lookup_key in self._storage[scope]:
                del self._storage[scope][lookup_key]
                logger.debug("Deleted context: %s (scope=%s)", key, scope)
                return True
            
            return False

    def query(
        self,
        pattern: Optional[str] = None,
        scope: Optional[ContextScope] = None,
        agent_id: Optional[str] = None,
        include_expired: bool = False
    ) -> List[ContextEntry]:
        """Query context entries matching criteria.
        
        Args:
            pattern: Glob-style pattern to match keys (e.g., "browser.*")
            scope: Filter by scope (None for all scopes)
            agent_id: Filter by agent ID
            include_expired: Include expired entries
            
        Returns:
            List of matching context entries
        """
        with self._lock:
            results = []
            
            scopes = [scope] if scope else list(ContextScope)
            
            for s in scopes:
                for entry in self._storage[s].values():
                    # Skip expired entries unless requested
                    if not include_expired and entry.is_expired():
                        continue
                    
                    # Filter by agent_id if specified
                    if agent_id and entry.agent_id != agent_id:
                        continue
                    
                    # Filter by pattern if specified
                    if pattern and not entry.matches_pattern(pattern):
                        continue
                    
                    results.append(entry)
            
            return results

    def get_history(
        self,
        key: str,
        scope: ContextScope = ContextScope.GLOBAL,
        agent_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[ContextEntry]:
        """Get version history for a context entry.
        
        Args:
            key: Context key
            scope: Scope level
            agent_id: Agent ID (required if scope is AGENT)
            limit: Maximum number of historical entries to return
            
        Returns:
            List of historical entries, newest first
        """
        with self._lock:
            lookup_key = self._make_lookup_key(key, scope, agent_id)
            history = self._history[scope].get(lookup_key, [])
            
            # Return newest first
            history = list(reversed(history))
            
            if limit:
                history = history[:limit]
            
            return history

    def subscribe(
        self,
        pattern: str,
        callback: Callable[[ContextEntry], None]
    ) -> str:
        """Subscribe to context changes matching a pattern.
        
        The callback will be invoked whenever a context entry matching the pattern
        is created or updated.
        
        Args:
            pattern: Glob-style pattern (e.g., "browser.*", "task.**.results")
            callback: Function to call with the updated ContextEntry
            
        Returns:
            Subscription ID that can be used to unsubscribe
        """
        with self._lock:
            subscription_id = str(uuid.uuid4())
            self._subscriptions[pattern].append((subscription_id, callback))
            logger.debug("Added subscription: %s for pattern: %s", subscription_id, pattern)
            return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a subscription.
        
        Args:
            subscription_id: ID returned from subscribe()
            
        Returns:
            True if subscription was removed, False if not found
        """
        with self._lock:
            for pattern, callbacks in self._subscriptions.items():
                for i, (sub_id, _) in enumerate(callbacks):
                    if sub_id == subscription_id:
                        callbacks.pop(i)
                        logger.debug("Removed subscription: %s", subscription_id)
                        return True
            
            return False

    def clear(
        self,
        scope: Optional[ContextScope] = None,
        agent_id: Optional[str] = None
    ) -> int:
        """Clear context entries.
        
        Args:
            scope: Clear only this scope (None to clear all)
            agent_id: Clear only entries for this agent
            
        Returns:
            Number of entries cleared
        """
        with self._lock:
            count = 0
            scopes = [scope] if scope else list(ContextScope)
            
            for s in scopes:
                if agent_id:
                    # Clear only entries for specific agent
                    to_delete = [
                        k for k, v in self._storage[s].items()
                        if v.agent_id == agent_id
                    ]
                    for k in to_delete:
                        del self._storage[s][k]
                        count += 1
                else:
                    # Clear all entries in scope
                    count += len(self._storage[s])
                    self._storage[s].clear()
            
            logger.info("Cleared %d context entries", count)
            return count

    def merge(
        self,
        contexts: List[ContextEntry],
        strategy: Optional[ConflictResolutionStrategy] = None
    ) -> ContextEntry:
        """Merge multiple context entries into one.
        
        Args:
            contexts: List of context entries to merge (must have same key)
            strategy: Override the default conflict resolution strategy
            
        Returns:
            Merged context entry
            
        Raises:
            ValueError: If contexts list is empty or entries have different keys
        """
        if not contexts:
            raise ValueError("Cannot merge empty context list")
        
        if len(set(c.key for c in contexts)) > 1:
            raise ValueError("Cannot merge contexts with different keys")
        
        strategy = strategy or self.conflict_strategy
        
        if strategy == ConflictResolutionStrategy.LAST_WRITE_WINS:
            # Return the newest entry
            return max(contexts, key=lambda c: c.timestamp)
        
        elif strategy == ConflictResolutionStrategy.VERSION_CHECK:
            # Return highest version
            return max(contexts, key=lambda c: c.version)
        
        elif strategy == ConflictResolutionStrategy.MERGE:
            # Attempt to merge values (only works for dict-like values)
            base = contexts[0]
            merged_value = {}
            
            for entry in contexts:
                if isinstance(entry.value, dict):
                    merged_value.update(entry.value)
                else:
                    # Can't merge non-dict values, fall back to last write wins
                    logger.warning("Cannot merge non-dict values, using last write wins")
                    return max(contexts, key=lambda c: c.timestamp)
            
            return ContextEntry(
                scope=base.scope,
                key=base.key,
                value=merged_value,
                agent_id=base.agent_id,
                version=max(c.version for c in contexts),
                metadata={"merged_from": [c.id for c in contexts]}
            )
        
        else:
            # Default to last write wins
            return max(contexts, key=lambda c: c.timestamp)

    async def _notify_subscribers(self, entry: ContextEntry) -> None:
        """Notify subscribers about a context change.
        
        Args:
            entry: The context entry that was created/updated
        """
        with self._lock:
            # Find matching subscriptions
            callbacks = []
            for pattern, subs in self._subscriptions.items():
                if entry.matches_pattern(pattern):
                    callbacks.extend([callback for _, callback in subs])
        
        # Call callbacks outside lock to prevent deadlocks
        for callback in callbacks:
            try:
                callback(entry)
            except Exception as e:
                logger.error("Error in subscription callback: %s", e, exc_info=True)

    def _make_lookup_key(
        self,
        key: str,
        scope: ContextScope,
        agent_id: Optional[str]
    ) -> str:
        """Create a lookup key for storage.
        
        For AGENT scope, combines key with agent_id to allow per-agent contexts.
        """
        if scope == ContextScope.AGENT and agent_id:
            return f"{agent_id}:{key}"
        return key


class ContextManager:
    """High-level API for agent context management.
    
    Provides a simplified interface for agents to interact with the context store.
    This class is designed to be used by individual agents and provides convenience
    methods for common operations.
    """

    def __init__(
        self,
        store: Optional[ContextStore] = None,
        agent_id: str = "system"
    ):
        """Initialize the context manager.
        
        Args:
            store: Existing ContextStore instance, or None to create a new one
            agent_id: ID of the agent using this manager
        """
        self.store = store or ContextStore()
        self.agent_id = agent_id
        logger.info("ContextManager initialized for agent: %s", agent_id)

    def set_global(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextEntry:
        """Set a global context value."""
        return self.store.set(
            key=key,
            value=value,
            scope=ContextScope.GLOBAL,
            agent_id=self.agent_id,
            ttl=ttl,
            metadata=metadata
        )

    def get_global(self, key: str) -> Optional[ContextEntry]:
        """Get a global context value."""
        return self.store.get(key=key, scope=ContextScope.GLOBAL)

    def set_agent(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextEntry:
        """Set an agent-specific context value."""
        return self.store.set(
            key=key,
            value=value,
            scope=ContextScope.AGENT,
            agent_id=self.agent_id,
            ttl=ttl,
            metadata=metadata
        )

    def get_agent(self, key: str, agent_id: Optional[str] = None) -> Optional[ContextEntry]:
        """Get an agent-specific context value.
        
        Args:
            key: Context key
            agent_id: Agent ID to retrieve context for (defaults to self.agent_id)
        """
        return self.store.get(
            key=key,
            scope=ContextScope.AGENT,
            agent_id=agent_id or self.agent_id
        )

    def set_task(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextEntry:
        """Set a task-specific context value."""
        return self.store.set(
            key=key,
            value=value,
            scope=ContextScope.TASK,
            agent_id=self.agent_id,
            ttl=ttl,
            metadata=metadata
        )

    def get_task(self, key: str) -> Optional[ContextEntry]:
        """Get a task-specific context value."""
        return self.store.get(key=key, scope=ContextScope.TASK, agent_id=self.agent_id)

    def subscribe(
        self,
        pattern: str,
        callback: Callable[[ContextEntry], None]
    ) -> str:
        """Subscribe to context changes matching a pattern."""
        return self.store.subscribe(pattern=pattern, callback=callback)

    def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a subscription."""
        return self.store.unsubscribe(subscription_id)

    def query(
        self,
        pattern: Optional[str] = None,
        scope: Optional[ContextScope] = None
    ) -> List[ContextEntry]:
        """Query context entries."""
        return self.store.query(
            pattern=pattern,
            scope=scope,
            agent_id=self.agent_id if scope == ContextScope.AGENT else None
        )

    def clear_agent_context(self) -> int:
        """Clear all context entries for this agent."""
        return self.store.clear(agent_id=self.agent_id)
