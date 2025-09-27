"""HTML rendering helpers for AI responses and generated pages."""

from __future__ import annotations

import base64
import os
import re
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, Template


def _discover_template_dir() -> Path:
    """Return the first available templates directory."""

    candidates = [
        Path(__file__).resolve().parent.parent / "templates",
        Path(os.getcwd()) / "src" / "minimal_browser" / "templates",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    # Fallback to package directory even if templates are missing; Jinja will raise
    return Path(__file__).resolve().parent


_TEMPLATE_DIR = _discover_template_dir()
_ENV = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)))


def render_template(name: str, context: Dict[str, Any]) -> str:
    """Render a Jinja2 template with the provided context."""

    template: Template = _ENV.get_template(name)
    return template.render(**context)


def wrap_content_as_html(content: str, query: str) -> str:
    """Wrap plain text content into a styled HTML document."""

    processed = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", content)
    processed = re.sub(r"\*(.*?)\*", r"<em>\1</em>", processed)
    processed = processed.replace("\n\n", "</p><p>")
    processed = processed.replace("\n", "<br>")

    return render_template(
        "ai_response.html",
        {
            "content": processed,
            "query": query,
        },
    )


def ensure_html(content: str, query: str) -> str:
    """Return the content as HTML, wrapping when necessary."""

    snippet = content.strip().lower()
    if "<html" in snippet or snippet.startswith("<!doctype"):
        return content
    effective_query = query or content
    return wrap_content_as_html(content, effective_query)


def create_data_url(html_content: str) -> str:
    """Encode HTML content into a data URL with base64 encoding."""

    html_with_charset = html_content
    if "<head>" in html_content and "charset=" not in html_content:
        html_with_charset = html_content.replace(
            "<head>",
            '<head>\n    <meta charset="UTF-8">',
        )

    encoded_html = base64.b64encode(html_with_charset.encode("utf-8")).decode("ascii")
    return f"data:text/html;charset=utf-8;base64,{encoded_html}"
