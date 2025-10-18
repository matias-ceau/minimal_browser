"""AI tools and response processing.

This module provides utilities for parsing AI responses and converting them
into type-safe Pydantic models. All parsing operations enforce strict type
validation to ensure data integrity throughout the AI interaction pipeline.
"""

from __future__ import annotations

import re
from typing import Tuple, cast

from pydantic import HttpUrl, ValidationError

from ..rendering.html import ensure_html, wrap_content_as_html
from .schemas import AIAction, HtmlAction, NavigateAction, SearchAction

# Optional: Import optimized text processor for performance
try:
    from ..native import TextProcessor

    _USE_NATIVE_OPTIMIZATION = True
except ImportError:
    _USE_NATIVE_OPTIMIZATION = False


class ResponseProcessor:
    """Processes AI responses and determines actions.
    
    This class provides static methods for parsing AI responses into type-safe
    Pydantic models. It supports both explicit prefixes (NAVIGATE:, SEARCH:, HTML:)
    and intelligent parsing based on content patterns.
    
    All parsing operations enforce strict type validation using Pydantic models
    to ensure data integrity throughout the AI interaction pipeline.
    """

    @staticmethod
    def parse_response(response: str) -> AIAction:
        """Parse AI response text and return a validated action model.
        
        This is the primary entry point for converting raw AI text responses
        into type-safe AIAction instances. The method handles various response
        formats and falls back to intelligent parsing when explicit prefixes
        are not provided.
        
        Args:
            response: Raw AI response text (may include context markers)
            
        Returns:
            A validated AIAction instance (NavigateAction, SearchAction, or HtmlAction)
            
        Raises:
            ValidationError: If the response cannot be parsed into a valid action
        """

        response_text, query = ResponseProcessor._extract_query_from_context(response)
        action_type, payload = ResponseProcessor._infer_action_components(
            response_text, query
        )
        return ResponseProcessor._build_action(action_type, payload, query)

    @staticmethod
    def parse_response_to_tuple(response: str) -> Tuple[str, str]:
        """Backward-compatible parser returning the legacy (type, payload) tuple."""

        action = ResponseProcessor.parse_response(response)
        return ResponseProcessor.action_to_tuple(action)

    @staticmethod
    def _extract_query_from_context(response_with_context: str) -> Tuple[str, str]:
        """Extract the original query from a context-prefixed response if present."""

        if "@@QUERY@@" in response_with_context:
            parts = response_with_context.split("@@QUERY@@", 1)
            return parts[0].strip(), parts[1].strip()
        return response_with_context.strip(), ""

    @staticmethod
    def _infer_action_components(response: str, query: str) -> Tuple[str, str]:
        """Determine action type and payload from raw response text."""

        if response.startswith("NAVIGATE:"):
            return "navigate", response[9:].strip()
        if response.startswith("SEARCH:"):
            return "search", response[7:].strip()
        if response.startswith("HTML:"):
            return "html", response[5:].strip()

        return ResponseProcessor._intelligent_parse(response, query)

    @staticmethod
    def _intelligent_parse(response: str, query: str) -> Tuple[str, str]:
        """Intelligently parse a response without explicit prefixes."""

        response_lower = response.lower()

        nav_patterns = [
            r"(?:navigate|go|open|visit)\s+(?:to\s+)?([^\s]+\.[a-z]{2,})",
            r"(?:open|visit)\s+([a-z]+\.com|[a-z]+\.org|[a-z]+\.net)",
        ]

        # Try optimized pattern extraction if available
        if _USE_NATIVE_OPTIMIZATION:
            for pattern in nav_patterns:
                url = TextProcessor.extract_url_from_text(response_lower, pattern)
                if url:
                    if not url.startswith(("http://", "https://")):
                        url = f"https://{url}"
                    return "navigate", url
        else:
            # Fallback to standard regex
            for pattern in nav_patterns:
                match = re.search(pattern, response_lower)
                if match:
                    url = match.group(1)
                    if not url.startswith(("http://", "https://")):
                        url = f"https://{url}"
                    return "navigate", url

        if any(word in response_lower for word in ["search for", "find", "look up"]):
            search_match = re.search(
                r'(?:search for|find|look up)\s+"?([^"]+)"?', response_lower
            )
            if search_match:
                return "search", search_match.group(1)

        html_indicators = {
            "create",
            "make",
            "generate",
            "build",
            "design",
            "todo",
            "calculator",
            "form",
            "page",
            "website",
        }

        # Use optimized keyword check if available
        if _USE_NATIVE_OPTIMIZATION:
            has_html_indicator = TextProcessor.fast_string_contains(
                response_lower, html_indicators
            )
        else:
            has_html_indicator = any(
                indicator in response_lower for indicator in html_indicators
            )

        if has_html_indicator:
            return "html", response

        if len(response.split()) <= 5:
            candidate = query or response
            return "search", candidate

        return "html", response

    @staticmethod
    def _build_action(action_type: str, payload: str, query: str) -> AIAction:
        """Convert action tuple into a validated `AIAction` instance.
        
        This method attempts to create the appropriate Pydantic model based on
        the action type, with fallback logic to ensure a valid action is always
        returned. All created actions are validated by Pydantic.
        
        Args:
            action_type: The type of action ("navigate", "search", or "html")
            payload: The action payload data
            query: The original user query (for fallback context)
            
        Returns:
            A validated AIAction instance
            
        Raises:
            ValidationError: Only if all fallback attempts fail (rare)
        """

        if action_type == "navigate":
            normalized = ResponseProcessor._normalize_url(payload)
            try:
                return NavigateAction(url=cast(HttpUrl, normalized))
            except ValidationError:
                candidate_query = payload.strip() or normalized
                try:
                    return SearchAction(query=candidate_query)
                except ValidationError:
                    html = wrap_content_as_html(payload, candidate_query)
                    return HtmlAction(html=html)

        if action_type == "search":
            try:
                return SearchAction(query=payload)
            except ValidationError:
                html = wrap_content_as_html(payload, query or payload)
                return HtmlAction(html=html)

        html_payload = ensure_html(payload, query or payload)
        return HtmlAction(html=html_payload)

    @staticmethod
    def action_to_tuple(action: AIAction) -> Tuple[str, str]:
        """Convert an `AIAction` instance back into (type, payload) format.
        
        This provides backward compatibility with code that expects the legacy
        (type, payload) tuple format instead of Pydantic models.
        
        Args:
            action: A validated AIAction instance
            
        Returns:
            A tuple of (action_type, payload)
            
        Raises:
            TypeError: If action is not a recognized AIAction type
        """

        if isinstance(action, NavigateAction):
            return action.type, str(action.url)
        if isinstance(action, SearchAction):
            return action.type, action.query
        if isinstance(action, HtmlAction):
            return action.type, action.html
        raise TypeError(f"Unsupported action type: {type(action)!r}")

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Ensure the provided URL includes a scheme for validation."""

        cleaned = url.strip()
        if not cleaned:
            return ""
        if not re.match(r"^[a-z]+://", cleaned, re.IGNORECASE):
            cleaned = f"https://{cleaned}"
        return cleaned
