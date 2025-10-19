# Tauri Overlay Proof of Concept

This proof of concept demonstrates how a lightweight Tauri companion window can run alongside the existing `minimal_browser` Qt shell. The goal is to prototype interactive overlays (AI dashboards, embedded web apps) without rewriting the entire UI stack.

## Overview

- **Host application**: PySide6/Qt (`minimal_browser`)
- **Overlay application**: Tauri (Rust + HTML/TypeScript)
- **IPC mechanism**: WebSocket bridge (JSON messages)
- **Use cases**: Floating command palette, contextual help, collaborative web tools

```text
Qt (PySide6) ──spawn──▶ Tauri binary
      ▲                      │
      │         JSON IPC     ▼
 overlay_bridge.py ◀──────────── Frontend (Vite/React, etc.)
```

## Prerequisites

- Rust toolchain with `cargo` and `tauri-cli`
- Node.js 18+ (for Vite/TypeScript frontend)
- Python 3.13 with `uv` (already required by `minimal_browser`)

Install the Tauri CLI if needed:

```bash
cargo install tauri-cli
```

## 1. Scaffold the Tauri project

From the repository root:

```bash
cd examples/tauri_overlay_poc
cargo tauri init --ci --app-name minimal-overlay --window-title "Minimal Overlay"
```

Recommended configuration tweaks:

- Set `distDir` to `../frontend/dist` to allow custom build pipelines.
- Disable automatic devtools in `tauri.conf.json` for production.
- Use `transparent: true` and `decorations: false` on the main window to create a frameless overlay.

## 2. Frontend bootstrap (optional)

If you prefer Vite + React:

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

Expose a simple overlay view in `frontend/src/App.tsx`:

```tsx
import { listen } from '@tauri-apps/api/event';
import { useEffect, useState } from 'react';

export default function App() {
  const [payload, setPayload] = useState({ title: 'Overlay Ready', body: '' });

  useEffect(() => {
    const unlisten = listen('overlay:update', event => {
      setPayload(event.payload as typeof payload);
    });
    return () => {
      unlisten.then(dispose => dispose());
    };
  }, []);

  return (
    <div className="overlay">
      <h1>{payload.title}</h1>
      <p>{payload.body}</p>
    </div>
  );
}
```

Style the overlay via `frontend/src/App.css` for a translucent card.

## 3. Rust commands

Add a command that forwards messages from the Qt host to the frontend:

```rust
// src-tauri/src/main.rs

#[derive(Clone, serde::Serialize, serde::Deserialize)]
struct OverlayMessage {
    title: String,
    body: String,
}

#[tauri::command]
async fn push_overlay(window: tauri::Window, message: OverlayMessage) -> Result<(), String> {
    window
        .emit("overlay:update", message)
        .map_err(|e| format!("Emit failed: {e}"))
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![push_overlay])
        .run(tauri::generate_context!())
        .expect("failed to run minimal overlay");
}
```

## 4. Python bridge (experimental)

Use `overlay_bridge.py` to start the Tauri binary and push data over a WebSocket.

```python
from pathlib import Path
from subprocess import Popen

from overlay_bridge import OverlayBridge

tauri_binary = Path(__file__).parent / "target/release/minimal-overlay"
bridge = OverlayBridge(binary_path=tauri_binary)

with bridge.launch() as session:
    session.send({
        "title": "Overlay Connected",
        "body": "Greetings from PySide6!",
    })
```

Make sure to build the Tauri app first:

```bash
cd examples/tauri_overlay_poc
cargo tauri build
```

## 5. Integration hook (Qt)

In `minimal_browser/minimal_browser.py`, guard the PoC with a feature flag:

```python
if config.features.overlay_tauri:
    self.overlay = OverlayBridge(...)
    self.overlay.send({"title": "AI", "body": chunk})
```

The PoC intentionally avoids shipping production code; treat it as an experimentation sandbox.

## Cleanup

To stop the overlay automatically when the Qt window closes, rely on the context manager provided by `OverlayBridge`. The bridge will terminate the child process and close the WebSocket session when leaving the `with` block.

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Overlay window flashes white | Missing transparency flags | Set `transparent: true` and inject CSS background |
| WebSocket connection refused | Bridge not running | Launch `overlay_bridge.py` before calling commands |
| Tauri closes unexpectedly | Qt process exited | Use `bridge.launch()` context manager or call `bridge.close()` explicitly |

---

This PoC is designed to answer **“Can Tauri host overlay windows beside our Qt shell?”**. Once validated, promote the bridge into a dedicated module with error handling, authentication, and CI coverage.
