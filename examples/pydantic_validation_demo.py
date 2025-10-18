#!/usr/bin/env python3
"""
Simple Pydantic validation examples for Minimal Browser AI integration.

This demonstrates the type safety provided by Pydantic models without
requiring the full browser environment.
"""

from pydantic import BaseModel, Field, ValidationError, HttpUrl
from typing import Annotated, Literal
from datetime import datetime


# Simplified AIModel example
class AIModel(BaseModel):
    """AI model configuration with type validation."""
    
    name: Annotated[str, Field(min_length=1)]
    provider: Annotated[str, Field(min_length=1)]
    max_tokens: Annotated[int, Field(gt=0)]
    supports_streaming: bool
    cost_per_token: Annotated[float, Field(ge=0.0)] = 0.0


# Action models (as in minimal_browser/ai/schemas.py)
class NavigateAction(BaseModel):
    """Navigate to a URL."""
    type: Literal["navigate"] = "navigate"
    url: HttpUrl


class SearchAction(BaseModel):
    """Perform a search."""
    type: Literal["search"] = "search"
    query: Annotated[str, Field(min_length=1, strip_whitespace=True)]


class HtmlAction(BaseModel):
    """Render HTML."""
    type: Literal["html"] = "html"
    html: Annotated[str, Field(min_length=1, strip_whitespace=True)]


# Conversation models
class ConversationMessage(BaseModel):
    """A conversation message."""
    role: Literal["system", "user", "assistant"]
    content: Annotated[str, Field(min_length=1, strip_whitespace=True)]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationMemory(BaseModel):
    """Conversation memory with automatic trimming."""
    max_messages: Annotated[int, Field(gt=0)] = 20
    messages: list[ConversationMessage] = Field(default_factory=list)
    
    def add(self, message: ConversationMessage) -> None:
        """Add a message and trim if needed."""
        self.messages.append(message)
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]


def demo_aimodel():
    """Demonstrate AIModel validation."""
    print("=" * 60)
    print("1. AIModel Validation")
    print("=" * 60)
    
    # Valid model
    print("\n✓ Creating valid AIModel:")
    model = AIModel(
        name="gpt-5-codex-preview",
        provider="openrouter",
        max_tokens=8000,
        supports_streaming=True,
        cost_per_token=0.000006
    )
    print(f"  Name: {model.name}")
    print(f"  Provider: {model.provider}")
    print(f"  Max tokens: {model.max_tokens}")
    
    # Invalid: empty name
    print("\n✗ Attempting empty name:")
    try:
        bad = AIModel(name="", provider="test", max_tokens=100, supports_streaming=True)
    except ValidationError as e:
        print(f"  ValidationError: {e.error_count()} error(s)")
        print(f"  {e.errors()[0]['msg']}")
    
    # Invalid: negative max_tokens
    print("\n✗ Attempting negative max_tokens:")
    try:
        bad = AIModel(name="test", provider="test", max_tokens=-100, supports_streaming=True)
    except ValidationError as e:
        print(f"  ValidationError: {e.error_count()} error(s)")
        print(f"  {e.errors()[0]['msg']}")


def demo_actions():
    """Demonstrate action validation."""
    print("\n" + "=" * 60)
    print("2. Action Validation")
    print("=" * 60)
    
    # Valid actions
    print("\n✓ Creating valid actions:")
    nav = NavigateAction(url='https://example.com')
    print(f"  Navigate: {nav.url}")
    
    search = SearchAction(query='python tutorials')
    print(f"  Search: {search.query}")
    
    html = HtmlAction(html='<h1>Hello</h1>')
    print(f"  HTML: {html.html}")
    
    # Invalid URL
    print("\n✗ Attempting invalid URL:")
    try:
        bad = NavigateAction(url='not-a-url')
    except ValidationError as e:
        print(f"  ValidationError: Invalid URL format")
    
    # Invalid query (whitespace only)
    print("\n✗ Attempting whitespace-only query:")
    try:
        bad = SearchAction(query='   ')
    except ValidationError as e:
        print(f"  ValidationError: Query must have content")


def demo_conversation():
    """Demonstrate conversation memory."""
    print("\n" + "=" * 60)
    print("3. ConversationMemory Validation")
    print("=" * 60)
    
    # Valid usage
    print("\n✓ Creating conversation memory:")
    memory = ConversationMemory(max_messages=5)
    
    memory.add(ConversationMessage(role="user", content="Hello"))
    memory.add(ConversationMessage(role="assistant", content="Hi"))
    print(f"  Messages: {len(memory.messages)}")
    
    # Test trimming
    print("\n✓ Testing auto-trim (max=5):")
    for i in range(6):
        memory.add(ConversationMessage(role="user", content=f"Msg {i}"))
    print(f"  After adding 6 more: {len(memory.messages)} (trimmed)")
    
    # Invalid: max_messages=0
    print("\n✗ Attempting max_messages=0:")
    try:
        bad = ConversationMemory(max_messages=0)
    except ValidationError as e:
        print(f"  ValidationError: max_messages must be > 0")
    
    # Invalid: wrong role
    print("\n✗ Attempting invalid role:")
    try:
        bad = ConversationMessage(role="invalid", content="test")
    except ValidationError as e:
        print(f"  ValidationError: role must be system/user/assistant")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("Minimal Browser: Pydantic AI Integration Demo")
    print("=" * 60)
    print("\nThis demonstrates type safety provided by Pydantic models.")
    print("The actual browser uses these patterns throughout the AI pipeline.")
    
    try:
        demo_aimodel()
        demo_actions()
        demo_conversation()
        
        print("\n" + "=" * 60)
        print("✓ All demos completed successfully!")
        print("=" * 60)
        print("\nBenefits of Pydantic integration:")
        print("  • Type safety at runtime")
        print("  • Automatic validation")
        print("  • Clear error messages")
        print("  • Self-documenting code")
        print("\nSee docs/PYDANTIC_INTEGRATION.md for details.")
        
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

