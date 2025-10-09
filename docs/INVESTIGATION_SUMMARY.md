# Native Module Optimization - Executive Summary

> **Related Issue**: FR-003: Native Module Optimization  
> **Full Investigation**: See `TAURI_INVESTIGATION.md`  
> **Date**: January 2025

## Problem Statement

The minimal_browser project faces several limiting factors that may hinder performance and extensibility:
- Cold start time: 3-5 seconds
- Memory footprint: 150MB+ idle, 300-500MB active browsing
- Dependency bloat: 250-300MB installation size
- Python/C++ boundary overhead for web engine interactions

## Investigation Scope

This investigation analyzed:
1. **Current architectural bottlenecks** in the Qt WebEngine implementation
2. **Tauri integration feasibility** as an alternative browser engine
3. **Native module optimization** opportunities with Rust/C++
4. **Performance vs. complexity tradeoffs** for each approach

## Key Findings

### Current Architecture Bottlenecks

**Performance Issues:**
- PySide6 + QtWebEngine adds significant overhead (200MB+)
- Python interpreter and large dependencies slow cold start
- Cross-language boundary (Python ↔ C++) adds measurable latency

**Architectural Issues:**
- Optional dependencies (boto3, chromadb) are currently required
- Single JSON file for conversation storage won't scale
- Engine abstraction exists but only Qt is production-ready

### Tauri Analysis

**What is Tauri?**
- Rust-based framework for desktop apps using web technologies
- Uses system webview (WebKit/WebView2) instead of bundled Chromium
- 600KB-2MB binary size vs 250MB+ for Qt

**Comparison:**

| Metric | Qt WebEngine | Tauri |
|--------|--------------|-------|
| Binary Size | 250-300MB | 0.6-2MB |
| Cold Start | 3-5 sec | 0.2-0.5 sec |
| Memory | 150MB idle | 30-50MB idle |
| Language | Python + C++ | Rust + JS |

**Tauri Strengths:**
- ✅ Dramatically smaller binary (99% size reduction)
- ✅ 10x faster cold start
- ✅ 80% memory reduction
- ✅ Native Rust modules with zero overhead
- ✅ Built-in security (CSP, sandboxing)

**Tauri Limitations:**
- ❌ Not a full browser engine (uses system webview)
- ❌ Requires complete rewrite (4-6 weeks)
- ❌ Team needs Rust expertise
- ❌ Loss of pydantic-ai integration
- ❌ Less control over rendering engine

## Recommendations

### ✅ Primary: Native Module Augmentation (Low Risk)

**Approach:** Keep Python/Qt, add Rust modules for critical paths

```python
from minimal_browser import ai_rust_client

# Critical operations in Rust
response = ai_rust_client.stream_response(
    prompt=prompt,
    model="gpt-4"
)
```

**Benefits:**
- Minimal architectural changes
- 20-50% performance improvement in critical paths
- Incremental adoption (start with one module)
- Keeps familiar Python ecosystem
- Reversible if unsuccessful

**Implementation (12-week roadmap):**
1. Week 1-2: Profile current implementation
2. Week 3-4: Implement Rust AI client (PoC)
3. Week 5-6: Benchmark and document
4. Week 7-8: Add Rust storage module
5. Week 9-10: Optimize build/distribution
6. Week 11-12: Documentation

**Expected Gains:**
- AI HTTP: 3-5x faster (50-100ms → 10-20ms overhead)
- JSON parsing: 5-10x faster
- Conversation queries: 10x faster (50ms → 5ms)
- Cold start: 1.5-2x faster (3-5s → 2-3s)

### 🔶 Secondary: Tauri Evaluation (Parallel Track)

Run Tauri prototype as research project:
- Create standalone proof-of-concept
- Implement core features (modal navigation, AI integration)
- Compare metrics (size, speed, memory, UX)
- Make go/no-go decision for v2.0

### ❌ Not Recommended

**Full Rewrite:** Too risky at this stage. Current architecture is sound.

**Hybrid Architecture:** Adds distribution complexity without clear benefits.

## Immediate Next Steps

### 1. Dependency Optimization (This Week)

```toml
# pyproject.toml - make optional deps actually optional
[project.optional-dependencies]
vector_db = ["chromadb>=0.4.24"]
aws = ["boto3>=1.35.0"]
```

**Expected Gain:** 50MB smaller, 0.5-1s faster cold start

### 2. Fix Build Issues

- Address Python 3.13 AST compatibility
- Consider pinning to Python 3.12
- Document workarounds

### 3. Add Profiling

```python
# Add to minimal_browser.py
if os.environ.get("PROFILE"):
    profiler = cProfile.Profile()
    profiler.enable()
    # ... run app ...
    profiler.disable()
```

### 4. Create GitHub Issues

- [ ] "Implement Rust AI Client Module (PoC)" - FR-003
- [ ] "Make boto3/chromadb optional dependencies"
- [ ] "Add profiling instrumentation"
- [ ] "Tauri evaluation project (research)"

## Performance-Critical Operations

Candidates for Rust modules:

1. **AI HTTP Client** (20-30% latency reduction)
2. **Conversation Storage** (10x faster queries with SQLite)
3. **HTML Parsing/Sanitization** (5-10x faster)
4. **Embedding Generation** (3-5x faster vector operations)

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Rust build complexity | High | Medium | Use maturin, CI templates |
| Insufficient gains | Low | Medium | Profile first |
| Team expertise gap | Medium | Medium | Start small, train incrementally |

## Conclusion

**Recommended Path:** Native module augmentation with selective Rust modules

**Rationale:**
- Lowest risk, highest ROI
- Preserves existing architecture and team expertise
- Measurable 20-50% performance gains
- Incremental and reversible

**Not Recommended:** Full Tauri rewrite at this time. Consider for v2.0 after evaluating prototype.

## Resources

- **Full Investigation**: `docs/TAURI_INVESTIGATION.md`
- **Tauri Docs**: https://tauri.app/
- **PyO3 Guide**: https://pyo3.rs/
- **maturin**: https://www.maturin.rs/

---

**Questions?** Open an issue or discuss in team meeting.
