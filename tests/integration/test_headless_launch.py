#!/usr/bin/env python3
"""Headless integration test that proves the app can launch.

This test runs in CI environments without display and verifies
the core functionality works.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Force headless mode for CI
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["QT_API"] = "pyside6"

from PySide6.QtWidgets import QApplication
from minimal_browser.minimal_browser import VimBrowser
from minimal_browser.storage.conversations import ConversationLog


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setApplicationName("Minimal Browser Headless Test")
    yield app


@pytest.mark.integration
def test_app_can_instantiate(qapp):
    """Test that the app can be instantiated without errors.
    
    Note: headless=False is used because we need the Qt widget tree for testing.
    The offscreen QT_QPA_PLATFORM handles rendering without a display.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_conversations.json"
        conv_log = ConversationLog(path=str(log_path))
        
        # Create browser instance (offscreen via QT_QPA_PLATFORM env var)
        browser = VimBrowser(conversation_log=conv_log, headless=False)
        
        # Verify it was created
        assert browser is not None
        assert hasattr(browser, 'mode')
        assert hasattr(browser, 'engine')
        
        # Clean up
        browser.close()


@pytest.mark.integration  
def test_app_initial_state(qapp):
    """Test the app's initial state is correct."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_conversations.json"
        conv_log = ConversationLog(path=str(log_path))
        
        browser = VimBrowser(conversation_log=conv_log, headless=False)
        
        # Check initial state
        assert browser.mode == "NORMAL"
        assert browser.command_buffer == ""
        assert isinstance(browser.buffers, list)
        assert browser.current_buffer == 0
        
        # Clean up
        browser.close()


@pytest.mark.integration
def test_app_can_navigate(qapp):
    """Test that the app can navigate to URLs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_conversations.json"
        conv_log = ConversationLog(path=str(log_path))
        
        browser = VimBrowser(conversation_log=conv_log, headless=False)
        
        # Navigate to a URL
        test_url = "https://example.com"
        browser.open_url(test_url)
        
        # Process events
        QApplication.processEvents()
        
        # Verify browser still works
        assert browser is not None
        
        # Clean up
        browser.close()


@pytest.mark.integration
def test_app_modes_work(qapp):
    """Test that modal interface works."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_conversations.json"
        conv_log = ConversationLog(path=str(log_path))
        
        browser = VimBrowser(conversation_log=conv_log, headless=False)
        
        # Test mode switching
        original_mode = browser.mode
        assert original_mode == "NORMAL"
        
        # Switch modes
        browser.mode = "COMMAND"
        assert browser.mode == "COMMAND"
        
        browser.mode = "INSERT"
        assert browser.mode == "INSERT"
        
        browser.mode = "NORMAL"
        assert browser.mode == "NORMAL"
        
        # Clean up
        browser.close()


@pytest.mark.integration
def test_help_screen_accessible(qapp):
    """Test that help screen can be shown."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_conversations.json"
        conv_log = ConversationLog(path=str(log_path))
        
        browser = VimBrowser(conversation_log=conv_log, headless=False)
        
        # Show help
        browser.show_help()
        
        # Process events
        QApplication.processEvents()
        
        # Verify browser still functional
        assert browser is not None
        
        # Clean up
        browser.close()


if __name__ == "__main__":
    print("="*60)
    print("Running headless integration tests...")
    print("="*60)
    pytest.main([__file__, "-v", "-s"])
