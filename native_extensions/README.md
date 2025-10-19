# Native Extensions

This directory contains optional Rust extensions for performance-critical operations.

## Building

### Prerequisites

Install Rust and maturin:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
pip install maturin
```

### Development Build

```bash
cd native_extensions
maturin develop
```

This compiles the Rust code and installs it into your Python environment.

### Release Build

```bash
maturin build --release
```

Creates optimized wheel in `target/wheels/`.

## Testing

Run Rust tests:
```bash
cargo test
```

Run integration tests:
```bash
cd ..
python3 benchmarks/test_native_integration.py
```

## Benchmarking

Compare native vs Python performance:
```bash
cd ..
python3 -m benchmarks.text_processing_benchmark
```

## Usage

Once installed, the native module is automatically detected and used:

```python
from minimal_browser.native import TextProcessor

# Automatically uses native implementation if available
result = TextProcessor.extract_url_from_text(text, pattern)
```

## Distribution

### Option 1: Source Distribution
Ship source code and compile during installation if Rust is available.

### Option 2: Pre-built Wheels
Build wheels for common platforms:
```bash
# Linux
docker run --rm -v $(pwd):/io konstin2/maturin build --release

# macOS
maturin build --release --target aarch64-apple-darwin
maturin build --release --target x86_64-apple-darwin

# Windows
maturin build --release --target x86_64-pc-windows-msvc
```

### Option 3: Conditional Installation
Make native extensions optional:
```bash
pip install minimal-browser              # Pure Python
pip install minimal-browser[native]      # With native optimizations
```
