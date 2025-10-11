"""Shared test utilities for importing modules without PySide6."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def get_src_dir() -> Path:
    """Get the src/minimal_browser directory."""
    test_dir = Path(__file__).parent
    return test_dir.parent / "src" / "minimal_browser"


def import_module_bypass_init(module_path: str, module_name: str = None):
    """Import a module directly from file path, bypassing package __init__.py.
    
    This is useful for testing modules that are part of packages with heavy
    dependencies (like PySide6) that aren't needed for the specific module.
    
    Args:
        module_path: Path to the .py file relative to src/minimal_browser
        module_name: Optional module name (defaults to filename without .py)
        
    Returns:
        The imported module
    """
    src_dir = get_src_dir()
    file_path = src_dir / module_path
    
    if module_name is None:
        module_name = file_path.stem
        
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {file_path}")
        
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
