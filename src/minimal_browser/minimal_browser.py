#!/usr/bin/env python3
# ruff: noqa: E402

import sys
import json
import os
import base64
import html
import requests  # type: ignore[import-untyped]
from typing import MutableMapping, Optional, cast


from PySide6.QtCore import QUrl, Qt, QTimer, QThread, Signal as pyqtSignal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QLabel,
    QLineEdit,
    QTabBar,
    QProgressBar,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import (
    QWebEngineProfile,
    QWebEngineSettings,
    QWebEnginePage,
)

from .engines.qt_engine import QtWebEngine
from .ai.schemas import AIAction, ConversationMemory
from .ai.tools import ResponseProcessor, URLBuilder
from .storage.conversations import ConversationLog


def to_data_url(html: str) -> str:
    """Encode HTML content into a data URL with base64 encoding"""
    encoded_html = base64.b64encode(html.encode("utf-8")).decode("ascii")
    return f"data:text/html;base64,{encoded_html}"


OS_ENV: MutableMapping[str, str] = cast(MutableMapping[str, str], os.environ)  # type: ignore[attr-defined]


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
    ):
        super().__init__()
        self.query = query
        self.current_url = current_url
        self.history = list(history or [])

    def run(self):
        try:
            print(f"AI Worker starting for query: {self.query}")
            self.progress_update.emit("Analyzing request...")

            response = self.get_ai_response(self.query, self.current_url)
            print(f"AI Worker got response: {response[:100]}...")

            self.response_ready.emit("success", response)
        except Exception as e:
            print(f"AI Worker error: {e}")
            self.response_ready.emit("error", str(e))

    def get_ai_response(self, query, current_url):
        """Get AI response from OpenRouter API"""
        # Get API key from environment variable
        api_key = OS_ENV.get("OPENROUTER_API_KEY")
        if not api_key:
            raise Exception("OPENROUTER_API_KEY environment variable not set")

        # Prepare the system prompt
        system_prompt = """You are a browser AI assistant. Based on the user's request, you should respond with one of these formats:

1. NAVIGATE:<url> - if user wants to go to a specific website
2. SEARCH:<query> - if user wants to search for something
3. HTML:<html_content> - if user wants you to create/generate content

Examples:
- "go to github" → NAVIGATE:https://github.com
- "search for python tutorials" → SEARCH:python tutorials  
- "create a todo list" → HTML:<complete html for todo app>
- "make a calculator" → HTML:<complete html for calculator>
- "explain quantum physics" → HTML:<complete html explanation page>

Current page context: """ + (current_url if current_url else "No current page")

        # Prepare the API request
        messages = [
            {"role": "system", "content": system_prompt},
            *self.history,
            {"role": "user", "content": query},
        ]

        data = {
            "model": "openai/gpt-5-chat",
            "messages": messages,
            "stream": True,
        }

        # Make streaming API request
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        buffer = ""
        ai_response = ""

        with requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            stream=True,
        ) as r:
            r.raise_for_status()

            for chunk in r.iter_content(chunk_size=1024, decode_unicode=True):
                buffer += chunk
                while True:
                    try:
                        # Find the next complete SSE line
                        line_end = buffer.find("\n")
                        if line_end == -1:
                            break
                        line = buffer[:line_end].strip()
                        buffer = buffer[line_end + 1 :]

                        if line.startswith("data: "):
                            data_content = line[6:]
                            if data_content == "[DONE]":
                                break
                            try:
                                data_obj = json.loads(data_content)
                                content = data_obj["choices"][0]["delta"].get("content")
                                if content:
                                    ai_response += content
                                    self.streaming_chunk.emit(content)
                            except json.JSONDecodeError:
                                pass
                    except Exception:
                        break

        # If response doesn't match our expected formats, promote it to HTML
        if not any(
            ai_response.startswith(prefix)
            for prefix in ["NAVIGATE:", "SEARCH:", "HTML:"]
        ):
            ai_response = f"HTML:{self.wrap_response_in_html(ai_response, query)}"

        action = ResponseProcessor.parse_response(ai_response)
        action_type, payload = ResponseProcessor.action_to_tuple(action)
        prefix_map = {
            "navigate": "NAVIGATE:",
            "search": "SEARCH:",
            "html": "HTML:",
        }
        prefix = prefix_map.get(action_type, "HTML:")
        return f"{prefix}{payload}"

    def wrap_response_in_html(self, content, query):
        """Wrap AI text response in nice HTML"""
        # Convert markdown-like formatting to HTML
        content = content.replace("**", "<strong>").replace("**", "</strong>")
        content = content.replace("*", "<em>").replace("*", "</em>")
        content = content.replace("\n\n", "</p><p>")
        content = content.replace("\n", "<br>")

        return f"""<!DOCTYPE html>
<html>
<head>
    <title>AI Response</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; margin: 0; padding: 40px; min-height: 100vh; line-height: 1.6;
        }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .content {{ 
            background: rgba(255,255,255,0.1); 
            padding: 30px; 
            border-radius: 15px; 
            backdrop-filter: blur(10px);
        }}
        .query {{ 
            background: rgba(0,0,0,0.2); 
            padding: 15px; 
            border-radius: 8px; 
            margin: 20px 0;
            font-style: italic;
        }}
        h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        p {{ margin-bottom: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Assistant</h1>
        </div>
        <div class="content">
            <div class="query">{query}</div>
            <p>{content}</p>
        </div>
    </div>
</body>
</html>"""

    def generate_html_page(self, query):
        """Generate a custom HTML page based on query"""
        return f"""HTML:<!DOCTYPE html>
<html>
<head>
    <title>AI Generated Page</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; margin: 0; padding: 40px; min-height: 100vh;
        }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        h1 {{ font-size: 2.5em; margin-bottom: 20px; }}
        .card {{ background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; margin: 20px 0; }}
        .btn {{ background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Response</h1>
        <div class="card">
            <h2>Query: {query}</h2>
            <p>I've created this custom page based on your request. This demonstrates how the AI can generate HTML content directly in the browser.</p>
            <button class="btn" onclick="alert('AI-generated interaction!')">Click me!</button>
        </div>
        <div class="card">
            <h3>What I can do:</h3>
            <ul>
                <li>Navigate to websites</li>
                <li>Generate custom HTML pages</li>
                <li>Create interactive tools</li>
                <li>Provide explanations</li>
                <li>Search the web</li>
            </ul>
        </div>
    </div>
</body>
</html>"""

    def generate_todo_html(self):
        """Generate a todo list HTML page"""
        return """HTML:<!DOCTYPE html>
<html>
<head>
    <title>AI Todo List</title>
    <style>
        body { font-family: system-ui; background: #f5f5f5; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        .input-group { display: flex; margin-bottom: 20px; }
        input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px 0 0 5px; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 0 5px 5px 0; cursor: pointer; }
        .todo-item { padding: 10px; border-bottom: 1px solid #eee; display: flex; align-items: center; }
        .todo-item.done { text-decoration: line-through; opacity: 0.6; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📝 AI Todo List</h1>
        <div class="input-group">
            <input type="text" id="todoInput" placeholder="Add a new task..." onkeypress="if(event.key==='Enter') addTodo()">
            <button onclick="addTodo()">Add</button>
        </div>
        <div id="todoList"></div>
    </div>
    <script>
        let todos = [];
        function addTodo() {
            const input = document.getElementById('todoInput');
            if (input.value.trim()) {
                todos.push({text: input.value, done: false});
                input.value = '';
                renderTodos();
            }
        }
        function toggleTodo(index) {
            todos[index].done = !todos[index].done;
            renderTodos();
        }
        function renderTodos() {
            const list = document.getElementById('todoList');
            list.innerHTML = todos.map((todo, i) => 
                `<div class="todo-item ${todo.done ? 'done' : ''}" onclick="toggleTodo(${i})">
                    ${todo.text}
                </div>`
            ).join('');
        }
    </script>
</body>
</html>"""

    def generate_calculator_html(self):
        """Generate a calculator HTML page"""
        return """HTML:<!DOCTYPE html>
<html>
<head>
    <title>AI Calculator</title>
    <style>
        body { font-family: system-ui; background: #2c3e50; color: white; margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .calculator { background: #34495e; padding: 20px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
        .display { width: 100%; height: 60px; font-size: 24px; text-align: right; padding: 10px; margin-bottom: 15px; border: none; background: #2c3e50; color: white; border-radius: 5px; }
        .buttons { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
        button { height: 60px; font-size: 18px; border: none; border-radius: 5px; cursor: pointer; transition: all 0.2s; }
        .num { background: #95a5a6; color: white; }
        .op { background: #e74c3c; color: white; }
        .eq { background: #27ae60; color: white; }
        button:hover { transform: scale(1.05); }
    </style>
</head>
<body>
    <div class="calculator">
        <input type="text" class="display" id="display" readonly>
        <div class="buttons">
            <button onclick="clearDisplay()" class="op">C</button>
            <button onclick="deleteLast()" class="op">⌫</button>
            <button onclick="appendToDisplay('/')" class="op">÷</button>
            <button onclick="appendToDisplay('*')" class="op">×</button>
            <button onclick="appendToDisplay('7')" class="num">7</button>
            <button onclick="appendToDisplay('8')" class="num">8</button>
            <button onclick="appendToDisplay('9')" class="num">9</button>
            <button onclick="appendToDisplay('-')" class="op">-</button>
            <button onclick="appendToDisplay('4')" class="num">4</button>
            <button onclick="appendToDisplay('5')" class="num">5</button>
            <button onclick="appendToDisplay('6')" class="num">6</button>
            <button onclick="appendToDisplay('+')" class="op">+</button>
            <button onclick="appendToDisplay('1')" class="num">1</button>
            <button onclick="appendToDisplay('2')" class="num">2</button>
            <button onclick="appendToDisplay('3')" class="num">3</button>
            <button onclick="calculate()" class="eq" style="grid-row: span 2;">=</button>
            <button onclick="appendToDisplay('0')" class="num" style="grid-column: span 2;">0</button>
            <button onclick="appendToDisplay('.')" class="num">.</button>
        </div>
    </div>
    <script>
        function appendToDisplay(value) {
            document.getElementById('display').value += value;
        }
        function clearDisplay() {
            document.getElementById('display').value = '';
        }
        function deleteLast() {
            const display = document.getElementById('display');
            display.value = display.value.slice(0, -1);
        }
        function calculate() {
            try {
                const result = eval(document.getElementById('display').value.replace('×', '*').replace('÷', '/'));
                document.getElementById('display').value = result;
            } catch (e) {
                document.getElementById('display').value = 'Error';
            }
        }
    </script>
</body>
</html>"""

    def generate_explanation_page(self, query):
        """Generate an explanation page"""
        return f"""HTML:<!DOCTYPE html>
<html>
<head>
    <title>AI Explanation</title>
    <style>
        body {{ font-family: Georgia, serif; background: #f8f9fa; margin: 0; padding: 40px; line-height: 1.6; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 20px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        .highlight {{ background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; }}
        .info-box {{ background: #d1ecf1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 AI Explanation</h1>
        <div class="highlight">
            <strong>Your Question:</strong> {query}
        </div>
        <div class="info-box">
            <p>This is a simulated AI explanation. In a real implementation, this would connect to an AI service like OpenAI's GPT or a local language model to provide detailed explanations.</p>
            <p>The AI could analyze your question and provide:</p>
            <ul>
                <li>Detailed explanations with examples</li>
                <li>Step-by-step breakdowns</li>
                <li>Related concepts and links</li>
                <li>Interactive demonstrations</li>
            </ul>
        </div>
        <h2>How it works:</h2>
        <p>When you press <strong>Space</strong> in the browser, you can ask questions and the AI will either:</p>
        <ol>
            <li><strong>Navigate</strong> to relevant websites</li>
            <li><strong>Generate HTML</strong> content directly in the browser</li>
            <li><strong>Create tools</strong> like calculators, todo lists, etc.</li>
            <li><strong>Provide explanations</strong> like this page</li>
        </ol>
    </div>
</body>
</html>"""

    def generate_info_page(self, query):
        """Generate a general info page"""
        return f"""HTML:<!DOCTYPE html>
<html>
<head>
    <title>AI Response</title>
    <style>
        body {{ font-family: system-ui; background: linear-gradient(45deg, #667eea, #764ba2); color: white; margin: 0; padding: 40px; min-height: 100vh; }}
        .container {{ max-width: 700px; margin: 0 auto; }}
        .card {{ background: rgba(255,255,255,0.15); backdrop-filter: blur(10px); padding: 30px; border-radius: 15px; margin: 20px 0; }}
        h1 {{ font-size: 2.2em; margin-bottom: 20px; }}
        .query {{ background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; font-style: italic; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Assistant</h1>
        <div class="card">
            <div class="query">"{query}"</div>
            <p>I understand you're asking about: <strong>{query}</strong></p>
            <p>This is a demonstration of the native AI integration. In a full implementation, I would:</p>
            <ul>
                <li>Analyze your request using natural language processing</li>
                <li>Determine the best response type (navigation, HTML generation, or explanation)</li>
                <li>Provide contextual and helpful responses</li>
                <li>Learn from the current page context</li>
            </ul>
        </div>
        <div class="card">
            <h3>Try asking me to:</h3>
            <ul>
                <li>"Navigate to GitHub"</li>
                <li>"Create a todo list"</li>
                <li>"Make a calculator"</li>
                <li>"Explain quantum computing"</li>
                <li>"Generate an HTML page about cats"</li>
            </ul>
        </div>
    </div>
</body>
</<html>"""


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
        self._init_nav_container()
        self._init_tab_bar()
        self._init_progress_bar()
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
        self.loading_overlay.setStyleSheet("""
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
        """)
        self.loading_overlay.setAlignment(Qt.AlignCenter)
        self.loading_overlay.hide()
        self.loading_overlay.raise_()

    def _init_profile_and_browser(self):
        self.profile = QWebEngineProfile()
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.ForcePersistentCookies
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
        self.setCentralWidget(self.browser)
        self.setMenuBar(None)
        self.statusBar().hide()

    def _init_nav_container(self):
        self.navbar_container = QWidget(self)
        layout = QVBoxLayout(self.navbar_container)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setMenuWidget(self.navbar_container)

    def _init_tab_bar(self):
        self.tab_bar = QTabBar()
        self.tab_bar.setMovable(True)
        self.navbar_container.layout().addWidget(self.tab_bar)
        self.tab_bar.currentChanged.connect(self._on_tab_changed)

    def _init_progress_bar(self):
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        self.navbar_container.layout().addWidget(self.progress_bar)

    def _init_command_line(self):
        self.command_line = QLineEdit(self)
        self.command_line.setStyleSheet(
            "QLineEdit { background-color: rgba(30,30,30,240); color: #fff; }"
        )
        self.command_line.hide()
        self.command_line.returnPressed.connect(self.execute_command)

    def _init_mode_timer(self):
        self.mode_timer = QTimer()
        self.mode_timer.timeout.connect(self.hide_mode_indicator)
        self.mode_timer.setSingleShot(True)

    def _connect_browser_signals(self):
        self.browser.loadStarted.connect(lambda: self.progress_bar.show())
        self.browser.loadProgress.connect(lambda p: self.progress_bar.setValue(p))
        self.browser.loadFinished.connect(lambda ok: self.progress_bar.hide())
        self.browser.loadStarted.connect(lambda: print("Page load started"))
        self.browser.loadProgress.connect(lambda p: print(f"Load progress: {p}%"))
        self.browser.loadFinished.connect(
            lambda ok: print(f"Page load finished: {'SUCCESS' if ok else 'FAILED'}")
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
            ]:
                # Let shortcuts handle these
                pass
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "command_line"):
            width = min(400, self.width() - 40)
            self.command_line.resize(width, 30)
            self.command_line.move((self.width() - width) // 2, self.height() - 50)
        if hasattr(self, "loading_overlay"):
            self.loading_overlay.resize(self.size())

    def normal_mode(self):
        self.mode = "NORMAL"
        self.command_line.hide()
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
            self.show_command_line("研究员 ")

    def show_help(self):
        if self.mode == "NORMAL":
            help_content = self.get_help_content()
            encoded_html = base64.b64encode(help_content.encode("utf-8")).decode(
                "ascii"
            )
            help_url = f"data:text/html;base64,{encoded_html}"
            self.open_url(help_url)

    def show_command_line(self, prefix):
        self.command_line.clear()
        self.command_line.setText(prefix)
        self.command_line.show()
        self.command_line.setFocus()
        self.update_title()

    def execute_command(self):
        command = self.command_line.text()

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

        # Handle data URLs differently
        if url.startswith("data:"):
            qurl = QUrl(url)
            print(f"Loading data URL, length: {len(url)}")
        else:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            qurl = QUrl(url)

        # Add to buffers if not already there
        if url not in self.buffers:
            self.buffers.append(url)
            self.current_buffer = len(self.buffers) - 1
            self.tab_bar.addTab(url.split("/")[2] if "//" in url else url)
        else:
            self.current_buffer = self.buffers.index(url)
        self.tab_bar.setCurrentIndex(self.current_buffer)

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
            self.tab_bar.removeTab(self.current_buffer)
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
        if self.mode == "NORMAL":
            if self.buffers and self.current_buffer < len(self.buffers):
                current_url = self.buffers[self.current_buffer]
                if current_url.startswith("data:"):
                    current_domain = "AI Generated Content"
                elif "/" in current_url and len(current_url.split("/")) > 2:
                    current_domain = current_url.split("/")[2]
                else:
                    current_domain = (
                        current_url[:30] + "..."
                        if len(current_url) > 30
                        else current_url
                    )
                title = (
                    f"[{self.current_buffer + 1}/{len(self.buffers)}] {current_domain}"
                )
            else:
                title = "Vim Browser"
        elif self.mode == "AI_CHAT":
            title = "-- 工程师 CHAT --"
        else:
            title = f"-- {self.mode} --"
        self.setWindowTitle(title)

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

    def _on_tab_changed(self, index):
        if 0 <= index < len(self.buffers):
            self.current_buffer = index
            self.browser.load(QUrl(self.buffers[self.current_buffer]))
            self.update_title()
