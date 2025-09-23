"""AI tools and response processing"""

import re
from typing import Tuple
from urllib.parse import quote
import base64

from pydantic import ValidationError

from .schemas import AIAction, HtmlAction, NavigateAction, SearchAction


class ResponseProcessor:
    """Processes AI responses and determines actions"""

    @staticmethod
    def parse_response(response: str) -> AIAction:
        """Parse AI response and return a validated action model."""
        response = response.strip()
        action_type, payload = ResponseProcessor._infer_action_components(response)
        return ResponseProcessor._build_action(action_type, payload)

    @staticmethod
    def parse_response_to_tuple(response: str) -> Tuple[str, str]:
        """Backward-compatible parser returning the legacy (type, payload) tuple."""
        action = ResponseProcessor.parse_response(response)
        return ResponseProcessor.action_to_tuple(action)
    
    @staticmethod
    def _infer_action_components(response: str) -> Tuple[str, str]:
        """Determine action type and payload from raw response text."""
        if response.startswith("NAVIGATE:"):
            return "navigate", response[9:].strip()
        if response.startswith("SEARCH:"):
            return "search", response[7:].strip()
        if response.startswith("HTML:"):
            return "html", response[5:].strip()

        return ResponseProcessor._intelligent_parse(response)

    @staticmethod
    def _intelligent_parse(response: str) -> Tuple[str, str]:
        """Intelligently parse response without explicit prefixes"""
        response_lower = response.lower()
        
        # Navigation patterns
        nav_patterns = [
            r"(?:navigate|go|open|visit)\s+(?:to\s+)?([^\s]+\.[a-z]{2,})",
            r"(?:open|visit)\s+([a-z]+\.com|[a-z]+\.org|[a-z]+\.net)",
        ]
        
        for pattern in nav_patterns:
            match = re.search(pattern, response_lower)
            if match:
                url = match.group(1)
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                return "navigate", url
        
        # Search patterns
        if any(word in response_lower for word in ['search for', 'find', 'look up']):
            # Extract search query
            search_match = re.search(r'(?:search for|find|look up)\s+"?([^"]+)"?', response_lower)
            if search_match:
                return "search", search_match.group(1)
        
        # HTML generation patterns
        html_indicators = [
            'create', 'make', 'generate', 'build', 'design',
            'todo', 'calculator', 'form', 'page', 'website'
        ]
        
        if any(indicator in response_lower for indicator in html_indicators):
            return "html", ResponseProcessor._wrap_as_html(response)

        # Default: treat as search for short responses, HTML for long ones
        if len(response.split()) <= 5:
            return "search", response
        else:
            return "html", ResponseProcessor._wrap_as_html(response)

    @staticmethod
    def _build_action(action_type: str, payload: str) -> AIAction:
        """Convert action tuple into a validated `AIAction` instance."""
        if action_type == "navigate":
            normalized = ResponseProcessor._normalize_url(payload)
            try:
                return NavigateAction(url=normalized)
            except ValidationError:
                # Fallback to search if the URL cannot be validated
                candidate_query = payload.strip() or normalized
                try:
                    return SearchAction(query=candidate_query)
                except ValidationError:
                    html = ResponseProcessor._wrap_as_html(payload)
                    return HtmlAction(html=html)

        if action_type == "search":
            try:
                return SearchAction(query=payload)
            except ValidationError:
                # Promote malformed queries to HTML informational pages
                html = ResponseProcessor._wrap_as_html(payload)
                return HtmlAction(html=html)

        # Treat everything else as HTML content
        html_payload = ResponseProcessor._ensure_html(payload)
        return HtmlAction(html=html_payload)

    @staticmethod
    def action_to_tuple(action: AIAction) -> Tuple[str, str]:
        """Convert an `AIAction` instance back into (type, payload) format."""
        if isinstance(action, NavigateAction):
            return action.type, action.url
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

        # Prepend https:// if the scheme is missing
        if not re.match(r"^[a-z]+://", cleaned, re.IGNORECASE):
            cleaned = f"https://{cleaned}"

        return cleaned

    @staticmethod
    def _ensure_html(content: str) -> str:
        """Return provided content as HTML, wrapping plain text when needed."""
        snippet = content.strip().lower()
        if "<html" in snippet or snippet.startswith("<!doctype"):
            return content
        return ResponseProcessor._wrap_as_html(content)
    
    @staticmethod
    def _wrap_as_html(content: str) -> str:
        """Wrap text content in HTML"""
        # Convert markdown-like formatting
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
        content = content.replace('\n\n', '</p><p>')
        content = content.replace('\n', '<br>')
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>AI Response</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; margin: 0; padding: 40px; min-height: 100vh; line-height: 1.6;
        }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        .content {{ 
            background: rgba(255,255,255,0.1); 
            padding: 30px; 
            border-radius: 15px; 
            backdrop-filter: blur(10px);
        }}
        h1 {{ font-size: 2.5em; margin-bottom: 20px; }}
        p {{ margin-bottom: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="content">
            <h1>🤖 AI Response</h1>
            <p>{content}</p>
        </div>
    </div>
</body>
</html>"""


class URLBuilder:
    """Builds data URLs for HTML content"""
    
    @staticmethod
    def create_data_url(html_content: str) -> str:
        """Create base64 data URL from HTML content"""
        encoded_html = base64.b64encode(html_content.encode('utf-8')).decode('ascii')
        return f"data:text/html;base64,{encoded_html}"
    
    @staticmethod
    def create_search_url(query: str, engine: str = "google") -> str:
        """Create search URL"""
        if engine == "google":
            return f"https://www.google.com/search?q={quote(query)}"
        elif engine == "duckduckgo":
            return f"https://duckduckgo.com/?q={quote(query)}"
        else:
            return f"https://www.google.com/search?q={quote(query)}"

    @staticmethod
    def resolve_action(action: AIAction, engine: str = "google") -> str:
        """Convert an AI action into a navigable URL or data URL."""
        if isinstance(action, NavigateAction):
            return str(action.url)
        if isinstance(action, SearchAction):
            return URLBuilder.create_search_url(action.query, engine=engine)
        if isinstance(action, HtmlAction):
            return URLBuilder.create_data_url(action.html)
        raise TypeError(f"Unsupported action type: {type(action)!r}")
