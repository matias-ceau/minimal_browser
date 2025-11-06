# Minimal Browser

Minimal Browser is a vim-inspired Qt WebEngine shell with a built-in AI copilot. It combines modal keyboard navigation, a lightweight UI, and structured AI actions so you can browse, generate content, or perform smart searches without leaving a terminal-style workflow.

> 📄 Looking for a deeper architectural dive? See [`ARCHITECTURE.md`](ARCHITECTURE.md).

## ✨ Highlights

- **Modal ergonomics:** NORMAL/COMMAND/INSERT modes with familiar vim keybindings.
- **Native AI assistant:** Structured responses (navigate/search/html) parsed via Pydantic for deterministic actions.
- **Pluggable engines:** Abstract `WebEngine` contract with Qt WebEngine (default) and GTK WebKit (optional) implementations.
- **Smart rendering:** AI HTML responses rendered via Jinja templates and injected as data URLs for instant previews.
- **Conversation memory:** Rolling in-memory history plus optional JSON persistence for long-running sessions.

## 🧱 Project Layout

```text
src/minimal_browser/
├── ai/                # AI models, schemas, structured agent, parsing logic
├── rendering/         # HTML templating + URL/data-URL builders
├── engines/           # Web engine abstractions and the Qt implementation
├── storage/           # Conversation logging utilities
├── templates/         # HTML templates (AI response card, help screen)
├── minimal_browser.py # VimBrowser UI, command palette, AI worker wiring
└── main.py            # Entry point + environment setup
```

## 🚀 Getting Started

### Prerequisites

- Python **3.12+** (project managed with [uv](https://docs.astral.sh/uv/))
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

## 🔧 Web Engine Selection

Minimal Browser supports multiple web engines through a pluggable architecture:

### Qt WebEngine (Default)
The default engine based on Chromium, providing full web standards support and excellent developer tools. Included with the PySide6 dependency.

### GTK WebKit Engine (Optional)
An alternative engine for Linux users who prefer GTK over Qt. Provides lighter system dependencies on GTK-based desktops.

**Installation:**
```bash
# Debian/Ubuntu
sudo apt install gir1.2-webkit-6.0 python3-gi

# Arch Linux
sudo pacman -S webkit2gtk python-gobject

# Fedora/RHEL
sudo dnf install webkit2gtk4.1 python3-gobject
```

**Usage:**
```python
from minimal_browser.engines.gtk_engine import GtkWebEngine

engine = GtkWebEngine()
# Pass to VimBrowser during initialization
```

**Note:** Qt WebEngine is recommended for most users. GTK WebKit is provided as an alternative for specific Linux deployments.

For a detailed comparison of engines, see the [Architecture Documentation](docs/development/ARCHITECTURE.md#9-web-engine-comparison).

## 🧭 Current Status & Known Gaps

The codebase is evolving quickly. Key gaps we plan to address next:

1. **Docs & onboarding:** This README and `ARCHITECTURE.md` are brand new—expect further polish, screenshots, and task-based guides.
2. **Testing baseline:** Unit tests exist for AI parsing, rendering, and storage (58 tests). Integration tests and UI component tests are planned.
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
