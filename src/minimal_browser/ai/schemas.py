"""Typed schemas for AI response actions using Pydantic."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field, HttpUrl, StringConstraints


class NavigateAction(BaseModel):
    """Represents a request to navigate the browser to a URL."""

    type: Literal["navigate"] = "navigate"
    url: HttpUrl


class SearchAction(BaseModel):
    """Represents a request to open a search query in the browser."""

    type: Literal["search"] = "search"
    query: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class HtmlAction(BaseModel):
    """Represents a request to render HTML in the browser."""

    type: Literal["html"] = "html"
    html: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class BookmarkAction(BaseModel):
    """Represents a request to add or manage a bookmark."""

    type: Literal["bookmark"] = "bookmark"
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    url: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    tags: list[str] = Field(default_factory=list)
    content: Optional[str] = None


AIAction = Annotated[
    Union[NavigateAction, SearchAction, HtmlAction, BookmarkAction],
    Field(discriminator="type"),
]
"""Discriminated union encapsulating the possible AI actions."""


class ConversationMessage(BaseModel):
    """Represents a chat message tracked in conversation memory."""

    role: Literal["system", "user", "assistant"]
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationMemory(BaseModel):
    """In-memory rolling buffer for AI conversation messages."""

    max_messages: int = 20
    messages: list[ConversationMessage] = Field(default_factory=list)

    def add(self, message: ConversationMessage) -> None:
        """Append a message and trim to the configured maximum."""
        self.messages.append(message)
        self.trim()

    def add_user(self, content: str) -> None:
        """Convenience helper to add a user-authored message."""
        self.add(ConversationMessage(role="user", content=content))

    def add_assistant(self, content: str) -> None:
        """Store a new assistant message in the memory buffer."""
        self.add(ConversationMessage(role="assistant", content=content))

    def trim(self) -> None:
        """Ensure the memory does not exceed the configured size."""
        overflow = len(self.messages) - self.max_messages
        if overflow > 0:
            del self.messages[:overflow]

    def as_history(self) -> list[dict[str, str]]:
        """Return a serializable list suitable for API payloads."""
        return [msg.model_dump(include={"role", "content"}) for msg in self.messages]
