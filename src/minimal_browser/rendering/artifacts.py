"""Helpers for building browser-ready artifacts like URLs and data pages."""

from __future__ import annotations

from urllib.parse import quote

from ..ai.schemas import (
    AIAction,
    BookmarkAction,
    HtmlAction,
    NavigateAction,
    SearchAction,
    WebappAction,
)
from .html import create_data_url
from .webapps import render_webapp


class URLBuilder:
    """Convert AI actions into browser destinations."""

    @staticmethod
    def create_search_url(query: str, engine: str = "google") -> str:
        if engine == "google":
            return f"https://www.google.com/search?q={quote(query)}"
        if engine == "duckduckgo":
            return f"https://duckduckgo.com/?q={quote(query)}"
        return f"https://www.google.com/search?q={quote(query)}"

    @staticmethod
    def resolve_action(action: AIAction, engine: str = "google") -> str:
        if isinstance(action, NavigateAction):
            return str(action.url)
        if isinstance(action, SearchAction):
            return URLBuilder.create_search_url(action.query, engine=engine)
        if isinstance(action, HtmlAction):
            return create_data_url(action.html)
        if isinstance(action, WebappAction):
            html = render_webapp(
                action.widget_type, theme=action.theme or "dark", title=action.title
            )
            return create_data_url(html)
        if isinstance(action, BookmarkAction):
            return str(action.url)
        raise TypeError(f"Unsupported action type: {type(action)!r}")
