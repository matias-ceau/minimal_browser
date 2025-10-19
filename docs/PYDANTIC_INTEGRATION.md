# Pydantic AI Integration

This document describes the Pydantic-based type validation system used throughout the Minimal Browser AI integration layer.

## Overview

All AI-related data structures use Pydantic models to enforce strict type validation and data integrity. This ensures that invalid data is caught early and provides clear error messages when validation fails.

## Core Components

### 1. AIModel (models.py)

The `AIModel` class defines AI provider configurations with comprehensive validation:

```python
from minimal_browser.ai import get_model

# Get a validated model configuration
model = get_model('gpt-5-codex-preview')
print(f"Provider: {model.provider}")  # Always lowercase
print(f"Max tokens: {model.max_tokens}")  # Always positive
```

**Field Validation:**
- `name`: Non-empty string (min_length=1)
- `provider`: Non-empty string, automatically lowercased
- `max_tokens`: Positive integer (gt=0)
- `cost_per_token`: Non-negative float (ge=0.0)
- `supports_streaming`: Boolean flag

**Example:**
```python
# This will raise ValidationError
try:
    bad_model = AIModel(
        name="",  # Empty name not allowed
        provider="test",
        max_tokens=-100,  # Negative tokens not allowed
        supports_streaming=True
    )
except ValidationError as e:
    print(f"Validation error: {e}")
```

### 2. AI Actions (schemas.py)

Three action types are defined with strict validation:

#### NavigateAction
Navigate to a specific URL:
```python
from minimal_browser.ai import NavigateAction

action = NavigateAction(url='https://example.com')
# URL is validated as a proper HTTP/HTTPS URL
```

#### SearchAction
Perform a search query:
```python
from minimal_browser.ai import SearchAction

action = SearchAction(query='python tutorials')
# Query is validated (min_length=1, whitespace trimmed)
```

#### HtmlAction
Render HTML content:
```python
from minimal_browser.ai import HtmlAction

action = HtmlAction(html='<h1>Hello World</h1>')
# HTML is validated (min_length=1, whitespace trimmed)
```

### 3. Conversation Memory (schemas.py)

Type-safe conversation tracking:

```python
from minimal_browser.ai import ConversationMemory

memory = ConversationMemory(max_messages=20)
memory.add_user("What is Python?")
memory.add_assistant("Python is a programming language.")

# Get serializable history for API calls
history = memory.as_history()
```

**Features:**
- Automatic message trimming when max_messages is exceeded
- Type validation for all messages
- Timestamp tracking for each message
- Serialization to API-compatible format

### 4. Structured AI Agent (structured.py)

The `StructuredBrowserAgent` uses pydantic-ai to enforce structured responses:

```python
from minimal_browser.ai.structured import StructuredBrowserAgent

agent = StructuredBrowserAgent(
    model_name="gpt-5-codex-preview",
    system_prompt="You are a helpful browser assistant.",
    history=[{"role": "user", "content": "Hello"}]
)

# This returns a validated AIAction
action = agent.run("Search for Python tutorials")
```

**Validation:**
- System prompt cannot be empty
- Model must be a known configuration
- History entries must have 'role' and 'content' fields
- User query cannot be empty
- All responses are validated as AIAction instances

### 5. Response Processing (tools.py)

The `ResponseProcessor` converts text responses into validated Pydantic models:

```python
from minimal_browser.ai import ResponseProcessor

# Parse various response formats
action1 = ResponseProcessor.parse_response("NAVIGATE: https://example.com")
action2 = ResponseProcessor.parse_response("SEARCH: python tutorials")
action3 = ResponseProcessor.parse_response("HTML: <h1>Hello</h1>")

# Intelligent parsing without prefixes
action4 = ResponseProcessor.parse_response("go to github.com")
# Returns NavigateAction with validated URL
```

**Features:**
- Explicit prefix support (NAVIGATE:, SEARCH:, HTML:)
- Intelligent parsing based on content patterns
- Automatic fallback to valid action types
- All returned actions are validated Pydantic models

## Benefits

### Type Safety
- Compile-time type checking with static analysis tools
- Runtime validation catches invalid data early
- Clear error messages when validation fails

### Data Integrity
- All AI responses are validated before use
- Invalid configurations are rejected at initialization
- Consistent data structures throughout the codebase

### Developer Experience
- IDE autocomplete for all model fields
- Self-documenting code through Pydantic models
- Easy serialization/deserialization for API calls

## Error Handling

All Pydantic validation errors are caught and provide detailed information:

```python
from pydantic import ValidationError

try:
    action = SearchAction(query="   ")  # Whitespace-only
except ValidationError as e:
    print(e.errors())
    # [{'type': 'string_too_short', 'loc': ('query',), ...}]
```

## Testing

The Pydantic integration ensures that all data structures are validated:

```python
# Example test
def test_model_validation():
    # Valid model
    model = get_model('gpt-5-codex-preview')
    assert model.max_tokens > 0
    
    # Invalid model
    with pytest.raises(ValidationError):
        AIModel(name="test", provider="test", max_tokens=-1, supports_streaming=True)
```

## Future Enhancements

Potential areas for further Pydantic integration:
- Configuration file validation
- User preferences validation
- Bookmark and history validation
- Plugin/extension validation

## Related Documentation

- [ARCHITECTURE.md](../ARCHITECTURE.md) - Overall architecture patterns
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Development guidelines
- [Pydantic Documentation](https://docs.pydantic.dev/) - Official Pydantic docs
