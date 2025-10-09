"""Optimized text processing with optional native acceleration.

This module provides text processing operations that can be accelerated
with native modules (Rust/C) when available, with automatic fallback
to pure Python implementations.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple


class TextProcessor:
    """Text processing with optional native acceleration."""

    # Class variable to track if native module is available
    _native_available: Optional[bool] = None
    _native_module = None

    @classmethod
    def _check_native_module(cls) -> bool:
        """Check if native module is available and cache result."""
        if cls._native_available is not None:
            return cls._native_available

        try:
            # Try to import the native module
            # This would be a Rust/C extension module in the future
            # For now, we prepare the structure for future integration
            import minimal_browser_native  # type: ignore

            cls._native_module = minimal_browser_native
            cls._native_available = True
            return True
        except ImportError:
            cls._native_available = False
            return False

    @staticmethod
    def extract_url_from_text(text: str, pattern: str) -> Optional[str]:
        """Extract URL from text using regex pattern.

        This operation can be CPU-intensive with complex patterns.
        Native implementation would use optimized regex engine (e.g., regex crate in Rust).

        Args:
            text: Input text to search
            pattern: Regex pattern to match

        Returns:
            Matched URL or None
        """
        # Future: Use native module if available
        # if TextProcessor._check_native_module():
        #     return TextProcessor._native_module.extract_url(text, pattern)

        # Pure Python fallback
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else None

    @staticmethod
    def find_all_patterns(text: str, patterns: list[str]) -> list[Tuple[str, str]]:
        """Find all matching patterns in text.

        Args:
            text: Input text to search
            patterns: List of regex patterns to match

        Returns:
            List of (pattern, match) tuples
        """
        # Future: Use native module if available
        # if TextProcessor._check_native_module():
        #     return TextProcessor._native_module.find_all_patterns(text, patterns)

        # Pure Python fallback
        results = []
        text_lower = text.lower()
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                results.append((pattern, match.group(0)))
        return results

    @staticmethod
    def fast_string_contains(text: str, keywords: set[str]) -> bool:
        """Check if any keyword exists in text (case-insensitive).

        This is a hot path operation that can benefit from native optimization.

        Args:
            text: Input text to search
            keywords: Set of keywords to check

        Returns:
            True if any keyword is found
        """
        # Future: Use native module if available
        # if TextProcessor._check_native_module():
        #     return TextProcessor._native_module.contains_any(text.lower(), keywords)

        # Pure Python fallback
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in keywords)

    @staticmethod
    def base64_encode_optimized(data: bytes) -> str:
        """Optimized base64 encoding for large HTML content.

        Args:
            data: Bytes to encode

        Returns:
            Base64 encoded string
        """
        # Future: Use native module if available
        # if TextProcessor._check_native_module():
        #     return TextProcessor._native_module.base64_encode(data)

        # Pure Python fallback
        import base64

        return base64.b64encode(data).decode("ascii")

    @staticmethod
    def markdown_to_html(text: str) -> str:
        """Convert simple markdown formatting to HTML.

        Optimizes conversion of bold (**text**) and italic (*text*) markers.

        Args:
            text: Markdown text

        Returns:
            HTML formatted text
        """
        # Future: Use native module if available
        # if TextProcessor._check_native_module():
        #     return TextProcessor._native_module.markdown_to_html(text)

        # Pure Python fallback
        result = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
        result = re.sub(r"\*(.*?)\*", r"<em>\1</em>", result)
        return result
