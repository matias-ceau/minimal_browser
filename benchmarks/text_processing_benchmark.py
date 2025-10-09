"""Benchmark tests for identifying CPU-intensive operations.

This module provides benchmarks to measure the performance of text processing
operations and identify candidates for native module optimization.

Run with: python -m benchmarks.text_processing_benchmark
"""

from __future__ import annotations

import time
import re
from typing import Callable, Dict, Any


def benchmark_operation(func: Callable, iterations: int = 1000) -> Dict[str, Any]:
    """Benchmark a function over multiple iterations."""
    start = time.perf_counter()
    for _ in range(iterations):
        func()
    elapsed = time.perf_counter() - start

    return {
        "iterations": iterations,
        "total_time": elapsed,
        "avg_time": elapsed / iterations,
        "ops_per_second": iterations / elapsed if elapsed > 0 else 0,
    }


def benchmark_regex_patterns():
    """Benchmark regex pattern matching operations."""
    # Sample text similar to AI responses
    text = """
    Navigate to https://github.com and search for Python projects.
    Create a todo list with items for: code review, testing, and deployment.
    Make a calculator that can handle complex expressions.
    Visit example.com or go to mozilla.org for documentation.
    """

    patterns = [
        r"(?:navigate|go|open|visit)\s+(?:to\s+)?([^\s]+\.[a-z]{2,})",
        r"(?:open|visit)\s+([a-z]+\.com|[a-z]+\.org|[a-z]+\.net)",
        r'(?:search for|find|look up)\s+"?([^"]+)"?',
    ]

    def run_patterns():
        for pattern in patterns:
            re.search(pattern, text.lower())

    return benchmark_operation(run_patterns, 10000)


def benchmark_string_contains():
    """Benchmark string contains operations."""
    text = "create a todo list with multiple items and features"
    keywords = {
        "create",
        "make",
        "generate",
        "build",
        "design",
        "todo",
        "calculator",
        "form",
        "page",
        "website",
    }

    def check_contains():
        text_lower = text.lower()
        any(keyword in text_lower for keyword in keywords)

    return benchmark_operation(check_contains, 50000)


def benchmark_markdown_conversion():
    """Benchmark markdown to HTML conversion."""
    text = """
    This is **bold text** and this is *italic text*.
    More **formatting** with *multiple* instances.
    **Another** bold and *another* italic.
    Regular text with **nested** and *mixed* formatting.
    """

    def convert_markdown():
        result = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
        result = re.sub(r"\*(.*?)\*", r"<em>\1</em>", result)
        return result

    return benchmark_operation(convert_markdown, 10000)


def benchmark_base64_encoding():
    """Benchmark base64 encoding operations."""
    import base64

    # Large HTML content similar to AI-generated responses
    html_content = """
    <!DOCTYPE html>
    <html>
    <head><title>Test</title></head>
    <body>
    """ + (
        "<p>Sample paragraph with content.</p>\n" * 100
    ) + """
    </body>
    </html>
    """

    def encode_content():
        base64.b64encode(html_content.encode("utf-8")).decode("ascii")

    return benchmark_operation(encode_content, 5000)


def run_all_benchmarks():
    """Run all benchmarks and print results."""
    print("\n" + "=" * 80)
    print("TEXT PROCESSING PERFORMANCE BENCHMARKS")
    print("=" * 80 + "\n")

    benchmarks = {
        "Regex Pattern Matching": benchmark_regex_patterns,
        "String Contains Check": benchmark_string_contains,
        "Markdown to HTML": benchmark_markdown_conversion,
        "Base64 Encoding": benchmark_base64_encoding,
    }

    results = {}
    for name, bench_func in benchmarks.items():
        print(f"Running: {name}...")
        result = bench_func()
        results[name] = result

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80 + "\n")

    for name, result in results.items():
        print(f"{name}:")
        print(f"  Iterations:     {result['iterations']:,}")
        print(f"  Total time:     {result['total_time']:.6f}s")
        print(f"  Avg time:       {result['avg_time']:.9f}s")
        print(f"  Ops/second:     {result['ops_per_second']:,.2f}")
        print()

    # Identify optimization candidates
    print("=" * 80)
    print("OPTIMIZATION CANDIDATES")
    print("=" * 80 + "\n")

    sorted_results = sorted(results.items(), key=lambda x: x[1]["avg_time"], reverse=True)

    print("Operations ranked by average execution time (slowest first):\n")
    for i, (name, result) in enumerate(sorted_results, 1):
        print(f"{i}. {name}: {result['avg_time']:.9f}s per operation")

    print(
        "\nRecommendation: Consider native module optimization for top operations.\n"
    )


if __name__ == "__main__":
    run_all_benchmarks()
