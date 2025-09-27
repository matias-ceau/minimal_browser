# GitHub Copilot Instructions for Minimal Browser

This project is a **vim-like browser with native AI integration** built using PySide6 and OpenRouter API. Understanding these architectural patterns is essential for effective development.

## Core Architecture

### Engine Abstraction Pattern
The browser uses pluggable web engines via abstract base class `src/minimal_browser/engines/base.py`:
- **QtWebEngine**: Primary implementation using PySide6 WebEngine
- **GtkWebEngine**: Alternative GTK implementation (development)
- Engine creation: `engine.create_widget()` returns the actual web view component

### AI Action Pipeline (Critical Pattern)
AI responses are processed through a **strict typed pipeline** using Pydantic schemas:

```python
# src/minimal_browser/ai/schemas.py defines:
AIAction = Union[NavigateAction, SearchAction, HtmlAction]
```

**Response Format Requirements** (ResponseProcessor enforces these):
- `NAVIGATE: <url>` → Opens URL in browser
- `SEARCH: <query>` → Performs Google search  
- `HTML: <content>` → Renders AI-generated HTML directly
- No prefix → Intelligent parsing based on content patterns

### Modal Interface System
Vim-like keybinding system with contextual modes:
- **NORMAL mode**: Default browsing (hjkl navigation, space for AI)
- **COMMAND mode**: Colon commands (`:q`, `:help`, `:e <url>`)
- **AI mode**: Space key activates AI interaction overlay
- Mode switching handled in `minimal_browser.py` event handlers

## Critical Development Workflows

### Adding New AI Actions (4-step process)
1. **Define schema** in `src/minimal_browser/ai/schemas.py`
2. **Update ResponseProcessor** in `src/minimal_browser/ai/tools.py` 
3. **Add parsing logic** for new response prefixes/patterns
4. **Wire handler** in main browser class `execute_ai_action()`

### AI Response Processing Pipeline
```python
# Flow: Raw AI text → Pydantic model → Browser action
response = ai_client.get_response(query)
action = ResponseProcessor.parse_response(response)  # Returns AIAction
self.execute_ai_action(action)  # Browser handles the action
```

### Data URL Pattern for AI Content
AI-generated HTML uses base64 data URLs for immediate rendering:
```python
# src/minimal_browser/minimal_browser.py
def to_data_url(html: str) -> str:
    """Encode HTML content into a data URL with base64 encoding"""
    try:
        html_bytes = html.encode("utf-8")
        encoded_html = base64.b64encode(html_bytes).decode("ascii")
        return f"data:text/html;charset=utf-8;base64,{encoded_html}"
    except (UnicodeEncodeError, UnicodeDecodeError) as e:
        # Fallback with error handling
        html_bytes = html.encode("utf-8", errors="replace")
        encoded_html = base64.b64encode(html_bytes).decode("ascii")
        return f"data:text/html;charset=utf-8;base64,{encoded_html}"
```

**Alternative rendering functions**:
- `src/minimal_browser/rendering/html.py` provides `create_data_url()` with charset handling
- `ensure_html()` and `wrap_content_as_html()` for content preprocessing

### OpenRouter Integration
Streaming AI responses via OpenRouter API:
- **Authentication**: `OPENROUTER_API_KEY` environment variable required
- **Model configuration**: Default model is `gpt-5-codex-preview` with fallback to `claude-3.5-sonnet`
- **Config location**: `src/minimal_browser/config/default_config.py` defines AIConfig
- **Model override**: Modify `AIConfig.model` field or use configuration files
- **Fallback mechanism**: Gracefully handles invalid model IDs by switching to Claude Sonnet

## Project-Specific Conventions

### Project Structure
```
src/minimal_browser/
├── ai/                # AI models, schemas, structured agent, parsing logic
├── rendering/         # HTML templating + URL/data-URL builders
├── engines/           # Web engine abstractions and the Qt implementation
├── storage/           # Conversation logging utilities
├── templates/         # HTML templates (AI response card, help screen)
├── config/            # Configuration management system
├── coordination/      # Multi-agent coordination (planned)
├── minimal_browser.py # VimBrowser UI, command palette, AI worker wiring
└── main.py            # Entry point + environment setup
```

### Qt WebEngine Configuration
Special handling for modern Python/Wayland compatibility:
```python
# src/minimal_browser/engines/qt_engine.py
profile = QWebEngineProfile.defaultProfile()
profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
# Error handling for Python 3.13/Wayland issues
```

### Async UI Updates
AI worker threads communicate via Qt signals:
```python
# Pattern used throughout minimal_browser.py
worker.response_ready.connect(self.handle_ai_response)
worker.streaming_chunk.connect(self.update_ai_progress)
```

### HTML Template System
AI-generated content uses template patterns in `src/minimal_browser/templates/`:
- Help system: Embedded HTML with CSS styling
- Calculator/Todo generators: Interactive JavaScript components
- Consistent styling: Gradient backgrounds, backdrop-filter blur effects

## Integration Points

### Storage Layer
- **ConversationLog**: JSON-based persistence for AI chat history
- **ConversationMemory**: In-memory rolling buffer (20 messages max)
- File paths: `~/.local/share/minimal_browser/` for user data

### Configuration System
Modern configuration management via `src/minimal_browser/config/default_config.py`:
- **BrowserConfig**: Window settings, user agent, headless mode
- **AIConfig**: Model selection, system prompts, feature flags
- **Storage**: XDG-compliant config directory (`~/.config/minimal_browser/`)
- **Format**: TOML-based configuration files

### Command System
Colon commands parsed in `execute_command()`:
- `:q` → Quit application
- `:e <url>` → Open URL
- `:help` → Show keybinding reference
- Pattern: `cmd, *args = command.split(' ', 1)`

### Keybinding Registration
Modal keybindings use Qt shortcuts with mode-aware handlers:
```python
# Pattern in _init_keybindings()
shortcut = QShortcut(QKeySequence("Space"), self)
shortcut.activated.connect(self.handle_ai_prompt)
```

## Development Commands

**Package Management**: Project uses [uv](https://docs.astral.sh/uv/) for dependency management
- **Install**: `uv sync` (installs all dependencies including dev group)
- **Run**: `uv run python -m minimal_browser` (requires OPENROUTER_API_KEY)
- **Dev Run**: `uv run python -m minimal_browser https://example.com`

**Build/Test**: 
- **Compile Check**: `python -m py_compile src/minimal_browser/minimal_browser.py`
- **Module Structure**: Main entry point is `src/minimal_browser/main.py`
- **Package Scripts**: `minimal-browser` command available after install

**Environment Setup**:
- Python **3.13+** required (specified in pyproject.toml)
- OpenRouter API key: `export OPENROUTER_API_KEY=your_key_here`

When modifying AI actions, always validate Pydantic schemas compile correctly and test both explicit prefixes (`HTML:`, `NAVIGATE:`) and intelligent parsing fallbacks.

## Best Practices for AI-Assisted Development

### Code Quality Standards
- **Type Safety**: All AI components use Pydantic models for validation
- **Error Handling**: Implement graceful fallbacks for AI/network failures
- **Testing**: Manually test AI actions with various input types
- **Documentation**: Update relevant sections when adding new patterns

### Contributing Guidelines
- Follow the established architecture patterns (Engine abstraction, AI pipeline, Modal interface)
- Test changes against both direct AI integration and fallback scenarios
- Maintain backward compatibility with existing AI action formats
- See `CONTRIBUTING.md` for detailed development workflow

### Debugging Tips
- Use `python -m py_compile` for syntax validation
- Check AI responses in browser developer tools (F12)
- Monitor console output for encoding/parsing errors
- Test with different AI models to ensure compatibility