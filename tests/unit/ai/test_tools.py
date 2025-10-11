"""Unit tests for AI response processing tools."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

# Direct module import to avoid loading __init__.py with PySide6 dependency
def import_module_direct(name: str, filepath: str):
    """Import module directly from file without loading parent __init__.py."""
    spec = importlib.util.spec_from_file_location(name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # Register for relative imports
    spec.loader.exec_module(module)
    return module

src_dir = Path(__file__).parent.parent.parent.parent / "src" / "minimal_browser"

# Import dependencies first
schemas_module = import_module_direct("minimal_browser.ai.schemas", str(src_dir / "ai" / "schemas.py"))
tools_module = import_module_direct("minimal_browser.ai.tools", str(src_dir / "ai" / "tools.py"))

HtmlAction = schemas_module.HtmlAction
NavigateAction = schemas_module.NavigateAction
SearchAction = schemas_module.SearchAction
ResponseProcessor = tools_module.ResponseProcessor


class TestResponseProcessorExplicitPrefixes:
    """Test ResponseProcessor with explicit prefixes."""

    def test_parse_navigate_prefix(self):
        """Test parsing NAVIGATE: prefix."""
        response = "NAVIGATE: https://github.com"
        action = ResponseProcessor.parse_response(response)
        assert isinstance(action, NavigateAction)
        assert str(action.url) == "https://github.com/"

    def test_parse_search_prefix(self):
        """Test parsing SEARCH: prefix."""
        response = "SEARCH: Python documentation"
        action = ResponseProcessor.parse_response(response)
        assert isinstance(action, SearchAction)
        assert action.query == "Python documentation"

    def test_parse_html_prefix(self):
        """Test parsing HTML: prefix."""
        response = "HTML: <h1>Generated Content</h1>"
        action = ResponseProcessor.parse_response(response)
        assert isinstance(action, HtmlAction)
        assert "<h1>Generated Content</h1>" in action.html

    def test_parse_navigate_case_insensitive(self):
        """Test NAVIGATE prefix is case-insensitive."""
        response = "navigate: https://example.com"
        action = ResponseProcessor.parse_response(response)
        assert isinstance(action, NavigateAction)


class TestResponseProcessorIntelligentParsing:
    """Test ResponseProcessor intelligent parsing without prefixes."""

    def test_parse_plain_url(self):
        """Test parsing plain URL without prefix."""
        response = "https://example.com"
        action = ResponseProcessor.parse_response(response)
        assert isinstance(action, NavigateAction)
        assert str(action.url) == "https://example.com/"

    def test_parse_url_in_sentence(self):
        """Test extracting URL from natural language."""
        response = "Navigate to https://github.com for more info"
        action = ResponseProcessor.parse_response(response)
        assert isinstance(action, NavigateAction)
        assert "github.com" in str(action.url)

    def test_parse_search_keywords(self):
        """Test detecting search intent from keywords."""
        response = "search for Python tutorials"
        action = ResponseProcessor.parse_response(response)
        assert isinstance(action, SearchAction)
        assert "python" in action.query.lower()

    def test_parse_html_generation_intent(self):
        """Test detecting HTML generation intent."""
        response = "create a todo list with items"
        action = ResponseProcessor.parse_response(response)
        assert isinstance(action, HtmlAction)


class TestResponseProcessorContextHandling:
    """Test ResponseProcessor with context markers."""

    def test_parse_with_query_context(self):
        """Test parsing response with @@QUERY@@ marker."""
        response = "NAVIGATE: https://example.com@@QUERY@@original user query"
        action = ResponseProcessor.parse_response(response)
        assert isinstance(action, NavigateAction)

    def test_extract_query_from_context(self):
        """Test extracting original query from context."""
        response = "Response text@@QUERY@@user query here"
        text, query = ResponseProcessor._extract_query_from_context(response)
        assert text == "Response text"
        assert query == "user query here"


class TestResponseProcessorEdgeCases:
    """Test ResponseProcessor edge cases and error handling."""

    def test_parse_empty_response(self):
        """Test handling empty response."""
        # Should default to HTML with empty content or raise error
        response = ""
        with pytest.raises(ValidationError):
            ResponseProcessor.parse_response(response)

    def test_parse_whitespace_only(self):
        """Test handling whitespace-only response."""
        response = "   \n   "
        with pytest.raises(ValidationError):
            ResponseProcessor.parse_response(response)

    def test_parse_invalid_url_in_navigate(self):
        """Test handling invalid URL in NAVIGATE command."""
        response = "NAVIGATE: not-a-valid-url"
        with pytest.raises(ValidationError):
            ResponseProcessor.parse_response(response)

    def test_parse_multiline_html(self):
        """Test parsing multiline HTML content."""
        response = """HTML: <!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body><h1>Test</h1></body>
        </html>"""
        action = ResponseProcessor.parse_response(response)
        assert isinstance(action, HtmlAction)
        assert "<!DOCTYPE html>" in action.html


class TestResponseProcessorBackwardCompatibility:
    """Test backward-compatible tuple parsing."""

    def test_parse_response_to_tuple_navigate(self):
        """Test tuple format for NavigateAction."""
        response = "NAVIGATE: https://example.com"
        action_type, payload = ResponseProcessor.parse_response_to_tuple(response)
        assert action_type == "navigate"
        assert "example.com" in payload

    def test_parse_response_to_tuple_search(self):
        """Test tuple format for SearchAction."""
        response = "SEARCH: Python docs"
        action_type, payload = ResponseProcessor.parse_response_to_tuple(response)
        assert action_type == "search"
        assert payload == "Python docs"

    def test_parse_response_to_tuple_html(self):
        """Test tuple format for HtmlAction."""
        response = "HTML: <h1>Test</h1>"
        action_type, payload = ResponseProcessor.parse_response_to_tuple(response)
        assert action_type == "html"
        assert "<h1>Test</h1>" in payload


class TestResponseProcessorActionToTuple:
    """Test action to tuple conversion."""

    def test_navigate_action_to_tuple(self):
        """Test converting NavigateAction to tuple."""
        action = NavigateAction(url="https://example.com")
        action_type, payload = ResponseProcessor.action_to_tuple(action)
        assert action_type == "navigate"
        assert "example.com" in payload

    def test_search_action_to_tuple(self):
        """Test converting SearchAction to tuple."""
        action = SearchAction(query="test query")
        action_type, payload = ResponseProcessor.action_to_tuple(action)
        assert action_type == "search"
        assert payload == "test query"

    def test_html_action_to_tuple(self):
        """Test converting HtmlAction to tuple."""
        action = HtmlAction(html="<p>Test</p>")
        action_type, payload = ResponseProcessor.action_to_tuple(action)
        assert action_type == "html"
        assert payload == "<p>Test</p>"
