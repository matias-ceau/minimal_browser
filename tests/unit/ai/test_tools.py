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

# Import dependencies first - schemas module (no dependencies)
schemas_module = import_module_direct("minimal_browser.ai.schemas", str(src_dir / "ai" / "schemas.py"))

# Import html module directly (needed by tools)
html_module = import_module_direct("minimal_browser.rendering.html", str(src_dir / "rendering" / "html.py"))

# Import webapps module (needed by tools)
webapps_module = import_module_direct("minimal_browser.rendering.webapps", str(src_dir / "rendering" / "webapps.py"))

# Register the modules in sys.modules so relative imports work
sys.modules["minimal_browser.rendering.html"] = html_module
sys.modules["minimal_browser.rendering.webapps"] = webapps_module

# Import tools module - now the relative imports should work
tools_module = import_module_direct("minimal_browser.ai.tools", str(src_dir / "ai" / "tools.py"))

HtmlAction = schemas_module.HtmlAction
NavigateAction = schemas_module.NavigateAction
SearchAction = schemas_module.SearchAction
WebappAction = schemas_module.WebappAction
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
        """Test lowercase navigate prefix falls back to search."""
        response = "navigate: https://example.com"
        action = ResponseProcessor.parse_response(response)
        # Lowercase "navigate:" is not recognized as explicit prefix, 
        # so it falls back to intelligent parsing which treats it as search
        assert isinstance(action, SearchAction)
        assert "navigate: https://example.com" in action.query


class TestResponseProcessorIntelligentParsing:
    """Test ResponseProcessor intelligent parsing without prefixes."""

    def test_parse_plain_url(self):
        """Test parsing plain URL without prefix falls back to search."""
        response = "https://example.com"
        action = ResponseProcessor.parse_response(response)
        # Plain URLs without explicit prefix are treated as short search queries
        # since they have <= 5 words
        assert isinstance(action, SearchAction)
        assert action.query == "https://example.com"

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
        """Test detecting webapp generation intent."""
        response = "create a todo list with items"
        action = ResponseProcessor.parse_response(response)
        # Now correctly identifies as webapp action due to "todo" keyword
        assert isinstance(action, WebappAction)
        assert action.widget_type == "todo"


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
        # Empty response falls back to HTML action with wrapped content
        response = ""
        action = ResponseProcessor.parse_response(response)
        assert isinstance(action, HtmlAction)
        # The HTML should contain some wrapped content
        assert action.html is not None

    def test_parse_whitespace_only(self):
        """Test handling whitespace-only response."""
        response = "   \n   "
        action = ResponseProcessor.parse_response(response)
        # Whitespace-only response gets stripped and falls back to HTML
        assert isinstance(action, HtmlAction)
        assert action.html is not None

    def test_parse_invalid_url_in_navigate(self):
        """Test handling invalid URL in NAVIGATE command."""
        response = "NAVIGATE: ://invalid-url-format"
        action = ResponseProcessor.parse_response(response)
        # Invalid URL in NAVIGATE falls back to SearchAction
        assert isinstance(action, SearchAction)
        assert action.query == "://invalid-url-format"

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

    def test_parse_response_to_tuple_webapp(self):
        """Test tuple format for WebappAction."""
        response = "WEBAPP: calculator"
        action_type, payload = ResponseProcessor.parse_response_to_tuple(response)
        assert action_type == "html"  # Converted to HTML
        assert "calculator" in payload.lower()



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

    def test_webapp_action_to_tuple(self):
        """Test converting WebappAction to tuple (converted to HTML)."""
        action = WebappAction(widget_type="calculator")
        action_type, payload = ResponseProcessor.action_to_tuple(action)
        assert action_type == "html"
        assert "calculator" in payload.lower()
        assert "<!DOCTYPE html>" in payload


class TestResponseProcessorWebappParsing:
    """Test ResponseProcessor webapp-specific parsing."""

    def test_parse_webapp_prefix(self):
        """Test explicit WEBAPP: prefix."""
        response = "WEBAPP: calculator"
        action = ResponseProcessor.parse_response(response)
        assert isinstance(action, WebappAction)
        assert action.widget_type == "calculator"

    def test_parse_webapp_tag_format(self):
        """Test parsing webapp XML-style tag."""
        response = 'WEBAPP: <webapp type="todo" theme="dark" />'
        action = ResponseProcessor.parse_response(response)
        assert isinstance(action, WebappAction)
        assert action.widget_type == "todo"
        assert action.theme == "dark"

    def test_parse_webapp_with_title(self):
        """Test parsing webapp with custom title."""
        response = 'WEBAPP: <webapp type="timer" title="My Timer" />'
        action = ResponseProcessor.parse_response(response)
        assert isinstance(action, WebappAction)
        assert action.widget_type == "timer"
        assert action.title == "My Timer"

    def test_parse_calculator_keyword(self):
        """Test intelligent parsing recognizes calculator."""
        response = "show me a calculator"
        action = ResponseProcessor.parse_response(response)
        assert isinstance(action, WebappAction)
        assert action.widget_type == "calculator"

    def test_parse_todo_keyword(self):
        """Test intelligent parsing recognizes todo."""
        response = "I need a todo list"
        action = ResponseProcessor.parse_response(response)
        assert isinstance(action, WebappAction)
        assert action.widget_type == "todo"

    def test_parse_timer_keyword(self):
        """Test intelligent parsing recognizes timer."""
        response = "create a timer for me"
        action = ResponseProcessor.parse_response(response)
        assert isinstance(action, WebappAction)
        assert action.widget_type == "timer"

    def test_parse_stopwatch_mapped_to_timer(self):
        """Test stopwatch is mapped to timer widget."""
        response = "I need a stopwatch"
        action = ResponseProcessor.parse_response(response)
        assert isinstance(action, WebappAction)
        assert action.widget_type == "timer"

    def test_parse_notes_keyword(self):
        """Test intelligent parsing recognizes notes."""
        response = "give me a notes app"
        action = ResponseProcessor.parse_response(response)
        assert isinstance(action, WebappAction)
        assert action.widget_type == "notes"
