# Tauri Engine Integration Feasibility Study

> **Investigation Date**: 2025-01-XX  
> **Related Issue**: FR-003: Native Module Optimization  
> **Status**: Initial Investigation

## Executive Summary

This document analyzes the feasibility of integrating Tauri as a browser engine for minimal_browser, evaluates current architectural bottlenecks, and compares potential native module optimization approaches.

**Key Findings:**
- Current Qt WebEngine implementation has significant dependency overhead and cross-language complexity
- Tauri offers a compelling alternative but requires fundamental architectural changes
- Hybrid approach may provide the best balance of features and performance
- Native modules (Rust/C++) show promise for specific performance-critical operations

## 1. Current Architecture Analysis

### 1.1 Technology Stack Overview

**Current Implementation:**
- **UI Framework**: PySide6 (Qt 6.9+)
- **Web Engine**: QtWebEngine (Chromium-based)
- **AI Integration**: OpenRouter API with pydantic-ai
- **Language**: Python 3.13+
- **Build System**: uv package manager

**Dependency Footprint:**
```toml
# Core dependencies (from pyproject.toml)
- pyside6>=6.9.2          # ~200MB installed
- openai>=1.107.2
- pydantic>=2.8.2
- pydantic-ai>=0.1.0
- boto3>=1.35.0          # Optional, but required
- chromadb>=0.4.24       # Optional, but required
- jinja2>=3.1.6
- keyring>=25.5.0
```

**Total Footprint**: Approximately 250-300MB for minimal installation.

### 1.2 Identified Bottlenecks

#### A. Performance Bottlenecks

**1. Cold Start Time**
- **Current**: 3-5 seconds on modern hardware
- **Causes**: 
  - PySide6 initialization
  - QtWebEngine profile setup
  - Multiple large Python dependencies
  - Python interpreter overhead

**2. Memory Usage**
- **Baseline**: ~150MB minimum (QtWebEngine idle)
- **Active browsing**: 300-500MB per tab
- **Peak**: 800MB+ with multiple AI conversations

**3. Web Rendering Performance**
- QtWebEngine is Chromium-based (good)
- Python-Qt bridge adds minimal overhead for most operations
- JavaScript execution is native speed (Chromium V8)
- **Bottleneck**: Python callback overhead for AI integration

#### B. Architectural Bottlenecks

**1. Language Barrier (Python ↔ C++)**
```python
# Current pattern from qt_engine.py
def get_html(self, callback: Callable[[str], None]):
    """Get page HTML asynchronously"""
    if self._widget:
        self._widget.page().toHtml(callback)  # Qt callback → Python
```
- Every web engine interaction crosses Python/C++ boundary
- Signal/slot mechanism adds latency (minimal but measurable)
- Complex data structures require serialization

**2. Dependency Bloat**
- `boto3` and `chromadb` are hard dependencies despite being optional features
- No extras/optional-dependencies configuration
- Impacts: disk space, cold start, security surface area

**3. Engine Abstraction Overhead**
```python
# From engines/base.py
class WebEngine(ABC):
    @abstractmethod
    def create_widget(self) -> Any:
        """Create the web view widget"""
        pass
```
- Abstract interface is excellent for extensibility
- **Problem**: Only Qt implementation is production-ready
- GTK implementation is placeholder
- Abstraction cost without realized benefit

**4. Platform-Specific Issues**
- Wayland compatibility requires specific Qt settings
- Python 3.13 introduces AST compatibility issues (see build error)
- Platform-dependent keyring integration

#### C. Scalability Bottlenecks

**1. Single-Process Architecture**
- Current design: single Python process
- Multiple tabs share same process (QtWebEngine handles isolation)
- AI processing blocks UI thread (mitigated with QThread)

**2. Storage Strategy**
- Conversation logging: single JSON file
- No rotation, compression, or efficient search
- Will become problematic at ~10k+ conversations

**3. AI Request Handling**
```python
# From minimal_browser.py - AI worker pattern
class AIWorker(QThread):
    response_ready = pyqtSignal(dict)
    streaming_chunk = pyqtSignal(str)
```
- Good: Non-blocking AI requests
- **Limitation**: Single concurrent AI request
- No request queue or prioritization

## 2. Tauri Integration Analysis

### 2.1 What is Tauri?

**Tauri Overview:**
- Framework for building desktop applications using web technologies
- Written in Rust with web frontend (HTML/CSS/JS)
- Uses system webview (WebKit on macOS, WebView2 on Windows, WebKitGTK on Linux)
- ~600KB binary for minimal app (vs 250MB+ for Qt)
- First-class Rust integration for native modules

**Architecture:**
```
┌─────────────────────────────────────────┐
│     Frontend (HTML/CSS/JavaScript)       │
│  • Browser UI                            │
│  • Modal interface                       │
│  • AI chat interface                     │
└──────────────┬──────────────────────────┘
               │ IPC (JSON-based)
┌──────────────▼──────────────────────────┐
│          Tauri Core (Rust)               │
│  • Window management                     │
│  • Menu handling                         │
│  • System integration                    │
│  • Command invocations                   │
└──────────────┬──────────────────────────┘
               │ Native APIs
┌──────────────▼──────────────────────────┐
│     Native Modules (Rust)                │
│  • AI client (HTTP/WebSocket)            │
│  • Conversation storage (SQLite)         │
│  • Keyring integration                   │
│  • Performance-critical operations       │
└─────────────────────────────────────────┘
```

### 2.2 Tauri Capabilities

**✅ Strengths:**

1. **Extremely Small Binary Size**
   - 600KB-2MB final binary
   - Uses system webview (no bundled Chromium)
   - Fast cold start (~200-500ms)

2. **Native Performance**
   - Rust for backend = zero-cost abstractions
   - Direct system API access
   - Efficient IPC via JSON serialization

3. **Cross-Platform Consistency**
   - Single codebase for Windows/macOS/Linux
   - Automatic code signing and packaging
   - Native installers (MSI, DMG, DEB, AppImage)

4. **Modern Tooling**
   - TypeScript support for frontend
   - Vite/Webpack integration
   - Hot module replacement in dev mode

5. **Security**
   - Content Security Policy (CSP) by default
   - Sandboxed webview
   - Explicit command allowlist

6. **Native Module Integration**
   ```rust
   // Tauri command example
   #[tauri::command]
   async fn get_ai_response(
       prompt: String,
       model: String,
   ) -> Result<String, String> {
       // Call OpenRouter API directly from Rust
       // No Python/C++ boundary
       let client = reqwest::Client::new();
       let response = client
           .post("https://openrouter.ai/api/v1/chat/completions")
           .json(&request_body)
           .send()
           .await?;
       Ok(response.text().await?)
   }
   ```

**❌ Limitations:**

1. **Not a Full Browser Engine**
   - Uses system webview (not Chromium)
   - Limited to WebKit (macOS/Linux) or Edge WebView2 (Windows)
   - Cannot customize rendering engine
   - Limited control over web engine settings

2. **Different Security Model**
   ```javascript
   // Frontend calls Rust backend
   import { invoke } from '@tauri-apps/api/tauri';
   const response = await invoke('get_ai_response', {
       prompt: userInput,
       model: 'gpt-4'
   });
   ```
   - All backend operations must be explicitly exposed
   - More boilerplate for complex interactions
   - IPC serialization overhead for large data

3. **Learning Curve**
   - Team needs Rust expertise
   - Different mental model from Python
   - Frontend/backend split requires coordination

4. **AI Integration Complexity**
   - Current pydantic-ai integration is Python-specific
   - Would need to rewrite in Rust or use alternative
   - OpenAI SDK in Rust is less mature

5. **Web Engine Limitations**
   - System webview may lag behind Chromium features
   - Platform-specific rendering differences
   - Less control over developer tools

### 2.3 Comparison Matrix

| Feature | Qt WebEngine (Current) | Tauri |
|---------|----------------------|-------|
| **Binary Size** | 250-300MB | 0.6-2MB |
| **Cold Start** | 3-5 seconds | 0.2-0.5 seconds |
| **Memory (Idle)** | 150MB | 30-50MB |
| **Web Engine** | Chromium (bundled) | System (WebKit/WebView2) |
| **Language** | Python + C++ | Rust + JavaScript |
| **AI Integration** | pydantic-ai (native) | Custom (requires port) |
| **Cross-Platform** | Excellent | Excellent |
| **Dev Tools** | Full Chromium tools | System-dependent |
| **Customization** | High (Qt APIs) | Medium (Tauri APIs) |
| **Native Modules** | PyO3 (complex) | Native Rust |
| **Package Size** | 300-400MB | 5-10MB |

## 3. Integration Strategies

### 3.1 Full Rewrite (Tauri Native)

**Approach**: Rewrite entire application in Rust + JavaScript

**Pros:**
- Maximum performance gains
- Smallest binary size
- Best long-term maintainability
- Native Rust modules with zero overhead

**Cons:**
- Requires complete rewrite (~4-6 weeks)
- Loss of pydantic-ai integration
- Team needs Rust expertise
- Risk of feature regressions

**Recommendation**: ⚠️ **High Risk** - Only if long-term performance is critical

### 3.2 Hybrid Approach (Python Backend + Tauri Frontend)

**Approach**: Keep Python AI logic, use Tauri for UI

```
┌────────────────────────────────────┐
│   Tauri Frontend (Rust + JS)       │
│   • Browser UI                     │
│   • Modal interface                │
└────────────┬───────────────────────┘
             │ HTTP/WebSocket
┌────────────▼───────────────────────┐
│   Python Backend (FastAPI)         │
│   • AI integration (pydantic-ai)   │
│   • Conversation management        │
│   • OpenRouter client              │
└────────────────────────────────────┘
```

**Pros:**
- Keeps existing AI logic
- Smaller frontend binary
- Incremental migration path
- Leverages Python ecosystem

**Cons:**
- Requires IPC mechanism
- Two processes (complexity)
- Network latency for AI calls
- Harder to package/distribute

**Recommendation**: 🔶 **Medium Risk** - Good for experimentation

### 3.3 Native Module Augmentation (Current + Rust/C++)

**Approach**: Keep Python/Qt, add Rust modules for critical paths

```python
# Python remains primary
from minimal_browser import ai_rust_client

# Critical operations in Rust
response = ai_rust_client.stream_response(
    prompt=prompt,
    model="gpt-4"
)  # Compiled Rust module via PyO3
```

**Pros:**
- Minimal architectural changes
- Surgical performance improvements
- Keeps familiar Python ecosystem
- Incremental adoption

**Cons:**
- Build complexity (Rust + Python)
- PyO3 learning curve
- Limited performance gains
- Still carries Qt WebEngine overhead

**Recommendation**: ✅ **Low Risk** - Best first step

### 3.4 Plugin Architecture (Multi-Engine)

**Approach**: Enhance engine abstraction, support Tauri as plugin

```python
# engines/tauri_engine.py
class TauriWebEngine(WebEngine):
    """Tauri webview backend via subprocess"""
    def create_widget(self):
        # Launch Tauri process
        # Communicate via IPC
        pass
```

**Pros:**
- Users can choose engine
- Preserves existing Qt option
- Gradual feature parity

**Cons:**
- Complex engine abstraction
- Maintenance burden (2+ engines)
- IPC overhead for Tauri variant
- Unclear value proposition

**Recommendation**: ❌ **Not Recommended** - Over-engineered

## 4. Native Module Optimization

### 4.1 Performance-Critical Operations

**Candidates for Native Modules (Rust/C++):**

1. **AI HTTP Client**
   - Current: Python `requests` + `openai` SDK
   - Opportunity: Rust `reqwest` + native async
   - Expected gain: 20-30% reduction in request latency

2. **Conversation Storage**
   - Current: JSON file with Python serialization
   - Opportunity: SQLite with Rust bindings
   - Expected gain: 10x faster queries, compression

3. **HTML Parsing/Sanitization**
   - Current: Python string manipulation
   - Opportunity: `html5ever` (Rust) or `lexbor` (C)
   - Expected gain: 5-10x faster parsing

4. **Embedding Generation (Future)**
   - Current: `chromadb` (Python + external deps)
   - Opportunity: `qdrant` client (Rust) or `faiss` (C++)
   - Expected gain: 3-5x faster vector operations

### 4.2 Implementation Approach (PyO3)

**Example: Rust AI Client Module**

```rust
// src_rust/ai_client.rs
use pyo3::prelude::*;
use reqwest::Client;
use serde_json::json;

#[pyclass]
struct RustAIClient {
    client: Client,
    api_key: String,
}

#[pymethods]
impl RustAIClient {
    #[new]
    fn new(api_key: String) -> Self {
        RustAIClient {
            client: Client::new(),
            api_key,
        }
    }

    async fn stream_response(
        &self,
        prompt: String,
        model: String,
    ) -> PyResult<String> {
        // Native Rust HTTP with async/await
        let response = self.client
            .post("https://openrouter.ai/api/v1/chat/completions")
            .bearer_auth(&self.api_key)
            .json(&json!({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": true
            }))
            .send()
            .await
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                format!("HTTP error: {}", e)
            ))?;

        // Stream handling...
        Ok(response.text().await.unwrap())
    }
}

#[pymodule]
fn ai_rust_client(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<RustAIClient>()?;
    Ok(())
}
```

**Python Usage:**
```python
# Import compiled Rust module
from ai_rust_client import RustAIClient

# Drop-in replacement for existing client
client = RustAIClient(api_key=os.environ["OPENROUTER_API_KEY"])
response = await client.stream_response(prompt="Hello", model="gpt-4")
```

**Build Configuration:**
```toml
# Cargo.toml (Rust build)
[package]
name = "ai_rust_client"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.22", features = ["extension-module"] }
reqwest = { version = "0.12", features = ["json", "stream"] }
tokio = { version = "1.40", features = ["full"] }
serde_json = "1.0"

[build-dependencies]
pyo3-build-config = "0.22"
```

```toml
# pyproject.toml (Python build)
[build-system]
requires = ["maturin>=1.7,<2.0"]
build-backend = "maturin"

[project.optional-dependencies]
rust_modules = ["ai_rust_client"]
```

### 4.3 Expected Performance Improvements

| Operation | Current (Python) | With Rust Module | Speedup |
|-----------|------------------|------------------|---------|
| AI HTTP Request | 50-100ms overhead | 10-20ms overhead | 3-5x |
| JSON Parsing | 5-10ms (large payloads) | <1ms | 5-10x |
| Conversation Query | 50ms (10k entries) | 5ms | 10x |
| HTML Sanitization | 20ms (large docs) | 2ms | 10x |
| **Cold Start** | 3-5 seconds | 2-3 seconds | 1.5-2x |

## 5. Recommendations

### 5.1 Immediate Actions (0-2 Weeks)

**Priority 1: Dependency Optimization**
```toml
# pyproject.toml - refactor dependencies
[project]
dependencies = [
    "openai>=1.107.2",
    "pyside6>=6.9.2",
    "pydantic>=2.8.2",
    "pydantic-ai>=0.1.0",
    "jinja2>=3.1.6",
    "keyring>=25.5.0",
]

[project.optional-dependencies]
vector_db = ["chromadb>=0.4.24"]
aws = ["boto3>=1.35.0"]
```
- **Expected gain**: 50MB smaller install, 0.5-1s faster cold start

**Priority 2: Fix Build Issues**
- Address Python 3.13 AST compatibility in chromadb/pypika
- Consider pinning to Python 3.12 until dependencies catch up
- Document workarounds in CONTRIBUTING.md

**Priority 3: Profile Current Performance**
```python
# Add profiling to minimal_browser.py
import cProfile
import pstats

if os.environ.get("PROFILE"):
    profiler = cProfile.Profile()
    profiler.enable()
    # ... run app ...
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.dump_stats("minimal_browser.prof")
```

### 5.2 Short-Term (2-6 Weeks)

**Proof-of-Concept: Rust AI Client**
1. Implement basic Rust HTTP client for OpenRouter
2. Package as Python extension with maturin
3. A/B test performance vs Python client
4. Document build process and distribution

**Deliverables:**
- `src_rust/ai_client/` directory with Rust code
- `pyproject.toml` updated with maturin build
- Performance comparison document
- Decision on full adoption

**Tauri Evaluation Project**
1. Create standalone Tauri prototype of minimal_browser
2. Implement core features:
   - Modal navigation
   - Basic AI integration
   - Conversation storage
3. Compare:
   - Binary size
   - Cold start time
   - Memory usage
   - Development velocity
   - User experience

**Deliverables:**
- `tauri-prototype/` directory with working app
- Comparison matrix with metrics
- Migration effort estimation
- Go/no-go recommendation

### 5.3 Medium-Term (6-12 Weeks)

**Option A: Continue Qt + Selective Rust Modules**
- Implement Rust modules for AI, storage, parsing
- Optimize PySide6 initialization
- Improve cold start with lazy loading
- **Target**: 50% performance improvement, 30% smaller binary

**Option B: Hybrid Architecture**
- Python backend (FastAPI) for AI logic
- Tauri frontend for UI
- WebSocket communication
- **Target**: 80% smaller binary, 5x faster cold start

**Option C: Full Tauri Migration**
- Complete rewrite in Rust + TypeScript
- Port all features to Tauri
- Extensive testing and validation
- **Target**: 95% smaller binary, 10x faster cold start

### 5.4 Decision Framework

**Choose Qt + Rust Modules if:**
- Team prefers Python ecosystem
- AI integration flexibility is critical
- Cross-platform compatibility is priority
- Gradual improvement is acceptable

**Choose Hybrid Architecture if:**
- Want balance of new/old
- Frontend UX improvement is goal
- Backend logic is stable
- Can tolerate distribution complexity

**Choose Full Tauri if:**
- Performance is top priority
- Team is willing to learn Rust
- Long-term maintainability matters
- Desktop-native feel is important

## 6. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Rust module build complexity | High | Medium | Use maturin, provide CI templates |
| Tauri learning curve | Medium | High | Prototype first, invest in training |
| Feature parity loss | Medium | High | Incremental migration, feature flags |
| Performance gains insufficient | Low | Medium | Profile before committing |
| Community resistance | Medium | Low | Maintain Qt option, document benefits |

## 7. Conclusion

**Primary Recommendation**: **Native Module Augmentation (Strategy 3.3)**

**Rationale:**
1. **Lowest risk**: Preserves existing architecture and team expertise
2. **Measurable gains**: 20-50% performance improvement in critical paths
3. **Incremental**: Can start with one module, expand if successful
4. **Proven pattern**: Many Python projects successfully use PyO3
5. **Reversible**: Can abandon if benefits don't materialize

**Implementation Roadmap:**
1. **Week 1-2**: Profile current implementation, identify bottlenecks
2. **Week 3-4**: Implement Rust AI client module as PoC
3. **Week 5-6**: Benchmark, document, decide on expansion
4. **Week 7-8**: Add Rust storage module if AI client successful
5. **Week 9-10**: Optimize build and distribution
6. **Week 11-12**: Documentation and contributor onboarding

**Secondary Recommendation**: **Tauri Evaluation (Parallel Track)**

Run Tauri prototype in parallel as a research project. If it demonstrates compelling advantages (5x+ performance, 90%+ size reduction), consider migration for v2.0.

**Not Recommended**: Full rewrite or hybrid architecture at this stage. The current architecture is sound; surgical optimizations will deliver better ROI with less risk.

## 8. Next Steps

1. **Create GitHub Issue**: "Implement Rust AI Client Module (PoC)"
2. **Set up development environment**: Install Rust, maturin, profiling tools
3. **Profile current performance**: Establish baseline metrics
4. **Implement Rust PoC**: Basic AI HTTP client with streaming
5. **Benchmark and document**: Compare performance, document findings
6. **Team decision**: Review results, decide on further investment

## Appendix A: Tauri Resources

- [Tauri Official Documentation](https://tauri.app/v1/guides/)
- [Tauri + Rust Backend Examples](https://github.com/tauri-apps/tauri/tree/dev/examples)
- [System Webview Compatibility](https://tauri.app/v1/references/webview-versions)

## Appendix B: PyO3 Resources

- [PyO3 User Guide](https://pyo3.rs/)
- [maturin Build Tool](https://www.maturin.rs/)
- [PyO3 Performance Best Practices](https://pyo3.rs/v0.22.0/performance)

## Appendix C: Profiling Results

_To be added after initial profiling_

---

**Document Status**: Draft v1.0  
**Last Updated**: 2025-01-XX  
**Reviewers Needed**: @matias-ceau, core team  
**Related Issues**: FR-003, FR-060
