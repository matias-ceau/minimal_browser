# Native Module Optimization - Quick Start

This directory contains benchmarking and testing tools for the native module optimization system.

## Quick Demo

Run the interactive demo to see the optimization system in action:

```bash
python3 benchmarks/demo_optimizations.py
```

This will:
- Check if native modules are available
- Demonstrate optimized operations
- Show performance metrics
- Compare throughput with/without native modules

## Benchmarking

Run comprehensive benchmarks to identify optimization candidates:

```bash
python3 -m benchmarks.text_processing_benchmark
```

Results show operations ranked by execution time (slowest first):
1. Base64 Encoding (~4.7μs per operation)
2. Regex Pattern Matching (~4.5μs per operation)
3. Markdown to HTML (~4.2μs per operation)
4. String Contains Check (~0.5μs per operation)

## Testing

Run integration tests to verify optimizations work correctly:

```bash
python3 benchmarks/test_native_integration.py
```

Tests verify:
- URL extraction from text
- Fast keyword detection
- Markdown to HTML conversion
- Base64 encoding
- Integration with browser components

## Files

- `demo_optimizations.py` - Interactive demonstration of optimizations
- `text_processing_benchmark.py` - Performance benchmarking suite
- `test_native_integration.py` - Integration tests

## Enabling Native Optimizations

The system works with pure Python by default. To enable native (Rust) optimizations:

```bash
# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install maturin (Rust-Python bridge)
pip install maturin

# Build and install native module
cd native_extensions
maturin develop
cd ..

# Verify it works
python3 benchmarks/demo_optimizations.py
```

You should see: "✓ Native module (minimal_browser_native) is AVAILABLE"

## Expected Performance Improvements

With native modules enabled:

| Operation              | Python     | Rust (Expected) | Speedup |
|------------------------|------------|-----------------|---------|
| Regex Pattern Matching | 221K ops/s | 500K-1M ops/s   | 2-5x    |
| Base64 Encoding        | 214K ops/s | 640K-2M ops/s   | 3-10x   |
| Markdown to HTML       | 236K ops/s | 500K-1M ops/s   | 2-4x    |
| String Contains        | 1.96M ops/s| 3M-6M ops/s     | 1.5-3x  |

## Documentation

For more details, see:
- `../NATIVE_OPTIMIZATION.md` - Complete optimization guide
- `../src/minimal_browser/native/README.md` - Integration guide
- `../native_extensions/README.md` - Rust extension build guide

## Development Workflow

1. **Profile first**: Run benchmarks to identify slow operations
2. **Implement Python**: Add fallback implementation
3. **Add tests**: Verify correctness
4. **Implement native**: Add Rust optimization
5. **Measure**: Compare before/after performance

## Contributing

When adding new optimizations:
1. Add benchmark in `text_processing_benchmark.py`
2. Add test in `test_native_integration.py`
3. Update `demo_optimizations.py` if appropriate
4. Document expected performance improvements

## Architecture

```
Pure Python (default)
  ↓
TextProcessor methods
  ↓
Check for native module
  ↓
  ├─→ Native available: Use Rust implementation
  └─→ Native unavailable: Use Python fallback
```

Key principle: **Transparent fallback** - code works everywhere, optimizations are optional.
