# Architecture Comparison Diagrams

## Current Architecture (Qt WebEngine)

```
┌─────────────────────────────────────────────────────────┐
│                   Python Application                     │
│                 (minimal_browser.py)                     │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │   AI Logic  │  │  Modal UI    │  │   Storage     │  │
│  │ (pydantic)  │  │  (Qt Slots)  │  │   (JSON)      │  │
│  └──────┬──────┘  └──────┬───────┘  └───────┬───────┘  │
│         │                │                   │          │
│         └────────────────┼───────────────────┘          │
│                          │                              │
│                   ┌──────▼──────┐                       │
│                   │   PySide6   │                       │
│                   │   Bindings  │                       │
│                   └──────┬──────┘                       │
└──────────────────────────┼──────────────────────────────┘
                           │ (Signal/Slot)
                    ┌──────▼──────────┐
                    │  QtWebEngine    │  ← 200MB Chromium
                    │   (C++ Core)    │
                    └─────────────────┘

Total Size: ~250-300MB
Cold Start: 3-5 seconds
Memory: 150MB+ idle
```

## Proposed: Native Module Augmentation

```
┌─────────────────────────────────────────────────────────┐
│              Python Application (Core)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │   AI Logic   │  │  Modal UI    │  │   Storage     │ │
│  │ (pydantic)   │  │  (Qt Slots)  │  │   (JSON)      │ │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────┘ │
│         │                 │                   │         │
└─────────┼─────────────────┼───────────────────┼─────────┘
          │                 │                   │
          │                 │                   │
    ┌─────▼─────┐    ┌──────▼──────┐    ┌──────▼──────┐
    │  Rust AI  │    │   PySide6   │    │Rust Storage │ ← NEW!
    │  Client   │    │   Bindings  │    │   (SQLite)  │
    │ (PyO3)    │    └──────┬──────┘    │   (PyO3)    │
    └───────────┘           │           └─────────────┘
         ↓                  │
    [OpenRouter]     ┌──────▼──────────┐
                     │  QtWebEngine    │
                     │   (C++ Core)    │
                     └─────────────────┘

Total Size: ~200-250MB (-20%)
Cold Start: 2-3 seconds (-40%)
Memory: 120MB+ idle (-20%)
```

## Alternative: Full Tauri Rewrite

```
┌─────────────────────────────────────────────────────────┐
│           Frontend (HTML/CSS/JavaScript)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │  Modal UI    │  │  AI Chat UI  │  │  Browser View │ │
│  │ (TypeScript) │  │ (React/Vue)  │  │  (Webview)    │ │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────┘ │
└─────────┼──────────────────┼──────────────────┼─────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │ (IPC/JSON)
┌─────────────────────────────▼─────────────────────────────┐
│                  Tauri Core (Rust)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │   AI Client  │  │  Window Mgmt │  │  Storage      │  │
│  │  (reqwest)   │  │  (Tauri API) │  │  (rusqlite)   │  │
│  └──────────────┘  └──────────────┘  └───────────────┘  │
└───────────────────────────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │ System Webview  │  ← WebKit/WebView2
                    │   (OS Native)   │
                    └─────────────────┘

Total Size: 0.6-2MB (-99%)
Cold Start: 0.2-0.5 seconds (-90%)
Memory: 30-50MB idle (-70%)
BUT: Requires full rewrite, loss of Python ecosystem
```

## Performance Comparison Chart

```
Metric          Current (Qt)    With Rust Modules    Full Tauri
────────────────────────────────────────────────────────────────
Binary Size     250-300MB       200-250MB (-20%)     0.6-2MB (-99%)
Cold Start      3-5 sec         2-3 sec (-40%)       0.2-0.5s (-90%)
Memory (idle)   150MB           120MB (-20%)         30-50MB (-70%)
AI Request      50-100ms        10-20ms (-70%)       10-20ms (-70%)
────────────────────────────────────────────────────────────────
Risk Level      Current         LOW ✅               HIGH ⚠️
Rewrite Effort  N/A             2-4 weeks            6-8 weeks
Team Learning   N/A             PyO3 basics          Rust + Tauri
Python Compat   Full            Full                 None (port needed)
────────────────────────────────────────────────────────────────
```

## Decision Matrix

```
                    Qt + Rust Modules    Full Tauri
────────────────────────────────────────────────────
Performance Gain         ★★★☆☆              ★★★★★
Binary Size              ★★☆☆☆              ★★★★★
Risk Level               ★★★★★              ★★☆☆☆
Effort Required          ★★★★☆              ★★☆☆☆
Python Ecosystem         ★★★★★              ★☆☆☆☆
Incremental Path         ★★★★★              ★☆☆☆☆
────────────────────────────────────────────────────
RECOMMENDED              ✅ YES             🔶 MAYBE (v2.0)
```

## Implementation Timeline

### Native Module Augmentation (Recommended)

```
Week 1-2:  [Profile] Identify bottlenecks
Week 3-4:  [Build] Rust AI client PoC
Week 5-6:  [Test] Benchmark & validate
Week 7-8:  [Expand] Add storage module
Week 9-10: [Optimize] Build & distribution
Week 11-12:[Document] User & dev guides
───────────────────────────────────────
Total: 12 weeks, Low Risk
```

### Full Tauri Migration (Alternative)

```
Week 1-2:  [Learn] Rust & Tauri training
Week 3-4:  [Build] Basic UI & navigation
Week 5-6:  [Port] AI integration in Rust
Week 7-8:  [Implement] Storage & state
Week 9-10: [Polish] UX & edge cases
Week 11-12:[Test] QA & user testing
───────────────────────────────────────
Total: 12 weeks, High Risk
Additional: +4 weeks for feature parity
```

## Technology Stack Comparison

```
┌───────────────────┬─────────────────┬──────────────────┐
│   Component       │   Current       │   With Tauri     │
├───────────────────┼─────────────────┼──────────────────┤
│ Language          │ Python 3.13     │ Rust + JS/TS     │
│ UI Framework      │ PySide6/Qt      │ Web (HTML/CSS)   │
│ Web Engine        │ QtWebEngine     │ System Webview   │
│ AI Integration    │ pydantic-ai     │ Custom Rust      │
│ Storage           │ JSON file       │ SQLite (Rust)    │
│ Build Tool        │ uv              │ cargo + npm      │
│ Package Format    │ Wheel/pip       │ AppImage/MSI/DMG │
│ Dev Experience    │ Python REPL     │ Rust analyzer    │
└───────────────────┴─────────────────┴──────────────────┘
```

## Dependency Graph Comparison

### Current (Qt WebEngine)
```
minimal-browser
├── pyside6 (200MB)
│   └── Qt WebEngine (Chromium)
├── pydantic-ai
│   └── openai
├── chromadb (100MB)
│   ├── onnxruntime
│   └── numpy/pandas
└── boto3 (50MB)
    └── botocore

Total: ~350MB transitive deps
```

### With Rust Modules
```
minimal-browser
├── pyside6 (200MB)
│   └── Qt WebEngine (Chromium)
├── pydantic-ai
│   └── openai
├── ai_rust_client (2MB) ← NEW!
│   └── reqwest (native)
└── storage_rust (1MB) ← NEW!
    └── rusqlite (native)

Total: ~203MB (chromadb/boto3 now optional)
```

### Full Tauri
```
minimal-browser-tauri
├── tauri-runtime (600KB)
│   └── System Webview (0KB - OS provided)
├── ai-client (Rust) (500KB)
│   └── reqwest
└── storage (Rust) (300KB)
    └── rusqlite

Total: ~1.4MB + system webview
```

---

**Visualization Notes:**
- ★ Rating: More stars = better for that metric
- Risk Level: More stars = safer/lower risk
- Sizes are approximate installed footprint
