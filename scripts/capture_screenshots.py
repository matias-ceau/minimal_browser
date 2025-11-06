#!/usr/bin/env python3
"""Script to capture screenshots of the browser for documentation.

This script launches the browser with a virtual display and captures
screenshots demonstrating key features.

Note: Uses XCB platform (X11) instead of offscreen because we need actual
rendering for screenshots. The offscreen platform doesn't generate visual
output suitable for screenshots.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

# Set up for running with virtual display
# XCB is needed for screenshot capture; offscreen doesn't render visuals
os.environ["QT_QPA_PLATFORM"] = "xcb"  # Use X11 for screenshot capture
os.environ["QT_API"] = "pyside6"
os.environ["DISPLAY"] = ":99"  # Virtual display

from PySide6.QtCore import Qt, QTimer, QSize, QUrl
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage

from minimal_browser.minimal_browser import VimBrowser
from minimal_browser.storage.conversations import ConversationLog


def wait_for_load(ms: int = 2000):
    """Wait for page load with event processing.
    
    Uses event processing loop instead of sleep to handle Qt events
    properly and avoid flaky timing issues.
    """
    start_time = time.time()
    while (time.time() - start_time) * 1000 < ms:
        QApplication.processEvents()
        time.sleep(0.1)  # Small sleep to prevent CPU spinning


def capture_screenshot(browser: VimBrowser, filename: str, wait_ms: int = 2000) -> Path:
    """Capture screenshot of the browser window.
    
    Args:
        browser: Browser instance to capture
        filename: Filename for the screenshot
        wait_ms: Milliseconds to wait before capture
        
    Returns:
        Path to saved screenshot
    """
    # Wait for rendering
    wait_for_load(wait_ms)
    
    # Create screenshot directory
    screenshot_dir = Path(__file__).parent.parent / "assets" / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    # Capture screenshot
    screenshot_path = screenshot_dir / filename
    
    # Grab the window pixmap
    pixmap = browser.grab()
    if not pixmap.isNull():
        success = pixmap.save(str(screenshot_path), "PNG")
        if success:
            print(f"✓ Screenshot saved: {filename}")
            return screenshot_path
        else:
            print(f"✗ Failed to save screenshot: {filename}")
    else:
        print(f"✗ Pixmap is null for: {filename}")
    
    return screenshot_path


def main():
    """Capture all screenshots for documentation."""
    print("="*70)
    print("Capturing Browser Screenshots for Documentation")
    print("="*70)
    
    # Create temporary conversation log
    import tempfile
    tmpdir = Path(tempfile.mkdtemp())
    log_path = tmpdir / "conversations.json"
    conv_log = ConversationLog(path=str(log_path))
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Minimal Browser Screenshot Capture")
    
    # Create browser
    print("\n1. Creating browser instance...")
    browser = VimBrowser(conversation_log=conv_log, headless=False)
    browser.resize(1280, 720)
    browser.show()
    
    try:
        # Screenshot 1: Initial Google homepage
        print("\n2. Capturing initial launch (Google homepage)...")
        wait_for_load(3000)
        capture_screenshot(browser, "01_browser_launch.png", wait_ms=1000)
        
        # Screenshot 2: Navigate to example.com
        print("\n3. Navigating to example.com...")
        browser.open_url("https://example.com")
        wait_for_load(4000)
        capture_screenshot(browser, "02_example_com.png", wait_ms=1000)
        
        # Screenshot 3: Navigate to Python.org
        print("\n4. Navigating to python.org...")
        browser.open_url("https://www.python.org")
        wait_for_load(4000)
        capture_screenshot(browser, "03_python_org.png", wait_ms=1000)
        
        # Screenshot 4: Help screen
        print("\n5. Showing help screen...")
        browser.show_help()
        wait_for_load(1500)
        capture_screenshot(browser, "04_help_screen.png", wait_ms=500)
        
        print("\n" + "="*70)
        print("✓ All screenshots captured successfully!")
        print(f"  Location: {Path(__file__).parent.parent / 'assets' / 'screenshots'}")
        print("="*70)
        
    except Exception as e:
        print(f"\n✗ Error during screenshot capture: {e}")
        import traceback
        traceback.print_exc()
    finally:
        browser.close()
        app.quit()


if __name__ == "__main__":
    # Check if running with xvfb
    if os.environ.get("DISPLAY") == ":99":
        print("Running with virtual display :99")
    
    main()
