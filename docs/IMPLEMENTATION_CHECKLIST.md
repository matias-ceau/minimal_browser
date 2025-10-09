# Implementation Checklist: Native Module Optimization

> **Based on**: FR-003 Investigation  
> **Strategy**: Native Module Augmentation (Rust/PyO3)  
> **Timeline**: 12 weeks  
> **Risk Level**: Low ✅

This document provides a concrete, step-by-step implementation plan for adding Rust native modules to minimal_browser.

## Phase 0: Preparation (Week 0 - Before Starting)

### Environment Setup

- [ ] **Install Rust toolchain**
  ```bash
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
  source $HOME/.cargo/env
  rustc --version  # Should show 1.75+
  ```

- [ ] **Install maturin** (Rust-Python bridge builder)
  ```bash
  pip install maturin
  maturin --version
  ```

- [ ] **Install profiling tools**
  ```bash
  pip install py-spy cProfile-viewer
  ```

- [ ] **Set up test environment**
  ```bash
  cd minimal_browser
  uv sync  # or pip install -e .
  export OPENROUTER_API_KEY="test-key"
  ```

### Documentation Review

- [ ] Read `docs/TAURI_INVESTIGATION.md` (full analysis)
- [ ] Read PyO3 guide: https://pyo3.rs/v0.22.0/
- [ ] Review maturin workflow: https://www.maturin.rs/

## Phase 1: Profiling & Analysis (Weeks 1-2)

### Week 1: Baseline Metrics

- [ ] **Add profiling infrastructure**
  ```python
  # src/minimal_browser/profiling.py
  import cProfile
  import pstats
  import os
  
  class Profiler:
      def __init__(self, enabled=None):
          self.enabled = enabled or os.environ.get("PROFILE", False)
          self.profiler = cProfile.Profile() if self.enabled else None
      
      def start(self):
          if self.enabled:
              self.profiler.enable()
      
      def stop(self, output_file="profile.stats"):
          if self.enabled:
              self.profiler.disable()
              stats = pstats.Stats(self.profiler)
              stats.dump_stats(output_file)
              print(f"Profile saved to {output_file}")
  ```

- [ ] **Profile cold start**
  ```bash
  PROFILE=1 python -m minimal_browser --exit-after-load
  python -m pstats profile.stats
  > sort cumulative
  > stats 20
  ```

- [ ] **Profile AI request handling**
  ```bash
  # Add timing to ai/client.py
  import time
  start = time.perf_counter()
  response = requests.post(...)
  print(f"AI request took {time.perf_counter() - start:.3f}s")
  ```

- [ ] **Measure memory usage**
  ```bash
  pip install memory_profiler
  @profile
  def create_browser():
      # ... existing code
  
  python -m memory_profiler minimal_browser.py
  ```

- [ ] **Document baseline metrics** in `docs/BASELINE_METRICS.md`

### Week 2: Identify Bottlenecks

- [ ] **Analyze profiling data**
  - Identify functions taking >100ms
  - Find repeated operations
  - Note cross-language boundaries

- [ ] **Create hotspot list** with priority:
  1. AI HTTP client
  2. JSON parsing/serialization
  3. Conversation storage queries
  4. HTML parsing/rendering

- [ ] **Estimate potential gains**
  - Calculate current time per operation
  - Research Rust alternatives
  - Project realistic improvements

## Phase 2: Rust AI Client PoC (Weeks 3-4)

### Week 3: Basic Implementation

- [ ] **Create Rust project structure**
  ```bash
  cd minimal_browser
  mkdir -p src_rust/ai_client
  cd src_rust/ai_client
  maturin init --bindings pyo3
  ```

- [ ] **Configure Cargo.toml**
  ```toml
  [package]
  name = "ai_rust_client"
  version = "0.1.0"
  edition = "2021"
  
  [lib]
  name = "ai_rust_client"
  crate-type = ["cdylib"]
  
  [dependencies]
  pyo3 = { version = "0.22", features = ["extension-module"] }
  reqwest = { version = "0.12", features = ["json", "stream"] }
  tokio = { version = "1.40", features = ["full"] }
  serde = { version = "1.0", features = ["derive"] }
  serde_json = "1.0"
  ```

- [ ] **Implement basic AI client**
  ```rust
  // src_rust/ai_client/src/lib.rs
  use pyo3::prelude::*;
  use reqwest::Client;
  use serde_json::json;
  
  #[pyclass]
  struct AIClient {
      client: Client,
      api_key: String,
      base_url: String,
  }
  
  #[pymethods]
  impl AIClient {
      #[new]
      fn new(api_key: String) -> Self {
          AIClient {
              client: Client::new(),
              api_key,
              base_url: "https://openrouter.ai/api/v1".to_string(),
          }
      }
      
      fn send_request(&self, prompt: String, model: String) -> PyResult<String> {
          // TODO: Implement async request
          Ok("Response from Rust".to_string())
      }
  }
  
  #[pymodule]
  fn ai_rust_client(_py: Python, m: &PyModule) -> PyResult<()> {
      m.add_class::<AIClient>()?;
      Ok(())
  }
  ```

- [ ] **Build and test**
  ```bash
  maturin develop
  python -c "from ai_rust_client import AIClient; print('Success!')"
  ```

### Week 4: Integration & Streaming

- [ ] **Add async/streaming support**
  ```rust
  use futures::StreamExt;
  
  #[pymethods]
  impl AIClient {
      fn stream_response<'py>(
          &self,
          py: Python<'py>,
          prompt: String,
          model: String,
      ) -> PyResult<&'py PyAny> {
          // Implement streaming with pyo3-asyncio
          pyo3_asyncio::tokio::future_into_py(py, async move {
              // Stream handling
              Ok(Python::with_gil(|py| {
                  "response".to_object(py)
              }))
          })
      }
  }
  ```

- [ ] **Create Python wrapper**
  ```python
  # src/minimal_browser/ai/rust_client.py
  from typing import AsyncIterator, Optional
  import ai_rust_client
  
  class RustAIClient:
      """Python wrapper for Rust AI client"""
      
      def __init__(self, api_key: str):
          self._client = ai_rust_client.AIClient(api_key)
      
      async def stream_response(
          self,
          prompt: str,
          model: str
      ) -> AsyncIterator[str]:
          # Wrapper implementation
          pass
  ```

- [ ] **Write integration tests**
  ```python
  # tests/test_rust_client.py
  import pytest
  from minimal_browser.ai.rust_client import RustAIClient
  
  @pytest.mark.asyncio
  async def test_rust_client_request():
      client = RustAIClient(api_key="test")
      response = await client.stream_response("test", "gpt-4")
      assert response is not None
  ```

## Phase 3: Benchmarking (Weeks 5-6)

### Week 5: Performance Testing

- [ ] **Create benchmark suite**
  ```python
  # benchmarks/ai_client_bench.py
  import time
  from minimal_browser.ai.client import PythonAIClient
  from minimal_browser.ai.rust_client import RustAIClient
  
  def benchmark_request(client, iterations=100):
      start = time.perf_counter()
      for i in range(iterations):
          # Send test request
          pass
      return (time.perf_counter() - start) / iterations
  
  python_time = benchmark_request(PythonAIClient())
  rust_time = benchmark_request(RustAIClient())
  print(f"Python: {python_time*1000:.2f}ms")
  print(f"Rust: {rust_time*1000:.2f}ms")
  print(f"Speedup: {python_time/rust_time:.2f}x")
  ```

- [ ] **Run benchmarks with different scenarios**
  - Small prompts (100 chars)
  - Medium prompts (1000 chars)
  - Large prompts (10000 chars)
  - Streaming vs non-streaming

- [ ] **Measure memory usage**
  ```bash
  pip install memray
  memray run --output rust_client.bin python -m minimal_browser
  memray flamegraph rust_client.bin
  ```

### Week 6: Decision Point

- [ ] **Compile results** in `docs/RUST_CLIENT_BENCHMARK.md`

- [ ] **Create comparison table**
  ```markdown
  | Metric              | Python | Rust | Improvement |
  |---------------------|--------|------|-------------|
  | Request latency     | 85ms   | 15ms | 5.7x        |
  | Memory overhead     | 12MB   | 2MB  | 6x          |
  | Cold start impact   | 0.8s   | 0.1s | 8x          |
  ```

- [ ] **Team decision: Go/No-Go**
  - If >3x improvement: Continue ✅
  - If 1-3x improvement: Consider ⚠️
  - If <1x improvement: Abort ❌

## Phase 4: Storage Module (Weeks 7-8)

_Only proceed if Phase 3 shows promising results_

### Week 7: SQLite Backend

- [ ] **Create Rust storage module**
  ```bash
  cd src_rust
  mkdir storage
  cd storage
  maturin init --bindings pyo3
  ```

- [ ] **Implement SQLite wrapper**
  ```rust
  // src_rust/storage/src/lib.rs
  use pyo3::prelude::*;
  use rusqlite::{Connection, Result};
  
  #[pyclass]
  struct ConversationStore {
      conn: Connection,
  }
  
  #[pymethods]
  impl ConversationStore {
      #[new]
      fn new(db_path: String) -> PyResult<Self> {
          let conn = Connection::open(db_path)
              .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(
                  format!("SQLite error: {}", e)
              ))?;
          
          // Create tables
          conn.execute(
              "CREATE TABLE IF NOT EXISTS conversations (
                  id INTEGER PRIMARY KEY,
                  timestamp INTEGER,
                  prompt TEXT,
                  response TEXT,
                  model TEXT
              )",
              [],
          ).unwrap();
          
          Ok(ConversationStore { conn })
      }
      
      fn add_conversation(
          &mut self,
          prompt: String,
          response: String,
          model: String,
      ) -> PyResult<i64> {
          // Implementation
          Ok(0)
      }
      
      fn search_conversations(
          &self,
          query: String,
          limit: i32,
      ) -> PyResult<Vec<(i64, String, String)>> {
          // Implementation
          Ok(vec![])
      }
  }
  ```

### Week 8: Migration & Testing

- [ ] **Create migration script**
  ```python
  # scripts/migrate_to_sqlite.py
  import json
  from storage_rust import ConversationStore
  
  def migrate_json_to_sqlite(json_path, db_path):
      store = ConversationStore(db_path)
      with open(json_path) as f:
          data = json.load(f)
      
      for conv in data["conversations"]:
          store.add_conversation(
              conv["prompt"],
              conv["response"],
              conv["model"]
          )
  ```

- [ ] **Add backward compatibility**
  ```python
  # src/minimal_browser/storage/conversations.py
  try:
      from storage_rust import ConversationStore as _RustStore
      USE_RUST = True
  except ImportError:
      USE_RUST = False
  
  class ConversationLog:
      def __init__(self, path):
          if USE_RUST:
              self._store = _RustStore(path)
          else:
              self._store = JSONStore(path)
  ```

## Phase 5: Build & Distribution (Weeks 9-10)

### Week 9: Build System

- [ ] **Update pyproject.toml**
  ```toml
  [build-system]
  requires = ["maturin>=1.7,<2.0"]
  build-backend = "maturin"
  
  [project.optional-dependencies]
  rust_modules = [
      "ai_rust_client",
      "storage_rust"
  ]
  ```

- [ ] **Set up CI/CD**
  ```yaml
  # .github/workflows/build-rust.yml
  name: Build Rust Modules
  
  on: [push, pull_request]
  
  jobs:
    build:
      runs-on: ${{ matrix.os }}
      strategy:
        matrix:
          os: [ubuntu-latest, macos-latest, windows-latest]
          python-version: ["3.12", "3.13"]
      
      steps:
        - uses: actions/checkout@v3
        - uses: actions/setup-python@v4
          with:
            python-version: ${{ matrix.python-version }}
        - uses: actions-rs/toolchain@v1
          with:
            toolchain: stable
        - name: Build wheels
          run: |
            pip install maturin
            cd src_rust/ai_client && maturin build --release
            cd ../storage && maturin build --release
  ```

### Week 10: Packaging

- [ ] **Build wheels for distribution**
  ```bash
  maturin build --release --out dist/
  ```

- [ ] **Test installation**
  ```bash
  pip install dist/ai_rust_client-*.whl
  pip install dist/storage_rust-*.whl
  python -c "import ai_rust_client; import storage_rust"
  ```

- [ ] **Update installation docs**

## Phase 6: Documentation (Weeks 11-12)

### Week 11: Developer Docs

- [ ] **Write development guide** (`docs/RUST_MODULES_DEV.md`)
  - How to build Rust modules
  - How to add new Rust functions
  - Debugging tips
  - Performance guidelines

- [ ] **Document API**
  ```python
  # Auto-generate from docstrings
  from ai_rust_client import AIClient
  help(AIClient)
  ```

### Week 12: User Docs & Release

- [ ] **Update README.md**
  - Mention Rust module benefits
  - Installation instructions
  - Performance improvements

- [ ] **Write migration guide**
  - How to enable Rust modules
  - Backward compatibility notes
  - Troubleshooting

- [ ] **Create release notes**

- [ ] **Tag release**
  ```bash
  git tag -a v0.3.0-rust-modules -m "Add Rust native modules"
  git push origin v0.3.0-rust-modules
  ```

## Success Metrics

Track these metrics throughout implementation:

| Metric | Baseline | Target | Actual |
|--------|----------|--------|--------|
| AI request latency | 85ms | <30ms | _TBD_ |
| Cold start time | 4.2s | <3s | _TBD_ |
| Memory usage | 165MB | <135MB | _TBD_ |
| Storage query time | 45ms | <5ms | _TBD_ |
| Binary size | 285MB | <250MB | _TBD_ |

## Rollback Plan

If at any phase the results are unsatisfactory:

1. **Phase 3 (Benchmarking)**: Abandon if <2x improvement
2. **Phase 4 (Storage)**: Can skip storage module, keep AI client only
3. **Any phase**: All Rust modules are optional - can disable via feature flags

## Resources

- **PyO3 Book**: https://pyo3.rs/
- **maturin Guide**: https://www.maturin.rs/
- **Rust Async Book**: https://rust-lang.github.io/async-book/
- **reqwest Docs**: https://docs.rs/reqwest/
- **rusqlite Docs**: https://docs.rs/rusqlite/

## Getting Help

- Open issue with `rust-modules` label
- Tag @maintainer for Rust-specific questions
- PyO3 Discord: https://discord.gg/rust-lang

---

**Checklist Status**: 0/90 completed  
**Last Updated**: 2025-01-XX  
**Next Review**: After Phase 3 (Week 6)
