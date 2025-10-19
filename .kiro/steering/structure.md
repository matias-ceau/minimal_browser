# Project Structure

## Source Organization

```
src/minimal_browser/
├── __init__.py              # Package exports
├── main.py                  # Application entry point
├── minimal_browser.py       # Main VimBrowser class (1400+ lines)
├── ai/                      # AI integration module
│   ├── __init__.py
│   ├── auth.py             # Authentication handling
│   ├── models.py           # AI model configurations
│   ├── schemas.py          # Pydantic data models
│   └── tools.py            # Response processing utilities
├── engines/                 # Web engine abstraction
│   ├── __init__.py
│   ├── base.py             # Abstract WebEngine interface
│   ├── gtk_engine.py       # GTK WebKit implementation
│   └── qt_engine.py        # Qt WebEngine implementation
├── storage/                 # Data persistence
│   └── conversations.py    # Conversation logging
└── templates/              # HTML templates
    ├── __init__.py
    └── help.html           # Built-in help page
```

## Key Architecture Patterns

### Engine Abstraction
- `WebEngine` base class defines common interface
- Concrete implementations for Qt and GTK
- Pluggable architecture for cross-platform support

### AI Integration
- `AIWorker` thread for non-blocking API calls
- Streaming response support with real-time updates
- Pydantic schemas for type-safe AI action parsing
- Three response types: Navigate, Search, HTML generation

### Modal Interface
- Vim-like modes: NORMAL, INSERT, COMMAND
- Keyboard shortcuts and command buffer system
- Status bar with mode indicators

### Data Flow
1. User input → Mode handling → Action dispatch
2. AI requests → Background worker → Response processing
3. Web navigation → Engine abstraction → Platform-specific rendering

## File Naming Conventions

- Snake case for Python files and modules
- Descriptive names reflecting functionality
- Clear separation between core logic and platform-specific code

## Import Organization

- Standard library imports first
- Third-party imports (PySide6, OpenAI, etc.)
- Local imports last
- Type hints using `from __future__ import annotations`