#!/usr/bin/env python3
# ruff: noqa: E402

import os
import sys
import html
import base64
from typing import MutableMapping, Optional, cast


from PySide6.QtCore import QUrl, Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QLabel,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import (
    QWebEngineProfile,
    QWebEngineSettings,
    QWebEnginePage,
)

from .engines.qt_engine import QtWebEngine
from .ai.schemas import AIAction, ConversationMemory
from .ai.tools import ResponseProcessor
from .rendering.artifacts import URLBuilder
from .storage.conversations import ConversationLog
from .ui.ai_worker import AIWorker
from .ui.command_palette import CommandPalette


def to_data_url(html: str) -> str:
    """Encode HTML content into a data URL with base64 encoding"""
    # Ensure HTML is properly encoded as UTF-8 bytes
    try:
        html_bytes = html.encode("utf-8")
        encoded_html = base64.b64encode(html_bytes).decode("ascii")
        return f"data:text/html;charset=utf-8;base64,{encoded_html}"
    except (UnicodeEncodeError, UnicodeDecodeError) as e:
        print(f"Encoding error in to_data_url: {e}")
        # Fallback: use error handling
        html_bytes = html.encode("utf-8", errors="replace")
        encoded_html = base64.b64encode(html_bytes).decode("ascii")
        return f"data:text/html;charset=utf-8;base64,{encoded_html}"


OS_ENV: MutableMapping[str, str] = cast(MutableMapping[str, str], os.environ)  # type: ignore[attr-defined]


class VimBrowser(QMainWindow):
    def __init__(self, conversation_log: ConversationLog, headless: bool = False):
        super().__init__()
        # Fix for Python 3.13 compatibility and Wayland envs
        OS_ENV.setdefault("QT_API", "pyside6")
        OS_ENV.setdefault("QT_QPA_PLATFORM", "wayland")
        OS_ENV.setdefault("WAYLAND_DISPLAY", OS_ENV.get("WAYLAND_DISPLAY", "wayland-0"))
        OS_ENV.setdefault("qt-scale-factor", "1")
        OS_ENV.setdefault("WLR_NO_HARDWARE_CURSORS", "1")
        self.mode = "NORMAL"
        self.command_buffer = ""
        self.active_command_prefix: Optional[str] = None
        self.buffers: list[str] = []
        self.current_buffer = 0
        self.ai_worker: Optional[AIWorker] = None
        self.last_query: Optional[str] = None
        self.current_ai_mode: str = "chat"
        self.ai_stream_buffer: str = ""
        self.conversation_log = conversation_log
        self.conv_memory: ConversationMemory = ConversationMemory()
        self.engine = QtWebEngine() if not headless else None
        self._dev_tools_window: Optional[QWebEngineView] = None
        self.initial_load = True
        self._init_ai_overlay()
        self._init_profile_and_browser()
        self._init_status_bar()
        self._init_command_line()
        self._init_mode_timer()
        self._connect_browser_signals()
        initial_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.google.com"
        self.open_url(initial_url)
        self.setup_keybindings()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.update_title()

    def _init_ai_overlay(self):
        self.loading_overlay = QLabel(self)
        self.loading_overlay.setStyleSheet(
            """
            QLabel {
                background-color: rgba(0, 0, 0, 0.7);
                color: white;
                border: none;
                font-size: 16px;
                font-family: monospace;
            }
            QLabel::before {
                content: "🤖 AI Thinking...";
                display: block;
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                0% { transform: translate(-50%, -50%) rotate(0deg); }
                100% { transform: translate(-50%, -50%) rotate(360deg); }
            }
            """
        )
        self.loading_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_overlay.hide()
        self.loading_overlay.raise_()

    def _init_profile_and_browser(self):
        self.profile = QWebEngineProfile()
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )
        self.profile.setPersistentStoragePath(
            os.path.join(os.path.expanduser("~"), ".minimal-browser")
        )
        try:
            self.browser = QWebEngineView()
            self.page = QWebEnginePage(self.profile, self)
            self.browser.setPage(self.page)
            settings = self.browser.settings()
            settings.setAttribute(
                QWebEngineSettings.WebAttribute.JavascriptEnabled, True
            )
        except Exception as e:
            print(f"WebEngine initialization error: {e}")
            self.browser = QWebEngineView()
        menubar = self.menuBar()
        if menubar is not None:
            menubar.setVisible(False)
        self.statusBar().hide()
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QStatusBar {
                background-color: #2d2d2d;
                color: #ffffff;
                border-top: 1px solid #555;
            }
        """)

    def _init_status_bar(self):
        self.status_widget = QWidget(self)
        self.status_widget.setFixedHeight(25)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create status bar content
        self.vim_status = QLabel()
        self.vim_status.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 4px 8px;
                font-family: monospace;
                font-size: 12px;
                border: none;
            }
        """)

        layout.addWidget(self.vim_status)
        self.status_widget.setLayout(layout)

        # Position at bottom
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.browser)
        main_layout.addWidget(self.status_widget)

        self.setCentralWidget(container)

    def _init_command_line(self):
        self.command_palette = CommandPalette(self)
        self.command_line = self.command_palette.input
        self.command_palette.hide()
        self.command_line.returnPressed.connect(self.execute_command)

    def _position_command_palette(self) -> None:
        if not hasattr(self, "command_palette"):
            return
        width = min(480, self.width() - 60)
        width = max(width, 300)
        height = self.command_palette.sizeHint().height()
        self.command_palette.resize(width, height)
        x = (self.width() - width) // 2
        y = self.height() - height - 60
        self.command_palette.move(max(20, x), max(40, y))

    def _init_mode_timer(self):
        self.mode_timer = QTimer()
        self.mode_timer.timeout.connect(self.hide_mode_indicator)
        self.mode_timer.setSingleShot(True)

    def _connect_browser_signals(self):
        self.browser.loadStarted.connect(lambda: print("Page load started"))
        self.browser.loadProgress.connect(lambda p: print(f"Load progress: {p}%"))
        self.browser.loadFinished.connect(
            lambda ok: print(f"Page load finished: {'SUCCESS' if ok else 'FAILED'}")
        )
        self.browser.loadFinished.connect(self._setup_insert_mode_detection)

    def _setup_insert_mode_detection(self):
        """Set up JavaScript to detect when input fields are focused"""
        js_code = """
        (function() {
            function updateMode(isInsert) {
                window.vimBrowserInsertMode = isInsert;
            }

            function addListeners() {
                const inputs = document.querySelectorAll('input, textarea, [contenteditable="true"]');
                inputs.forEach(function(element) {
                    element.addEventListener('focus', function() {
                        updateMode(true);
                    });
                    element.addEventListener('blur', function() {
                        updateMode(false);
                    });
                });
            }

            // Run immediately and also when DOM changes
            addListeners();

            // Use MutationObserver to detect new inputs added dynamically
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'childList') {
                        addListeners();
                    }
                });
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        })();
        """
        self.browser.page().runJavaScript(js_code)

        # Set up timer to check insert mode status
        self.insert_mode_timer = QTimer()
        self.insert_mode_timer.timeout.connect(self._check_insert_mode)
        self.insert_mode_timer.start(200)  # Check every 200ms

    def _check_insert_mode(self):
        """Check if we're in insert mode by querying JavaScript"""

        def handle_result(result):
            if result and self.mode == "NORMAL":
                self.mode = "INSERT"
                self.update_title()
            elif not result and self.mode == "INSERT":
                self.mode = "NORMAL"
                self.update_title()

        self.browser.page().runJavaScript(
            "window.vimBrowserInsertMode || false", handle_result
        )

    def _current_url(self) -> str:
        if hasattr(self, "browser") and self.browser:
            return self.browser.url().toString()
        return ""

    def _start_ai_request(self, query: str, mode: str) -> None:
        query = query.strip()
        if not query:
            self._show_notification("AI request requires content", timeout=2500)
            return

        if self.ai_worker and self.ai_worker.isRunning():
            self._show_notification("AI is already processing a request", timeout=2500)
            return

        current_url = self._current_url()
        history = self.conv_memory.as_history()
        worker = AIWorker(query, current_url=current_url, history=history)
        worker.response_ready.connect(self._on_ai_response_ready)
        worker.progress_update.connect(self._on_ai_progress_update)
        worker.streaming_chunk.connect(self._on_ai_stream_chunk)

        self.ai_worker = worker
        self.last_query = query
        self.current_ai_mode = mode
        self.ai_stream_buffer = ""

        self.conv_memory.add_user(query)
        self.loading_overlay.setText("🤖 Analyzing request...")
        self.loading_overlay.show()
        self.loading_overlay.raise_()

        worker.start()

    def _on_ai_progress_update(self, message: str) -> None:
        if not message:
            return
        self.loading_overlay.setText(f"🤖 {message}")

    def _on_ai_stream_chunk(self, chunk: str) -> None:
        if not chunk:
            return
        self.ai_stream_buffer += chunk
        preview = self.ai_stream_buffer.strip()
        if preview:
            self.loading_overlay.setText(preview[-160:])

    def _on_ai_response_ready(self, status: str, payload: str) -> None:
        self.loading_overlay.hide()
        self.loading_overlay.clear()

        if self.ai_worker:
            self.ai_worker.deleteLater()
        self.ai_worker = None
        self.ai_stream_buffer = ""

        if status != "success":
            self._handle_ai_error(payload)
            return

        self.conv_memory.add_assistant(payload)
        if self.conversation_log and self.last_query is not None:
            self.conversation_log.append(self.last_query, payload)

        try:
            action = ResponseProcessor.parse_response(payload)
        except Exception as exc:  # pragma: no cover - defensive fallback
            print(f"AI response parsing failed: {exc}")
            action = ResponseProcessor.parse_response(f"HTML:{payload}")

        self._apply_ai_action(action)
        self._show_notification(f"AI {action.type} ready", timeout=3000)
        self.normal_mode()

    def _apply_ai_action(self, action: AIAction) -> None:
        destination = URLBuilder.resolve_action(action)
        self.open_url(destination)

    def _handle_ai_error(self, message: str) -> None:
        print(f"AI error: {message}")
        self._show_notification(f"AI error: {message}", timeout=4000)
        self.normal_mode()

    def _show_notification(self, message: str, timeout: int = 3000) -> None:
        if not message:
            return
        status_bar = self.statusBar()
        status_bar.show()
        status_bar.showMessage(message, timeout)
        QTimer.singleShot(timeout, status_bar.hide)

    def setup_keybindings(self):
        # Escape key - always goes to normal mode
        QShortcut(QKeySequence("Escape"), self, self.normal_mode)

        # Normal mode shortcuts
        QShortcut(QKeySequence(":"), self, self.command_mode)
        QShortcut(QKeySequence("/"), self, self.search_mode)
        QShortcut(QKeySequence("s"), self, self.smart_search_mode)  # Smart search
        QShortcut(QKeySequence("a"), self, self.ai_search_mode)  # AI/LLM search
        QShortcut(QKeySequence("F1"), self, self.show_help)  # Help
        # Note: "?" keybinding handled in keyPressEvent instead of QShortcut
        # This avoids Wayland compatibility issues with QKeySequence("?")
        QShortcut(QKeySequence("F10"), self, self.toggle_dev_tools)  # Developer Tools
        QShortcut(QKeySequence("Ctrl+U"), self, self.view_source)  # View Source
        QShortcut(QKeySequence("Ctrl+I"), self, self.show_debug_info)  # Debug Info
        QShortcut(QKeySequence("r"), self, self.reload_page)
        QShortcut(QKeySequence("H"), self, self.go_back)
        QShortcut(QKeySequence("L"), self, self.go_forward)
        QShortcut(QKeySequence("n"), self, self.next_buffer)
        QShortcut(QKeySequence("p"), self, self.prev_buffer)
        QShortcut(QKeySequence("o"), self, self.open_prompt)
        QShortcut(QKeySequence("t"), self, self.new_buffer)
        QShortcut(QKeySequence("x"), self, self.close_buffer)
        QShortcut(QKeySequence("q"), self, self.quit_if_normal)
        QShortcut(QKeySequence("Ctrl+T"), self, self.new_buffer)
        QShortcut(QKeySequence("Ctrl+W"), self, self.close_buffer)
        QShortcut(QKeySequence("Ctrl+R"), self, self.reload_page)
        QShortcut(QKeySequence("Ctrl+Tab"), self, self.next_buffer)

    def keyPressEvent(self, event):
        if self.mode == "NORMAL":
            key = event.text()
            # Handle "?" key directly in keyPressEvent - more reliable in Wayland than QShortcut
            if key == "?":
                event.accept()  # Accept the event to prevent further processing
                self._safe_show_help()
                return
            key_lower = key.lower()
            if key_lower in [
                ":",
                "/",
                "s",
                "a",
                "r",
                "h",
                "l",
                "n",
                "p",
                "o",
                "t",
                "x",
                "q",
                "j",
                "k",
                "d",
                "u",
                "g",
                " ",
            ]:
                # Let shortcuts handle these
                pass
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "command_palette"):
            self._position_command_palette()
        if hasattr(self, "loading_overlay"):
            self.loading_overlay.resize(self.size())

    def normal_mode(self):
        self.mode = "NORMAL"
        if hasattr(self, "command_palette"):
            self.command_palette.hide()
        if hasattr(self, "command_line"):
            self.command_line.clear()
        self.active_command_prefix = None
        self.update_title()
        self.setFocus()

    def command_mode(self):
        if self.mode == "NORMAL":
            self.mode = "COMMAND"
            self.show_command_line(":")

    def search_mode(self):
        if self.mode == "NORMAL":
            self.mode = "COMMAND"
            self.show_command_line("/")

    def open_prompt(self):
        if self.mode == "NORMAL":
            self.mode = "COMMAND"
            self.show_command_line("o ")

    def smart_search_mode(self):
        if self.mode == "NORMAL":
            self.mode = "COMMAND"
            self.show_command_line("s ")

    def smart_search(self, query: str) -> None:
        query = query.strip()
        if not query:
            return
        if " " not in query and "." in query:
            self.open_url(query)
        else:
            self.open_url(URLBuilder.create_search_url(query))

    def ai_search(self, query: str) -> None:
        self._start_ai_request(query, mode="search")

    def ai_search_mode(self):
        if self.mode == "NORMAL":
            self.mode = "COMMAND"
            self.show_command_line("a ")

    def ai_chat(self, query: str) -> None:
        self._start_ai_request(query, mode="chat")

    def ai_chat_mode(self):
        if self.mode == "NORMAL":
            self.mode = "AI_CHAT"
            self.show_command_line("🤖 ")

    def _safe_show_help(self):
        """Wrapper for show_help that catches all exceptions to prevent crashes"""
        import traceback
        try:
            self.show_help()
        except Exception as e:
            print(f"Error showing help: {e}")
            traceback.print_exc()
            # Show a notification instead of crashing
            self._show_notification("Help screen unavailable", timeout=2000)

    def show_help(self):
        if self.mode == "NORMAL":
            try:
                help_content = self.get_help_content()
                # Use the existing to_data_url helper which handles encoding properly
                help_url = to_data_url(help_content)
                self.open_url(help_url)
            except Exception as e:
                import traceback
                print(f"Error in show_help: {e}")
                traceback.print_exc()
                # Don't re-raise to prevent UI crash

    def show_command_line(self, prefix: str) -> None:
        self.active_command_prefix = prefix
        if hasattr(self, "command_palette"):
            self.command_palette.configure(prefix)
            self.command_palette.show()
            self.command_palette.raise_()
            self._position_command_palette()
        if hasattr(self, "command_line"):
            self.command_line.setFocus()
        self.update_title()

    def execute_command(self) -> None:
        raw_text = self.command_line.text()
        prefix = self.active_command_prefix or ""
        content = raw_text.strip()

        if prefix:
            command = prefix + content
        else:
            command = raw_text.strip()

        if not command:
            self.normal_mode()
            return

        if command.startswith(":"):
            self.execute_vim_command(command[1:])
        elif command.startswith("/"):
            self.search_page(command[1:])
        elif command.startswith("o "):
            self.open_url(command[2:])
        elif command.startswith("s "):
            self.smart_search(command[2:])
        elif command.startswith("a "):
            self.ai_search(command[2:])
        elif command.startswith("🤖"):
            query = command[2:]
            print(f"Executing AI chat with query: '{query}'")
            self.ai_chat(query)

        self.normal_mode()

    def execute_vim_command(self, cmd):
        cmd = cmd.strip()

        if cmd in ["q", "quit"]:
            self.close()
        elif cmd in ["w", "write"]:
            pass
        elif cmd in ["wq"]:
            self.close()
        elif cmd in ["help", "h"]:
            self.show_help()
        elif cmd.startswith("e "):
            url = cmd[2:]
            self.open_url(url)
        elif cmd.startswith("b"):
            if cmd == "b":
                self.show_buffers()
            elif cmd.startswith("bd"):
                self.close_buffer()
            elif cmd.startswith("bn"):
                self.next_buffer()
            elif cmd.startswith("bp"):
                self.prev_buffer()
        elif cmd.isdigit():
            buf_num = int(cmd) - 1
            if 0 <= buf_num < len(self.buffers):
                self.current_buffer = buf_num
                self.browser.load(QUrl(self.buffers[self.current_buffer]))
                self.update_title()

    def toggle_dev_tools(self):
        if not hasattr(self, "browser") or self.browser is None:
            self._show_notification(
                "Developer tools are unavailable in headless mode", timeout=3000
            )
            return

        page = self.browser.page()
        if not hasattr(page, "setDevToolsPage"):
            print("Developer tools not available in this Qt version")
            self._show_notification(
                "Developer tools not available in this Qt version", timeout=3500
            )
            return

        if self._dev_tools_window is None:
            self._dev_tools_window = QWebEngineView()
            self._dev_tools_window.setWindowTitle("Developer Tools")
            self._dev_tools_window.resize(900, 600)
            page.setDevToolsPage(self._dev_tools_window.page())

        if self._dev_tools_window.isVisible():
            self._dev_tools_window.hide()
        else:
            self._dev_tools_window.show()
            self._dev_tools_window.raise_()
            self._dev_tools_window.activateWindow()

    def search_page(self, query):
        if query:
            self.browser.findText(query)

    def open_url(self, url):
        print(f"Opening URL: {url[:100]}...")  # Debug logging

        # Handle data URLs differently - extract HTML for setHtml() which is more Wayland-compatible
        if url.startswith("data:"):
            # Extract HTML from data URL for setHtml() - more reliable in Wayland
            try:
                # Parse data:text/html;base64,<data>
                if "base64," in url:
                    base64_data = url.split("base64,", 1)[1]
                    html_content = base64.b64decode(base64_data).decode("utf-8")
                elif "charset=utf-8;base64," in url:
                    base64_data = url.split("charset=utf-8;base64,", 1)[1]
                    html_content = base64.b64decode(base64_data).decode("utf-8")
                else:
                    # Fallback to QUrl if we can't parse
                    qurl = QUrl(url)
                    html_content = None
            except Exception:
                qurl = QUrl(url)
                html_content = None
        else:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            qurl = QUrl(url)
            html_content = None

        # Add to buffers if not already there
        if url not in self.buffers:
            self.buffers.append(url)
            self.current_buffer = len(self.buffers) - 1
        else:
            self.current_buffer = self.buffers.index(url)
        
        # Wayland fix: Ensure window is shown and activated before loading
        if not self.isVisible():
            self.show()
        self.raise_()
        self.activateWindow()
        
        # Wayland-compatible loading: Use setHtml() for data URLs, load() for regular URLs
        def load_content():
            if html_content is not None:
                # Use setHtml() for data URLs - more reliable in Wayland
                if self.initial_load:
                    self.browser.page().setHtml(html_content, QUrl("about:blank"))
                    self.initial_load = False
                else:
                    self.setWindowTitle("Switching...")
                    self.browser.page().setHtml(html_content, QUrl("about:blank"))
            else:
                # Use load() for regular URLs
                if self.initial_load:
                    self.browser.load(qurl)
                    self.initial_load = False
                else:
                    self.setWindowTitle("Switching...")
                    self.browser.load(qurl)
        
        # For data URLs in Wayland, use a small delay to ensure window is ready
        if url.startswith("data:") and html_content is not None:
            QTimer.singleShot(50, load_content)  # 50ms delay for Wayland compatibility
        else:
            load_content()
        self.update_title()

    def reload_page(self):
        if self.mode == "NORMAL":
            self.browser.reload()

    def go_back(self):
        if self.mode == "NORMAL":
            self.browser.back()

    def go_forward(self):
        if self.mode == "NORMAL":
            self.browser.forward()

    def new_buffer(self):
        if self.mode == "NORMAL":
            self.open_prompt()

    def close_buffer(self):
        if len(self.buffers) > 1:
            del self.buffers[self.current_buffer]
            if self.current_buffer >= len(self.buffers):
                self.current_buffer = len(self.buffers) - 1
            self.browser.load(QUrl(self.buffers[self.current_buffer]))
        else:
            self.close()
        self.update_title()

    def next_buffer(self):
        if self.mode == "NORMAL" and len(self.buffers) > 1:
            self.current_buffer = (self.current_buffer + 1) % len(self.buffers)
            self.setWindowTitle("Switching...")
            self.browser.load(QUrl(self.buffers[self.current_buffer]))
            self.update_title()

    def prev_buffer(self):
        if self.mode == "NORMAL" and len(self.buffers) > 1:
            self.current_buffer = (self.current_buffer - 1) % len(self.buffers)
            self.setWindowTitle("Switching...")
            self.browser.load(QUrl(self.buffers[self.current_buffer]))
            self.update_title()

    def scroll_page(self, pixels):
        if self.mode == "NORMAL":
            direction = 1 if pixels > 0 else -1
            distance = abs(pixels)
            js = f"""
            function smoothScroll() {{
                let start = window.pageYOffset;
                let current = start;
                let step = {direction} * Math.min(20, {distance});
                function animate() {{
                    current += step;
                    window.scrollTo(0, current);
                    let remaining = Math.abs({distance} - Math.abs(current - start));
                    if (remaining > 0) {{
                        requestAnimationFrame(animate);
                    }}
                }}
                animate();
            }}
            smoothScroll();
            """
            self.browser.page().runJavaScript(js)

    def scroll_top(self):
        if self.mode == "NORMAL":
            self.browser.page().runJavaScript("window.scrollTo(0, 0);")

    def scroll_bottom(self):
        if self.mode == "NORMAL":
            self.browser.page().runJavaScript(
                "window.scrollTo(0, document.body.scrollHeight);"
            )

    def quit_if_normal(self):
        if self.mode == "NORMAL":
            self.close()

    def view_source(self):
        if not hasattr(self, "browser") or self.browser is None:
            self._show_notification("Browser instance unavailable", timeout=2500)
            return

        def handle_html(content: str) -> None:
            if not content:
                self._show_notification("Unable to retrieve page source", timeout=3000)
                return
            escaped = html.escape(content)
            source_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Page Source</title>
                <style>
                    body {{ background: #1e1e1e; color: #dcdcdc; margin: 0; padding: 16px; font-family: monospace; }}
                    pre {{ white-space: pre-wrap; word-wrap: break-word; }}
                    h1 {{ color: #4a9eff; }}
                </style>
            </head>
            <body>
                <h1>Page Source: {html.escape(self._current_url() or "unknown")}</h1>
                <pre>{escaped}</pre>
            </body>
            </html>
            """
            self.open_url(to_data_url(source_html))

        self.browser.page().toHtml(handle_html)

    def show_debug_info(self):
        debug_rows = [
            ("Current URL", self._current_url() or "unknown"),
            ("Mode", self.mode),
            ("Buffers", ", ".join(self.buffers) if self.buffers else "none"),
            (
                "AI Worker Running",
                "yes" if self.ai_worker and self.ai_worker.isRunning() else "no",
            ),
            ("Engine", self.engine.engine_name if self.engine else "None (headless)"),
        ]
        rows_html = "".join(
            f"<tr><th>{html.escape(label)}</th><td>{html.escape(value)}</td></tr>"
            for label, value in debug_rows
        )
        debug_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Debug Info</title>
            <style>
                body {{ background: #202020; color: #f0f0f0; font-family: system-ui; padding: 24px; }}
                table {{ border-collapse: collapse; width: 100%; max-width: 700px; }}
                th, td {{ border: 1px solid #444; padding: 8px; text-align: left; }}
                th {{ background: #2f2f2f; color: #4a9eff; width: 180px; }}
            </style>
        </head>
        <body>
            <h1>VimBrowser Debug Info</h1>
            <table>
                {rows_html}
            </table>
        </body>
        </html>
        """
        self.open_url(to_data_url(debug_html))

    def show_buffers(self):
        if self.buffers:
            buf_info = f"Buffers: {', '.join(f'{i + 1}:{url.split("/")[-1][:20]}' for i, url in enumerate(self.buffers))}"
            self.setWindowTitle(buf_info)
            self.mode_timer.start(3000)

    def update_title(self):
        self.setWindowTitle("Minimal Browser")

        # Update vim status bar
        if hasattr(self, "vim_status"):
            current_url = ""
            if self.buffers and self.current_buffer < len(self.buffers):
                current_url = self.buffers[self.current_buffer]
                if current_url.startswith("data:"):
                    current_url = "AI Generated Content"
                elif len(current_url) > 60:
                    current_url = current_url[:57] + "..."

            buffer_info = (
                f"[{self.current_buffer + 1}/{len(self.buffers)}]"
                if self.buffers
                else "[0/0]"
            )
            mode_text = f"-- {self.mode} --" if self.mode != "NORMAL" else "NORMAL"

            status_text = f"{buffer_info} {current_url} | {mode_text}"
            self.vim_status.setText(status_text)

    def hide_mode_indicator(self):
        if self.mode == "NORMAL":
            self.update_title()

    def get_help_content(self):
        return """<!DOCTYPE html>
<html>
<head>
    <title>Vim Browser Help</title>
    <style>
        body {
            font-family: monospace;
            background: rgba(30,30,30,1);
            color: #ffffff;
            padding: 20px;
            line-height: 1.6;
        }
        h1, h2 {
            color: #4a9eff;
        }
        .key {
            background: #333;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: bold;
        }
        .section {
            margin-bottom: 30px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
        }
        td {
            padding: 8px;
            border-bottom: 1px solid #333;
        }
        .cmd {
            color: #90ee90;
        }
    </style>
</head>
<body>
    <h1>Vim Browser Help</h1>
    
    <div class="section">
        <h2>Navigation</h2>
        <table>
            <tr>
                <td><span class="key">j/k</span></td>
                <td>Scroll down/up</td>
            </tr>
            <tr>
                <td><span class="key">d/u</span></td>
                <td>Page down/up</td>
            </tr>
            <tr>
                <td><span class="key">g/G</span></td>
                <td>Top/bottom of page</td>
            </tr>
            <tr>
                <td><span class="key">H/L</span></td>
                <td>Back/forward</td>
            </tr>
            <tr>
                <td><span class="key">r</span></td>
                <td>Reload page</td>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Buffers (Tabs)</h2>
        <table>
            <tr>
                <td><span class="key">n/p</span></td>
                <td>Next/previous buffer</td>
            </tr>
            <tr>
                <td><span class="key">t</span></td>
                <td>New buffer</td>
            </tr>
            <tr>
                <td><span class="key">x</span></td>
                <td>Close buffer</td>
            </tr>
            <tr>
                <td><span class="key">:b</span></td>
                <td>Show buffers</td>
            </tr>
            <tr>
                <td><span class="key">:1,2,3...</span></td>
                <td>Go to buffer number</td>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Opening URLs & Search</h2>
        <table>
            <tr>
                <td><span class="key">o</span></td>
                <td>Open URL</td>
            </tr>
            <tr>
                <td><span class="key">s</span></td>
                <td>Smart search (Google or URL)</td>
            </tr>
            <tr>
                <td><span class="key">a</span></td>
                <td>AI search (ChatGPT)</td>
            </tr>
            <tr>
                <td><span class="key">Space</span></td>
                <td>Native AI chat</td>
            </tr>
            <tr>
                <td><span class="key">/</span></td>
                <td>Search in page</td>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Developer Tools</h2>
        <table>
            <tr>
                <td><span class="key">F10</span></td>
                <td>Toggle developer tools</td>
            </tr>
            <tr>
                <td><span class="key">Ctrl+U</span></td>
                <td>View page source</td>
            </tr>
            <tr>
                <td><span class="key">Ctrl+I</span></td>
                <td>Show debug info</td>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <h2>AI Integration</h2>
        <table>
            <tr>
                <td><span class="key">Space</span></td>
                <td>Ask AI anything - it can navigate or create content</td>
            </tr>
            <tr colspan="2"><td></td><td>Examples:</td></tr>
            <tr>
                <td></td>
                <td>"navigate to github" &rarr; Opens GitHub</td>
            </tr>
            <tr>
                <td></td>
                <td>"create a todo list" &rarr; Generates interactive todo app</td>
            </tr>
            <tr>
                <td></td>
                <td>"make a calculator" &rarr; Creates working calculator</td>
            </tr>
            <tr>
                <td></td>
                <td>"explain quantum physics" &rarr; Generates explanation page</td>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Commands (:)</h2>
        <table>
            <tr>
                <td><span class="cmd">:q</span></td>
                <td>Quit</td>
            </tr>
            <tr>
                <td><span class="cmd">:help</span></td>
                <td>Show this help</td>
            </tr>
            <tr>
                <td><span class="cmd">:e &lt;url&gt;</span></td>
                <td>Open URL</td>
            </tr>
            <tr>
                <td><span class="cmd">:bd</span></td>
                <td>Close buffer</td>
            </tr>
            <tr>
                <td><span class="cmd">:bn/:bp</span></td>
                <td>Next/previous buffer</td>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Modes</h2>
        <table>
            <tr>
                <td><span class="key">NORMAL</span></td>
                <td>Default mode for navigation</td>
            </tr>
            <tr>
                <td><span class="key">COMMAND</span></td>
                <td>Typing commands or URLs</td>
            </tr>
            <tr>
                <td><span class="key">Escape</span></td>
                <td>Return to NORMAL mode</td>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Examples</h2>
        <p><span class="key">s python tutorial</span> &rarr; Google search</p>
        <p><span class="key">s github.com</span> &rarr; Open GitHub</p>
        <p><span class="key">a explain quantum computing</span> &rarr; Ask ChatGPT</p>
        <p><span class="key">Space navigate to reddit</span> &rarr; AI opens Reddit</p>
        <p><span class="key">Space create a calculator</span> &rarr; AI generates calculator</p>
        <p><span class="key">o reddit.com</span> &rarr; Open Reddit</p>
    </div>
    
    <p style="margin-top: 40px; color: #666;"><span class="key">Press Escape</span> to return to normal browsing</p>
</body>
</html>"""