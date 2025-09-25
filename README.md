# Minimal Browser

A **vim-like browser with native AI integration** built with PySide6 and OpenRouter API. Navigate the web with familiar keybindings while seamlessly interacting with AI for content generation, explanations, and smart navigation.

## Quick Start

### Prerequisites
- Python 3.13+
- OpenRouter API key

### Installation
```bash
pip install -e .
export OPENROUTER_API_KEY="your-api-key-here"
minimal-browser
```

### Basic Usage
- **Space**: Ask AI anything - it can navigate, search, or create content
- **h/j/k/l**: Navigate (vim-style)
- **:q**: Quit
- **:help**: Show all keybindings
- **Escape**: Return to normal mode

## Key Features

### AI Integration
Press **Space** and ask natural language questions:
- "navigate to github" → Opens GitHub
- "create a todo list" → Generates interactive HTML todo app  
- "explain quantum physics" → Creates educational content
- "search python tutorials" → Performs web search

### Modal Interface
Familiar vim-like modes:
- **NORMAL**: Default browsing and navigation
- **COMMAND**: Colon commands (`:e <url>`, `:help`)
- **AI**: Space-activated AI interaction

### Engine Abstraction
Pluggable web engine architecture:
- Primary: Qt WebEngine (PySide6)
- Alternative: GTK WebEngine (development)

## Documentation

### For Developers
- **[GitHub Copilot Instructions](.github/copilot-instructions.md)**: Essential architecture patterns and development workflows for AI coding agents
- **[Architecture Critique](.github/ARCHITECTURE_CRITIQUE.md)**: Current state analysis and improvement recommendations
- **[Roadmap](ROADMAP.md)**: Planned features and development priorities
- **[Feature Requests](FEATURE_REQUESTS.md)**: Individual feature tracking with FR-### numbering

### Architecture Overview
- **Engine Layer**: Abstract web engine interface with Qt/GTK implementations
- **AI Pipeline**: Pydantic-validated response processing (`NAVIGATE:`, `SEARCH:`, `HTML:` formats)
- **Storage**: JSON-based conversation logging and in-memory session management
- **UI**: Modal keybinding system with Qt shortcuts and command palette

## Development

### Build & Test
```bash
# Syntax validation
python -m py_compile src/minimal_browser/minimal_browser.py

# Run from source
python -m minimal_browser
```

### Adding AI Actions
1. Define Pydantic schema in `src/minimal_browser/ai/schemas.py`
2. Update `ResponseProcessor` in `src/minimal_browser/ai/tools.py`
3. Add parsing logic for new response patterns
4. Wire handler in main browser class

### Project Structure
```
src/minimal_browser/
├── ai/                 # AI integration (OpenRouter, schemas, tools)
├── engines/            # Web engine abstraction (Qt, GTK)
├── storage/            # Conversation logging
├── templates/          # HTML templates for AI content
└── minimal_browser.py  # Main application (1,569 lines - needs refactoring)
```

## Contributing

See [Architecture Critique](.github/ARCHITECTURE_CRITIQUE.md) for detailed analysis of current state and improvement opportunities.

### High Priority Items
- Extract HTML templates from Python strings to separate files
- Split monolithic main browser class
- Add comprehensive error handling
- Create development setup documentation

## License

[Add license information]
