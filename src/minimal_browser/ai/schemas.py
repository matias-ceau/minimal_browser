"""Typed schemas for AI response actions using Pydantic."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field, HttpUrl, StringConstraints


class NavigateAction(BaseModel):
    """Represents a request to navigate the browser to a URL.
    
    This action instructs the browser to load a specific URL. The URL must be
    a valid HTTP or HTTPS URL as validated by Pydantic's HttpUrl type.
    
    Attributes:
        type: Literal discriminator for action type (always "navigate")
        url: The HTTP/HTTPS URL to navigate to
    """

    type: Literal["navigate"] = "navigate"
    url: HttpUrl


class SearchAction(BaseModel):
    """Represents a request to open a search query in the browser.
    
    This action instructs the browser to perform a search using the configured
    search engine (typically Google). The query is automatically URL-encoded.
    
    Attributes:
        type: Literal discriminator for action type (always "search")
        query: The search query string (whitespace trimmed, min 1 character)
    """

    type: Literal["search"] = "search"
    query: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class HtmlAction(BaseModel):
    """Represents a request to render HTML in the browser.
    
    This action instructs the browser to render AI-generated HTML content.
    The HTML is encoded as a data URL and loaded directly into the browser.
    
    Attributes:
        type: Literal discriminator for action type (always "html")
        html: The HTML content to render (whitespace trimmed, min 1 character)
    """

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
    """Represents a chat message tracked in conversation memory.
    
    This model enforces type-safe message storage with automatic timestamp
    tracking. Messages are validated to ensure they have valid roles and
    non-empty content.
    
    Attributes:
        role: The message author role (system, user, or assistant)
        content: The message content (whitespace trimmed, min 1 character)
        created_at: Timestamp when the message was created (auto-generated)
    """

    role: Literal["system", "user", "assistant"]
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationMemory(BaseModel):
    """In-memory rolling buffer for AI conversation messages.
    
    This model maintains a fixed-size buffer of conversation messages with
    automatic trimming when the maximum size is exceeded. All messages are
    type-validated using Pydantic.
    
    Attributes:
        max_messages: Maximum number of messages to retain (default: 20)
        messages: List of conversation messages
    """

    max_messages: Annotated[int, Field(gt=0, description="Maximum messages to retain")] = 20
    messages: list[ConversationMessage] = Field(default_factory=list)

    def add(self, message: ConversationMessage) -> None:
        """Append a message and trim to the configured maximum.
        
        Args:
            message: The ConversationMessage to add (must be valid Pydantic model)
            
        Raises:
            ValueError: If message is not a valid ConversationMessage instance
        """
        if not isinstance(message, ConversationMessage):
            raise ValueError(
                f"Expected ConversationMessage, got {type(message).__name__}"
            )
        self.messages.append(message)
        self.trim()

    def add_user(self, content: str) -> None:
        """Convenience helper to add a user-authored message.
        
        Args:
            content: The message content (will be validated by ConversationMessage)
            
        Raises:
            ValidationError: If content is empty or invalid
        """
        self.add(ConversationMessage(role="user", content=content))

    def add_assistant(self, content: str) -> None:
        """Store a new assistant message in the memory buffer.
        
        Args:
            content: The message content (will be validated by ConversationMessage)
            
        Raises:
            ValidationError: If content is empty or invalid
        """
        self.add(ConversationMessage(role="assistant", content=content))

    def trim(self) -> None:
        """Ensure the memory does not exceed the configured size."""
        overflow = len(self.messages) - self.max_messages
        if overflow > 0:
            del self.messages[:overflow]

    def as_history(self) -> list[dict[str, str]]:
        """Return a serializable list suitable for API payloads."""
        return [msg.model_dump(include={"role", "content"}) for msg in self.messages]
