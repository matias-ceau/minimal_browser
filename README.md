# Minimal Browser

Minimal Browser is a vim-inspired Qt WebEngine shell with a built-in AI copilot. It combines modal keyboard navigation, a lightweight UI, and structured AI actions so you can browse, generate content, or perform smart searches without leaving a terminal-style workflow.

> 📄 Looking for a deeper architectural dive? See [`ARCHITECTURE.md`](ARCHITECTURE.md).  
> 🔬 Interested in performance optimization and Tauri integration? See [`INVESTIGATION_TAURI_ENGINE.md`](INVESTIGATION_TAURI_ENGINE.md).

## ✨ Highlights

- **Modal ergonomics:** NORMAL/COMMAND/INSERT modes with familiar vim keybindings.
- **Native AI assistant:** Structured responses (navigate/search/html) parsed via Pydantic for deterministic actions.
- **AI vision analysis:** Capture screenshots and analyze them with GPT-4o vision capabilities (Ctrl+Shift+S).
- **Pluggable engines:** Abstract `WebEngine` contract with a Qt WebEngine implementation today and hooks for GTK/others tomorrow.
- **Smart rendering:** AI HTML responses rendered via Jinja templates and injected as data URLs for instant previews.
- **Conversation memory:** Rolling in-memory history plus optional JSON persistence for long-running sessions.
- **File browser with embeddings:** Browse local files, index with semantic search, and find code/assets using natural language queries.
- **Performance optimizations:** Optional native (Rust/C) modules for CPU-intensive operations with transparent fallback to pure Python.

## 🧱 Project Layout

```text
src/minimal_browser/
├── ai/                # AI models, schemas, structured agent, parsing logic, auth
├── rendering/         # HTML templating, URL/data-URL builders, web apps
├── engines/           # Web engine abstractions (Qt, GTK implementations)
├── storage/           # Conversations, bookmarks, file browser, databases
├── export/            # Page export to HTML, Markdown, PDF
├── ui/                # Command palette, AI worker threads
├── coordination/      # Multi-agent coordination patterns (experimental)
├── native/            # Optional native optimizations (Rust/C)
├── config/            # Configuration management and defaults
├── templates/         # HTML templates (AI response card, help screen)
├── minimal_browser.py # VimBrowser UI, command execution, AI integration
└── main.py            # Entry point + environment setup

native_extensions/     # Optional Rust extensions for performance
benchmarks/            # Performance benchmarks and tests
tests/                 # Unit and integration tests
├── unit/              # Unit tests for AI, rendering, storage
└── integration/       # Integration tests (planned)
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

## 📑 Page Export

Export the current page to multiple formats:

### Commands

- **`:export-html`** - Save page as HTML file
- **`:export-md`** or **`:export-markdown`** - Convert page to Markdown
- **`:export-pdf`** - Save page as PDF document

### Features

- **Automatic file naming**: Exports use sanitized page titles with timestamps
- **Smart formatting**: Markdown conversion preserves structure via html2text
- **PDF rendering**: High-quality PDF generation using WeasyPrint
- **Default location**: Files saved to `~/Downloads` by default

### Example

```bash
# Export current page as Markdown
:export-md

# Export as PDF
:export-pdf
```

## 🔖 Bookmark Management

Minimal Browser includes a built-in bookmark system with tagging and search capabilities.

### Commands

- **`:bm add [url] [title]`** - Add bookmark (uses current page if no URL provided)
- **`:bm list [tag]`** - List all bookmarks or filter by tag
- **`:bm search <query>`** - Search bookmarks by title, URL, or content
- **`:bm tags`** - Show all available tags
- **`:bm delete <id>`** - Remove a bookmark

### Features

- **Smart tagging**: Organize bookmarks with multiple tags
- **Full-text search**: Search across titles, URLs, and content snippets
- **Metadata storage**: Capture page content and timestamps
- **Persistent storage**: JSON-backed bookmark database

### External Browser Integration

Open pages in your system's default browser or specific browsers:

- **`:browser`** or **`:ext`** - Open current page in default browser
- **`:browser firefox`** - Open in Firefox
- **`:browser chrome`** - Open in Chrome/Chromium
- **`:browser-list`** - Show available browsers

## ⚡ Performance Optimizations (Optional)

Minimal Browser includes an optional native module system that accelerates CPU-intensive operations (regex matching, base64 encoding, markdown conversion) using Rust. The system provides 2-10x performance improvements while maintaining transparent fallback to pure Python.

**To enable native optimizations (requires Rust):**

```bash
# Install Rust if not already installed
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install maturin (Rust-Python bridge)
pip install maturin

# Build and install native module
cd native_extensions
maturin develop
cd ..
```

**Verify it's working:**

```bash
python3 benchmarks/demo_optimizations.py
```

**Performance benchmarking:**

```bash
python3 -m benchmarks.text_processing_benchmark
```

For detailed information, see [`NATIVE_OPTIMIZATION.md`](NATIVE_OPTIMIZATION.md) and [`benchmarks/README.md`](benchmarks/README.md).

## 🧭 Current Status & Known Gaps

The codebase has evolved significantly with robust core functionality:

1. **Testing**: Unit tests cover core AI parsing, schemas, rendering, and storage modules in `tests/unit/`. Integration tests and UI testing frameworks are planned next.
2. **AI UX resiliency:** Errors fall back to notifications; retries and offline modes still need design.
3. **Security review:** Qt WebEngine settings allow local content to access remote URLs and disable XSS auditing for AI-generated HTML. Documenting and tightening this behavior is on the roadmap.
4. **Optional dependency slimming:** Packages like `boto3`, `chromadb`, and `weasyprint` are currently hard dependencies even though their integrations are optional.
5. **Coordination module:** The `coordination/` directory contains experimental multi-agent patterns that are not yet production-ready.

For a detailed critique and near-term roadmap, see the **Architecture Roadmap** section in [`ARCHITECTURE.md`](ARCHITECTURE.md).

## 🗺️ Roadmap Snapshot

- Documentation refresh and contributor onboarding
- Automated tests for AI pipelines and rendering
- Configurable AI model routing with health checks
- Rendering toolkit for richer AI-generated mini-apps
- Storage enhancements (SQLite/LiteFS) for searchable history
- **Native module optimization**: Investigation into Tauri and Rust/C++ modules (see `docs/TAURI_INVESTIGATION.md`)

Track progress in [`ROADMAP.md`](ROADMAP.md) and detailed feature ideas in [`FEATURE_REQUESTS.md`](FEATURE_REQUESTS.md).

## 🤝 Contributing

Contributions are welcome! If you're planning a sizable change:

1. Open an issue or draft proposal referencing the relevant roadmap/feature entry.
2. Keep pull requests focused; follow conventional commit guidelines if possible.
3. Run `uv run python -m py_compile src/minimal_browser/...` before submitting to catch syntax regressions. (Automated tests coming soon.)

## 📄 License

_License information pending. If you plan to distribute, confirm licensing with the project maintainer._
