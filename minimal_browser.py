#!/usr/bin/env python3

import sys
from PyQt6.QtCore import QUrl
from PyQt6.QtSerialPort import QSerialPort
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QSplitter,
    QGraphicsView,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from rich.console import Console


class SimpleBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minimal Browser")

        # Create a splitter for horizontal layout
        splitter = QSplitter()

        # Set up the web engine view
        self.browser = QWebEngineView()
        if sys.argv[1:]:
            path = QUrl(sys.argv[1])
        else:
            path = QUrl("https://www.google.com")
        self.browser.load(path)

        # Create console widget
        self.console = Console()
        console_widget = QWidget()
        console_layout = QVBoxLayout()
        console_layout.addWidget(self.console)
        console_widget.setLayout(console_layout)

        # Add widgets to splitter
        splitter.addWidget(self.browser)
        splitter.addWidget(console_widget)

        # Set initial sizes (50-50 split)
        splitter.setSizes([int(self.width() * 0.5), int(self.width() * 0.5)])

        # Set splitter as central widget
        self.setCentralWidget(splitter)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimpleBrowser()
    window.show()
    sys.exit(app.exec())
