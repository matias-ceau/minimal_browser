"""Unit tests for conversation storage."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path and import directly to avoid PySide6 dependency
src_path = Path(__file__).parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from minimal_browser.storage import conversations as conv_module

ConversationLog = conv_module.ConversationLog
ConversationMemory = conv_module.ConversationMemory


class TestConversationMemory:
    """Test ConversationMemory class."""

    def test_create_empty_memory(self):
        """Test creating empty conversation memory."""
        memory = ConversationMemory()
        assert memory.get_history() == []

    def test_add_single_message(self):
        """Test adding a single message."""
        memory = ConversationMemory()
        memory.add_message("user", "Hello")
        history = memory.get_history()
        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"

    def test_add_multiple_messages(self):
        """Test adding multiple messages."""
        memory = ConversationMemory()
        memory.add_message("user", "Hello")
        memory.add_message("assistant", "Hi there")
        memory.add_message("user", "How are you?")
        history = memory.get_history()
        assert len(history) == 3
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"
        assert history[2]["role"] == "user"

    def test_memory_max_size(self):
        """Test memory respects max size limit."""
        memory = ConversationMemory(max_messages=5)
        for i in range(10):
            memory.add_message("user", f"Message {i}")
        history = memory.get_history()
        assert len(history) <= 5

    def test_clear_history(self):
        """Test clearing conversation history."""
        memory = ConversationMemory()
        memory.add_message("user", "Message 1")
        memory.add_message("user", "Message 2")
        memory.clear()
        assert memory.get_history() == []


class TestConversationLog:
    """Test ConversationLog class."""

    def test_create_log_with_custom_path(self):
        """Test creating log with custom path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_log.json"
            log = ConversationLog(str(log_path))
            assert log.log_path == log_path

    def test_save_single_conversation(self):
        """Test saving a single conversation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_log.json"
            log = ConversationLog(str(log_path))
            
            messages = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"},
            ]
            log.save_conversation(messages)
            
            assert log_path.exists()

    def test_load_saved_conversations(self):
        """Test loading saved conversations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_log.json"
            log = ConversationLog(str(log_path))
            
            messages = [
                {"role": "user", "content": "Test message"},
            ]
            log.save_conversation(messages)
            
            # Create new log instance and load
            log2 = ConversationLog(str(log_path))
            loaded = log2.get_recent_conversations(1)
            assert len(loaded) >= 1
            assert loaded[0]["messages"][0]["content"] == "Test message"

    def test_save_multiple_conversations(self):
        """Test saving multiple conversations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_log.json"
            log = ConversationLog(str(log_path))
            
            for i in range(3):
                messages = [{"role": "user", "content": f"Message {i}"}]
                log.save_conversation(messages)
            
            loaded = log.get_recent_conversations(3)
            assert len(loaded) >= 3

    def test_get_recent_conversations_limit(self):
        """Test getting limited number of recent conversations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_log.json"
            log = ConversationLog(str(log_path))
            
            for i in range(5):
                messages = [{"role": "user", "content": f"Message {i}"}]
                log.save_conversation(messages)
            
            recent = log.get_recent_conversations(2)
            assert len(recent) == 2
