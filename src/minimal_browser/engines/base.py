"""Abstract base class for web engines"""

from abc import ABC, abstractmethod
from typing import Callable, Any


class WebEngine(ABC):
    """Abstract web engine interface"""
    
    @abstractmethod
    def create_widget(self) -> Any:
        """Create the web view widget"""
        pass
    
    @abstractmethod
    def load_url(self, url: str):
        """Load a URL"""
        pass
    
    @abstractmethod
    def reload(self):
        """Reload current page"""
        pass
    
    @abstractmethod
    def go_back(self):
        """Navigate back"""
        pass
    
    @abstractmethod
    def go_forward(self):
        """Navigate forward"""
        pass
    
    @abstractmethod
    def find_text(self, text: str):
        """Find text in page"""
        pass
    
    @abstractmethod
    def get_html(self, callback: Callable[[str], None]):
        """Get page HTML asynchronously"""
        pass
    
    @abstractmethod
    def get_url(self) -> str:
        """Get current URL"""
        pass
    
    @abstractmethod
    def set_load_started_callback(self, callback: Callable[[], None]):
        """Set callback for load started"""
        pass
    
    @abstractmethod
    def set_load_progress_callback(self, callback: Callable[[int], None]):
        """Set callback for load progress"""
        pass
    
    @abstractmethod
    def set_load_finished_callback(self, callback: Callable[[bool], None]):
        """Set callback for load finished"""
        pass
    
    @abstractmethod
    def run_javascript(self, script: str):
        """Execute JavaScript"""
        pass
    
    @abstractmethod
    def configure_settings(self):
        """Configure engine-specific settings"""
        pass
    
    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Get engine name"""
        pass
    
    @property
    @abstractmethod
    def supports_dev_tools(self) -> bool:
        """Check if engine supports developer tools"""
        pass