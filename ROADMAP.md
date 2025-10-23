# Minimal Browser Roadmap

This roadmap summarizes near-term priorities (next 4–6 weeks) and medium-term initiatives. It is intentionally lean—create GitHub issues for each item before implementation and link back to the relevant section below.

> For architecture context and a deeper critique, read [`ARCHITECTURE.md`](ARCHITECTURE.md).

## ✅ Recently Landed

- Structured AI pipeline powered by `pydantic-ai`
- Rendering subsystem split (`ai/` parsing vs `rendering/` output)
- Conversation log compaction and JSON guardrails
- Automatic Claude Sonnet fallback when OpenRouter preview models fail
- BookmarkAction schema for AI-driven bookmark management
- Page export functionality (HTML, Markdown, PDF) via `export/exporter.py`
- External browser integration for opening pages in system browsers
- File browser with semantic search using ChromaDB embeddings
- UI module split with dedicated command palette and AI worker
- Keyring integration for secure API key storage
- Unit test coverage for core modules (AI, rendering, storage)
- Optional native extensions for performance optimization

## 📌 Active Focus (0–6 Weeks)

### P0 · Documentation & Onboarding
- [x] Polish README with feature documentation
- [x] Update `ARCHITECTURE.md` with current module structure (2025-10-21)
- [ ] Add screenshots demonstrating key features
- [ ] Publish contributor setup guide (uv, lint/test commands)
- [ ] Keep documentation aligned with each release

### P0 · Testing Expansion
- [x] Add unit tests for AI parsing, schemas, rendering, and storage
- [ ] Add integration tests for multi-component workflows
- [ ] Add UI testing framework for browser interactions
- [ ] Configure CI job running `uv run ruff check` + unit tests

### P1 · AI Model Experience
- [ ] Expose model selection & fallback order via config/UI
- [ ] Cache failed model IDs during a session to avoid repeat 400s
- [x] Document API key management with keyring integration

### P1 · Rendering Toolkit
- [x] Create `rendering/webapps.py` module structure
- [ ] Document API patterns for dynamic widgets and dashboards
- [ ] Provide reusable template snippets (cards, grids, code blocks)
- [ ] Document sanitation guidelines for AI-generated HTML

### P1 · Security Posture
- [ ] Audit relaxed WebEngine settings; document risks and toggles
- [ ] Add optional HTML sanitization toggle before loading AI output
- [ ] Evaluate CSP or sandbox iframes for generated content

### P2 · Storage & Productivity
- [x] Implement bookmark storage with tags and search
- [x] Implement file browser with ChromaDB embedding search
- [x] Add page export to HTML, Markdown, and PDF
- [ ] Prototype SQLite-backed conversation history with search/filter
- [ ] Export conversations as Markdown/HTML bundles
- [ ] Add conversation search and filtering UI

### P2 · UX Enhancements
- [x] Implement command palette with visual styling
- [ ] Add icons and theming to command palette
- [ ] AI sidebar / split view exploration
- [ ] Inline status overlays for AI streaming feedback
- [x] External browser integration for cross-browser workflows

## 🌅 Long-Term Ideas

- [x] Performance profiling and native extensions (Rust/C++) - **See `NATIVE_OPTIMIZATION.md`**
- [x] Screenshot capture + vision-enabled AI analysis - **Implemented with Ctrl+Shift+S**
- [ ] Integration with system password stores and persistent login cookies
- [ ] Portable packaging (AppImage, Flatpak) with environment auto-detection
- [ ] Multi-agent coordination patterns - **Experimental in `coordination/`**

## 📝 Process Notes

- Track work through GitHub issues/PRs linked to roadmap bullets.
- Favor incremental changes; keep `main` shippable.
- Update this document alongside major releases to maintain alignment with actual progress.
