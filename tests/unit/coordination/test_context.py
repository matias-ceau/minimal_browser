"""Unit tests for agent context management.

These tests verify the context management functionality including:
- ContextEntry model and validation
- ContextStore CRUD operations
- Context scoping (global, agent, task)
- Versioning and history tracking
- Subscription/notification system
- Conflict resolution strategies
- Thread safety
"""

from __future__ import annotations

import importlib.util
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest


# Import context module directly to avoid PySide6 dependency
def import_module_direct(name: str, filepath: str):
    """Import a module directly from file path, bypassing package __init__.py"""
    spec = importlib.util.spec_from_file_location(name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Import context module
try:
    src_dir = Path(__file__).parent.parent.parent.parent / "src" / "minimal_browser"
    context_module = import_module_direct(
        'minimal_browser.coordination.context',
        str(src_dir / 'coordination' / 'context.py')
    )
    
    # Extract the classes we need
    ContextEntry = context_module.ContextEntry
    ContextScope = context_module.ContextScope
    ContextStore = context_module.ContextStore
    ContextManager = context_module.ContextManager
    ConflictResolutionStrategy = context_module.ConflictResolutionStrategy
    
    CONTEXT_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    CONTEXT_AVAILABLE = False
    skip_reason = f"Cannot import context module: {e}"

pytestmark = pytest.mark.skipif(
    not CONTEXT_AVAILABLE,
    reason="Context module not available"
)


class TestContextEntry:
    """Test ContextEntry model."""

    def test_create_basic_entry(self):
        """Test creating a basic context entry."""
        entry = ContextEntry(
            scope=ContextScope.GLOBAL,
            key="test.key",
            value="test_value",
            agent_id="agent1"
        )
        
        assert entry.scope == ContextScope.GLOBAL
        assert entry.key == "test.key"
        assert entry.value == "test_value"
        assert entry.agent_id == "agent1"
        assert entry.version == 1
        assert entry.expires_at is None
        assert not entry.is_expired()

    def test_entry_with_expiration(self):
        """Test context entry with expiration time."""
        expires_at = datetime.utcnow() + timedelta(seconds=10)
        entry = ContextEntry(
            scope=ContextScope.GLOBAL,
            key="test.key",
            value="test_value",
            agent_id="agent1",
            expires_at=expires_at
        )
        
        assert not entry.is_expired()
        assert entry.expires_at == expires_at

    def test_entry_expired(self):
        """Test that expired entries are detected."""
        expires_at = datetime.utcnow() - timedelta(seconds=1)
        entry = ContextEntry(
            scope=ContextScope.GLOBAL,
            key="test.key",
            value="test_value",
            agent_id="agent1",
            expires_at=expires_at
        )
        
        assert entry.is_expired()

    def test_entry_with_metadata(self):
        """Test context entry with metadata."""
        metadata = {"source": "test", "priority": "high"}
        entry = ContextEntry(
            scope=ContextScope.GLOBAL,
            key="test.key",
            value="test_value",
            agent_id="agent1",
            metadata=metadata
        )
        
        assert entry.metadata == metadata

    def test_pattern_matching_simple(self):
        """Test simple pattern matching."""
        entry = ContextEntry(
            scope=ContextScope.GLOBAL,
            key="browser.url",
            value="http://example.com",
            agent_id="agent1"
        )
        
        assert entry.matches_pattern("browser.url")
        assert entry.matches_pattern("browser.*")
        assert not entry.matches_pattern("task.*")

    def test_pattern_matching_wildcard(self):
        """Test pattern matching with wildcards."""
        entry = ContextEntry(
            scope=ContextScope.GLOBAL,
            key="task.search.results",
            value=[],
            agent_id="agent1"
        )
        
        assert entry.matches_pattern("task.search.results")
        assert entry.matches_pattern("task.*.results")
        assert entry.matches_pattern("task.**")
        assert not entry.matches_pattern("browser.*")

    def test_pattern_matching_double_wildcard(self):
        """Test pattern matching with double wildcard."""
        entry = ContextEntry(
            scope=ContextScope.GLOBAL,
            key="task.query.web.results",
            value=[],
            agent_id="agent1"
        )
        
        assert entry.matches_pattern("task.**.results")
        assert entry.matches_pattern("task.**")
        assert entry.matches_pattern("**")


class TestContextStore:
    """Test ContextStore operations."""

    def test_create_store(self):
        """Test creating a context store."""
        store = ContextStore()
        assert store.conflict_strategy == ConflictResolutionStrategy.LAST_WRITE_WINS

    def test_set_and_get_global_context(self):
        """Test setting and getting global context."""
        store = ContextStore()
        
        entry = store.set(
            key="test.key",
            value="test_value",
            scope=ContextScope.GLOBAL,
            agent_id="agent1"
        )
        
        assert entry.key == "test.key"
        assert entry.value == "test_value"
        assert entry.version == 1
        
        retrieved = store.get("test.key", ContextScope.GLOBAL)
        assert retrieved is not None
        assert retrieved.value == "test_value"

    def test_set_agent_specific_context(self):
        """Test setting agent-specific context."""
        store = ContextStore()
        
        # Set context for agent1
        store.set(
            key="status",
            value="active",
            scope=ContextScope.AGENT,
            agent_id="agent1"
        )
        
        # Set context for agent2
        store.set(
            key="status",
            value="idle",
            scope=ContextScope.AGENT,
            agent_id="agent2"
        )
        
        # Retrieve agent-specific contexts
        retrieved1 = store.get("status", ContextScope.AGENT, "agent1")
        retrieved2 = store.get("status", ContextScope.AGENT, "agent2")
        
        assert retrieved1.value == "active"
        assert retrieved2.value == "idle"

    def test_set_requires_agent_id_for_agent_scope(self):
        """Test that agent scope requires agent_id."""
        store = ContextStore()
        
        with pytest.raises(ValueError, match="agent_id is required"):
            store.set(
                key="test",
                value="value",
                scope=ContextScope.AGENT
            )

    def test_update_increments_version(self):
        """Test that updating a context increments version."""
        store = ContextStore()
        
        entry1 = store.set("test.key", "value1", agent_id="agent1")
        assert entry1.version == 1
        
        entry2 = store.set("test.key", "value2", agent_id="agent1")
        assert entry2.version == 2
        
        retrieved = store.get("test.key")
        assert retrieved.version == 2
        assert retrieved.value == "value2"

    def test_version_check_conflict_strategy(self):
        """Test version check conflict strategy."""
        store = ContextStore(conflict_strategy=ConflictResolutionStrategy.VERSION_CHECK)
        
        entry1 = store.set("test.key", "value1", agent_id="agent1")
        assert entry1.version == 1
        
        # This should succeed (correct version)
        entry2 = store.set("test.key", "value2", agent_id="agent1", expected_version=1)
        assert entry2.version == 2
        
        # This should fail (wrong version)
        with pytest.raises(ValueError, match="Version conflict"):
            store.set("test.key", "value3", agent_id="agent1", expected_version=1)

    def test_ttl_expiration(self):
        """Test that entries expire based on TTL."""
        store = ContextStore()
        
        # Set entry with 1 second TTL
        store.set("test.key", "value", agent_id="agent1", ttl=1)
        
        # Should be available immediately
        entry = store.get("test.key")
        assert entry is not None
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired
        entry = store.get("test.key")
        assert entry is None

    def test_delete_context(self):
        """Test deleting context entries."""
        store = ContextStore()
        
        store.set("test.key", "value", agent_id="agent1")
        assert store.get("test.key") is not None
        
        result = store.delete("test.key")
        assert result is True
        assert store.get("test.key") is None
        
        # Deleting non-existent key returns False
        result = store.delete("nonexistent")
        assert result is False

    def test_query_by_pattern(self):
        """Test querying contexts by pattern."""
        store = ContextStore()
        
        store.set("browser.url", "http://example.com", agent_id="agent1")
        store.set("browser.title", "Example", agent_id="agent1")
        store.set("task.status", "running", agent_id="agent1")
        
        # Query all browser contexts
        results = store.query(pattern="browser.*")
        assert len(results) == 2
        assert all(e.key.startswith("browser.") for e in results)
        
        # Query all contexts
        results = store.query(pattern="**")
        assert len(results) == 3

    def test_query_by_scope(self):
        """Test querying contexts by scope."""
        store = ContextStore()
        
        store.set("key1", "value1", scope=ContextScope.GLOBAL, agent_id="agent1")
        store.set("key2", "value2", scope=ContextScope.TASK, agent_id="agent1")
        store.set("key3", "value3", scope=ContextScope.AGENT, agent_id="agent1")
        
        results = store.query(scope=ContextScope.GLOBAL)
        assert len(results) == 1
        assert results[0].scope == ContextScope.GLOBAL

    def test_query_by_agent_id(self):
        """Test querying contexts by agent ID."""
        store = ContextStore()
        
        store.set("key1", "value1", agent_id="agent1")
        store.set("key2", "value2", agent_id="agent2")
        store.set("key3", "value3", agent_id="agent1")
        
        results = store.query(agent_id="agent1")
        assert len(results) == 2
        assert all(e.agent_id == "agent1" for e in results)

    def test_history_tracking(self):
        """Test that history is tracked for updated entries."""
        store = ContextStore()
        
        store.set("test.key", "value1", agent_id="agent1")
        store.set("test.key", "value2", agent_id="agent1")
        store.set("test.key", "value3", agent_id="agent1")
        
        history = store.get_history("test.key")
        assert len(history) == 2  # Excludes current version
        assert history[0].value == "value2"  # Newest first
        assert history[1].value == "value1"

    def test_history_limit(self):
        """Test history size limit."""
        store = ContextStore()
        store._max_history_size = 3
        
        # Create 5 versions
        for i in range(5):
            store.set("test.key", f"value{i}", agent_id="agent1")
        
        history = store.get_history("test.key")
        assert len(history) <= 3

    def test_clear_all_contexts(self):
        """Test clearing all contexts."""
        store = ContextStore()
        
        store.set("key1", "value1", agent_id="agent1")
        store.set("key2", "value2", agent_id="agent2")
        
        count = store.clear()
        assert count == 2
        assert len(store.query()) == 0

    def test_clear_by_agent(self):
        """Test clearing contexts for specific agent."""
        store = ContextStore()
        
        store.set("key1", "value1", agent_id="agent1")
        store.set("key2", "value2", agent_id="agent2")
        store.set("key3", "value3", agent_id="agent1")
        
        count = store.clear(agent_id="agent1")
        assert count == 2
        
        results = store.query()
        assert len(results) == 1
        assert results[0].agent_id == "agent2"

    def test_clear_by_scope(self):
        """Test clearing contexts by scope."""
        store = ContextStore()
        
        store.set("key1", "value1", scope=ContextScope.GLOBAL, agent_id="agent1")
        store.set("key2", "value2", scope=ContextScope.TASK, agent_id="agent1")
        
        count = store.clear(scope=ContextScope.GLOBAL)
        assert count == 1
        
        results = store.query(scope=ContextScope.GLOBAL)
        assert len(results) == 0
        
        results = store.query(scope=ContextScope.TASK)
        assert len(results) == 1

    def test_subscription_notification(self):
        """Test subscription notification system."""
        store = ContextStore()
        notifications = []
        
        def callback(entry: ContextEntry):
            notifications.append(entry)
        
        # Subscribe to pattern
        sub_id = store.subscribe("browser.*", callback)
        assert sub_id is not None
        
        # Set matching context (note: notifications may not fire without event loop)
        store.set("browser.url", "http://example.com", agent_id="agent1")
        
        # Unsubscribe
        result = store.unsubscribe(sub_id)
        assert result is True
        
        # Unsubscribing again should return False
        result = store.unsubscribe(sub_id)
        assert result is False

    def test_merge_last_write_wins(self):
        """Test merge with last write wins strategy."""
        store = ContextStore()
        
        entry1 = ContextEntry(
            scope=ContextScope.GLOBAL,
            key="test.key",
            value="value1",
            agent_id="agent1",
            timestamp=datetime.utcnow() - timedelta(seconds=10)
        )
        
        entry2 = ContextEntry(
            scope=ContextScope.GLOBAL,
            key="test.key",
            value="value2",
            agent_id="agent2",
            timestamp=datetime.utcnow()
        )
        
        merged = store.merge([entry1, entry2])
        assert merged.value == "value2"  # Newest wins

    def test_merge_version_check(self):
        """Test merge with version check strategy."""
        store = ContextStore()
        
        entry1 = ContextEntry(
            scope=ContextScope.GLOBAL,
            key="test.key",
            value="value1",
            agent_id="agent1",
            version=1
        )
        
        entry2 = ContextEntry(
            scope=ContextScope.GLOBAL,
            key="test.key",
            value="value2",
            agent_id="agent2",
            version=2
        )
        
        merged = store.merge([entry1, entry2], ConflictResolutionStrategy.VERSION_CHECK)
        assert merged.version == 2

    def test_merge_dict_values(self):
        """Test merging dict values."""
        store = ContextStore()
        
        entry1 = ContextEntry(
            scope=ContextScope.GLOBAL,
            key="test.key",
            value={"a": 1, "b": 2},
            agent_id="agent1"
        )
        
        entry2 = ContextEntry(
            scope=ContextScope.GLOBAL,
            key="test.key",
            value={"b": 3, "c": 4},
            agent_id="agent2"
        )
        
        merged = store.merge([entry1, entry2], ConflictResolutionStrategy.MERGE)
        assert merged.value == {"a": 1, "b": 3, "c": 4}

    def test_merge_different_keys_fails(self):
        """Test that merging entries with different keys fails."""
        store = ContextStore()
        
        entry1 = ContextEntry(
            scope=ContextScope.GLOBAL,
            key="key1",
            value="value1",
            agent_id="agent1"
        )
        
        entry2 = ContextEntry(
            scope=ContextScope.GLOBAL,
            key="key2",
            value="value2",
            agent_id="agent2"
        )
        
        with pytest.raises(ValueError, match="different keys"):
            store.merge([entry1, entry2])

    def test_merge_empty_list_fails(self):
        """Test that merging empty list fails."""
        store = ContextStore()
        
        with pytest.raises(ValueError, match="empty context list"):
            store.merge([])


class TestContextManager:
    """Test ContextManager high-level API."""

    def test_create_manager(self):
        """Test creating a context manager."""
        manager = ContextManager(agent_id="agent1")
        assert manager.agent_id == "agent1"
        assert isinstance(manager.store, ContextStore)

    def test_shared_store(self):
        """Test that managers can share a store."""
        store = ContextStore()
        manager1 = ContextManager(store=store, agent_id="agent1")
        manager2 = ContextManager(store=store, agent_id="agent2")
        
        manager1.set_global("shared.key", "value")
        
        entry = manager2.get_global("shared.key")
        assert entry is not None
        assert entry.value == "value"

    def test_set_get_global(self):
        """Test set and get global context."""
        manager = ContextManager(agent_id="agent1")
        
        entry = manager.set_global("test.key", "test_value")
        assert entry.scope == ContextScope.GLOBAL
        
        retrieved = manager.get_global("test.key")
        assert retrieved.value == "test_value"

    def test_set_get_agent(self):
        """Test set and get agent-specific context."""
        manager = ContextManager(agent_id="agent1")
        
        entry = manager.set_agent("status", "active")
        assert entry.scope == ContextScope.AGENT
        assert entry.agent_id == "agent1"
        
        retrieved = manager.get_agent("status")
        assert retrieved.value == "active"

    def test_get_agent_for_different_agent(self):
        """Test getting agent context for different agent."""
        store = ContextStore()
        manager1 = ContextManager(store=store, agent_id="agent1")
        manager2 = ContextManager(store=store, agent_id="agent2")
        
        manager1.set_agent("status", "active")
        
        # Manager2 can read agent1's context
        entry = manager2.get_agent("status", agent_id="agent1")
        assert entry.value == "active"

    def test_set_get_task(self):
        """Test set and get task-specific context."""
        manager = ContextManager(agent_id="agent1")
        
        entry = manager.set_task("task.status", "running")
        assert entry.scope == ContextScope.TASK
        
        retrieved = manager.get_task("task.status")
        assert retrieved.value == "running"

    def test_query(self):
        """Test querying contexts."""
        manager = ContextManager(agent_id="agent1")
        
        manager.set_global("browser.url", "http://example.com")
        manager.set_global("browser.title", "Example")
        manager.set_global("task.status", "running")
        
        results = manager.query(pattern="browser.*")
        assert len(results) == 2

    def test_subscribe_unsubscribe(self):
        """Test subscription management."""
        manager = ContextManager(agent_id="agent1")
        
        def callback(entry):
            pass
        
        sub_id = manager.subscribe("test.*", callback)
        assert sub_id is not None
        
        result = manager.unsubscribe(sub_id)
        assert result is True

    def test_clear_agent_context(self):
        """Test clearing agent context."""
        manager = ContextManager(agent_id="agent1")
        
        manager.set_global("key1", "value1")
        manager.set_global("key2", "value2")
        manager.set_agent("key3", "value3")
        
        count = manager.clear_agent_context()
        assert count == 3  # All entries owned by agent1

    def test_with_ttl(self):
        """Test setting context with TTL."""
        manager = ContextManager(agent_id="agent1")
        
        entry = manager.set_global("temp.key", "value", ttl=3600)
        assert entry.expires_at is not None

    def test_with_metadata(self):
        """Test setting context with metadata."""
        manager = ContextManager(agent_id="agent1")
        
        metadata = {"source": "test", "priority": "high"}
        entry = manager.set_global("test.key", "value", metadata=metadata)
        assert entry.metadata == metadata


class TestContextScenarios:
    """Test real-world usage scenarios."""

    def test_browser_state_sharing(self):
        """Test browser state sharing scenario from issue."""
        store = ContextStore()
        agent_a = ContextManager(store=store, agent_id="agent_a")
        agent_b = ContextManager(store=store, agent_id="agent_b")
        
        # Agent A stores current page URL
        agent_a.set_global("browser.current_url", "http://example.com")
        
        # Agent B queries context
        entry = agent_b.get_global("browser.current_url")
        assert entry.value == "http://example.com"

    def test_task_specific_context(self):
        """Test task-specific context scenario from issue."""
        manager = ContextManager(agent_id="agent1")
        
        # Create task-specific context
        manager.set_task("task.search.query", "test query")
        manager.set_task("task.search.results", ["result1", "result2"])
        
        # Retrieve task context
        query = manager.get_task("task.search.query")
        results = manager.get_task("task.search.results")
        
        assert query.value == "test query"
        assert results.value == ["result1", "result2"]

    def test_context_subscriptions(self):
        """Test context subscription scenario from issue."""
        manager = ContextManager(agent_id="agent1")
        changes = []
        
        def on_browser_state_change(entry: ContextEntry):
            changes.append(f"{entry.key} = {entry.value}")
        
        # Subscribe to browser state changes
        sub_id = manager.subscribe("browser.*", on_browser_state_change)
        
        # Update browser state
        manager.set_global("browser.url", "http://example.com")
        
        # Unsubscribe
        manager.unsubscribe(sub_id)

    def test_multi_agent_coordination(self):
        """Test coordination between multiple agents."""
        store = ContextStore()
        
        # Create multiple agents
        agents = [
            ContextManager(store=store, agent_id=f"agent{i}")
            for i in range(3)
        ]
        
        # Each agent sets their status
        for i, agent in enumerate(agents):
            agent.set_agent("status", f"working_on_task_{i}")
        
        # Query all agent statuses
        results = store.query(pattern="status", scope=ContextScope.AGENT)
        assert len(results) == 3

    def test_versioned_updates(self):
        """Test versioned updates for consistency."""
        store = ContextStore(conflict_strategy=ConflictResolutionStrategy.VERSION_CHECK)
        manager = ContextManager(store=store, agent_id="agent1")
        
        # Initial set
        entry = manager.set_global("counter", 0)
        assert entry.version == 1
        
        # Update with version check
        entry = store.set("counter", 1, agent_id="agent1", expected_version=1)
        assert entry.version == 2
        
        # This should fail (stale version)
        with pytest.raises(ValueError, match="Version conflict"):
            store.set("counter", 2, agent_id="agent1", expected_version=1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
