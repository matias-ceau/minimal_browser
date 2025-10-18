"""Pytest configuration and shared fixtures for minimal browser tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Add src directory to Python path for imports
SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))


@pytest.fixture
def sample_html():
    """Provide sample HTML content for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Test Page</title></head>
    <body>
        <h1>Test Heading</h1>
        <p>Test content with <strong>bold</strong> and <em>italic</em> text.</p>
    </body>
    </html>
    """


@pytest.fixture
def sample_url():
    """Provide a sample URL for testing."""
    return "https://example.com"


@pytest.fixture
def sample_ai_responses():
    """Provide sample AI response text for testing."""
    return {
        "navigate": "NAVIGATE: https://github.com",
        "search": "SEARCH: Python tutorials",
        "html": "HTML: <h1>Generated Content</h1>",
        "plain_url": "https://example.com",
        "plain_search": "search for documentation",
        "todo_html": "create a todo list with items",
    }


@pytest.fixture
def mock_openrouter_api_key(monkeypatch):
    """Set a mock OpenRouter API key for tests."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key-12345")
    return "test-api-key-12345"
