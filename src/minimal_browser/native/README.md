# Native Module Optimization Guide

This guide explains the native module optimization infrastructure for Minimal Browser and how to integrate Rust or C extensions for CPU-intensive operations.

## Overview

The browser includes an optional native module system that allows performance-critical operations to be implemented in Rust or C, with automatic fallback to pure Python when native modules are unavailable.

## Architecture

```
src/minimal_browser/native/
├── __init__.py           # Module exports
├── text_processor.py     # Optimized text operations with native fallback
├── profiling.py          # Performance profiling utilities
└── README.md            # This file

benchmarks/
└── text_processing_benchmark.py  # Performance benchmarks
```

## Design Principles

1. **Transparent Fallback**: All native operations have pure Python implementations
2. **Zero Dependencies**: Native modules are optional; the browser works without them
3. **Profiling-Driven**: Optimize only operations identified as bottlenecks
4. **Minimal Interface**: Keep the native/Python boundary simple and clean

## Performance Profiling

### Running Benchmarks

Identify optimization candidates by running the benchmark suite:

```bash
python -m benchmarks.text_processing_benchmark
```

This will measure:
- Regex pattern matching (AI response parsing)
- String contains operations (keyword detection)
- Markdown to HTML conversion
- Base64 encoding (data URL generation)

### Using the Profiler in Code

```python
from minimal_browser.native.profiling import get_profiler

profiler = get_profiler()

# Option 1: Context manager
with profiler.measure("my_operation"):
    # code to profile
    pass

# Option 2: Decorator
@profiler.profile_function
def my_function():
    pass

# Print report
profiler.print_report()
```

## Using Optimized Text Operations

The `TextProcessor` class provides optimized implementations:

```python
from minimal_browser.native import TextProcessor

# Extract URL from text
url = TextProcessor.extract_url_from_text(
    "Navigate to example.com",
    r"(?:navigate|go|open)\s+(?:to\s+)?([^\s]+\.[a-z]{2,})"
)

# Check for keywords
has_keyword = TextProcessor.fast_string_contains(
    "create a todo list",
    {"create", "make", "generate"}
)

# Convert markdown to HTML
html = TextProcessor.markdown_to_html("**bold** and *italic*")

# Optimized base64 encoding
encoded = TextProcessor.base64_encode_optimized(b"content")
```

## Future: Adding Rust Extensions

### Prerequisites

```bash
pip install maturin  # Rust-Python bridge
```

### Project Structure

```
native_extensions/
├── Cargo.toml
├── src/
│   └── lib.rs
└── pyproject.toml
```

### Example Rust Implementation

**Cargo.toml:**
```toml
[package]
name = "minimal_browser_native"
version = "0.1.0"
edition = "2021"

[lib]
name = "minimal_browser_native"
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.20", features = ["extension-module"] }
regex = "1.10"
base64 = "0.21"
```

**src/lib.rs:**
```rust
use pyo3::prelude::*;
use regex::Regex;

#[pyfunction]
fn extract_url(text: &str, pattern: &str) -> PyResult<Option<String>> {
    let re = Regex::new(pattern).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Invalid regex: {}", e))
    })?;
    
    Ok(re.captures(&text.to_lowercase())
        .and_then(|cap| cap.get(1))
        .map(|m| m.as_str().to_string()))
}

#[pyfunction]
fn base64_encode(data: &[u8]) -> String {
    base64::encode(data)
}

#[pymodule]
fn minimal_browser_native(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(extract_url, m)?)?;
    m.add_function(wrap_pyfunction!(base64_encode, m)?)?;
    Ok(())
}
```

### Building

```bash
cd native_extensions
maturin develop  # Development build
maturin build --release  # Production build
```

### Integration

The `TextProcessor` class automatically detects and uses the native module when available:

```python
# In text_processor.py
try:
    import minimal_browser_native
    cls._native_module = minimal_browser_native
    cls._native_available = True
except ImportError:
    cls._native_available = False
```

## Optimization Candidates

Based on profiling, these operations are candidates for native optimization:

### High Priority
1. **Regex Pattern Matching** (ResponseProcessor._intelligent_parse)
   - Multiple regex operations per AI response
   - Rust's `regex` crate is highly optimized

2. **Base64 Encoding** (create_data_url)
   - Large HTML content encoding
   - Rust's `base64` crate is faster than Python

### Medium Priority
3. **Markdown Conversion** (wrap_content_as_html)
   - Frequent regex substitutions
   - Could use specialized parser

4. **String Contains** (keyword detection)
   - Multiple substring searches
   - Could use optimized trie/hash structure

## Performance Expectations

Expected speedup with native modules (based on typical benchmarks):

- Regex operations: 2-5x faster
- Base64 encoding: 3-10x faster (depending on data size)
- Markdown conversion: 2-4x faster
- String contains: 1.5-3x faster

## Distribution

### Option 1: Optional Wheels
Distribute pre-built wheels for common platforms:
- `minimal-browser[native]` - includes native extensions
- `minimal-browser` - pure Python only

### Option 2: Runtime Compilation
Include Rust source and compile during installation if Rust toolchain is available.

### Option 3: Pure Python Default
Ship pure Python by default; users can manually install native modules.

**Recommendation**: Start with Option 3 (current implementation) and add Option 1 if performance improvements prove significant.

## Testing

Ensure native and Python implementations produce identical results:

```python
def test_text_processor_consistency():
    text = "Navigate to example.com"
    pattern = r"(?:navigate|go)\s+(?:to\s+)?([^\s]+\.[a-z]{2,})"
    
    # Force pure Python
    TextProcessor._native_available = False
    python_result = TextProcessor.extract_url_from_text(text, pattern)
    
    # Use native if available
    TextProcessor._native_available = None
    native_result = TextProcessor.extract_url_from_text(text, pattern)
    
    assert python_result == native_result
```

## References

- [PyO3 Documentation](https://pyo3.rs/) - Rust-Python bindings
- [Maturin](https://github.com/PyO3/maturin) - Build and publish Rust Python packages
- [pybind11](https://github.com/pybind/pybind11) - C++ alternative to PyO3
