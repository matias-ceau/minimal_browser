"""Native module optimizations for CPU-intensive operations.

This module provides optional native (Rust/C) implementations of CPU-intensive
operations with automatic fallback to pure Python when native modules are unavailable.
"""

from .text_processor import TextProcessor

__all__ = ["TextProcessor"]
