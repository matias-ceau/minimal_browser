"""AI tools and response processing."""

from __future__ import annotations

import re
from typing import Tuple, cast

from pydantic import HttpUrl, ValidationError

from ..rendering.html import ensure_html, wrap_content_as_html
from ..rendering.webapps import render_webapp, parse_webapp_tag
from .schemas import AIAction, HtmlAction, NavigateAction, SearchAction, WebappAction


class ResponseProcessor:
    """Processes AI responses and determines actions."""

    @staticmethod
    def parse_response(response: str) -> AIAction:
        """Parse AI response text and return a validated action model."""

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
        if response.startswith("WEBAPP:"):
            return "webapp", response[7:].strip()

        return ResponseProcessor._intelligent_parse(response, query)

    @staticmethod
    def _intelligent_parse(response: str, query: str) -> Tuple[str, str]:
        """Intelligently parse a response without explicit prefixes."""

        response_lower = response.lower()

        nav_patterns = [
            r"(?:navigate|go|open|visit)\s+(?:to\s+)?([^\s]+\.[a-z]{2,})",
            r"(?:open|visit)\s+([a-z]+\.com|[a-z]+\.org|[a-z]+\.net)",
        ]

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

        # Check for webapp indicators
        webapp_indicators = {
            "calculator",
            "todo",
            "timer",
            "stopwatch",
            "notes",
            "note-taking",
        }
        
        if any(indicator in response_lower for indicator in webapp_indicators):
            # Try to extract widget type
            for widget_type in ["calculator", "todo", "timer", "stopwatch", "notes"]:
                if widget_type in response_lower:
                    # Map stopwatch to timer
                    if widget_type == "stopwatch":
                        widget_type = "timer"
                    return "webapp", widget_type

        html_indicators = {
            "create",
            "make",
            "generate",
            "build",
            "design",
            "form",
            "page",
            "website",
        }

        if any(indicator in response_lower for indicator in html_indicators):
            return "html", response

        if len(response.split()) <= 5:
            candidate = query or response
            return "search", candidate

        return "html", response

    @staticmethod
    def _build_action(action_type: str, payload: str, query: str) -> AIAction:
        """Convert action tuple into a validated `AIAction` instance."""

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

        if action_type == "webapp":
            # Check if payload is a tag like <webapp type="calculator" />
            if payload.startswith("<webapp"):
                params = parse_webapp_tag(payload)
                widget_type = params.get("type", payload)
                theme = params.get("theme")
                title = params.get("title")
            else:
                # Simple widget type string
                widget_type = payload
                theme = None
                title = None
            
            try:
                return WebappAction(
                    widget_type=widget_type,
                    theme=theme,
                    title=title
                )
            except ValidationError:
                # Fall back to HTML if webapp action is invalid
                html = wrap_content_as_html(payload, query or payload)
                return HtmlAction(html=html)

        html_payload = ensure_html(payload, query or payload)
        return HtmlAction(html=html_payload)

    @staticmethod
    def action_to_tuple(action: AIAction) -> Tuple[str, str]:
        """Convert an `AIAction` instance back into (type, payload) format."""

        if isinstance(action, NavigateAction):
            return action.type, str(action.url)
        if isinstance(action, SearchAction):
            return action.type, action.query
        if isinstance(action, HtmlAction):
            return action.type, action.html
        if isinstance(action, WebappAction):
            # Convert WebappAction to HTML
            html = render_webapp(
                action.widget_type,
                theme=action.theme or "dark",
                title=action.title
            )
            return "html", html
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
