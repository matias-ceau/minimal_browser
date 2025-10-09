# Minimal Browser Roadmap

This roadmap summarizes near-term priorities (next 4–6 weeks) and medium-term initiatives. It is intentionally lean—create GitHub issues for each item before implementation and link back to the relevant section below.

> For architecture context and a deeper critique, read [`ARCHITECTURE.md`](ARCHITECTURE.md).

## ✅ Recently Landed

- Structured AI pipeline powered by `pydantic-ai`
- Rendering subsystem split (`ai/` parsing vs `rendering/` output)
- Conversation log compaction and JSON guardrails
- Automatic Claude Sonnet fallback when OpenRouter preview models fail

## 📌 Active Focus (0–6 Weeks)

### P0 · Documentation & Onboarding
- [ ] Polish README with screenshots and quick tasks _(in progress)_
- [ ] Publish contributor setup guide (uv, lint/test commands)
- [ ] Keep `ARCHITECTURE.md` updated with each release

### P0 · Testing Baseline
- [ ] Add smoke tests for `ResponseProcessor` parsing heuristics
- [ ] Add tests for `rendering.html.ensure_html` and `URLBuilder`
- [ ] Configure CI job running `uv run ruff check` + unit tests

### P1 · AI Model Experience
- [ ] Expose model selection & fallback order via config/UI
- [ ] Cache failed model IDs during a session to avoid repeat 400s
- [ ] Document API key management and rate-limit expectations

### P1 · Rendering Toolkit
- [ ] Define API for `rendering/webapps.py` (dynamic widgets, dashboards)
- [ ] Provide reusable template snippets (cards, grids, code blocks)
- [ ] Document sanitation guidelines for AI-generated HTML

### P1 · Security Posture
- [ ] Audit relaxed WebEngine settings; document risks and toggles
- [ ] Add optional HTML sanitization toggle before loading AI output
- [ ] Evaluate CSP or sandbox iframes for generated content

### P2 · Storage & Productivity
- [ ] Prototype SQLite-backed conversation history with search/filter
- [ ] Export conversations as Markdown/HTML bundles
- [ ] Sync bookmarks/files with embedding search (ties to `FEATURE_REQUESTS.md` FR-011/012)

### P2 · UX Enhancements
- [ ] AI sidebar / split view exploration
- [ ] Command palette visual refresh (icons, theming)
- [ ] Inline status overlays for AI streaming feedback

## 🌅 Long-Term Ideas

- Performance profiling and potential native extensions (Rust/C++) - **See `docs/TAURI_INVESTIGATION.md`**
- Integration with system password stores and persistent login cookies
- Screenshot capture + vision-enabled AI analysis of the current page
- Portable packaging (AppImage, Flatpak) with environment auto-detection

## 📝 Process Notes

- Track work through GitHub issues/PRs linked to roadmap bullets.
- Favor incremental changes; keep `main` shippable.
- Update this document alongside major releases to maintain alignment with actual progress.
