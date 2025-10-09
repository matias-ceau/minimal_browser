# Minimal Browser

Minimal Browser is a vim-inspired Qt WebEngine shell with a built-in AI copilot. It combines modal keyboard navigation, a lightweight UI, and structured AI actions so you can browse, generate content, or perform smart searches without leaving a terminal-style workflow.

> 📄 Looking for a deeper architectural dive? See [`ARCHITECTURE.md`](ARCHITECTURE.md).

## ✨ Highlights

- **Modal ergonomics:** NORMAL/COMMAND/INSERT modes with familiar vim keybindings.
- **Native AI assistant:** Structured responses (navigate/search/html) parsed via Pydantic for deterministic actions.
- **Pluggable engines:** Abstract `WebEngine` contract with a Qt WebEngine implementation today and hooks for GTK/others tomorrow.
- **Smart rendering:** AI HTML responses rendered via Jinja templates and injected as data URLs for instant previews.
- **Conversation memory:** Rolling in-memory history plus optional JSON persistence for long-running sessions.
- **File browser with embeddings:** Browse local files, index with semantic search, and find code/assets using natural language queries.

## 🧱 Project Layout

```text
src/minimal_browser/
├── ai/                # AI models, schemas, structured agent, parsing logic
├── rendering/         # HTML templating + URL/data-URL builders
├── engines/           # Web engine abstractions and the Qt implementation
├── storage/           # Conversation logging, file browser, embeddings
├── templates/         # HTML templates (AI response, help, file browser)
├── minimal_browser.py # VimBrowser UI, command palette, AI worker wiring
└── main.py            # Entry point + environment setup
```

## 🚀 Getting Started

### Prerequisites

- Python **3.13** (project managed with [uv](https://docs.astral.sh/uv/))
- Qt WebEngine runtime (installed automatically with `PySide6` via uv)
- An **OpenRouter** API key in your environment (`OPENROUTER_API_KEY`)

### Installation

```bash
uv sync
```

### Running the Browser

```bash
uv run python -m minimal_browser
# or launch with an initial URL
uv run python -m minimal_browser https://example.com
```

The first run seeds persistent profile data under `~/.minimal-browser/` and conversation history under `~/.minimal_browser/conversations.json`.

## 🤖 AI Configuration

AI models are defined in `src/minimal_browser/ai/models.py`. By default the browser targets `openrouter/openai/gpt-5-codex-preview`, with an automatic fallback to `anthropic/claude-3.5-sonnet` if the preview model is unavailable.

To override the model, adjust the config returned by `AppConfig` (see `src/minimal_browser/config/default_config.py`) or extend the model registry with new entries. Be sure to provide a valid OpenRouter model slug and set the matching API key via `OPENROUTER_API_KEY`.

### API Key Management

Minimal Browser supports secure API key storage through system keychains:

- **GNOME Keyring** (Linux)
- **macOS Keychain** (macOS)
- **Windows Credential Manager** (Windows)

**Priority order for loading API keys:**

1. **Environment variables** (highest priority) - `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
2. **System keychain** - Keys stored via `keyring` library
3. **Runtime set keys** (lowest priority) - Temporary keys set during session

**Storing keys in keychain:**

```python
from minimal_browser.ai.auth import auth_manager

# Store a key in the system keychain
auth_manager.set_key('openrouter', 'your-api-key', store_in_keychain=True)

# Keys stored in keychain persist across sessions
```

**Using environment variables (traditional method):**

```bash
export OPENROUTER_API_KEY="your-api-key-here"
uv run python -m minimal_browser
```

The keychain integration is optional - if `keyring` is not available or fails, the browser will fall back to environment variables only.

## 📁 File Browser with Embeddings

Minimal Browser includes a built-in file browser with semantic search capabilities powered by ChromaDB embeddings.

![File Browser UI](https://github.com/user-attachments/assets/267b62a0-d48b-4415-b04d-707ef965e9eb)

### Commands

- **`:files [path]`** or **`:fb [path]`** - Browse local directories
  - Without path: Opens home directory
  - With path: Opens specified directory (supports `~` expansion)
  
- **`:index [path]`** - Index files with embeddings for semantic search
  - Recursively indexes up to 100 text-based files
  - Supports: `.py`, `.js`, `.md`, `.txt`, `.json`, `.xml`, etc.
  - Shows progress and completion notifications

- **`:search-files <query>`** - Search indexed files semantically
  - Natural language queries: "database connection logic", "error handling"
  - Returns top 10 matches with file paths and types

### Features

- **Visual file browser**: Modern UI with file type icons, sizes, and MIME types
- **Smart navigation**: Click directories to browse, use parent/home shortcuts
- **Semantic indexing**: ChromaDB-powered embedding search for code and documents
- **Hidden file filtering**: Automatically skips dot files and system files
- **Permission handling**: Gracefully handles inaccessible files and directories

### Example Workflow

```bash
# Browse your project
:files ~/my-project

# Index the codebase
:index ~/my-project

# Search for specific functionality
:search-files authentication middleware
```

For detailed documentation, see [`FILE_BROWSER_DOCS.md`](FILE_BROWSER_DOCS.md).

## 🧭 Current Status & Known Gaps

The codebase is evolving quickly. Key gaps we plan to address next:

1. **Docs & onboarding:** This README and `ARCHITECTURE.md` are brand new—expect further polish, screenshots, and task-based guides.
2. **Testing baseline:** There is no automated test suite yet. We intend to add smoke tests for AI parsing, rendering helpers, and conversation logging.
3. **AI UX resiliency:** Errors fall back to notifications; retries and offline modes still need design.
4. **Security review:** Qt WebEngine settings allow local content to access remote URLs and disable XSS auditing for AI-generated HTML. Documenting and tightening this behavior is on the roadmap.
5. **Optional dependency slimming:** Packages like `boto3` and `chromadb` are currently hard dependencies even though their integrations are optional.

For a detailed critique and near-term roadmap, see the **Architecture Roadmap** section in [`ARCHITECTURE.md`](ARCHITECTURE.md).

## 🗺️ Roadmap Snapshot

- Documentation refresh and contributor onboarding
- Automated tests for AI pipelines and rendering
- Configurable AI model routing with health checks
- Rendering toolkit for richer AI-generated mini-apps
- Storage enhancements (SQLite/LiteFS) for searchable history

Track progress in [`ROADMAP.md`](ROADMAP.md) and detailed feature ideas in [`FEATURE_REQUESTS.md`](FEATURE_REQUESTS.md).

## 🤝 Contributing

Contributions are welcome! If you're planning a sizable change:

1. Open an issue or draft proposal referencing the relevant roadmap/feature entry.
2. Keep pull requests focused; follow conventional commit guidelines if possible.
3. Run `uv run python -m py_compile src/minimal_browser/...` before submitting to catch syntax regressions. (Automated tests coming soon.)

## 📄 License

_License information pending. If you plan to distribute, confirm licensing with the project maintainer._
