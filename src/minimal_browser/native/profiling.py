"""Performance profiling utilities for identifying optimization opportunities."""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Callable, Dict, List, Any
from functools import wraps


class PerformanceProfiler:
    """Simple performance profiler for measuring function execution times."""

    def __init__(self):
        self.measurements: Dict[str, List[float]] = {}
        self.call_counts: Dict[str, int] = {}

    @contextmanager
    def measure(self, operation: str):
        """Context manager for measuring operation duration.

        Usage:
            with profiler.measure("my_operation"):
                # code to measure
                pass
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            if operation not in self.measurements:
                self.measurements[operation] = []
                self.call_counts[operation] = 0
            self.measurements[operation].append(duration)
            self.call_counts[operation] += 1

    def profile_function(self, func: Callable) -> Callable:
        """Decorator for profiling function calls.

        Usage:
            @profiler.profile_function
            def my_function():
                pass
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.measure(func.__name__):
                return func(*args, **kwargs)

        return wrapper

    def get_stats(self, operation: str) -> Dict[str, Any]:
        """Get statistics for an operation."""
        if operation not in self.measurements:
            return {}

        times = self.measurements[operation]
        return {
            "count": self.call_counts[operation],
            "total": sum(times),
            "mean": sum(times) / len(times),
            "min": min(times),
            "max": max(times),
        }

    def print_report(self):
        """Print a formatted report of all measurements."""
        if not self.measurements:
            print("No measurements recorded")
            return

        print("\n" + "=" * 80)
        print("PERFORMANCE PROFILING REPORT")
        print("=" * 80)

        for operation in sorted(self.measurements.keys()):
            stats = self.get_stats(operation)
            print(f"\n{operation}:")
            print(f"  Calls:        {stats['count']}")
            print(f"  Total time:   {stats['total']:.6f}s")
            print(f"  Mean time:    {stats['mean']:.6f}s")
            print(f"  Min time:     {stats['min']:.6f}s")
            print(f"  Max time:     {stats['max']:.6f}s")

        print("\n" + "=" * 80 + "\n")

    def reset(self):
        """Clear all measurements."""
        self.measurements.clear()
        self.call_counts.clear()


# Global profiler instance (can be disabled in production)
_global_profiler = PerformanceProfiler()


def get_profiler() -> PerformanceProfiler:
    """Get the global profiler instance."""
    return _global_profiler
