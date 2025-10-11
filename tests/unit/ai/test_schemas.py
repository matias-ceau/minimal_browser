"""Unit tests for AI schemas (Pydantic models).

Note: These tests require pydantic but not PySide6. They test the schema
definitions and validation logic in isolation.
"""

from __future__ import annotations

import pytest

# Skip all tests if pydantic is not available
pytest.importorskip("pydantic")

# Try to import - if PySide6 is required, these tests will be skipped
try:
    from pydantic import HttpUrl, ValidationError
    from minimal_browser.ai.schemas import (
        AIAction,
        HtmlAction,
        NavigateAction,
        SearchAction,
    )
    SCHEMAS_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    SCHEMAS_AVAILABLE = False
    skip_reason = f"Cannot import schemas: {e}"

pytestmark = pytest.mark.skipif(
    not SCHEMAS_AVAILABLE,
    reason="Schemas not available - may require PySide6 or other dependencies"
)


class TestNavigateAction:
    """Test NavigateAction model."""

    def test_valid_navigate_action(self):
        """Test creating a valid NavigateAction."""
        action = NavigateAction(url="https://example.com")
        assert action.type == "navigate"
        assert str(action.url) == "https://example.com/"

    def test_navigate_action_with_http(self):
        """Test NavigateAction with HTTP URL."""
        action = NavigateAction(url="http://example.com")
        assert action.type == "navigate"
        assert str(action.url).startswith("http://")

    def test_navigate_action_invalid_url(self):
        """Test NavigateAction rejects invalid URLs."""
        with pytest.raises(ValidationError):
            NavigateAction(url="not-a-valid-url")

    def test_navigate_action_missing_scheme(self):
        """Test NavigateAction rejects URLs without scheme."""
        with pytest.raises(ValidationError):
            NavigateAction(url="example.com")


class TestSearchAction:
    """Test SearchAction model."""

    def test_valid_search_action(self):
        """Test creating a valid SearchAction."""
        action = SearchAction(query="Python tutorials")
        assert action.type == "search"
        assert action.query == "Python tutorials"

    def test_search_action_strips_whitespace(self):
        """Test SearchAction strips leading/trailing whitespace."""
        action = SearchAction(query="  Python tutorials  ")
        assert action.query == "Python tutorials"

    def test_search_action_empty_string(self):
        """Test SearchAction rejects empty strings."""
        with pytest.raises(ValidationError):
            SearchAction(query="")

    def test_search_action_only_whitespace(self):
        """Test SearchAction rejects whitespace-only strings."""
        with pytest.raises(ValidationError):
            SearchAction(query="   ")


class TestHtmlAction:
    """Test HtmlAction model."""

    def test_valid_html_action(self):
        """Test creating a valid HtmlAction."""
        html = "<h1>Hello World</h1>"
        action = HtmlAction(html=html)
        assert action.type == "html"
        assert action.html == html

    def test_html_action_strips_whitespace(self):
        """Test HtmlAction strips leading/trailing whitespace."""
        action = HtmlAction(html="  <h1>Hello</h1>  ")
        assert action.html == "<h1>Hello</h1>"

    def test_html_action_complex_html(self):
        """Test HtmlAction with complex HTML."""
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body><h1>Test</h1></body>
        </html>
        """
        action = HtmlAction(html=html)
        assert "<html>" in action.html
        assert "<h1>Test</h1>" in action.html

    def test_html_action_empty_string(self):
        """Test HtmlAction rejects empty strings."""
        with pytest.raises(ValidationError):
            HtmlAction(html="")


class TestAIActionUnion:
    """Test AIAction Union type behavior."""

    def test_discriminated_union_navigate(self):
        """Test AIAction can be a NavigateAction."""
        action: AIAction = NavigateAction(url="https://example.com")
        assert isinstance(action, NavigateAction)
        assert action.type == "navigate"

    def test_discriminated_union_search(self):
        """Test AIAction can be a SearchAction."""
        action: AIAction = SearchAction(query="test query")
        assert isinstance(action, SearchAction)
        assert action.type == "search"

    def test_discriminated_union_html(self):
        """Test AIAction can be an HtmlAction."""
        action: AIAction = HtmlAction(html="<p>Test</p>")
        assert isinstance(action, HtmlAction)
        assert action.type == "html"
