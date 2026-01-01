# Minimal Browser Architecture & Technical Assessment

> Last updated: 2025-09-25

## 1. Executive Overview

Minimal Browser is a modal, vim-inspired Qt WebEngine shell with a tightly integrated AI assistant. The desktop UI is written in PySide6, while AI interactions are routed through OpenRouter (or compatible) large language models. The recent refactor split AI parsing from HTML/data-URL rendering to clarify responsibilities and unlock future rendering engines.

* Mission: Deliver a lightweight, scriptable browser with first-class AI copiloting for navigation, content synthesis, and smart search.
* Guiding principles: modal ergonomics, structured AI responses, engine pluggability, and transparent storage of conversations/profile data.

## 2. High-Level Component Map

```text
┌────────────────────────────────────────────────────────────────┐
│            Qt UI Layer (PySide6 / VimBrowser class)             │
│  • Mode handling, command palette, keybindings                  │
│  • WebEngine view + profile management                          │
│  • Status overlays, notifications, dev tools                    │
└──────────────┬──────────────────────────────────────────────────┘
               │ Qt signals / slots
┌──────────────▼──────────────────────────────────────────────────┐
│            Coordination & Background Workers                   │
│  • AIWorker thread orchestrates requests & streaming updates    │
│  • ConversationMemory buffers AI dialogue                      │
│  • Storage (JSON log) persists conversations                    │
└──────────────┬──────────────────────────────────────────────────┘
               │ AI queries / responses
┌──────────────▼──────────────────────────────────────────────────┐
│                 AI Integration Layer                           │
│  • StructuredBrowserAgent (pydantic-ai wrapper)                 │
│  • ResponseProcessor parses model output → AIAction             │
│  • Models registry (OpenRouter/OpenAI/Anthropic configs)        │
└──────────────┬──────────────────────────────────────────────────┘
               │ AIAction objects
┌──────────────▼──────────────────────────────────────────────────┐
│                   Rendering Subsystem                          │
│  • rendering/html.py: template discovery & HTML wrapping        │
│  • rendering/artifacts.py: URLBuilder (search/data URLs)        │
│  • Future: rendering/webapps.py for complex apps                │
└──────────────┬──────────────────────────────────────────────────┘
               │ URLs / data URLs
┌──────────────▼──────────────────────────────────────────────────┐
│                 Engines (pluggable web views)                   │
│  • engines/base.py abstract contract                           │
│  • engines/qt_engine.py concrete Qt WebEngine                  │
│  • Placeholder gtk_engine.py for experimentation               │
└────────────────────────────────────────────────────────────────┘
```

## 3. Detailed Flow

1. **User input** (vim commands, AI prompt) is captured by `VimBrowser` and, for AI queries, dispatched to `AIWorker`.
2. **AIWorker** builds a structured prompt via `StructuredBrowserAgent`, which calls OpenRouter/OpenAI.
3. **StructuredBrowserAgent** enforces `AIAction` output using `pydantic-ai`. When OpenRouter rejects a preferred model, it automatically falls back to `claude-opus-4.5` and logs a notice.
4. **ResponseProcessor** interprets the model's string payload (prefix-based or heuristics) into typed `AIAction` instances.
5. **rendering.artifacts.URLBuilder** translates actions into concrete destinations: direct URLs, search queries, or base64 data URLs produced by `rendering.html.create_data_url`.
6. **VimBrowser** loads the destination into the active WebEngine instance, updates the UI, and records the interaction in `ConversationLog` and `ConversationMemory`.

## 4. Key Modules & Responsibilities

| Layer      | Module(s)                                           | Role                                                |
| ---------- | --------------------------------------------------- | --------------------------------------------------- |
| UI & Modes | `minimal_browser.VimBrowser`, `CommandPalette`      | Modal UX, keybindings, status reporting             |
| Engines    | `engines/base.py`, `engines/qt_engine.py`           | Abstract + Qt WebEngine implementation              |
| AI Models  | `ai/models.py`, `ai/structured.py`, `ai/client.py`  | Model registry, structured agent, direct API client |
| AI Parsing | `ai/tools.py`, `ai/schemas.py`                      | Parse model output into typed actions               |
| Rendering  | `rendering/html.py`, `rendering/artifacts.py`       | HTML templating, data URL generation, URL resolver  |
| Storage    | `storage/conversations.py`                          | JSON-based conversation logging with compaction     |
| Templates  | `templates/ai_response.html`, `templates/help.html` | Stylized AI response rendering                      |

## 5. Architecture Strengths

* **Structured Responses**: Pydantic-based action schemas enforce predictable AI outputs and enable deterministic UI handling.
* **Rendering Separation**: Moving HTML/data URL logic into `rendering/` clarifies the AI parsing layer and prepares for richer templating.
* **Pluggable Engines**: Abstract `WebEngine` contract future-proofs non-Qt implementations (e.g., GTK, headless backends).
* **Conversation Hygiene**: `ConversationLog` now compacts entries and guards against corrupt log files.
* **Fallback Resilience**: Automatic Claude Sonnet fallback keeps AI features usable when preview models are unavailable.

## 6. Current Gaps & Critique

1. **Documentation Debt**: README is empty and the roadmap/feature list references pre-refactor structure. No newcomer guide or architecture link.
2. **Testing Coverage**: No automated tests (unit or integration). AI pipeline and rendering conversions are unverified.
3. **Error Handling**: Structured fallback paths exist, but high-level UX when AI fails is limited to status messages; no retry UX or offline mode.
4. **Dependency Footprint**: `pydantic-ai`, `chromadb`, and `boto3` are optional but installed unconditionally; evaluate extras/optional deps for startup time.
5. **AI Configuration**: Model fallback hardcodes Claude Sonnet; there is no user-configurable hierarchy or caching of availability signals.
6. **Rendering Extensibility**: `rendering/webapps.py` is a placeholder—no documented pattern for complex interactive experiences.
7. **Security Posture**: Relaxed WebEngine settings (LocalContentCanAccessRemoteUrls, XSS disabled) lack compensating controls or sandbox explanation.
8. **Storage Strategy**: Conversation logging remains a single JSON file; no rotation, search, or encryption.
9. **Build & Tooling**: Recent refactors rely on manual `py_compile`; continuous integration, lint, or packaging checks not enforced.

## 7. Architecture Roadmap (Next 4–6 Weeks)

| Priority | Workstream                     | Description                                                                                                                       |
| -------- | ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| P0       | **Documentation Refresh**      | Publish updated README, architecture guide (this file), and contributor onboarding steps. Link from repo root.                    |
| P0       | **Testing Baseline**           | Add smoke tests for `ResponseProcessor`, `URLBuilder`, and `ConversationLog`. Mock AI responses to ensure deterministic behavior. |
| P1       | **Configurable Model Routing** | Expose user-configurable model preferences and fallback order via config file/UI. Cache failed model IDs per session.             |
| P1       | **Rendering Toolkit**          | Define interfaces and examples for `rendering/webapps.py` (widgets, dashboards). Document templating best practices.              |
| P1       | **Security Review**            | Document rationale for relaxed WebEngine flags, explore sandboxing or toggles for untrusted HTML.                                 |
| P2       | **Storage Evolution**          | Evaluate SQLite or LiteFS for conversation logs to support search/filter/export.                                                  |
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

---

_This document should be kept in sync with major architectural changes. Update the “Last updated” timestamp and the risk register whenever significant features land._
