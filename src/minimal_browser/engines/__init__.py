"""Web engine abstraction layer"""

from .base import WebEngine
from .qt_engine import QtWebEngine

# Auto-detect available engines
AVAILABLE_ENGINES = {}

try:
    from .qt_engine import QtWebEngine
    AVAILABLE_ENGINES['qt'] = QtWebEngine
except ImportError:
    pass

try:
    from .gtk_engine import GtkWebEngine
    AVAILABLE_ENGINES['gtk'] = GtkWebEngine
except ImportError:
    pass

# Default engine preference
DEFAULT_ENGINE = 'qt' if 'qt' in AVAILABLE_ENGINES else 'gtk'

def get_engine(engine_type: str = None) -> WebEngine:
    """Get web engine instance"""
    if engine_type is None:
        engine_type = DEFAULT_ENGINE
    
    if engine_type not in AVAILABLE_ENGINES:
        raise ValueError(f"Engine '{engine_type}' not available. Available: {list(AVAILABLE_ENGINES.keys())}")
    
    return AVAILABLE_ENGINES[engine_type]()

__all__ = ["WebEngine", "get_engine", "AVAILABLE_ENGINES", "DEFAULT_ENGINE"]