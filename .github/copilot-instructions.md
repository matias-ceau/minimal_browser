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
    html_bytes = html.encode("utf-8")
    encoded_html = base64.b64encode(html_bytes).decode("ascii")
    return f"data:text/html;charset=utf-8;base64,{encoded_html}"
```

### OpenRouter Integration
Streaming AI responses via OpenRouter API:
- **Authentication**: `OPENROUTER_API_KEY` environment variable required
- **Model configuration**: `src/minimal_browser/ai/models.py` defines available models
- **Fallback mechanism**: Gracefully handles invalid model IDs by switching to Claude Sonnet

## Project-Specific Conventions

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

**Build/Test**: `python -m py_compile src/minimal_browser/minimal_browser.py`
**Run**: `python -m minimal_browser` (requires OPENROUTER_API_KEY)
**Structure**: Main entry point is `src/minimal_browser/main.py`

When modifying AI actions, always validate Pydantic schemas compile correctly and test both explicit prefixes (`HTML:`, `NAVIGATE:`) and intelligent parsing fallbacks.