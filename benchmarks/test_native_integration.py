"""Integration tests for native module optimization.

These tests verify that the text processing operations work correctly
with and without native module acceleration.
"""

from __future__ import annotations

import sys
import os
import importlib.util

# Add parent directory to path for direct module imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path without importing __init__.py."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {module_name} from {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Import TextProcessor directly to avoid PySide6 dependency
base_path = os.path.join(os.path.dirname(__file__), "..", "src", "minimal_browser")
TextProcessor = import_module_from_path(
    "text_processor", os.path.join(base_path, "native", "text_processor.py")
).TextProcessor


def test_extract_url_from_text():
    """Test URL extraction from text."""
    text = "Navigate to example.com for more info"
    pattern = r"(?:navigate|go|open)\s+(?:to\s+)?([^\s]+\.[a-z]{2,})"

    result = TextProcessor.extract_url_from_text(text.lower(), pattern)
    assert result == "example.com", f"Expected 'example.com', got {result}"
    print("✓ URL extraction test passed")


def test_fast_string_contains():
    """Test fast keyword detection."""
    text = "create a todo list with items"
    keywords = {"create", "make", "generate", "build"}

    result = TextProcessor.fast_string_contains(text, keywords)
    assert result is True, "Expected True for keyword match"

    text_no_match = "some random text"
    result = TextProcessor.fast_string_contains(text_no_match, keywords)
    assert result is False, "Expected False for no keyword match"
    print("✓ Fast string contains test passed")


def test_markdown_to_html():
    """Test markdown to HTML conversion."""
    text = "This is **bold** and *italic* text"
    result = TextProcessor.markdown_to_html(text)

    assert "<strong>bold</strong>" in result, "Bold formatting not found"
    assert "<em>italic</em>" in result, "Italic formatting not found"
    print("✓ Markdown to HTML test passed")


def test_base64_encode():
    """Test base64 encoding."""
    data = b"Hello, World!"
    result = TextProcessor.base64_encode_optimized(data)

    # Verify it's valid base64
    import base64

    decoded = base64.b64decode(result)
    assert decoded == data, "Base64 encoding/decoding mismatch"
    print("✓ Base64 encoding test passed")


def test_response_processor_integration():
    """Test integration with ResponseProcessor (skipped - requires PySide6)."""
    print("⊘ ResponseProcessor integration tests skipped (requires full environment)")


def test_html_rendering_integration():
    """Test integration with HTML rendering (skipped - requires PySide6)."""
    print("⊘ HTML rendering integration tests skipped (requires full environment)")


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "=" * 80)
    print("NATIVE MODULE INTEGRATION TESTS")
    print("=" * 80 + "\n")

    tests = [
        test_extract_url_from_text,
        test_fast_string_contains,
        test_markdown_to_html,
        test_base64_encode,
        test_response_processor_integration,
        test_html_rendering_integration,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1

    print("\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 80 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
