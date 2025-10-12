"""Unit tests for HTML rendering utilities."""

from __future__ import annotations

import base64
import sys
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

# Import html module directly
html_module = import_module_direct("minimal_browser.rendering.html", str(src_dir / "rendering" / "html.py"))

create_data_url = html_module.create_data_url
ensure_html = html_module.ensure_html
wrap_content_as_html = html_module.wrap_content_as_html


class TestCreateDataUrl:
    """Test create_data_url function."""

    def test_create_data_url_simple_html(self):
        """Test creating data URL from simple HTML."""
        html = "<h1>Hello World</h1>"
        result = create_data_url(html)
        assert result.startswith("data:text/html;charset=utf-8;base64,")

    def test_create_data_url_decoding(self):
        """Test data URL can be decoded back to original HTML."""
        html = "<h1>Test Content</h1>"
        result = create_data_url(html)
        # Extract base64 part
        base64_part = result.split(",", 1)[1]
        decoded = base64.b64decode(base64_part).decode("utf-8")
        assert decoded == html

    def test_create_data_url_complex_html(self):
        """Test creating data URL from complex HTML."""
        html = """<!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body><h1>Test</h1></body>
        </html>"""
        result = create_data_url(html)
        assert result.startswith("data:text/html")
        # Verify content is preserved
        base64_part = result.split(",", 1)[1]
        decoded = base64.b64decode(base64_part).decode("utf-8")
        assert "<!DOCTYPE html>" in decoded

    def test_create_data_url_unicode(self):
        """Test creating data URL with Unicode characters."""
        html = "<h1>Hello 世界 🌍</h1>"
        result = create_data_url(html)
        base64_part = result.split(",", 1)[1]
        decoded = base64.b64decode(base64_part).decode("utf-8")
        assert decoded == html
        assert "世界" in decoded
        assert "🌍" in decoded

    def test_create_data_url_empty_string(self):
        """Test creating data URL from empty string."""
        result = create_data_url("")
        assert result.startswith("data:text/html")


class TestEnsureHtml:
    """Test ensure_html function."""

    def test_ensure_html_with_doctype(self):
        """Test ensure_html with complete HTML document."""
        html = "<!DOCTYPE html><html><body>test</body></html>"
        result = ensure_html(html, "test query")
        assert result == html

    def test_ensure_html_with_html_tag(self):
        """Test ensure_html with HTML tag but no doctype."""
        html = "<html><body>test</body></html>"
        result = ensure_html(html, "test query")
        # Should wrap or return as-is depending on implementation
        assert "<html>" in result or "<!DOCTYPE html>" in result

    def test_ensure_html_plain_text(self):
        """Test ensure_html wraps plain text."""
        text = "Plain text content"
        result = ensure_html(text, "test query")
        # Should be wrapped in HTML
        assert "<html>" in result or "<!DOCTYPE html>" in result
        assert "Plain text content" in result

    def test_ensure_html_with_tags(self):
        """Test ensure_html with HTML tags but no html/body."""
        html = "<h1>Title</h1><p>Content</p>"
        result = ensure_html(html, "test query")
        assert "<h1>Title</h1>" in result
        assert "<p>Content</p>" in result


class TestWrapContentAsHtml:
    """Test wrap_content_as_html function."""

    def test_wrap_content_basic(self):
        """Test wrapping basic content."""
        content = "Test content"
        query = "test query"
        result = wrap_content_as_html(content, query)
        assert "Test content" in result
        assert "<html>" in result or "<!DOCTYPE html>" in result

    def test_wrap_content_preserves_html(self):
        """Test wrapping preserves existing HTML."""
        content = "<h1>Title</h1><p>Paragraph</p>"
        query = "test"
        result = wrap_content_as_html(content, query)
        assert "<h1>Title</h1>" in result
        assert "<p>Paragraph</p>" in result

    def test_wrap_content_with_unicode(self):
        """Test wrapping content with Unicode."""
        content = "Content with émojis 🎉"
        query = "test"
        result = wrap_content_as_html(content, query)
        assert "émojis" in result
        assert "🎉" in result

    def test_wrap_content_empty_query(self):
        """Test wrapping with empty query."""
        content = "Test content"
        query = ""
        result = wrap_content_as_html(content, query)
        assert "Test content" in result
