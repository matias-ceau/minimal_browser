"""Qt WebEngine implementation"""

from typing import Callable
from .base import WebEngine

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
    from PySide6.QtCore import QUrl
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False


class QtWebEngine(WebEngine):
    """Qt WebEngine implementation"""
    
    def __init__(self):
        if not QT_AVAILABLE:
            raise ImportError("Qt WebEngine not available")
        
        self._widget = None
        self._dev_tools = None
    
    def create_widget(self) -> QWebEngineView:
        """Create Qt web view widget"""
        print("Initializing QWebEngineView...")
        
        try:
            self._widget = QWebEngineView()
            print("QWebEngineView created successfully")
            
            self.configure_settings()
            print("WebEngine settings configured")
            
            # Configure profile
            profile = QWebEngineProfile.defaultProfile()
            profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
            profile.setHttpCacheMaximumSize(50 * 1024 * 1024)  # 50MB cache
            print("WebEngine profile configured")
            
        except Exception as e:
            print(f"WebEngine initialization error: {e}")
            # Fallback: create a basic web view without advanced settings
            self._widget = QWebEngineView()
        
        return self._widget
    
    def load_url(self, url: str):
        """Load a URL"""
        if self._widget:
            print(f"Loading URL: {url[:100]}...")
            
            # Handle data URLs differently
            if url.startswith('data:'):
                qurl = QUrl(url)
                print(f"Loading data URL, length: {len(url)}")
            else:
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                qurl = QUrl(url)
            
            self._widget.load(qurl)
    
    def reload(self):
        """Reload current page"""
        if self._widget:
            self._widget.reload()
    
    def go_back(self):
        """Navigate back"""
        if self._widget:
            self._widget.back()
    
    def go_forward(self):
        """Navigate forward"""
        if self._widget:
            self._widget.forward()
    
    def find_text(self, text: str):
        """Find text in page"""
        if self._widget and text:
            self._widget.findText(text)
    
    def get_html(self, callback: Callable[[str], None]):
        """Get page HTML asynchronously"""
        if self._widget:
            self._widget.page().toHtml(callback)
    
    def get_url(self) -> str:
        """Get current URL"""
        if self._widget:
            return self._widget.url().toString()
        return ""
    
    def set_load_started_callback(self, callback: Callable[[], None]):
        """Set callback for load started"""
        if self._widget:
            self._widget.loadStarted.connect(callback)
    
    def set_load_progress_callback(self, callback: Callable[[int], None]):
        """Set callback for load progress"""
        if self._widget:
            self._widget.loadProgress.connect(callback)
    
    def set_load_finished_callback(self, callback: Callable[[bool], None]):
        """Set callback for load finished"""
        if self._widget:
            self._widget.loadFinished.connect(callback)
    
    def run_javascript(self, script: str):
        """Execute JavaScript"""
        if self._widget:
            self._widget.page().runJavaScript(script)
    
    def configure_settings(self):
        """Configure Qt WebEngine settings"""
        if not self._widget:
            return
        
        settings = self._widget.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.XSSAuditingEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.SpatialNavigationEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.HyperlinkAuditingEnabled, False)
    
    def toggle_dev_tools(self):
        """Toggle developer tools"""
        if not self._widget:
            return
        
        page = self._widget.page()
        if hasattr(page, 'setDevToolsPage'):
            # Create dev tools window if it doesn't exist
            if not self._dev_tools:
                from PySide6.QtWebEngineWidgets import QWebEngineView
                self._dev_tools = QWebEngineView()
                self._dev_tools.setWindowTitle("Developer Tools")
                self._dev_tools.resize(800, 600)
                page.setDevToolsPage(self._dev_tools.page())
            
            # Toggle visibility
            if self._dev_tools.isVisible():
                self._dev_tools.hide()
            else:
                self._dev_tools.show()
        else:
            print("Developer tools not available in this Qt version")
    
    @property
    def engine_name(self) -> str:
        """Get engine name"""
        return "Qt WebEngine"
    
    @property
    def supports_dev_tools(self) -> bool:
        """Check if engine supports developer tools"""
        return True