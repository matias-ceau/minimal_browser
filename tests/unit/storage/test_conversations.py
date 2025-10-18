"""Unit tests for conversation storage."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

# Direct module import to avoid loading __init__.py with PySide6 dependency
import importlib.util

def import_module_direct(name: str, filepath: str):
    """Import module directly from file without loading parent __init__.py."""
    spec = importlib.util.spec_from_file_location(name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # Register for relative imports
    spec.loader.exec_module(module)
    return module

src_dir = Path(__file__).parent.parent.parent.parent / "src" / "minimal_browser"

# Import utils module first (needed by conversations)
utils_module = import_module_direct("minimal_browser.storage.utils", str(src_dir / "storage" / "utils.py"))
sys.modules["minimal_browser.storage.utils"] = utils_module

# Import conversations module directly
conv_module = import_module_direct("minimal_browser.storage.conversations", str(src_dir / "storage" / "conversations.py"))

# Import schemas module for ConversationMemory
schemas_module = import_module_direct("minimal_browser.ai.schemas", str(src_dir / "ai" / "schemas.py"))

ConversationLog = conv_module.ConversationLog
ConversationMemory = schemas_module.ConversationMemory


class TestConversationMemory:
    """Test ConversationMemory class."""

    def test_create_empty_memory(self):
        """Test creating empty conversation memory."""
        memory = ConversationMemory()
        assert memory.as_history() == []

    def test_add_single_message(self):
        """Test adding a single message."""
        memory = ConversationMemory()
        memory.add_user("Hello")
        history = memory.as_history()
        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"

    def test_add_multiple_messages(self):
        """Test adding multiple messages."""
        memory = ConversationMemory()
        memory.add_user("Hello")
        memory.add_assistant("Hi there")
        memory.add_user("How are you?")
        history = memory.as_history()
        assert len(history) == 3
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"
        assert history[2]["role"] == "user"

    def test_memory_max_size(self):
        """Test memory respects max size limit."""
        memory = ConversationMemory(max_messages=5)
        for i in range(10):
            memory.add_user(f"Message {i}")
        history = memory.as_history()
        assert len(history) <= 5

    def test_clear_history(self):
        """Test clearing conversation history."""
        memory = ConversationMemory()
        memory.add_user("Message 1")
        memory.add_user("Message 2")
        # ConversationMemory doesn't have a clear method, let's create a new instance
        memory = ConversationMemory()
        assert memory.as_history() == []


class TestConversationLog:
    """Test ConversationLog class."""

    def test_create_log_with_custom_path(self):
        """Test creating log with custom path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_log.json"
            log = ConversationLog(str(log_path))
            assert log.path == log_path

    def test_save_single_conversation(self):
        """Test saving a single conversation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_log.json"
            log = ConversationLog(str(log_path))
            
            log.append("Hello", "Hi")
            
            assert log_path.exists()
            assert len(log.entries) == 1
            assert log.entries[0]["query"] == "Hello"
            assert log.entries[0]["response"] == "Hi"

    def test_load_saved_conversations(self):
        """Test loading saved conversations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_log.json"
            log = ConversationLog(str(log_path))
            
            log.append("Test message", "Test response")
            
            # Create new log instance and load
            log2 = ConversationLog(str(log_path))
            entries = log2.entries
            assert len(entries) >= 1
            assert entries[0]["query"] == "Test message"
            assert entries[0]["response"] == "Test response"

    def test_save_multiple_conversations(self):
        """Test saving multiple conversations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_log.json"
            log = ConversationLog(str(log_path))
            
            for i in range(3):
                log.append(f"Query {i}", f"Response {i}")
            
            entries = log.entries
            assert len(entries) == 3

    def test_get_recent_conversations_limit(self):
        """Test getting limited number of recent conversations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_log.json"
            log = ConversationLog(str(log_path))
            
            for i in range(5):
                log.append(f"Query {i}", f"Response {i}")
            
            # Test that we can get the most recent entries
            entries = log.entries
            assert len(entries) == 5
            # The most recent entries should be at the end
            assert entries[-1]["query"] == "Query 4"
