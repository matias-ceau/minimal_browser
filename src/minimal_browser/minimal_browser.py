#!/usr/bin/env python3

import sys
import json
import os
import time
import base64
import requests

# Fix for Python 3.13 compatibility
os.environ.setdefault("QT_API", "pyside6")

# Native Wayland support
os.environ.setdefault("QT_QPA_PLATFORM", "wayland")
os.environ.setdefault(
    "QTWEBENGINE_CHROMIUM_FLAGS",
    "--no-sandbox --disable-dev-shm-usage --disable-gpu --disable-gpu-compositing --enable-software-rasterizer --disable-background-timer-throttling --disable-renderer-backgrounding --disable-backgrounding-occluded-windows",
)

# Hyprland-specific fixes
os.environ.setdefault("QT_WAYLAND_DISABLE_WINDOWDECORATION", "0")
os.environ.setdefault("WAYLAND_DISPLAY", os.environ.get("WAYLAND_DISPLAY", "wayland-0"))
os.environ.setdefault("QT_SCALE_FACTOR", "1")
os.environ.setdefault("WLR_NO_HARDWARE_CURSORS", "1")  # Hyprland compatibility
os.environ.setdefault("QT_WAYLAND_FORCE_DPI", "96")

from PySide6.QtCore import QUrl, Qt, QTimer, QThread, Signal as pyqtSignal
from PySide6.QtGui import QKeySequence, QShortcut, QFont, QPainter, QColor
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QLabel,
    QLineEdit,
    QTextEdit,
    QScrollArea,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import (
    QWebEngineProfile,
    QWebEngineSettings,
    QWebEnginePage,
)
import os
from src.storage.conversations import ConversationLog


class AIWorker(QThread):
    """Worker thread for AI API calls with streaming support"""

    response_ready = pyqtSignal(str, str)  # response_type, content
    progress_update = pyqtSignal(str)  # progress message
    streaming_chunk = pyqtSignal(str)  # streaming response chunk

    def __init__(self, query, current_url=""):
        super().__init__()
        self.query = query
        self.current_url = current_url

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
        api_key = os.getenv("OPENROUTER_API_KEY")
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
        data = {
            "model": "openai/gpt-5-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
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

        # If response doesn't start with our expected formats, treat as HTML
        if not any(
            ai_response.startswith(prefix)
            for prefix in ["NAVIGATE:", "SEARCH:", "HTML:"]
        ):
            ai_response = f"HTML:{self.wrap_response_in_html(ai_response, query)}"

        return ai_response

    def removed_fallback_function(self, query):
        """Fallback response when API is not available"""
        print(f"Using fallback response for: {query}")
        query_lower = query.lower()

        if "navigate" in query_lower or "go to" in query_lower or "open" in query_lower:
            if "github" in query_lower:
                return "NAVIGATE:https://github.com"
            elif "reddit" in query_lower:
                return "NAVIGATE:https://reddit.com"
            elif "youtube" in query_lower:
                return "NAVIGATE:https://youtube.com"
            elif "google" in query_lower:
                return "NAVIGATE:https://google.com"
            else:
                return f"SEARCH:{query}"

        elif (
            "html" in query_lower
            or "create" in query_lower
            or "make" in query_lower
            or "generate" in query_lower
        ):
            if "todo" in query_lower or "list" in query_lower:
                return self.generate_todo_html()
            elif "calculator" in query_lower:
                return self.generate_calculator_html()
            else:
                # For any HTML request, create a simple HTML page
                html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>AI Generated Page</title>
    <style>
        body {{
            font-family: system-ui, -apple-system, sans-serif;
            margin: 0;
            padding: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .card {{
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            max-width: 600px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}
        h1 {{
            font-size: 2.5em;
            margin-bottom: 20px;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }}
        p {{
            font-size: 1.2em;
            line-height: 1.6;
            margin-bottom: 20px;
        }}
        button {{
            background: #4CAF50;
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 16px;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        button:hover {{
            background: #45a049;
            transform: translateY(-2px);
        }}
        .query {{
            background: rgba(0, 0, 0, 0.2);
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="card">
        <h1>🤖 AI Generated Content</h1>
        <div class="query">Your request: "{query}"</div>
        <p>Success! I've created this HTML page for you.</p>
        <p>This demonstrates that the AI can generate custom web content directly in the browser.</p>
        <button onclick="alert('Hello from the AI! 🤖')">Click me!</button>
        <p style="margin-top: 30px; font-size: 0.9em; opacity: 0.8;">
            Try asking me to create other things like "make a calculator" or "create a todo list"
        </p>
    </div>
</body>
</html>"""
                return f"HTML:{html_content}"

        else:
            # Default: search for simple queries, create info page for complex ones
            if len(query.split()) <= 3:
                return f"SEARCH:{query}"
            else:
                return f"HTML:<!DOCTYPE html><html><head><title>AI Response</title><style>body{{font-family:system-ui;padding:40px;background:#f0f0f0;color:#333;}}.container{{max-width:800px;margin:0 auto;background:white;padding:30px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1);}}</style></head><body><div class='container'><h1>🤖 AI Response</h1><p><strong>Your query:</strong> {query}</p><p>This is a response generated by the AI assistant. In a full implementation, this would be a more detailed and contextual response.</p></div></body></html>"

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
            margin-bottom: 20px;
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
            <div class="query">"{query}"</div>
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
</html>"""


class VimBrowser(QMainWindow):
    def __init__(self):
        super().__init__()

        # Vim modes
        self.mode = "NORMAL"
        self.command_buffer = ""

        # Buffer management
        self.buffers = []
        self.current_buffer = 0

        # AI integration
        self.ai_worker = None
        self.last_query = None
        # Conversation logging
        conv_path = os.path.join(
            os.path.expanduser("~"), ".config", "minimal-browser", "conversations.json"
        )
        self.conversation_log = ConversationLog(conv_path)

        # Loading overlay for AI responses
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

        self.initial_load = True

        # Create persistent profile for cookies
        self.profile = QWebEngineProfile()
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.ForcePersistentCookies
        )
        self.profile.setPersistentStoragePath(
            os.path.join(os.path.expanduser("~"), ".minimal-browser")
        )

        # Create web view with optimized settings
        print("Initializing QWebEngineView...")
        try:
            self.browser = QWebEngineView()
            print("QWebEngineView created successfully")

            # Create page with persistent profile
            self.page = QWebEnginePage(self.profile, self)
            self.browser.setPage(self.page)

            # Optimize web engine settings for speed
            settings = self.browser.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)
            settings.setAttribute(
                QWebEngineSettings.WebAttribute.JavascriptEnabled, True
            )
            settings.setAttribute(
                QWebEngineSettings.WebAttribute.LocalStorageEnabled, True
            )
            settings.setAttribute(
                QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
            )
            settings.setAttribute(
                QWebEngineSettings.WebAttribute.XSSAuditingEnabled, False
            )
            settings.setAttribute(
                QWebEngineSettings.WebAttribute.SpatialNavigationEnabled, False
            )
            settings.setAttribute(
                QWebEngineSettings.WebAttribute.HyperlinkAuditingEnabled, False
            )
            print("WebEngine settings configured")

            # Use custom profile for caching
            self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
            self.profile.setHttpCacheMaximumSize(50 * 1024 * 1024)  # 50MB cache
            print("Persistent profile configured")

        except Exception as e:
            print(f"WebEngine initialization error: {e}")
            # Fallback: create a basic web view without advanced settings
            self.browser = QWebEngineView()

        self.setCentralWidget(self.browser)
        # Hide all UI elements
        self.setMenuBar(None)
        self.statusBar().hide()

        # Minimal command line (overlay style, hidden by default)
        self.command_line = QLineEdit(self)
        self.command_line.setStyleSheet("""
            QLineEdit {
                background-color: rgba(30, 30, 30, 240);
                color: #ffffff;
                border: 1px solid #555;
                padding: 4px 8px;
                font-family: monospace;
                font-size: 12px;
            }
        """)
        self.command_line.hide()
        self.command_line.returnPressed.connect(self.execute_command)

        # Timer for hiding mode indicator
        self.mode_timer = QTimer()
        self.mode_timer.timeout.connect(self.hide_mode_indicator)
        self.mode_timer.setSingleShot(True)

        # Connect load signals for debugging
        self.browser.loadStarted.connect(lambda: print("Page load started"))
        self.browser.loadProgress.connect(lambda p: print(f"Load progress: {p}%"))
        self.browser.loadFinished.connect(
            lambda ok: print(f"Page load finished: {'SUCCESS' if ok else 'FAILED'}")
        )

        # Load initial URL
        initial_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.google.com"
        print(f"Loading initial URL: {initial_url}")
        self.open_url(initial_url)

        # Set up vim-like keybindings
        self.setup_keybindings()

        # Focus management
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Update window title to show mode subtly
        self.update_title()

    def setup_keybindings(self):
        # Escape key - always goes to normal mode
        QShortcut(QKeySequence("Escape"), self, self.normal_mode)

        # Normal mode shortcuts
        QShortcut(QKeySequence(":"), self, self.command_mode)
        QShortcut(QKeySequence("/"), self, self.search_mode)
        QShortcut(QKeySequence("s"), self, self.smart_search_mode)  # Smart search
        QShortcut(QKeySequence("a"), self, self.ai_search_mode)  # AI/LLM search
        QShortcut(QKeySequence("F1"), self, self.show_help)  # Help
        QShortcut(QKeySequence(" "), self, self.ai_chat_mode)  # AI Chat (Space)
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

        # Scrolling
        QShortcut(QKeySequence("j"), self, lambda: self.scroll_page(50))
        QShortcut(QKeySequence("k"), self, lambda: self.scroll_page(-50))
        QShortcut(QKeySequence("d"), self, lambda: self.scroll_page(300))
        QShortcut(QKeySequence("u"), self, lambda: self.scroll_page(-300))
        QShortcut(QKeySequence("g"), self, self.scroll_top)
        QShortcut(QKeySequence("G"), self, self.scroll_bottom)

    def keyPressEvent(self, event):
        if self.mode == "NORMAL":
            # In normal mode, handle single key commands
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
        # Position command line at bottom center
        if hasattr(self, "command_line"):
            width = min(400, self.width() - 40)
            self.command_line.resize(width, 30)
            self.command_line.move((self.width() - width) // 2, self.height() - 50)
        # Resize loading overlay
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

    def ai_search_mode(self):
        if self.mode == "NORMAL":
            self.mode = "COMMAND"
            self.show_command_line("a ")

    def ai_chat_mode(self):
        if self.mode == "NORMAL":
            self.mode = "AI_CHAT"
            self.show_command_line("🤖 ")

    def show_help(self):
        if self.mode == "NORMAL":
            help_content = self.get_help_content()
            # Create a data URL with base64 encoding
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
        elif command.startswith("🤖 "):
            query = command[2:]
            print(f"Executing AI chat with query: '{query}'")
            self.ai_chat(query)

        self.normal_mode()

    def execute_vim_command(self, cmd):
        cmd = cmd.strip()

        if cmd in ["q", "quit"]:
            self.close()
        elif cmd in ["w", "write"]:
            # Could implement bookmarking here
            pass
        elif cmd in ["wq"]:
            self.close()
        elif cmd in ["help", "h"]:
            self.show_help()
        elif cmd.startswith("e "):
            # Edit/open URL
            url = cmd[2:]
            self.open_url(url)
        elif cmd.startswith("b"):
            # Buffer commands
            if cmd == "b":
                self.show_buffers()
            elif cmd.startswith("bd"):
                self.close_buffer()
            elif cmd.startswith("bn"):
                self.next_buffer()
            elif cmd.startswith("bp"):
                self.prev_buffer()
        elif cmd.isdigit():
            # Go to buffer number
            buf_num = int(cmd) - 1
            if 0 <= buf_num < len(self.buffers):
                self.current_buffer = buf_num
                self.browser.load(QUrl(self.buffers[self.current_buffer]))
                self.update_title()

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
            self.setWindowTitle("Switching buffer...")
            self.browser.load(QUrl(self.buffers[self.current_buffer]))
            self.update_title()

    def prev_buffer(self):
        if self.mode == "NORMAL" and len(self.buffers) > 1:
            self.current_buffer = (self.current_buffer - 1) % len(self.buffers)
            self.setWindowTitle("Switching buffer...")
            self.browser.load(QUrl(self.buffers[self.current_buffer]))
            self.update_title()

    def scroll_page(self, pixels):
        if self.mode == "NORMAL":
            # Smoother scrolling with easing
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

    def show_buffers(self):
        # Show buffer info briefly in title
        if self.buffers:
            buf_info = f"Buffers: {', '.join(f'{i + 1}:{url.split("/")[-1][:20]}' for i, url in enumerate(self.buffers))}"
            self.setWindowTitle(buf_info)
            self.mode_timer.start(3000)  # Hide after 3 seconds

    def update_title(self):
        if self.mode == "NORMAL":
            # Show buffer info subtly
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
            title = "-- AI CHAT --"
        else:
            title = f"-- {self.mode} --"

        self.setWindowTitle(title)

    def hide_mode_indicator(self):
        if self.mode == "NORMAL":
            self.update_title()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Position command line at bottom center
        if hasattr(self, "command_line"):
            width = min(400, self.width() - 40)
            self.command_line.resize(width, 30)
            self.command_line.move((self.width() - width) // 2, self.height() - 50)

    def smart_search(self, query):
        """Smart search - detects if it's a URL or search query"""
        query = query.strip()
        if not query:
            return

        # Check if it looks like a URL
        if ("." in query and " " not in query) or query.startswith(
            ("http://", "https://")
        ):
            self.open_url(query)
        else:
            # Use Google search
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            self.open_url(search_url)

    def ai_search(self, query):
        """AI/LLM search - opens query in ChatGPT or similar"""
        query = query.strip()
        if not query:
            return

        # Use ChatGPT (you can change this to your preferred AI service)
        ai_url = f"https://chat.openai.com/?q={query.replace(' ', '%20')}"
        self.open_url(ai_url)

    def ai_chat(self, query):
        """Native AI chat - processes query with AI"""
        query = query.strip()
        if not query:
            return

        self.last_query = query
        print(f"AI Chat Query: {query}")  # Debug logging
        # Log query start
        self.conversation_log.append(query, None)

        # Show loading overlay
        self.loading_overlay.resize(self.size())
        self.loading_overlay.show()
        self.loading_overlay.raise_()

        # Show loading state in title
        self.setWindowTitle("🤖 AI Thinking...")

        # Get current page URL for context
        current_url = self.buffers[self.current_buffer] if self.buffers else ""

        # Start AI worker thread
        self.ai_worker = AIWorker(query, current_url)
        self.ai_worker.response_ready.connect(self.handle_ai_response)
        self.ai_worker.progress_update.connect(self.update_progress)
        self.ai_worker.start()

    def handle_ai_response(self, response_type, content):
        """Handle AI response"""
        print(f"AI Response: {response_type} - {content[:100]}...")  # Debug logging

        # Hide loading overlay
        self.loading_overlay.hide()

        if response_type == "error":
            self.setWindowTitle(f"AI Error: {content}")
            self.mode_timer.start(3000)
            return

        # Parse AI response
        if content.startswith("NAVIGATE:"):
            url = content[9:]  # Remove "NAVIGATE:" prefix
            print(f"Navigating to: {url}")
            self.open_url(url)
        elif content.startswith("SEARCH:"):
            query = content[7:]  # Remove "SEARCH:" prefix
            print(f"Searching for: {query}")
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            self.open_url(search_url)
        elif content.startswith("HTML:"):
            html_content = content[5:]  # Remove "HTML:" prefix
            print(f"Creating HTML content: {len(html_content)} chars")
            # Create data URL with the HTML content - use base64 encoding for better compatibility
            import base64

            encoded_html = base64.b64encode(html_content.encode("utf-8")).decode(
                "ascii"
            )
            data_url = f"data:text/html;base64,{encoded_html}"
            print(f"Data URL length: {len(data_url)}")
            self.open_url(data_url)
        else:
            # Default: treat as HTML content
            print(f"Creating default HTML: {len(content)} chars")
            import base64

            encoded_html = base64.b64encode(content.encode("utf-8")).decode("ascii")
            data_url = f"data:text/html;base64,{encoded_html}"
            self.open_url(data_url)

        # Log final response
        try:
            if self.last_query:
                self.conversation_log.update_last_response(content)
        except Exception as e:
            print(f"Conversation log error: {e}")
        self.update_title()

    def update_progress(self, message):
        """Update progress in window title"""
        self.setWindowTitle(f"🤖 {message}")
        print(f"Progress: {message}")  # Debug logging

    def toggle_dev_tools(self):
        """Toggle developer tools (F10)"""
        if self.mode == "NORMAL":
            # Get the web page and show dev tools
            page = self.browser.page()
            if hasattr(page, "setDevToolsPage"):
                # Create dev tools window if it doesn't exist
                if not hasattr(self, "dev_tools"):
                    from PySide6.QtWebEngineWidgets import QWebEngineView

                    self.dev_tools = QWebEngineView()
                    self.dev_tools.setWindowTitle("Developer Tools")
                    self.dev_tools.resize(800, 600)
                    page.setDevToolsPage(self.dev_tools.page())

                # Toggle visibility
                if self.dev_tools.isVisible():
                    self.dev_tools.hide()
                else:
                    self.dev_tools.show()
            else:
                print("Developer tools not available in this Qt version")

    def view_source(self):
        """View page source (Ctrl+U)"""
        if self.mode == "NORMAL":
            # Get the HTML source of current page
            self.browser.page().toHtml(self.show_source_in_new_buffer)

    def show_buffer_overlay(self):
        """Show overlay during buffer switch"""
        self.buffer_overlay.resize(self.size())
        self.buffer_overlay.show()
        self.buffer_overlay.raise_()

    def hide_buffer_overlay(self):
        """Hide buffer overlay after load"""
        self.buffer_overlay.hide()

    def on_load_finished(self, ok):
        print(f"Page load finished: {'SUCCESS' if ok else 'FAILED'}")
        if self.initial_load and ok:
            self.initial_load = False
        else:
            self.setWindowTitle(self.update_title())

    def show_source_in_new_buffer(self, html):
        """Show HTML source in a new buffer"""
        # Create a simple HTML viewer for the source
        source_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Page Source</title>
    <style>
        body {{
            font-family: 'Courier New', monospace;
            background: #1e1e1e;
            color: #d4d4d4;
            margin: 0;
            padding: 20px;
            line-height: 1.4;
        }}
        .header {{
            background: #2d2d30;
            color: #cccccc;
            padding: 15px;
            margin: -20px -20px 20px -20px;
            border-bottom: 1px solid #3e3e42;
        }}
        pre {{
            background: #252526;
            padding: 20px;
            border-radius: 5px;
            overflow: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .tag {{ color: #569cd6; }}
        .attr {{ color: #9cdcfe; }}
        .string {{ color: #ce9178; }}
        .comment {{ color: #6a9955; font-style: italic; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>📄 Page Source</h2>
        <p>Current page HTML source ({len(html)} characters)</p>
    </div>
    <pre>{html.replace("<", "<").replace(">", ">")}</pre>
</body>
</html>"""

        # Create data URL and open in new buffer
        encoded_html = base64.b64encode(source_html.encode("utf-8")).decode("ascii")
        data_url = f"data:text/html;base64,{encoded_html}"
        self.setWindowTitle("Loading source...")
        self.browser.load(QUrl(data_url))
        print(f"Source view created: {len(html)} characters")

    def show_debug_info(self):
        """Show debug information (Ctrl+I)"""
        if self.mode == "NORMAL":
            current_url = self.browser.url().toString()
            print(f"\n=== DEBUG INFO ===")
            print(f"Current URL: {current_url}")
            print(f"Buffer count: {len(self.buffers)}")
            print(f"Current buffer: {self.current_buffer}")
            print(f"Mode: {self.mode}")
            if self.buffers:
                print(f"All buffers:")
                for i, buf in enumerate(self.buffers):
                    marker = " -> " if i == self.current_buffer else "    "
                    print(f"{marker}{i + 1}: {buf[:80]}...")
            print("==================\n")

            # Also show in title briefly
            self.setWindowTitle(
                f"Debug: {len(self.buffers)} buffers, URL: {current_url[:50]}..."
            )
            self.mode_timer.start(3000)

    def handle_streaming_chunk(self, chunk):
        """Handle streaming response chunks"""
        # For future streaming implementation
        pass

    def get_help_content(self):
        """Generate help content as HTML"""
        return """<!DOCTYPE html>
<html>
<head>
    <title>Vim Browser Help</title>
    <style>
        body { 
            font-family: monospace; 
            background: #1e1e1e; 
            color: #ffffff; 
            padding: 20px; 
            line-height: 1.6;
        }
        h1, h2 { color: #4a9eff; }
        .key { 
            background: #333; 
            padding: 2px 6px; 
            border-radius: 3px; 
            font-weight: bold;
        }
        .section { margin-bottom: 30px; }
        table { border-collapse: collapse; width: 100%; }
        td { padding: 8px; border-bottom: 1px solid #333; }
        .cmd { color: #90ee90; }
    </style>
</head>
<body>
    <h1>Vim Browser Help</h1>
    
    <div class="section">
        <h2>Navigation</h2>
        <table>
            <tr><td><span class="key">j/k</span></td><td>Scroll down/up</td></tr>
            <tr><td><span class="key">d/u</span></td><td>Page down/up</td></tr>
            <tr><td><span class="key">g/G</span></td><td>Top/bottom of page</td></tr>
            <tr><td><span class="key">H/L</span></td><td>Back/forward</td></tr>
            <tr><td><span class="key">r</span></td><td>Reload page</td></tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Buffers (Tabs)</h2>
        <table>
            <tr><td><span class="key">n/p</span></td><td>Next/previous buffer</td></tr>
            <tr><td><span class="key">t</span></td><td>New buffer</td></tr>
            <tr><td><span class="key">x</span></td><td>Close buffer</td></tr>
            <tr><td><span class="key">:b</span></td><td>Show buffers</td></tr>
            <tr><td><span class="key">:1,2,3...</span></td><td>Go to buffer number</td></tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Opening URLs & Search</h2>
        <table>
            <tr><td><span class="key">o</span></td><td>Open URL</td></tr>
            <tr><td><span class="key">s</span></td><td>Smart search (Google or URL)</td></tr>
            <tr><td><span class="key">a</span></td><td>AI search (ChatGPT)</td></tr>
            <tr><td><span class="key">Space</span></td><td>Native AI chat</td></tr>
            <tr><td><span class="key">/</span></td><td>Search in page</td></tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Developer Tools</h2>
        <table>
            <tr><td><span class="key">F12</span></td><td>Toggle developer tools</td></tr>
            <tr><td><span class="key">Ctrl+U</span></td><td>View page source</td></tr>
            <tr><td><span class="key">Ctrl+I</span></td><td>Show debug info</td></tr>
        </table>
    </div>
    
    <div class="section">
        <h2>AI Integration</h2>
        <table>
            <tr><td><span class="key">Space</span></td><td>Ask AI anything - it can navigate or create content</td></tr>
            <tr><td colspan="2">Examples:</td></tr>
            <tr><td></td><td>"navigate to github" &rarr; Opens GitHub</td></tr>
            <tr><td></td><td>"create a todo list" &rarr; Generates interactive todo app</td></tr>
            <tr><td></td><td>"make a calculator" &rarr; Creates working calculator</td></tr>
            <tr><td></td><td>"explain quantum physics" &rarr; Generates explanation page</td></tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Commands (:)</h2>
        <table>
            <tr><td><span class="cmd">:q</span></td><td>Quit</td></tr>
            <tr><td><span class="cmd">:help</span></td><td>Show this help</td></tr>
            <tr><td><span class="cmd">:e &lt;url&gt;</span></td><td>Open URL</td></tr>
            <tr><td><span class="cmd">:bd</span></td><td>Close buffer</td></tr>
            <tr><td><span class="cmd">:bn/:bp</span></td><td>Next/previous buffer</td></tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Modes</h2>
        <table>
            <tr><td><span class="key">NORMAL</span></td><td>Default mode for navigation</td></tr>
            <tr><td><span class="key">COMMAND</span></td><td>Typing commands or URLs</td></tr>
            <tr><td><span class="key">Escape</span></td><td>Return to NORMAL mode</td></tr>
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
    
    <p style="margin-top: 40px; color: #666;">Press <span class="key">Escape</span> to return to normal browsing</p>
</body>
</html>"""


def main():
    # Python 3.13 + Qt compatibility fixes
    if hasattr(Qt, "AA_ShareOpenGLContexts"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

    # Wayland-specific Qt fixes
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)

    # Set up application with optimizations
    app = QApplication(sys.argv)
    from PySide6.QtWebEngineCore import QWebEngineProfile

    QWebEngineProfile.defaultProfile().setPersistentCookiesPolicy(
        QWebEngineProfile.ForcePersistentCookies
    )
    app.setApplicationName("Minimal Browser")
    app.setApplicationVersion("0.2.0")

    from PySide6.QtWebEngineCore import QWebEngineProfile

    QWebEngineProfile.defaultProfile().setPersistentCookiesPolicy(
        QWebEngineProfile.ForcePersistentCookies
    )
    QWebEngineProfile.defaultProfile().setPersistentStoragePath(
        os.path.join(os.path.expanduser("~"), ".config", "minimal-browser")
    )

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
