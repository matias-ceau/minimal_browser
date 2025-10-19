#!/usr/bin/env python3
"""Example script demonstrating native module optimization usage.

This script shows how the optimization system works and how to measure
performance improvements.
"""

import sys
import os
import time
import importlib.util

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path without importing __init__.py."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {module_name} from {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Import modules directly to avoid PySide6 dependency
base_path = os.path.join(os.path.dirname(__file__), "..", "src", "minimal_browser")
TextProcessor = import_module_from_path(
    "text_processor", os.path.join(base_path, "native", "text_processor.py")
).TextProcessor

profiling_module = import_module_from_path(
    "profiling", os.path.join(base_path, "native", "profiling.py")
)
get_profiler = profiling_module.get_profiler


def demo_url_extraction():
    """Demonstrate optimized URL extraction."""
    print("\n" + "=" * 80)
    print("URL EXTRACTION DEMO")
    print("=" * 80)

    texts = [
        "Navigate to github.com for source code",
        "Visit example.com or check mozilla.org",
        "Go to python.org for documentation",
    ]

    pattern = r"(?:navigate|go|visit)\s+(?:to\s+)?([^\s]+\.[a-z]{2,})"

    profiler = get_profiler()

    for text in texts:
        with profiler.measure("url_extraction"):
            url = TextProcessor.extract_url_from_text(text.lower(), pattern)
        print(f"Text: {text}")
        print(f"  -> Extracted: {url}")

    print("\nPerformance:")
    stats = profiler.get_stats("url_extraction")
    print(f"  Total time: {stats['total']:.6f}s")
    print(f"  Mean time:  {stats['mean']:.9f}s")


def demo_keyword_detection():
    """Demonstrate optimized keyword detection."""
    print("\n" + "=" * 80)
    print("KEYWORD DETECTION DEMO")
    print("=" * 80)

    texts = [
        "Create a todo list with items",
        "Some random text",
        "Generate a report",
        "Build a new feature",
    ]

    keywords = {"create", "make", "generate", "build", "design"}

    profiler = get_profiler()

    for text in texts:
        with profiler.measure("keyword_detection"):
            has_keyword = TextProcessor.fast_string_contains(text, keywords)
        print(f"Text: {text}")
        print(f"  -> Has keyword: {has_keyword}")

    print("\nPerformance:")
    stats = profiler.get_stats("keyword_detection")
    print(f"  Total time: {stats['total']:.6f}s")
    print(f"  Mean time:  {stats['mean']:.9f}s")


def demo_markdown_conversion():
    """Demonstrate optimized markdown to HTML conversion."""
    print("\n" + "=" * 80)
    print("MARKDOWN TO HTML DEMO")
    print("=" * 80)

    texts = [
        "This is **bold** text",
        "This is *italic* text",
        "Mix **bold** and *italic* formatting",
    ]

    profiler = get_profiler()

    for text in texts:
        with profiler.measure("markdown_conversion"):
            html = TextProcessor.markdown_to_html(text)
        print(f"Markdown: {text}")
        print(f"  -> HTML: {html}")

    print("\nPerformance:")
    stats = profiler.get_stats("markdown_conversion")
    print(f"  Total time: {stats['total']:.6f}s")
    print(f"  Mean time:  {stats['mean']:.9f}s")


def demo_base64_encoding():
    """Demonstrate optimized base64 encoding."""
    print("\n" + "=" * 80)
    print("BASE64 ENCODING DEMO")
    print("=" * 80)

    data_samples = [
        b"Short text",
        b"Medium length text " * 10,
        b"Long text content " * 100,
    ]

    profiler = get_profiler()

    for i, data in enumerate(data_samples, 1):
        with profiler.measure("base64_encoding"):
            encoded = TextProcessor.base64_encode_optimized(data)
        print(f"Sample {i} ({len(data)} bytes):")
        print(f"  -> Encoded length: {len(encoded)} characters")

    print("\nPerformance:")
    stats = profiler.get_stats("base64_encoding")
    print(f"  Total time: {stats['total']:.6f}s")
    print(f"  Mean time:  {stats['mean']:.9f}s")


def demo_performance_comparison():
    """Compare pure Python vs optimized implementations."""
    print("\n" + "=" * 80)
    print("PERFORMANCE COMPARISON")
    print("=" * 80)

    # Simulate workload similar to actual usage
    texts = [
        "Navigate to github.com and search for Python projects",
        "Create a todo list with items",
        "Generate a report with **bold** headings",
    ] * 100

    keywords = {"create", "make", "generate", "build", "design"}
    pattern = r"(?:navigate|go)\s+(?:to\s+)?([^\s]+\.[a-z]{2,})"

    print(f"\nProcessing {len(texts)} text samples...")

    start = time.perf_counter()
    for text in texts:
        TextProcessor.extract_url_from_text(text.lower(), pattern)
        TextProcessor.fast_string_contains(text, keywords)
        TextProcessor.markdown_to_html(text)
    elapsed = time.perf_counter() - start

    print(f"Total time: {elapsed:.6f}s")
    print(f"Throughput: {len(texts) / elapsed:.2f} samples/second")

    # Check if native module is being used
    if TextProcessor._check_native_module():
        print("\n✓ Using NATIVE module (optimized)")
    else:
        print("\n○ Using PURE PYTHON (fallback)")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 80)
    print("MINIMAL BROWSER - NATIVE MODULE OPTIMIZATION DEMO")
    print("=" * 80)

    # Check if native module is available
    print("\nChecking for native module...")
    if TextProcessor._check_native_module():
        print("✓ Native module (minimal_browser_native) is AVAILABLE")
        print("  Performance-critical operations will use optimized implementations")
    else:
        print("○ Native module is NOT available")
        print("  Using pure Python fallback (still functional, just slower)")
        print("\n  To enable native optimizations:")
        print("    cd native_extensions")
        print("    pip install maturin")
        print("    maturin develop")

    # Run demonstrations
    demo_url_extraction()
    demo_keyword_detection()
    demo_markdown_conversion()
    demo_base64_encoding()
    demo_performance_comparison()

    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print("\nFor more details, see:")
    print("  - NATIVE_OPTIMIZATION.md")
    print("  - src/minimal_browser/native/README.md")
    print("  - native_extensions/README.md")
    print()


if __name__ == "__main__":
    main()
