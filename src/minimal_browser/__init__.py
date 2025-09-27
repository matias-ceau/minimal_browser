"""
Minimal Browser - A vim-like browser with native AI integration
"""

# Only import main components when PySide6 is available
try:
    from .minimal_browser import VimBrowser
    from .main import main
    __all__ = ["VimBrowser", "main"]
except ImportError:
    # Allow importing submodules even without PySide6
    __all__ = []