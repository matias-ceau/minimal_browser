"""GTK WebKit engine implementation.

This module provides a GTK-based web engine using WebKit for platforms
that prefer or require GTK over Qt. The implementation is feature-complete
but requires GTK 4.0 and WebKit 6.0 to be installed.

Installation:
    Debian/Ubuntu:
        sudo apt install gir1.2-webkit-6.0 python3-gi
    
    Arch Linux:
        sudo pacman -S webkit2gtk python-gobject
    
    Fedora/RHEL:
        sudo dnf install webkit2gtk4.1 python3-gobject

Usage:
    from minimal_browser.engines.gtk_engine import GtkWebEngine
    
    engine = GtkWebEngine()
    # Use with VimBrowser or other components

Note: This engine is an alternative to the Qt WebEngine and provides
similar functionality but with different system requirements. Qt WebEngine
is the default and recommended engine for most use cases.

Platform Support:
    - Linux: Full support with GTK 4.0/WebKit 6.0
    - macOS: Experimental (requires MacPorts or Homebrew GTK installation)
    - Windows: Not recommended (GTK on Windows has limited WebKit support)

Known Limitations:
    - Developer tools integration differs from Qt WebEngine
    - Some Qt-specific features may not be available
    - Requires separate GTK/WebKit system dependencies
"""

from typing import Callable
from .base import WebEngine

try:
    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("WebKit", "6.0")
    from gi.repository import WebKit

    GTK_AVAILABLE = True
except ImportError:
    GTK_AVAILABLE = False


class GtkWebEngine(WebEngine):
    """GTK WebKit engine implementation"""

    def __init__(self):
        if not GTK_AVAILABLE:
            raise ImportError("GTK WebKit not available")

        self._widget = None

    def create_widget(self):
        """Create GTK web view widget"""
        print("Initializing WebKit WebView...")

        self._widget = WebKit.WebView()
        self.configure_settings()

        print("WebKit WebView created successfully")
        return self._widget

    def load_url(self, url: str):
        """Load a URL"""
        if self._widget:
            print(f"Loading URL: {url[:100]}...")

            if not url.startswith(("http://", "https://", "data:")):
                url = "https://" + url

            self._widget.load_uri(url)

    def reload(self):
        """Reload current page"""
        if self._widget:
            self._widget.reload()

    def go_back(self):
        """Navigate back"""
        if self._widget:
            self._widget.go_back()

    def go_forward(self):
        """Navigate forward"""
        if self._widget:
            self._widget.go_forward()

    def find_text(self, text: str):
        """Find text in page"""
        if self._widget and text:
            find_controller = self._widget.get_find_controller()
            find_controller.search(text, WebKit.FindOptions.NONE, 100)

    def get_html(self, callback: Callable[[str], None]):
        """Get page HTML asynchronously"""
        if self._widget:

            def on_html_ready(source, result, user_data):
                try:
                    html = source.get_data_finish(result)
                    callback(html.get_data().decode("utf-8"))
                except Exception as e:
                    print(f"Error getting HTML: {e}")
                    callback("")

            self._widget.get_web_resource().get_data(None, on_html_ready, None)

    def get_url(self) -> str:
        """Get current URL"""
        if self._widget:
            return self._widget.get_uri() or ""
        return ""

    def set_load_started_callback(self, callback: Callable[[], None]):
        """Set callback for load started"""
        if self._widget:
            self._widget.connect(
                "load-changed",
                lambda webview, event: callback()
                if event == WebKit.LoadEvent.STARTED
                else None,
            )

    def set_load_progress_callback(self, callback: Callable[[int], None]):
        """Set callback for load progress"""
        if self._widget:
            self._widget.connect(
                "notify::estimated-load-progress",
                lambda webview, param: callback(
                    int(webview.get_estimated_load_progress() * 100)
                ),
            )

    def set_load_finished_callback(self, callback: Callable[[bool], None]):
        """Set callback for load finished"""
        if self._widget:
            self._widget.connect(
                "load-changed",
                lambda webview, event: callback(True)
                if event == WebKit.LoadEvent.FINISHED
                else None,
            )

    def run_javascript(self, script: str):
        """Execute JavaScript"""
        if self._widget:
            self._widget.evaluate_javascript(script, -1, None, None, None, None, None)

    def configure_settings(self):
        """Configure WebKit settings"""
        if not self._widget:
            return

        settings = self._widget.get_settings()
        settings.set_enable_javascript(True)
        settings.set_enable_plugins(False)
        settings.set_enable_local_storage(True)
        settings.set_hardware_acceleration_policy(
            WebKit.HardwareAccelerationPolicy.ALWAYS
        )

    def capture_screenshot(self, callback: Callable[[bytes], None]):
        """Capture a screenshot of the current page asynchronously
        
        Args:
            callback: Function to call with PNG image data as bytes
            
        Note:
            GTK WebKit screenshot functionality requires additional GTK
            rendering APIs. This is a placeholder implementation that
            returns empty bytes. Full implementation would require:
            - GTK snapshot APIs (gtk_widget_snapshot)
            - Cairo surface to PNG conversion
        """
        if not self._widget:
            print("Cannot capture screenshot: widget not available")
            callback(b"")
            return
        
        # TODO: Implement GTK-based screenshot capture
        # This would require:
        # 1. Use gtk_widget_snapshot() to capture widget as GtkSnapshot
        # 2. Convert snapshot to cairo surface
        # 3. Write cairo surface to PNG in memory
        # 4. Return PNG bytes via callback
        print("Screenshot capture not yet implemented for GTK WebEngine")
        callback(b"")

    @property
    def engine_name(self) -> str:
        """Get engine name"""
        return "GTK WebKit"

    @property
    def supports_dev_tools(self) -> bool:
        """Check if engine supports developer tools"""
        return True  # WebKit has built-in inspector
