# Technology Stack

## Build System & Package Management

- **Package Manager**: `uv` (Python package manager)
- **Build Backend**: `uv_build` 
- **Python Version**: Requires Python 3.13+

## Core Dependencies

- **PySide6**: Qt6 bindings for GUI and web engine
- **OpenAI**: AI API integration
- **Requests**: HTTP client for API calls
- **Pydantic**: Data validation and serialization

## Architecture

- **Web Engines**: Pluggable architecture supporting Qt and GTK backends
- **AI Integration**: OpenRouter API with streaming support
- **Storage**: JSON-based conversation logging
- **Modal Interface**: Vim-like keybinding system

## Environment Setup

The application requires several environment variables:
- `OPENROUTER_API_KEY`: Required for AI functionality
- `QT_API=pyside6`: Qt backend selection
- `QT_QPA_PLATFORM=wayland`: Wayland support (Linux)

## Common Commands

```bash
# Install dependencies
uv sync

# Run the application
uv run minimal-browser [url]

# Run with specific URL
uv run minimal-browser https://example.com

# Type checking
mypy src/

# Code formatting
ruff format src/
ruff check src/
```

## Platform Compatibility

- **Linux**: Primary target with Wayland/X11 support
- **Cross-platform**: Qt engine provides Windows/macOS compatibility
- **Hyprland**: Specific optimizations for this Wayland compositor