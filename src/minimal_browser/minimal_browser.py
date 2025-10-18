#!/usr/bin/env python3
# ruff: noqa: E402

import os
import sys
import html
import base64
import webbrowser
import uuid
import requests  # type: ignore[import-untyped]
from typing import MutableMapping, Optional, cast


from PySide6.QtCore import QUrl, Qt, QTimer, QEvent
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QMainWindow, QWidget
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
from .rendering.html import render_template, create_data_url
from .storage.conversations import ConversationLog
from .export.exporter import PageExporter
from .templates import get_help_content
from .config.default_config import DEFAULT_CONFIG
from .ui import CommandPalette, AIWorker
from .storage.bookmarks import BookmarkStore, Bookmark


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


COMMAND_PROMPT_STYLES: dict[str, dict[str, str]] = {
    ":": {
        "icon": "⌨️",
        "label": "Command Mode",
        "placeholder": "Run a Vim command (e.g. :help)",
        "bg_color": "rgba(30, 30, 50, 220)",
        "border_color": "rgba(100, 100, 180, 0.3)",
    },
    "/": {
        "icon": "🔍",
        "label": "Find in Page",
        "placeholder": "Search the current page",
        "bg_color": "rgba(30, 50, 30, 220)",
        "border_color": "rgba(100, 180, 100, 0.3)",
    },
    "o ": {
        "icon": "🌐",
        "label": "Open URL",
        "placeholder": "Enter a URL to visit",
        "bg_color": "rgba(20, 30, 40, 220)",
        "border_color": "rgba(80, 120, 180, 0.3)",
    },
    "s ": {
        "icon": "🧭",
        "label": "Smart Search",
        "placeholder": "Search the web with context",
        "bg_color": "rgba(40, 30, 20, 220)",
        "border_color": "rgba(180, 140, 100, 0.3)",
    },
    "a ": {
        "icon": "🤖",
        "label": "AI Search",
        "placeholder": "Ask the AI to find information",
        "bg_color": "rgba(50, 20, 50, 220)",
        "border_color": "rgba(180, 100, 180, 0.3)",
    },
    "🤖 ": {
        "icon": "💬",
        "label": "AI Chat",
        "placeholder": "Chat with the AI assistant",
        "bg_color": "rgba(40, 20, 40, 220)",
        "border_color": "rgba(160, 80, 160, 0.3)",
    },
    "📷 ": {
        "icon": "📸",
        "label": "Screenshot Analysis",
        "placeholder": "Ask a question about the screenshot",
        "bg_color": "rgba(30, 40, 50, 220)",
        "border_color": "rgba(100, 140, 180, 0.3)",
    },
}

# Ordered list of command prompt modes for cycling
COMMAND_PROMPT_ORDER = [":", "/", "o ", "s ", "a "]


class CommandPalette(QWidget):
    """Lightweight command palette widget with icon + input"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("CommandPalette")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)

        self.icon_label = QLabel("⌨️")
        self.icon_label.setObjectName("CommandIcon")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedWidth(28)

        self.mode_label = QLabel("Command Mode")
        self.mode_label.setObjectName("CommandLabel")

        header.addWidget(self.icon_label)
        header.addWidget(self.mode_label)
        header.addStretch()

        self.input = QLineEdit()
        self.input.setObjectName("CommandInput")
        self.input.setClearButtonEnabled(True)
        self.input.setPlaceholderText("Run a Vim command (e.g. :help)")

        layout.addLayout(header)
        layout.addWidget(self.input)

        self.setStyleSheet(
            """
            #CommandPalette {
                background-color: rgba(20, 20, 20, 220);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.12);
            }
            #CommandLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 12px;
                font-weight: 600;
                letter-spacing: 1.1px;
                text-transform: uppercase;
            }
            #CommandIcon {
                font-size: 18px;
            }
            #CommandInput {
                background-color: rgba(255, 255, 255, 0.07);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 10px;
                color: #ffffff;
                font-size: 14px;
                padding: 10px 14px;
                selection-background-color: rgba(118, 75, 162, 0.6);
            }
            #CommandInput:focus {
                border: 1px solid rgba(134, 84, 204, 0.8);
                background-color: rgba(255, 255, 255, 0.12);
            }
            """
        )

        self.setFocusProxy(self.input)

    def configure(self, prefix: str) -> None:
        style = COMMAND_PROMPT_STYLES.get(prefix)
        if style is None:
            style = {
                "icon": "⌨️",
                "label": "Command Mode",
                "placeholder": "Type a command",
                "bg_color": "rgba(20, 20, 20, 220)",
                "border_color": "rgba(255, 255, 255, 0.12)",
            }
        self.icon_label.setText(style["icon"])
        self.mode_label.setText(style["label"])
        self.input.setPlaceholderText(style["placeholder"])
        self.input.clear()
        
        # Update dynamic colors
        bg_color = style.get("bg_color", "rgba(20, 20, 20, 220)")
        border_color = style.get("border_color", "rgba(255, 255, 255, 0.12)")
        
        self.setStyleSheet(
            f"""
            #CommandPalette {{
                background-color: {bg_color};
                border-radius: 12px;
                border: 1px solid {border_color};
            }}
            #CommandLabel {{
                color: rgba(255, 255, 255, 0.8);
                font-size: 12px;
                font-weight: 600;
                letter-spacing: 1.1px;
                text-transform: uppercase;
            }}
            #CommandIcon {{
                font-size: 18px;
            }}
            #CommandInput {{
                background-color: rgba(255, 255, 255, 0.07);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 10px;
                color: #ffffff;
                font-size: 14px;
                padding: 10px 14px;
                selection-background-color: rgba(118, 75, 162, 0.6);
            }}
            #CommandInput:focus {{
                border: 1px solid rgba(134, 84, 204, 0.8);
                background-color: rgba(255, 255, 255, 0.12);
            }}
            """
        )


class AIWorker(QThread):
    """Worker thread for AI API calls with streaming support"""

    response_ready = pyqtSignal(str, str)  # response_type, content
    progress_update = pyqtSignal(str)  # progress message
    streaming_chunk = pyqtSignal(str)  # streaming response chunk

    def __init__(
        self,
        query: str,
        current_url: str = "",
        history: Optional[list[dict[str, str]]] = None,
        screenshot_data: Optional[bytes] = None,
    ):
        super().__init__()
        self.query = query
        self.current_url = current_url
        self.history = list(history or [])
        self.screenshot_data = screenshot_data

    def run(self):
        try:
            print(f"AI Worker starting for query: {self.query}")
            if self.screenshot_data:
                print(f"Screenshot included: {len(self.screenshot_data)} bytes")
            self.progress_update.emit("Analyzing request...")

            response = self.get_ai_response(self.query, self.current_url)
            print(f"AI Worker got response: {response[:100]}...")

            self.response_ready.emit("success", response)
        except Exception as e:
            print(f"AI Worker error: {e}")
            self.response_ready.emit("error", str(e))

    def get_ai_response(self, query: str, current_url: str) -> str:
        """Get a structured AI response using pydantic-ai."""
        # For screenshot queries, use a direct API call instead of structured agent
        if self.screenshot_data:
            return self._get_vision_response(query, current_url)
        
        system_prompt = get_browser_assistant_prompt(current_url)
        agent = StructuredBrowserAgent(
            system_prompt=system_prompt,
            history=self.history,
        )

        self.progress_update.emit("Requesting structured action…")
        try:
            action = agent.run(query)
        except StructuredAIError as exc:
            raise Exception(str(exc)) from exc
        except requests.exceptions.RequestException as exc:
            raise Exception(f"API request failed: {exc}") from exc
        except Exception as exc:  # pragma: no cover - defensive fallback
            raise Exception(f"AI processing failed: {exc}") from exc

        action_type, payload = ResponseProcessor.action_to_tuple(action)

        prefix_map = {
            "navigate": "NAVIGATE:",
            "search": "SEARCH:",
            "html": "HTML:",
        }
        prefix = prefix_map.get(action_type, "HTML:")

        summary = f"{action.type.upper()}: {payload[:160]}"
        self.streaming_chunk.emit(summary)

        return f"{prefix}{payload}"
    
    def _get_vision_response(self, query: str, current_url: str) -> str:
        """Get an AI response with vision capabilities for screenshot analysis."""
        import base64
        from .ai.auth import auth_manager
        
        # Encode screenshot as base64
        screenshot_base64 = base64.b64encode(self.screenshot_data).decode('utf-8')
        
        self.progress_update.emit("Analyzing screenshot with vision model…")
        
        # Use OpenRouter with a vision-capable model
        api_key = auth_manager.get_key("openrouter")
        if not api_key:
            raise Exception("OpenRouter API key not found")
        
        # Build the messages with image
        system_prompt = f"You are analyzing a screenshot of a webpage. The page URL is: {current_url or 'unknown'}"
        
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        # Add conversation history if available
        for msg in self.history[-5:]:  # Last 5 messages for context
            messages.append(msg)
        
        # Add the user query with image
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": query
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{screenshot_base64}"
                    }
                }
            ]
        })
        
        # Call OpenRouter API with a vision model
        api_url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        # Use GPT-4 Vision or Claude 3.5 Sonnet (both support vision)
        data = {
            "model": "openai/gpt-4o",  # GPT-4o has vision capabilities
            "messages": messages,
            "max_tokens": 2000,
        }
        
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        if not content:
            raise Exception("No response from vision model")
        
        self.streaming_chunk.emit(f"ANALYSIS: {content[:160]}")
        
        # Return as HTML content
        return f"HTML:{content}"
# Load UI configuration
COMMAND_PROMPT_STYLES = DEFAULT_CONFIG.ui.command_prompt_styles
COMMAND_PROMPT_ORDER = DEFAULT_CONFIG.ui.command_prompt_order


class VimBrowser(QMainWindow):
    def __init__(self, conversation_log: ConversationLog, bookmark_store=None, headless: bool = False):
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
        self.bookmark_store = bookmark_store
        self.conv_memory: ConversationMemory = ConversationMemory()
        self.engine = QtWebEngine() if not headless else None
        self._dev_tools_window: Optional[QWebEngineView] = None
        self.initial_load = True
        
        # Command completion state
        self.available_commands = [
            "q", "quit", "w", "write", "wq", "help", "h",
            "e ", "b", "bd", "bn", "bp",
            "browser", "browser-list", "browser ", "ext", "external",
            "files", "files ", "fb", "fb ", "index", "index ", "search-files ",
            "bm", "bm ", "bm add", "bm list", "bm search", "bm del", "bm tags",
        ]
        self.completion_index = -1
        self.completion_candidates: list[str] = []
        
        # URL history for 'o' prompt suggestions
        self.url_history: list[str] = []
        self.url_history_max = 50  # Keep last 50 URLs
        
        # Screenshot analysis state
        self._pending_screenshot: Optional[bytes] = None
        
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
        # Use a named profile for persistent cookies and storage
        self.profile = QWebEngineProfile("minimal-browser", self)
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
        
        # Install event filter for Tab key completion
        self.command_line.installEventFilter(self)
        
        # Reset completion state when text changes
        self.command_line.textChanged.connect(self.reset_completion)

    def eventFilter(self, obj, event):
        """Handle Tab key for command completion in command line."""
        if obj == self.command_line and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Tab:
                self.handle_command_completion()
                return True
        return super().eventFilter(obj, event)

    def handle_command_completion(self):
        """Handle Tab key command completion for : mode and URL suggestions for o mode."""
        current_text = self.command_line.text()
        
        # Handle command completion for : mode
        if self.active_command_prefix == ":":
            # If we're cycling through completions, continue
            if self.completion_candidates and self.completion_index >= 0:
                self.completion_index = (self.completion_index + 1) % len(self.completion_candidates)
                self.command_line.setText(self.completion_candidates[self.completion_index])
                return
            
            # Find matching commands
            self.completion_candidates = [
                cmd for cmd in self.available_commands 
                if cmd.startswith(current_text)
            ]
            
            if not self.completion_candidates:
                # No matches, reset
                self.completion_index = -1
                return
            
            if len(self.completion_candidates) == 1:
                # Single match, complete it
                self.command_line.setText(self.completion_candidates[0])
                self.completion_index = -1
                self.completion_candidates = []
            else:
                # Multiple matches, start cycling
                self.completion_index = 0
                self.command_line.setText(self.completion_candidates[0])
        
        # Handle URL history completion for 'o' mode
        elif self.active_command_prefix == "o ":
            # If we're cycling through completions, continue
            if self.completion_candidates and self.completion_index >= 0:
                self.completion_index = (self.completion_index + 1) % len(self.completion_candidates)
                self.command_line.setText(self.completion_candidates[self.completion_index])
                return
            
            # Find matching URLs from history
            if current_text:
                self.completion_candidates = [
                    url for url in self.url_history 
                    if current_text.lower() in url.lower()
                ]
            else:
                # No text, show recent URLs
                self.completion_candidates = self.url_history[:10]
            
            if not self.completion_candidates:
                self.completion_index = -1
                return
            
            if len(self.completion_candidates) == 1:
                # Single match, complete it
                self.command_line.setText(self.completion_candidates[0])
                self.completion_index = -1
                self.completion_candidates = []
            else:
                # Multiple matches, start cycling
                self.completion_index = 0
                self.command_line.setText(self.completion_candidates[0])

    def reset_completion(self):
        """Reset command completion state when text changes."""
        # Only reset if we're not in the middle of Tab cycling
        if not self.command_line.hasFocus():
            return
        # Don't reset during Tab completion
        if self.completion_index < 0:
            self.completion_candidates = []


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
    
    def _start_screenshot_analysis(self, query: str) -> None:
        """Start AI analysis of the captured screenshot."""
        query = query.strip()
        if not query:
            self._show_notification("Screenshot analysis requires a question", timeout=2500)
            return
        
        if not hasattr(self, "_pending_screenshot") or not self._pending_screenshot:
            self._show_notification("No screenshot available", timeout=2500)
            return

        if self.ai_worker and self.ai_worker.isRunning():
            self._show_notification("AI is already processing a request", timeout=2500)
            return

        current_url = self._current_url()
        history = self.conv_memory.as_history()
        
        # Create worker with screenshot data
        worker = AIWorker(
            query, 
            current_url=current_url, 
            history=history,
            screenshot_data=self._pending_screenshot
        )
        worker.response_ready.connect(self._on_ai_response_ready)
        worker.progress_update.connect(self._on_ai_progress_update)
        worker.streaming_chunk.connect(self._on_ai_stream_chunk)

        self.ai_worker = worker
        self.last_query = f"[Screenshot Analysis] {query}"
        self.current_ai_mode = "screenshot"
        self.ai_stream_buffer = ""

        self.conv_memory.add_user(f"[Screenshot] {query}")
        self.loading_overlay.setText("📷 Analyzing screenshot...")
        self.loading_overlay.show()
        self.loading_overlay.raise_()

        # Clear the pending screenshot
        self._pending_screenshot = None

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

        # Command mode cycling with Ctrl+Arrow keys
        QShortcut(QKeySequence("Ctrl+Down"), self, lambda: self.cycle_command_mode(1))
        QShortcut(QKeySequence("Ctrl+Up"), self, lambda: self.cycle_command_mode(-1))
        
        # Show URL history in 'o' mode
        QShortcut(QKeySequence("Ctrl+Space"), self, self.show_url_history)

        # Normal mode shortcuts
        QShortcut(QKeySequence(":"), self, self.command_mode)
        QShortcut(QKeySequence("/"), self, self.search_mode)
        QShortcut(QKeySequence("s"), self, self.smart_search_mode)  # Smart search
        QShortcut(QKeySequence("a"), self, self.ai_search_mode)  # AI/LLM search
        QShortcut(QKeySequence("F1"), self, self.show_help)  # Help
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
        
        # External browser integration
        QShortcut(QKeySequence("Ctrl+Shift+O"), self, self.open_in_external_browser)  # Open in external browser
        QShortcut(QKeySequence("e"), self, self.open_in_external_browser)  # Quick external browser
        
        # Screenshot analysis
        QShortcut(QKeySequence("Ctrl+Shift+S"), self, self.screenshot_analysis_mode)  # Screenshot + AI analysis

    def keyPressEvent(self, event):
        if self.mode == "NORMAL":
            key = event.text().lower()
            if key in [
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
                "e",
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

    def cycle_command_mode(self, direction: int = 1) -> None:
        """Cycle through command prompt modes with Ctrl+Arrow keys.
        
        Args:
            direction: 1 for next mode, -1 for previous mode
        """
        if self.mode != "COMMAND":
            return
        
        current_prefix = self.active_command_prefix or ":"
        
        try:
            current_index = COMMAND_PROMPT_ORDER.index(current_prefix)
            next_index = (current_index + direction) % len(COMMAND_PROMPT_ORDER)
            next_prefix = COMMAND_PROMPT_ORDER[next_index]
            
            # Save current input text
            current_text = self.command_line.text() if hasattr(self, "command_line") else ""
            
            # Switch to new mode
            self.show_command_line(next_prefix)
            
            # Restore text if it makes sense (empty or compatible)
            if current_text and hasattr(self, "command_line"):
                self.command_line.setText(current_text)
        except ValueError:
            # Current prefix not in order list, default to command mode
            self.show_command_line(":")

    def command_mode(self):
        if self.mode == "NORMAL":
            self.mode = "COMMAND"
            self.show_command_line(":")

    def search_mode(self):
        if self.mode == "NORMAL":
            self.mode = "COMMAND"
            self.show_command_line("/")

    def show_url_history(self):
        """Show URL history in a popup when in 'o' mode."""
        if self.mode != "COMMAND" or self.active_command_prefix != "o ":
            return
        
        if not self.url_history:
            self._show_notification("No URL history available", timeout=2000)
            return
        
        # Show notification with recent URLs
        recent_urls = self.url_history[:5]
        history_preview = "\n".join([f"{i+1}. {url[:60]}" for i, url in enumerate(recent_urls)])
        self._show_notification(
            f"Recent URLs (press Tab to cycle):\n{history_preview}", 
            timeout=5000
        )

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

    def screenshot_analysis_mode(self):
        """Capture screenshot and prompt user for question about it."""
        if self.mode != "NORMAL":
            return
        
        self._show_notification("Capturing screenshot...", timeout=2000)
        
        # Capture screenshot asynchronously
        if hasattr(self, "browser") and self.browser:
            def on_screenshot_captured(image_bytes: bytes):
                if not image_bytes:
                    self._show_notification("Screenshot capture failed", timeout=2500)
                    return
                
                # Store screenshot data for the AI worker
                self._pending_screenshot = image_bytes
                
                # Show command palette for user to ask a question
                self.mode = "SCREENSHOT_ANALYSIS"
                self.show_command_line("📷 ")
                self._show_notification("Screenshot captured! Ask a question about it.", timeout=2500)
            
            # Use Qt WebEngineView's grab method
            try:
                pixmap = self.browser.grab()
                from PySide6.QtCore import QBuffer, QIODevice
                from PySide6.QtGui import QImage
                
                # Convert pixmap to QImage
                image = pixmap.toImage()
                
                # Convert to PNG bytes
                buffer = QBuffer()
                buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                image.save(buffer, "PNG")
                
                # Get the bytes
                image_bytes = buffer.data().data()
                buffer.close()
                
                on_screenshot_captured(image_bytes)
            except Exception as e:
                print(f"Error capturing screenshot: {e}")
                self._show_notification("Screenshot capture failed", timeout=2500)
        else:
            self._show_notification("Browser not available", timeout=2500)

    def show_help(self):
        if self.mode == "NORMAL":
            help_content = self.get_help_content()
            encoded_html = base64.b64encode(help_content.encode("utf-8")).decode(
                "ascii"
            )
            help_url = f"data:text/html;base64,{encoded_html}"
            self.open_url(help_url)

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
        elif command.startswith("📷 "):
            query = command[3:].strip()
            if query:
                print(f"Executing screenshot analysis with query: '{query}'")
                self._start_screenshot_analysis(query)
            else:
                self._show_notification("Please provide a question about the screenshot", timeout=2500)
                self.normal_mode()

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
        elif cmd.startswith("browser"):
            # Handle external browser commands
            if cmd == "browser":
                # Open current page in default external browser
                self.open_in_external_browser()
            elif cmd == "browser-list":
                # List available browsers
                self.list_available_browsers()
            elif cmd.startswith("browser "):
                # Parse browser command: "browser firefox" or "browser firefox https://example.com"
                parts = cmd[8:].split(' ', 1)
                if len(parts) == 1:
                    # Just browser name, open current page
                    browser_name = parts[0]
                    if browser_name in ['list', '-list']:
                        self.list_available_browsers()
                    else:
                        self.open_in_specific_browser(browser_name)
                else:
                    # Browser name and URL
                    browser_name, url = parts
                    self.open_in_specific_browser(browser_name, url)
        elif cmd.startswith("bm"):
            # Handle bookmark commands
            self.execute_bookmark_command(cmd)
        elif cmd in ["ext", "external"]:
            # Shorthand for opening in external browser
            self.open_in_external_browser()
        elif cmd.startswith("files") or cmd.startswith("fb"):
            # File browser commands
            if cmd in ["files", "fb"]:
                # Show file browser for current directory
                self.show_file_browser()
            elif cmd.startswith("files "):
                # Browse specific directory
                path = cmd[6:].strip()
                self.show_file_browser(path)
            elif cmd.startswith("fb "):
                # Browse specific directory (shorthand)
                path = cmd[3:].strip()
                self.show_file_browser(path)
        elif cmd.startswith("index"):
            # Index files with embeddings
            if cmd.startswith("index "):
                path = cmd[6:].strip()
                self.index_directory(path)
            else:
                self.index_directory()
        elif cmd.startswith("search-files"):
            # Search indexed files
            if cmd.startswith("search-files "):
                query = cmd[13:].strip()
                self.search_indexed_files(query)
            else:
                self._show_notification("Usage: :search-files <query>", timeout=2000)
        elif cmd.startswith("export"):
            # Handle export commands
            if cmd in ["export-html", "export html"]:
                self.export_page_html()
            elif cmd in ["export-md", "export-markdown", "export md"]:
                self.export_page_markdown()
            elif cmd in ["export-pdf", "export pdf"]:
                self.export_page_pdf()
            elif cmd == "export":
                # Show export help
                self._show_notification(
                    "Export commands:\n"
                    ":export-html - Save page as HTML\n"
                    ":export-md - Convert page to Markdown\n"
                    ":export-pdf - Save page as PDF",
                    timeout=5000
                )
        elif cmd.isdigit():
            buf_num = int(cmd) - 1
            if 0 <= buf_num < len(self.buffers):
                self.current_buffer = buf_num
                self.browser.load(QUrl(self.buffers[self.current_buffer]))
                self.update_title()

    def open_in_external_browser(self, url: Optional[str] = None) -> None:
        """Open URL in system default browser or specified browser."""
        if url is None:
            # Get current page URL
            current_url = self.browser.url().toString()
            if not current_url or current_url.startswith("data:"):
                self._show_notification("Cannot open data URLs in external browser", timeout=2500)
                return
            url = current_url
        
        try:
            # Clean up the URL if it's a data URL or local content
            if url.startswith("data:"):
                self._show_notification("Cannot open data URLs in external browser", timeout=2500)
                return
            
            # Ensure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            webbrowser.open(url)
            self._show_notification(f"Opened in external browser: {url[:50]}...", timeout=2000)
            
        except Exception as e:
            print(f"Failed to open URL in external browser: {e}")
            self._show_notification("Failed to open URL in external browser", timeout=2500)

    def list_available_browsers(self) -> None:
        """Show available browsers on the system."""
        try:
            # Get all registered browsers
            browsers = []
            
            # Add common browser names that webbrowser might recognize
            common_browsers = [
                'firefox', 'chrome', 'chromium', 'safari', 'edge', 'opera'
            ]
            
            for browser in common_browsers:
                try:
                    browser_obj = webbrowser.get(browser)
                    if browser_obj:
                        browsers.append(browser)
                except webbrowser.Error:
                    continue
            
            if browsers:
                browser_list = ", ".join(browsers)
                self._show_notification(f"Available browsers: {browser_list}", timeout=4000)
            else:
                self._show_notification("Using system default browser", timeout=2000)
                
        except Exception as e:
            print(f"Failed to list browsers: {e}")
            self._show_notification("Could not detect available browsers", timeout=2500)

    def open_in_specific_browser(self, browser_name: str, url: Optional[str] = None) -> None:
        """Open URL in a specific browser."""
        if url is None:
            current_url = self.browser.url().toString()
            if not current_url or current_url.startswith("data:"):
                self._show_notification("Cannot open data URLs in external browser", timeout=2500)
                return
            url = current_url
        
        try:
            if url.startswith("data:"):
                self._show_notification("Cannot open data URLs in external browser", timeout=2500)
                return
            
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Try to get the specific browser
            browser_obj = webbrowser.get(browser_name)
            browser_obj.open(url)
            self._show_notification(f"Opened in {browser_name}: {url[:40]}...", timeout=2000)
            
        except webbrowser.Error:
            self._show_notification(f"Browser '{browser_name}' not found", timeout=2500)
        except Exception as e:
            print(f"Failed to open URL in {browser_name}: {e}")
            self._show_notification(f"Failed to open URL in {browser_name}", timeout=2500)

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

        # Handle data URLs differently
        if url.startswith("data:"):
            qurl = QUrl(url)
            print(f"Loading data URL, length: {len(url)}")
        # Handle file:// URLs  
        elif url.startswith("file://"):
            qurl = QUrl(url)
            print(f"Loading file URL: {url}")
        else:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            qurl = QUrl(url)

        # Track URL history (skip data URLs)
        if not url.startswith("data:") and url not in self.url_history:
            self.url_history.insert(0, url)
            # Keep only last N URLs
            if len(self.url_history) > self.url_history_max:
                self.url_history = self.url_history[:self.url_history_max]

        # Add to buffers if not already there
        if url not in self.buffers:
            self.buffers.append(url)
            self.current_buffer = len(self.buffers) - 1
        else:
            self.current_buffer = self.buffers.index(url)

        if self.initial_load:
            self.browser.load(qurl)
            self.initial_load = False
        else:
            self.setWindowTitle("Switching...")
            self.browser.load(qurl)
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
        """Display a detailed list of all buffers with quick switching."""
        if not self.buffers:
            self._show_notification("No buffers open", timeout=2000)
            return
        
        # Create a detailed HTML view of buffers
        buffer_rows = []
        for i, url in enumerate(self.buffers):
            is_current = i == self.current_buffer
            current_marker = "►" if is_current else " "
            row_class = "current" if is_current else ""
            
            # Extract meaningful title from URL
            if url.startswith("data:"):
                display_url = "AI Generated Content"
                domain = "data:"
            elif url.startswith("file://"):
                display_url = url[7:]  # Remove file://
                domain = "file:"
            else:
                display_url = url
                # Extract domain
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    domain = parsed.netloc or parsed.scheme
                except Exception:
                    domain = url.split('/')[0]
            
            # Truncate long URLs
            if len(display_url) > 80:
                display_url = display_url[:77] + "..."
            
            buffer_rows.append(f"""
            <tr class="{row_class}" onclick="window.switchBuffer({i})">
                <td class="marker">{current_marker}</td>
                <td class="index">{i + 1}</td>
                <td class="domain">{html.escape(domain)}</td>
                <td class="url">{html.escape(display_url)}</td>
            </tr>
            """)
        
        buffers_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Buffers</title>
            <style>
                body {{
                    background: #1a1a1a;
                    color: #e0e0e0;
                    font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', monospace;
                    padding: 30px;
                    margin: 0;
                }}
                h1 {{
                    color: #4a9eff;
                    font-size: 28px;
                    margin-bottom: 10px;
                }}
                .subtitle {{
                    color: #888;
                    font-size: 14px;
                    margin-bottom: 30px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    background: #242424;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                }}
                th {{
                    background: #2d2d2d;
                    color: #4a9eff;
                    text-align: left;
                    padding: 12px 16px;
                    font-weight: 600;
                    font-size: 13px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                tr {{
                    border-bottom: 1px solid #333;
                    cursor: pointer;
                    transition: background-color 0.2s;
                }}
                tr:hover {{
                    background: #2a2a2a;
                }}
                tr.current {{
                    background: #2d3d4d;
                }}
                tr.current:hover {{
                    background: #334455;
                }}
                td {{
                    padding: 12px 16px;
                    font-size: 14px;
                }}
                td.marker {{
                    width: 30px;
                    color: #4a9eff;
                    font-weight: bold;
                    text-align: center;
                }}
                td.index {{
                    width: 50px;
                    color: #888;
                    font-weight: 600;
                }}
                td.domain {{
                    width: 200px;
                    color: #9370db;
                    font-weight: 500;
                }}
                td.url {{
                    color: #d0d0d0;
                    word-break: break-all;
                }}
                .help {{
                    margin-top: 30px;
                    padding: 20px;
                    background: #242424;
                    border-radius: 8px;
                    border-left: 3px solid #4a9eff;
                }}
                .help h3 {{
                    color: #4a9eff;
                    margin-top: 0;
                    font-size: 16px;
                }}
                .help p {{
                    margin: 8px 0;
                    color: #aaa;
                    font-size: 13px;
                }}
                .key {{
                    background: #333;
                    padding: 2px 8px;
                    border-radius: 4px;
                    color: #4a9eff;
                    font-family: monospace;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <h1>📑 Buffer List</h1>
            <p class="subtitle">Click a row or press the buffer number to switch</p>
            
            <table>
                <thead>
                    <tr>
                        <th></th>
                        <th>#</th>
                        <th>Domain</th>
                        <th>URL</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(buffer_rows)}
                </tbody>
            </table>
            
            <div class="help">
                <h3>💡 Quick Navigation</h3>
                <p><span class="key">:1</span>, <span class="key">:2</span>, etc. - Jump to buffer by number</p>
                <p><span class="key">n</span> / <span class="key">p</span> - Next/Previous buffer</p>
                <p><span class="key">:bn</span> / <span class="key">:bp</span> - Next/Previous buffer (command mode)</p>
                <p><span class="key">x</span> or <span class="key">:bd</span> - Close current buffer</p>
                <p><span class="key">Escape</span> - Return to normal mode</p>
            </div>
            
            <script>
                function switchBuffer(index) {{
                    // Note: This won't work in real use since we can't communicate back to Qt easily
                    // The main way to switch is still via :1, :2, etc. commands
                    console.log('Switch to buffer', index);
                }}
            </script>
        </body>
        </html>
        """
        
        self.open_url(to_data_url(buffers_html))

    def show_file_browser(self, path: Optional[str] = None):
        """Display file browser for the given path."""
        from pathlib import Path
        from .storage.file_browser import FileBrowser
        from .rendering.html import render_template, create_data_url
        
        try:
            # Initialize file browser
            if path:
                target_path = Path(path).expanduser().resolve()
            else:
                target_path = Path.home()
            
            browser = FileBrowser(target_path)
            
            # Get directory listing
            entries = browser.list_directory()
            
            # Prepare context for template
            context = {
                "current_path": str(browser.current_path),
                "parent_path": str(browser.current_path.parent) if browser.current_path.parent != browser.current_path else None,
                "home_path": str(Path.home()),
                "entries": [entry.to_dict() for entry in entries],
            }
            
            # Render template
            html_content = render_template("file_browser.html", context)
            
            # Open in browser
            self.open_url(create_data_url(html_content))
            
        except Exception as e:
            error_msg = f"Failed to browse directory: {e}"
            self._show_notification(error_msg, timeout=3000)
            print(error_msg)

    def index_directory(self, path: Optional[str] = None):
        """Index files in directory with embeddings."""
        from pathlib import Path
        from .storage.file_browser import FileIndexer
        
        try:
            # Determine target path
            if path:
                target_path = Path(path).expanduser().resolve()
            else:
                target_path = Path.home()
            
            if not target_path.is_dir():
                self._show_notification(f"Not a directory: {target_path}", timeout=2000)
                return
            
            # Show progress notification
            self._show_notification(f"Indexing files in {target_path}...", timeout=2000)
            
            # Index files
            indexer = FileIndexer()
            count = indexer.index_directory(target_path, recursive=True, max_files=100)
            
            # Show completion
            self._show_notification(f"Indexed {count} files", timeout=3000)
            
        except Exception as e:
            error_msg = f"Failed to index directory: {e}"
            self._show_notification(error_msg, timeout=3000)
            print(error_msg)

    def search_indexed_files(self, query: str):
        """Search indexed files by semantic similarity."""
        from .storage.file_browser import FileIndexer
        from .rendering.html import render_template, create_data_url
        
        try:
            indexer = FileIndexer()
            results = indexer.search_files(query, n_results=10)
            
            if not results:
                self._show_notification("No matching files found", timeout=2000)
                return
            
            # Build HTML for results
            results_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>File Search Results</title>
    <style>
        body {{
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #e0e0e0;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 20px;
            backdrop-filter: blur(10px);
        }}
        h1 {{ color: #4fc3f7; }}
        .query {{
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .result {{
            background: rgba(255, 255, 255, 0.05);
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 10px;
            transition: all 0.2s;
        }}
        .result:hover {{
            background: rgba(255, 255, 255, 0.1);
            transform: translateX(5px);
        }}
        .file-path {{
            color: #81c784;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .file-type {{
            color: #9e9e9e;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 File Search Results</h1>
        <div class="query">
            <strong>Query:</strong> {html.escape(query)}
        </div>
        <div class="results">
"""
            
            for result in results:
                file_path = result.get('path', 'Unknown')
                file_name = result.get('name', 'Unknown')
                file_type = result.get('type', 'unknown')
                
                results_html += f"""
            <div class="result">
                <div class="file-path">📄 {html.escape(file_name)}</div>
                <div style="color: #b0b0b0; font-size: 0.85em;">{html.escape(file_path)}</div>
                <div class="file-type">Type: {html.escape(file_type)}</div>
            </div>
"""
            
            results_html += """
        </div>
    </div>
</body>
</html>
"""
            
            self.open_url(create_data_url(results_html))
            
        except Exception as e:
            error_msg = f"Failed to search files: {e}"
            self._show_notification(error_msg, timeout=3000)
            print(error_msg)
    def execute_bookmark_command(self, cmd: str) -> None:
        """Handle bookmark subcommands."""
        if not self.bookmark_store:
            self._show_notification("Bookmark store not initialized", timeout=2500)
            return
        
        parts = cmd.split(maxsplit=2)
        subcommand = parts[1] if len(parts) > 1 else "list"
        
        if subcommand == "add":
            # Add current page as bookmark
            current_url = self.browser.url().toString()
            if not current_url or current_url.startswith("data:"):
                self._show_notification("Cannot bookmark data URLs", timeout=2500)
                return
            
            # Get title from page or use URL
            title = current_url
            try:
                # Try to get page title
                title = self.browser.page().title() or current_url
            except Exception:
                pass
            
            # Parse additional args (tags)
            tags = []
            if len(parts) > 2:
                tags = [t.strip() for t in parts[2].split(",")]
            
            bookmark = Bookmark(
                id=str(uuid.uuid4()),
                title=title,
                url=current_url,
                tags=tags,
                bookmark_type="url",
            )
            self.bookmark_store.add(bookmark)
            self._show_notification(f"Bookmark added: {title[:40]}", timeout=2500)
        
        elif subcommand == "list":
            # Show all bookmarks
            self.show_bookmarks()
        
        elif subcommand == "search":
            # Search bookmarks
            if len(parts) < 3:
                self._show_notification("Usage: :bm search <query>", timeout=2500)
                return
            query = parts[2]
            self.show_bookmarks(query=query)
        
        elif subcommand == "del" or subcommand == "delete":
            # Delete a bookmark by ID
            if len(parts) < 3:
                self._show_notification("Usage: :bm del <id>", timeout=2500)
                return
            bookmark_id = parts[2]
            if self.bookmark_store.remove(bookmark_id):
                self._show_notification(f"Bookmark {bookmark_id[:8]} deleted", timeout=2500)
            else:
                self._show_notification(f"Bookmark {bookmark_id[:8]} not found", timeout=2500)
        
        elif subcommand == "tags":
            # Show all tags
            tags = self.bookmark_store.get_all_tags()
            if tags:
                tags_html = "<br>".join(f"#{tag}" for tag in tags)
                self._show_notification(f"Tags: {', '.join(tags)}", timeout=3000)
            else:
                self._show_notification("No tags found", timeout=2000)
        
        else:
            self._show_notification(f"Unknown bookmark command: {subcommand}", timeout=2500)

    def show_bookmarks(self, query: Optional[str] = None) -> None:
        """Display bookmarks in a styled HTML view."""
        if not self.bookmark_store:
            self._show_notification("Bookmark store not initialized", timeout=2500)
            return
        
        # Get bookmarks based on query
        if query:
            bookmarks = self.bookmark_store.search(query)
        else:
            bookmarks = self.bookmark_store.list_all()
        
        # Get statistics
        all_tags = self.bookmark_store.get_all_tags()
        
        # Render template
        html_content = render_template(
            "bookmarks.html",
            {
                "bookmarks": bookmarks,
                "total_count": len(self.bookmark_store.list_all()),
                "tag_count": len(all_tags),
                "query": query,
            }
        )
        
        # Load in browser
        self.open_url(create_data_url(html_content))

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

    def export_page_html(self):
        """Export current page as HTML snapshot."""
        if not hasattr(self, "browser") or self.browser is None:
            self._show_notification("Browser instance unavailable", timeout=2500)
            return

        def handle_html(html_content: str) -> None:
            try:
                exporter = PageExporter()
                url = self._current_url() or "page"
                output_path = exporter.export_html(html_content, url)
                self._show_notification(
                    f"HTML exported to:\n{output_path}",
                    timeout=5000
                )
            except Exception as e:
                self._show_notification(
                    f"Export failed: {str(e)}",
                    timeout=3000
                )

        self.browser.page().toHtml(handle_html)

    def export_page_markdown(self):
        """Export current page as Markdown."""
        if not hasattr(self, "browser") or self.browser is None:
            self._show_notification("Browser instance unavailable", timeout=2500)
            return

        def handle_html(html_content: str) -> None:
            try:
                exporter = PageExporter()
                url = self._current_url() or "page"
                output_path = exporter.export_markdown(html_content, url)
                self._show_notification(
                    f"Markdown exported to:\n{output_path}",
                    timeout=5000
                )
            except Exception as e:
                self._show_notification(
                    f"Export failed: {str(e)}",
                    timeout=3000
                )

        self.browser.page().toHtml(handle_html)

    def export_page_pdf(self):
        """Export current page as PDF."""
        if not hasattr(self, "browser") or self.browser is None:
            self._show_notification("Browser instance unavailable", timeout=2500)
            return

        def handle_html(html_content: str) -> None:
            try:
                exporter = PageExporter()
                url = self._current_url() or "page"
                output_path = exporter.export_pdf(html_content, url)
                self._show_notification(
                    f"PDF exported to:\n{output_path}",
                    timeout=5000
                )
            except Exception as e:
                self._show_notification(
                    f"Export failed: {str(e)}",
                    timeout=3000
                )

        self.browser.page().toHtml(handle_html)

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
                <td>Show detailed buffer list with URLs</td>
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
                <td>Open URL (with Tab completion for history)</td>
            </tr>
            <tr>
                <td><span class="key">e</span></td>
                <td>Open current page in external browser</td>
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
        <h2>Command Prompt Features</h2>
        <table>
            <tr>
                <td><span class="key">Ctrl+Up/Down</span></td>
                <td>Cycle between command modes (:, /, o, s, a)</td>
            </tr>
            <tr>
                <td><span class="key">Tab</span></td>
                <td>Complete commands (:) or cycle URL history (o)</td>
            </tr>
            <tr>
                <td><span class="key">Ctrl+Space</span></td>
                <td>Show recent URL history (in o mode)</td>
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
            <tr>
                <td><span class="key">Ctrl+Shift+O</span></td>
                <td>Open current page in external browser</td>
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
            <tr>
                <td><span class="cmd">:browser</span></td>
                <td>Open current page in external browser</td>
            </tr>
            <tr>
                <td><span class="cmd">:browser &lt;name&gt;</span></td>
                <td>Open in specific browser (firefox, chrome, etc.)</td>
            </tr>
            <tr>
                <td><span class="cmd">:browser-list</span></td>
                <td>List available browsers</td>
            </tr>
            <tr>
                <td><span class="cmd">:ext</span></td>
                <td>Open current page in external browser (shorthand)</td>
            </tr>
            <tr>
                <td><span class="cmd">:files [path]</span></td>
                <td>Browse local files and directories</td>
            </tr>
            <tr>
                <td><span class="cmd">:fb [path]</span></td>
                <td>File browser (shorthand)</td>
            </tr>
            <tr>
                <td><span class="cmd">:index [path]</span></td>
                <td>Index files with embeddings for search</td>
            </tr>
            <tr>
                <td><span class="cmd">:search-files &lt;query&gt;</span></td>
                <td>Search indexed files semantically</td>
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
