# Feature Requests

Each feature request below should map to a GitHub Issue before implementation. Keep metadata (priority, status, owners) up to date so the roadmap reflects reality.

Legend: **Priority** = (High/Medium/Low), **Status** = (Idea ▢ / Planned ◧ / In Progress ◑ / Shipped ◉)

---

## P0 · Documentation & Onboarding

### FR-001: Contributor Setup Guide
- **Summary:** Document environment bootstrap (uv, PySide6 deps, lint/test commands) and add troubleshooting for Wayland/Qt.
- **Priority:** High · **Status:** ▢ Idea

### FR-002: Screen Captures & Walkthroughs
- **Summary:** Add screenshots/GIFs of modal workflow and AI assistant to README.
- **Priority:** Medium · **Status:** ▢ Idea

---

## P0 · Testing Baseline

### FR-010: AI Parsing Smoke Tests
- **Summary:** Unit-test `ResponseProcessor` heuristic paths (navigate/search/html, malformed prefixes).
- **Priority:** High · **Status:** ▢ Idea

### FR-011: Rendering Utility Tests
- **Summary:** Cover `rendering.html.ensure_html`, template rendering, and data URL generation.
- **Priority:** High · **Status:** ▢ Idea

### FR-012: CI Pipeline
- **Summary:** Add GitHub Actions workflow running ruff + unit tests on PRs.
- **Priority:** Medium · **Status:** ▢ Idea

### FR-013: Bindings for Installed Browser Apps
- **Summary:** Provide easy bindings to already installed browser apps for system integration.
- **Priority:** Medium · **Status:** ◉ Shipped

---

## P1 · AI Model Experience

### FR-020: Configurable Model Fallbacks
- **Summary:** Expose an ordered list of preferred models in config/UI with graceful degradation logging.
- **Priority:** High · **Status:** ▢ Idea

### FR-021: Model Health Cache
- **Summary:** Track failing model IDs per session to avoid repeated 400 responses from OpenRouter.
- **Priority:** Medium · **Status:** ▢ Idea

### FR-022: API Key Vault Integration
- **Summary:** Support pulling OpenRouter keys from system keychains.
- **Priority:** Medium · **Status:** ◉ Shipped

---

## P1 · Rendering Toolkit

### FR-030: Webapp Component API
- **Summary:** Formalize `rendering/webapps.py` with helpers for dashboards, widgets, and interactive mini-app shells.
- **Priority:** Medium · **Status:** ▢ Idea

### FR-031: Template Library
- **Summary:** Provide reusable template fragments (cards, timelines, tables) for AI-generated HTML.
- **Priority:** Medium · **Status:** ▢ Idea

### FR-032: HTML Sanitization Toggle
- **Summary:** Optional sanitization pass before loading AI HTML (e.g., Bleach).
- **Priority:** High · **Status:** ▢ Idea

---

## P1 · Security & Privacy

### FR-040: WebEngine Safety Settings UI
- **Summary:** Allow users to toggle relaxed security flags (LocalContentCanAccessRemoteUrls, XSS auditing) with documentation.
- **Priority:** High · **Status:** ▢ Idea

### FR-041: HTML Sandbox Mode
- **Summary:** Load AI HTML in an isolated iframe or sandboxed profile.
- **Priority:** Medium · **Status:** ▢ Idea

---

## P2 · Storage & Productivity

### FR-050: SQLite Conversation Store
- **Summary:** Replace JSON log with searchable SQLite (filters, timestamps, export).
- **Priority:** Medium · **Status:** ▢ Idea

### FR-051: Conversation Export Bundles
- **Summary:** Export queries/responses as Markdown, HTML, or zip bundles.
- **Priority:** Medium · **Status:** ▢ Idea

### FR-052: Smart Bookmark Vault
- **Summary:** Store bookmarks/files/snippets with embedding search and recall interface.
- **Priority:** Medium · **Status:** ▢ Idea

### FR-053: File Browser with Embeddings
- **Summary:** Browse local files, index with embeddings, and surface in AI prompts.
- **Priority:** Low · **Status:** ▢ Idea

---

## P3 · Long-Term Explorations

### FR-003: Native Module Optimization
- **Summary:** Investigate and implement native modules (Rust/C++) for performance-critical operations. Research Tauri integration as alternative browser engine.
- **Priority**: Medium · **Status**: ◧ Planned
- **Investigation Document**: See `docs/TAURI_INVESTIGATION.md`

### FR-060: Native Performance Modules
- **Summary:** Profile hotspots and trial Rust/C++ modules for CPU/GPU-heavy tasks.
- **Priority:** Low · **Status:** ◧ Planned (superseded by FR-003)

### FR-061: Persistent Login Cookies
- **Summary:** Enable long-lived sessions with secure cookie storage.
- **Priority:** Low · **Status:** ◉ Shipped

### FR-062: System Password Store Integration
- **Summary:** Integrate with GNOME Keyring, macOS Keychain, Windows Credential Manager.
- **Priority:** Medium · **Status:** ◉ Shipped

### FR-063: AI Screenshot Analysis
- **Summary:** Capture screenshots, feed vision-capable models, return annotations.
- **Priority:** Medium · **Status:** ▢ Idea