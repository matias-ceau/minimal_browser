# GitHub Copilot Instructions for Minimal Browser

This project is a **vim-like browser with native AI integration** built using PySide6 and OpenRouter API. Understanding these architectural patterns is essential for effective development.

## Quick Reference

### Essential Commands
```bash
# Setup
uv sync                                    # Install all dependencies

# Testing
pytest                                     # Run all tests
pytest tests/unit/ai/ -v                   # Run specific test suite
pytest --cov=src/minimal_browser          # Run with coverage

# Code Quality
ruff format src/                           # Format code
ruff check src/minimal_browser            # Lint code
python -m py_compile src/minimal_browser/[file].py  # Syntax check

# Running
uv run python -m minimal_browser          # Start browser
uv run python -m minimal_browser [url]    # Start with URL
```

### When Working on Code
1. **Always run tests** before and after changes: `pytest tests/unit/[relevant]/`
2. **Check syntax** after edits: `python -m py_compile [file].py`
3. **Run linter** to catch issues: `ruff check src/minimal_browser`
4. **Test manually** for UI changes: `uv run python -m minimal_browser`

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

## Testing

### Running Tests
The project uses **pytest** for testing. Tests are organized in the `tests/` directory:

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/unit/ai/           # AI module tests
pytest tests/unit/rendering/    # Rendering module tests
pytest tests/unit/storage/      # Storage module tests

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=src/minimal_browser --cov-report=term-missing

# Run tests for a specific file
pytest tests/unit/ai/test_schemas.py
```

### Test Structure
- **tests/unit/**: Unit tests for individual modules
  - `ai/`: Tests for AI schemas, tools, and response processing
  - `rendering/`: Tests for HTML rendering and data URL creation
  - `storage/`: Tests for conversation storage and memory
- **tests/integration/**: Integration tests (placeholder for future)

### Writing Tests
When adding new functionality, follow the existing test patterns:
- Use pytest fixtures defined in `conftest.py`
- Test both success and error cases
- Mock external dependencies (OpenRouter API, WebEngine)
- Keep tests focused and independent

## Linting and Code Quality

### Code Formatting
Use **ruff** for code formatting and linting:

```bash
# Format code
ruff format src/

# Check for linting issues
ruff check src/minimal_browser

# Check specific error categories (syntax errors, undefined names)
ruff check src/minimal_browser --select=E9,F63,F7,F82
```

### Type Checking
Use **mypy** for static type checking (when available):

```bash
mypy src/minimal_browser --ignore-missing-imports
```

### Pre-commit Checklist
Before committing code changes:
1. Run syntax validation: `python -m py_compile src/minimal_browser/[modified_file].py`
2. Run relevant tests: `pytest tests/unit/[relevant_test_dir]/`
3. Check formatting: `ruff check src/minimal_browser`
4. Verify imports and type hints are correct

## Common Pitfalls and Gotchas

### Python Version Compatibility
- **Python 3.13+ required** - Don't use features from older Python versions that have changed
- PySide6 requires specific Python versions - check compatibility before upgrading

### Qt WebEngine Issues
- **Headless environments**: Use `QT_QPA_PLATFORM=offscreen` for CI/testing
- **Wayland compatibility**: Set `QT_QPA_PLATFORM=wayland` on Wayland systems
- **Profile management**: Always use `QWebEngineProfile.defaultProfile()` patterns

### AI Response Processing
- **Never skip ResponseProcessor** - All AI responses must go through Pydantic validation
- **Data URL encoding**: Always use UTF-8 encoding with proper error handling
- **HTML sanitization**: Be cautious with user-generated HTML content

### Dependencies
- **ChromaDB compatibility**: Can cause build issues in some environments
- **uv vs pip**: Prefer `uv` for development, but document pip fallbacks
- **Native extensions**: Optional Rust extensions should have Python fallbacks

### Git Workflow
- **Don't force push** - Rebase locally before pushing
- **Keep commits atomic** - One logical change per commit
- **Branch naming**: Use `feature/`, `fix/`, `docs/` prefixes

## Build System

### Using uv (Recommended)
```bash
# Install dependencies (including dev dependencies)
uv sync

# Run the browser
uv run python -m minimal_browser

# Run with custom URL
uv run python -m minimal_browser https://example.com
```

### Using pip (Fallback)
If `uv` is not available:
```bash
# Install core dependencies
pip install pydantic>=2.8.2 pyside6>=6.9.2 openai>=1.107.2 requests>=2.32.5

# Install dev dependencies
pip install pytest pytest-cov

# Run the browser
python -m minimal_browser
```

### Environment Variables
Required for full functionality:
- `OPENROUTER_API_KEY`: OpenRouter API key for AI features
- `QT_QPA_PLATFORM`: Qt platform abstraction (optional, for specific environments)

## Tool Usage Best Practices

### Parallel Tool Calls
When exploring code or making multiple independent changes, **call tools in parallel**:
- ✅ Good: Read 3 different files simultaneously
- ✅ Good: View directory + check git status + read file in one call
- ❌ Bad: Read files one at a time when they're independent

### Sequential Tool Calls
When operations depend on previous results, call tools sequentially:
- ✅ Good: Read file → analyze content → make targeted edit
- ✅ Good: Run tests → check failures → fix specific issues
- ❌ Bad: Try to guess file content without reading it first

### File Editing Patterns
Use `str_replace` for surgical changes:
- Always include enough context in `old_str` to make it unique
- When making multiple changes to the same file, call `str_replace` multiple times in sequence
- Each call applies in order, so later calls see earlier changes
- For new files, use `create` instead

### Testing Workflow
1. **Before changes**: Run relevant tests to establish baseline
2. **After changes**: Run same tests to verify no regressions
3. **For new features**: Add tests before implementation
4. **For bugs**: Add failing test, fix bug, verify test passes

## Examples of Successful Contributions

### Example 1: Adding a New AI Action Type

**Context**: User wants to add a `BOOKMARK` action that saves URLs to a file.

**Steps**:
1. Define schema in `src/minimal_browser/ai/schemas.py`:
   ```python
   class BookmarkAction(BaseModel):
       action_type: Literal["bookmark"] = "bookmark"
       url: str
       title: str | None = None
   ```

2. Update `AIAction` union:
   ```python
   AIAction = Union[NavigateAction, SearchAction, HtmlAction, BookmarkAction]
   ```

3. Add parser in `ResponseProcessor` (`src/minimal_browser/ai/tools.py`):
   ```python
   def parse_response(response: str) -> AIAction:
       if response.startswith("BOOKMARK:"):
           url = response[9:].strip()
           return BookmarkAction(url=url)
   ```

4. Wire handler in `minimal_browser.py`:
   ```python
   def execute_ai_action(self, action: AIAction):
       if isinstance(action, BookmarkAction):
           self._save_bookmark(action.url, action.title)
   ```

5. Test:
   ```bash
   pytest tests/unit/ai/test_schemas.py
   python -m minimal_browser  # Manual test
   ```

### Example 2: Fixing HTML Encoding Issue

**Context**: AI-generated HTML with emoji causes encoding errors.

**Steps**:
1. Locate the issue: `src/minimal_browser/minimal_browser.py:to_data_url()`
2. Read existing implementation to understand encoding
3. Add error handling for problematic characters:
   ```python
   try:
       html_bytes = html.encode("utf-8")
   except UnicodeEncodeError:
       html_bytes = html.encode("utf-8", errors="replace")
   ```
4. Test with emoji content:
   ```bash
   pytest tests/unit/rendering/test_html.py
   # Manually test with: "Show me a calculator 🧮"
   ```

### Example 3: Adding Configuration Option

**Context**: User wants to configure default AI model.

**Steps**:
1. Update `src/minimal_browser/config/default_config.py`:
   ```python
   class AIConfig(BaseModel):
       model: str = "gpt-5-codex-preview"
       fallback_model: str = "claude-3.5-sonnet"
       # Add new option
       default_model: str | None = None
   ```

2. Add model selection logic in AI client
3. Update documentation in `README.md` and this file
4. Test configuration loading:
   ```bash
   pytest tests/unit/  # Verify config tests pass
   ```

## Troubleshooting

### "Module not found" errors
- Run `uv sync` to install dependencies
- Check Python version: `python --version` (should be 3.13+)
- Verify virtual environment is activated

### Tests fail with "WebEngine not available"
- Tests should work without PySide6 using mocks
- Check `tests/conftest.py` for proper mocking setup
- Use `QT_QPA_PLATFORM=offscreen` environment variable

### Linting errors in AI-generated code
- Run `ruff format src/` to auto-fix formatting
- Check for unused imports: `ruff check --select F401`
- Verify type hints are correct: `mypy src/minimal_browser`

### Commits fail or branch is behind
- Pull latest changes: `git pull origin main`
- Rebase if needed: `git rebase main`
- Never force push unless you're certain

## Additional Resources

- **ARCHITECTURE.md**: Detailed technical architecture documentation
- **CONTRIBUTING.md**: Contributor guidelines and workflow
- **TESTING.md**: Comprehensive testing documentation
- **ROADMAP.md**: Future feature planning
- **pyproject.toml**: Dependency specifications and project metadata

---

**Note for GitHub Copilot**: This project values **minimal, surgical changes** that maintain existing patterns. When suggesting modifications:
1. Preserve the vim-like modal interface
2. Maintain Pydantic schema validation for AI responses
3. Keep the engine abstraction intact
4. Follow established error handling patterns
5. Add tests for new functionality
6. Update documentation when changing public APIs