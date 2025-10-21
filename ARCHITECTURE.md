# Minimal Browser Architecture & Technical Assessment

> Last updated: 2025-10-21

## 1. Executive Overview

Minimal Browser is a modal, vim-inspired Qt WebEngine shell with a tightly integrated AI assistant. The desktop UI is written in PySide6, while AI interactions are routed through OpenRouter (or compatible) large language models. The recent refactor split AI parsing from HTML/data-URL rendering to clarify responsibilities and unlock future rendering engines.

* Mission: Deliver a lightweight, scriptable browser with first-class AI copiloting for navigation, content synthesis, and smart search.
* Guiding principles: modal ergonomics, structured AI responses, engine pluggability, and transparent storage of conversations/profile data.

## 2. High-Level Component Map

```text
┌────────────────────────────────────────────────────────────────┐
│            Qt UI Layer (PySide6 / VimBrowser class)             │
│  • Mode handling, command palette (ui/command_palette.py)       │
│  • WebEngine view + profile management                          │
│  • Status overlays, notifications, dev tools                    │
└──────────────┬──────────────────────────────────────────────────┘
               │ Qt signals / slots
┌──────────────▼──────────────────────────────────────────────────┐
│            Coordination & Background Workers                   │
│  • AIWorker thread (ui/ai_worker.py) orchestrates requests      │
│  • ConversationMemory buffers AI dialogue                      │
│  • Storage layer persists conversations, bookmarks, files       │
│  • coordination/ for multi-agent patterns (experimental)        │
└──────────────┬──────────────────────────────────────────────────┘
               │ AI queries / responses
┌──────────────▼──────────────────────────────────────────────────┐
│                 AI Integration Layer                           │
│  • StructuredBrowserAgent (pydantic-ai wrapper)                 │
│  • ResponseProcessor parses model output → AIAction             │
│  • Models registry (OpenRouter/OpenAI/Anthropic configs)        │
│  • Authentication via auth.py with keyring support              │
└──────────────┬──────────────────────────────────────────────────┘
               │ AIAction objects (Navigate/Search/Html/Bookmark)
┌──────────────▼──────────────────────────────────────────────────┐
│                   Rendering & Export Subsystem                 │
│  • rendering/html.py: template discovery & HTML wrapping        │
│  • rendering/artifacts.py: URLBuilder (search/data URLs)        │
│  • rendering/webapps.py: complex interactive apps               │
│  • export/exporter.py: HTML, Markdown, PDF export               │
└──────────────┬──────────────────────────────────────────────────┘
               │ URLs / data URLs / exported files
┌──────────────▼──────────────────────────────────────────────────┐
│                 Engines (pluggable web views)                   │
│  • engines/base.py abstract contract                           │
│  • engines/qt_engine.py concrete Qt WebEngine                  │
│  • engines/gtk_engine.py for GTK experimentation               │
└────────────────────────────────────────────────────────────────┘
```

## 3. Detailed Flow

1. **User input** (vim commands, AI prompt) is captured by `VimBrowser` and, for AI queries, dispatched to `AIWorker`.
2. **AIWorker** builds a structured prompt via `StructuredBrowserAgent`, which calls OpenRouter/OpenAI.
3. **StructuredBrowserAgent** enforces `AIAction` output using `pydantic-ai`. When OpenRouter rejects a preferred model, it automatically falls back to `claude-4-sonnet` and logs a notice.
4. **ResponseProcessor** interprets the model's string payload (prefix-based or heuristics) into typed `AIAction` instances.
5. **rendering.artifacts.URLBuilder** translates actions into concrete destinations: direct URLs, search queries, or base64 data URLs produced by `rendering.html.create_data_url`.
6. **VimBrowser** loads the destination into the active WebEngine instance, updates the UI, and records the interaction in `ConversationLog` and `ConversationMemory`.

## 4. Key Modules & Responsibilities

| Layer        | Module(s)                                                      | Role                                                      |
| ------------ | -------------------------------------------------------------- | --------------------------------------------------------- |
| UI & Modes   | `minimal_browser.VimBrowser`, `ui/command_palette.py`          | Modal UX, command palette, keybindings, status reporting  |
| UI Workers   | `ui/ai_worker.py`                                              | Background thread for AI requests with Qt signals         |
| Engines      | `engines/base.py`, `engines/qt_engine.py`, `engines/gtk_engine.py` | Abstract contract + Qt/GTK WebEngine implementations |
| AI Models    | `ai/models.py`, `ai/structured.py`, `ai/client.py`             | Model registry, structured agent, direct API client       |
| AI Auth      | `ai/auth.py`                                                   | API key management with keyring/environment support       |
| AI Parsing   | `ai/tools.py`, `ai/schemas.py`                                 | Parse model output into typed actions (Navigate/Search/Html/Bookmark) |
| Rendering    | `rendering/html.py`, `rendering/artifacts.py`, `rendering/webapps.py` | HTML templating, data URL generation, URL resolver, web apps |
| Export       | `export/exporter.py`                                           | Page export to HTML, Markdown, and PDF formats            |
| Storage      | `storage/conversations.py`, `storage/bookmarks.py`, `storage/file_browser.py` | Conversations, bookmarks, file indexing with embeddings |
| Storage Util | `storage/databases.py`, `storage/keystore.py`, `storage/utils.py` | Database helpers, secure storage, utility functions    |
| Coordination | `coordination/agentic_struct.py`                               | Multi-agent coordination patterns (experimental)          |
| Native       | `native/text_processor.py`, `native/profiling.py`              | Optional Rust/C extensions for performance                |
| Templates    | `templates/ai_response.html`, `templates/help.py`              | Stylized AI response rendering and help system            |

## 5. Architecture Strengths

* **Structured Responses**: Pydantic-based action schemas (Navigate, Search, Html, Bookmark) enforce predictable AI outputs and enable deterministic UI handling.
* **Rendering Separation**: Moving HTML/data URL logic into `rendering/` clarifies the AI parsing layer and prepares for richer templating.
* **Export Capabilities**: Built-in page export to HTML, Markdown, and PDF via `export/exporter.py` using html2text and WeasyPrint.
* **Pluggable Engines**: Abstract `WebEngine` contract future-proofs non-Qt implementations (e.g., GTK, headless backends).
* **Comprehensive Storage**: Multiple storage backends for conversations, bookmarks, file browsing with semantic search via ChromaDB.
* **Conversation Hygiene**: `ConversationLog` compacts entries and guards against corrupt log files.
* **Secure Authentication**: Keyring integration via `ai/auth.py` for secure API key storage across platforms.
* **Fallback Resilience**: Automatic Claude Sonnet fallback keeps AI features usable when preview models are unavailable.
* **Command Palette**: Dedicated `ui/command_palette.py` provides consistent command interface across modes.
* **Test Coverage**: Unit tests in `tests/unit/` cover AI parsing, schemas, rendering, and storage modules.

## 6. Current Gaps & Critique

1. **Testing Expansion Needed**: Unit tests exist for core modules (AI, rendering, storage) but integration tests and UI testing infrastructure are minimal.
2. **Error Handling**: Structured fallback paths exist, but high-level UX when AI fails is limited to status messages; no retry UX or offline mode.
3. **Dependency Footprint**: `pydantic-ai`, `chromadb`, `boto3`, `weasyprint` are optional but installed unconditionally; evaluate extras/optional deps for startup time.
4. **AI Configuration**: Model fallback hardcodes Claude Sonnet; there is no user-configurable hierarchy or caching of availability signals.
5. **Rendering Extensibility**: `rendering/webapps.py` exists but lacks documented patterns for complex interactive experiences.
6. **Security Posture**: Relaxed WebEngine settings (LocalContentCanAccessRemoteUrls, XSS disabled) lack compensating controls or sandbox explanation.
7. **Storage Strategy**: Conversation logging remains a single JSON file; no rotation, search, or encryption.
8. **Coordination Module**: `coordination/` directory exists with agent structures but is largely experimental with empty placeholder files.
9. **Export Documentation**: Export commands (:export-html, :export-md, :export-pdf) exist in code but not well-documented in user guides.
10. **Build & Tooling**: Continuous integration, lint, or packaging checks not fully enforced; relies on manual verification.

## 7. Architecture Roadmap (Next 4–6 Weeks)

| Priority | Workstream                     | Description                                                                                                                       |
| -------- | ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| P0       | **Documentation Refresh**      | ✓ Updated ARCHITECTURE.md with current module structure. Maintain alignment with code changes through regular reviews.            |
| P0       | **Testing Expansion**          | Extend existing unit test coverage to integration tests for UI workflows and multi-component interactions.                        |
| P1       | **Configurable Model Routing** | Expose user-configurable model preferences and fallback order via config file/UI. Cache failed model IDs per session.             |
| P1       | **Export Documentation**       | Document export workflow (:export-html, :export-md, :export-pdf) with examples and configuration options.                         |
| P1       | **Security Review**            | Document rationale for relaxed WebEngine flags, explore sandboxing or toggles for untrusted HTML.                                 |
| P2       | **Storage Evolution**          | Evaluate SQLite or LiteFS for conversation logs to support search/filter/export. Consider encryption for sensitive data.          |
| P2       | **Coordination Patterns**      | Flesh out `coordination/` module with documented multi-agent patterns and examples.                                               |
| P2       | **Deployment Story**           | Document packaging (AppImage/Flatpak) and environment constraints (Wayland, GPU).                                                 |

## 8. Risk Register

| Risk                             | Impact                                              | Mitigation                                                                      |
| -------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------- |
| OpenRouter model churn           | Loss of AI functionality when preview models vanish | Implement dynamic discovery, fallback queue configuration, cached health checks |
| UI regressions (Wayland/Qt 6.9+) | Browser fails on non-Wayland or older Qt setups     | Add startup diagnostics, document env overrides, consider runtime checks        |
| HTML injection via AI            | Generated HTML executed with relaxed security       | Introduce sanitization or user prompt before loading AI-generated content       |
| Optional dependency bloat        | Slower cold start, unused packages                  | Gate optional integrations behind extras/`pyproject` optional-dependencies      |

## 9. References & Related Docs

* `.github/copilot-instructions.md` – in-repo assistant briefing
* `ROADMAP.md` / `FEATURE_REQUESTS.md` – feature planning snapshots (pending refresh)
* `src/minimal_browser/main.py` – entry point enforcing environment settings
* `src/minimal_browser/minimal_browser.py` – canonical source for mode handling and AI orchestration
* `scripts/check_docs.py` – documentation health check script for verifying docs are current

### Documentation Maintenance

This architecture document should be kept in sync with major code changes. To help automate verification:

1. **Update date**: Change the "Last updated" timestamp at the top when making significant changes
2. **Run health checks**: Use `python3 scripts/check_docs.py` to verify documentation completeness
3. **Review regularly**: Check documentation during release cycles or after adding new modules
4. **Risk register**: Update the risk register when new architectural concerns emerge

The `check_docs.py` script can be integrated into CI workflows to catch documentation drift automatically.

---

_This document should be kept in sync with major architectural changes. Update the “Last updated” timestamp and the risk register whenever significant features land._
