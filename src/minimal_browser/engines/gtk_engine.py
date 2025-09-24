"""GTK WebKit engine implementation (placeholder)"""

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

    @property
    def engine_name(self) -> str:
        """Get engine name"""
        return "GTK WebKit"

    @property
    def supports_dev_tools(self) -> bool:
        """Check if engine supports developer tools"""
        return True  # WebKit has built-in inspector
