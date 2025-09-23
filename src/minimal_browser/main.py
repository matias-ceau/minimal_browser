#!/usr/bin/env python3

import sys
import os

# Fix for Python 3.13 compatibility
os.environ.setdefault('QT_API', 'pyside6')

# Native Wayland support
os.environ.setdefault('QT_QPA_PLATFORM', 'wayland')
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS', 
    '--no-sandbox --disable-dev-shm-usage --disable-gpu --disable-gpu-compositing --enable-software-rasterizer --disable-background-timer-throttling --disable-renderer-backgrounding --disable-backgrounding-occluded-windows')

# Hyprland-specific fixes
os.environ.setdefault('QT_WAYLAND_DISABLE_WINDOWDECORATION', '0')
os.environ.setdefault('WAYLAND_DISPLAY', os.environ.get('WAYLAND_DISPLAY', 'wayland-0'))
os.environ.setdefault('QT_SCALE_FACTOR', '1')
os.environ.setdefault('WLR_NO_HARDWARE_CURSORS', '1')  # Hyprland compatibility
os.environ.setdefault('QT_WAYLAND_FORCE_DPI', '96')

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from .browser import VimBrowser


def main():
    # Python 3.13 + Qt compatibility fixes
    if hasattr(Qt, 'AA_ShareOpenGLContexts'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    
    # Wayland-specific Qt fixes
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    
    # Set up application with optimizations
    app = QApplication(sys.argv)
    app.setApplicationName("Minimal Browser")
    app.setApplicationVersion("0.2.0")
    
    # Additional Qt WebEngine fixes for Python 3.13 + Wayland
    try:
        from PySide6.QtWebEngineCore import QWebEngineSettings
        # Skip global settings - they're not needed and the method name varies
        print("Skipping global WebEngine settings (not critical)")
    except Exception as e:
        print(f"WebEngine settings warning: {e}")
    
    # Create and show browser
    browser = VimBrowser()
    browser.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()