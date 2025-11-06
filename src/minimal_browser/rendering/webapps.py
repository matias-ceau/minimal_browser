"""Web applications rendering module.

This module provides a comprehensive framework for rendering interactive web
applications and widgets within the browser. It includes:

- Interactive HTML templates (cards, grids, tables, timelines)
- JavaScript-based mini-apps (calculator, todo, timer, notes)
- Dynamic component rendering from AI responses
- Widget system with registry and API for AI-generated apps
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WidgetType(str, Enum):
    """Available widget types."""
    
    CALCULATOR = "calculator"
    TODO = "todo"
    TIMER = "timer"
    NOTES = "notes"
    CHART = "chart"
    DASHBOARD = "dashboard"
    CARD = "card"
    GRID = "grid"
    TABLE = "table"
    TIMELINE = "timeline"


class WidgetTheme(str, Enum):
    """Available widget themes."""
    
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class WidgetConfig(BaseModel):
    """Configuration for a widget instance.
    
    Attributes:
        type: The widget type to render
        theme: Visual theme (light/dark/auto)
        title: Optional widget title
        data: Optional data payload for the widget
        props: Additional widget-specific properties
    """
    
    type: WidgetType
    theme: WidgetTheme = WidgetTheme.DARK
    title: Optional[str] = None
    data: Optional[Any] = None
    props: Dict[str, Any] = Field(default_factory=dict)


class WidgetRegistry:
    """Registry for available widgets and their templates.
    
    This class manages widget definitions and provides methods to generate
    HTML for registered widget types.
    """
    
    _widgets: Dict[WidgetType, str] = {}
    
    @classmethod
    def register(cls, widget_type: WidgetType, template_func: callable) -> None:
        """Register a widget template function.
        
        Args:
            widget_type: The type of widget to register
            template_func: Function that generates HTML for the widget
        """
        cls._widgets[widget_type] = template_func
    
    @classmethod
    def is_registered(cls, widget_type: WidgetType) -> bool:
        """Check if a widget type is registered.
        
        Args:
            widget_type: The widget type to check
            
        Returns:
            True if the widget is registered, False otherwise
        """
        return widget_type in cls._widgets
    
    @classmethod
    def render(cls, config: WidgetConfig) -> str:
        """Render a widget to HTML.
        
        Args:
            config: The widget configuration
            
        Returns:
            HTML string for the widget
            
        Raises:
            ValueError: If widget type is not registered
        """
        if config.type not in cls._widgets:
            raise ValueError(f"Widget type '{config.type}' is not registered")
        
        template_func = cls._widgets[config.type]
        return template_func(config)
    
    @classmethod
    def list_widgets(cls) -> List[WidgetType]:
        """Get a list of all registered widget types.
        
        Returns:
            List of registered widget types
        """
        return list(cls._widgets.keys())


def _get_base_styles(theme: WidgetTheme) -> str:
    """Get base CSS styles for widgets.
    
    Args:
        theme: The theme to use
        
    Returns:
        CSS string with base widget styles
    """
    if theme == WidgetTheme.DARK:
        bg_color = "#1a1a2e"
        text_color = "#eee"
        accent_color = "#667eea"
        border_color = "#333"
        card_bg = "#16213e"
        input_bg = "#0f1419"
    else:
        bg_color = "#f5f5f5"
        text_color = "#333"
        accent_color = "#667eea"
        border_color = "#ddd"
        card_bg = "#fff"
        input_bg = "#fff"
    
    return f"""
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: {bg_color};
            color: {text_color};
            padding: 20px;
            line-height: 1.6;
        }}
        .widget-container {{
            max-width: 800px;
            margin: 0 auto;
            background: {card_bg};
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .widget-header {{
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid {border_color};
        }}
        .widget-title {{
            font-size: 2em;
            font-weight: bold;
            color: {accent_color};
        }}
        button {{
            background: {accent_color};
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s;
        }}
        button:hover {{
            opacity: 0.8;
            transform: translateY(-2px);
        }}
        button:active {{
            transform: translateY(0);
        }}
        input, textarea {{
            background: {input_bg};
            color: {text_color};
            border: 1px solid {border_color};
            padding: 10px;
            border-radius: 8px;
            font-size: 1em;
            width: 100%;
        }}
        input:focus, textarea:focus {{
            outline: none;
            border-color: {accent_color};
        }}
    """


def _render_calculator(config: WidgetConfig) -> str:
    """Render a calculator widget.
    
    Args:
        config: Widget configuration
        
    Returns:
        HTML string for calculator widget
    """
    title = config.title or "Calculator"
    styles = _get_base_styles(config.theme)
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {styles}
        .calculator {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-top: 20px;
        }}
        .display {{
            grid-column: 1 / -1;
            background: {'#0f1419' if config.theme == WidgetTheme.DARK else '#fff'};
            border: 1px solid {'#333' if config.theme == WidgetTheme.DARK else '#ddd'};
            padding: 20px;
            font-size: 2em;
            text-align: right;
            border-radius: 8px;
            margin-bottom: 10px;
            font-family: monospace;
            min-height: 60px;
        }}
        .btn-calc {{
            padding: 20px;
            font-size: 1.2em;
            border-radius: 8px;
        }}
        .btn-span-2 {{
            grid-column: span 2;
        }}
        .btn-operator {{
            background: #764ba2;
        }}
        .btn-clear {{
            background: #e74c3c;
        }}
    </style>
</head>
<body>
    <div class="widget-container">
        <div class="widget-header">
            <div class="widget-title">🧮 {title}</div>
        </div>
        <div class="display" id="display">0</div>
        <div class="calculator">
            <button class="btn-calc btn-clear" onclick="clearDisplay()">C</button>
            <button class="btn-calc btn-operator" onclick="appendOperator('/')">/</button>
            <button class="btn-calc btn-operator" onclick="appendOperator('*')">×</button>
            <button class="btn-calc btn-operator" onclick="deleteLastChar()">⌫</button>
            
            <button class="btn-calc" onclick="appendNumber('7')">7</button>
            <button class="btn-calc" onclick="appendNumber('8')">8</button>
            <button class="btn-calc" onclick="appendNumber('9')">9</button>
            <button class="btn-calc btn-operator" onclick="appendOperator('-')">−</button>
            
            <button class="btn-calc" onclick="appendNumber('4')">4</button>
            <button class="btn-calc" onclick="appendNumber('5')">5</button>
            <button class="btn-calc" onclick="appendNumber('6')">6</button>
            <button class="btn-calc btn-operator" onclick="appendOperator('+')">+</button>
            
            <button class="btn-calc" onclick="appendNumber('1')">1</button>
            <button class="btn-calc" onclick="appendNumber('2')">2</button>
            <button class="btn-calc" onclick="appendNumber('3')">3</button>
            <button class="btn-calc btn-operator btn-span-2" style="grid-row: span 2" onclick="calculate()">=</button>
            
            <button class="btn-calc btn-span-2" onclick="appendNumber('0')">0</button>
            <button class="btn-calc" onclick="appendNumber('.')">.</button>
        </div>
    </div>
    <script>
        let currentValue = '0';
        let previousValue = '';
        let operation = '';
        let shouldResetDisplay = false;
        
        function updateDisplay() {{
            document.getElementById('display').textContent = currentValue;
        }}
        
        function clearDisplay() {{
            currentValue = '0';
            previousValue = '';
            operation = '';
            shouldResetDisplay = false;
            updateDisplay();
        }}
        
        function deleteLastChar() {{
            if (currentValue.length > 1) {{
                currentValue = currentValue.slice(0, -1);
            }} else {{
                currentValue = '0';
            }}
            updateDisplay();
        }}
        
        function appendNumber(num) {{
            if (shouldResetDisplay) {{
                currentValue = num;
                shouldResetDisplay = false;
            }} else {{
                if (currentValue === '0' && num !== '.') {{
                    currentValue = num;
                }} else if (!(num === '.' && currentValue.includes('.'))) {{
                    currentValue += num;
                }}
            }}
            updateDisplay();
        }}
        
        function appendOperator(op) {{
            if (operation && previousValue && !shouldResetDisplay) {{
                calculate();
            }}
            previousValue = currentValue;
            operation = op;
            shouldResetDisplay = true;
        }}
        
        function calculate() {{
            if (!operation || !previousValue) return;
            
            const prev = parseFloat(previousValue);
            const current = parseFloat(currentValue);
            let result;
            
            switch(operation) {{
                case '+': result = prev + current; break;
                case '-': result = prev - current; break;
                case '*': result = prev * current; break;
                case '/': result = prev / current; break;
                default: return;
            }}
            
            currentValue = String(result);
            operation = '';
            previousValue = '';
            shouldResetDisplay = true;
            updateDisplay();
        }}
    </script>
</body>
</html>"""


def _render_todo(config: WidgetConfig) -> str:
    """Render a todo list widget.
    
    Args:
        config: Widget configuration
        
    Returns:
        HTML string for todo widget
    """
    title = config.title or "Todo List"
    styles = _get_base_styles(config.theme)
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {styles}
        .todo-input {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }}
        .todo-input input {{
            flex: 1;
        }}
        .todo-list {{
            list-style: none;
        }}
        .todo-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 15px;
            margin-bottom: 10px;
            background: {'#0f1419' if config.theme == WidgetTheme.DARK else '#f9f9f9'};
            border-radius: 8px;
            border: 1px solid {'#333' if config.theme == WidgetTheme.DARK else '#ddd'};
            transition: all 0.3s;
        }}
        .todo-item:hover {{
            transform: translateX(5px);
        }}
        .todo-item.completed {{
            opacity: 0.6;
        }}
        .todo-item.completed .todo-text {{
            text-decoration: line-through;
        }}
        .todo-checkbox {{
            width: 20px;
            height: 20px;
            cursor: pointer;
        }}
        .todo-text {{
            flex: 1;
            font-size: 1.1em;
        }}
        .todo-delete {{
            background: #e74c3c;
            padding: 5px 15px;
            font-size: 0.9em;
        }}
        .stats {{
            margin-top: 20px;
            padding: 15px;
            background: {'#0f1419' if config.theme == WidgetTheme.DARK else '#f9f9f9'};
            border-radius: 8px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="widget-container">
        <div class="widget-header">
            <div class="widget-title">📝 {title}</div>
        </div>
        <div class="todo-input">
            <input type="text" id="todoInput" placeholder="Add a new task..." onkeypress="handleKeyPress(event)">
            <button onclick="addTodo()">Add</button>
        </div>
        <ul class="todo-list" id="todoList"></ul>
        <div class="stats" id="stats">
            <span id="statsText">No tasks yet</span>
        </div>
    </div>
    <script>
        let todos = [];
        
        function updateStats() {{
            const total = todos.length;
            const completed = todos.filter(t => t.completed).length;
            const remaining = total - completed;
            
            const statsText = document.getElementById('statsText');
            if (total === 0) {{
                statsText.textContent = 'No tasks yet';
            }} else {{
                statsText.textContent = `${{total}} total · ${{completed}} completed · ${{remaining}} remaining`;
            }}
        }}
        
        function renderTodos() {{
            const list = document.getElementById('todoList');
            list.innerHTML = '';
            
            todos.forEach((todo, index) => {{
                const li = document.createElement('li');
                li.className = 'todo-item' + (todo.completed ? ' completed' : '');
                
                li.innerHTML = `
                    <input type="checkbox" class="todo-checkbox" 
                           ${{todo.completed ? 'checked' : ''}}
                           onchange="toggleTodo(${{index}})">
                    <span class="todo-text">${{todo.text}}</span>
                    <button class="todo-delete" onclick="deleteTodo(${{index}})">Delete</button>
                `;
                
                list.appendChild(li);
            }});
            
            updateStats();
        }}
        
        function addTodo() {{
            const input = document.getElementById('todoInput');
            const text = input.value.trim();
            
            if (text) {{
                todos.push({{ text, completed: false }});
                input.value = '';
                renderTodos();
            }}
        }}
        
        function toggleTodo(index) {{
            todos[index].completed = !todos[index].completed;
            renderTodos();
        }}
        
        function deleteTodo(index) {{
            todos.splice(index, 1);
            renderTodos();
        }}
        
        function handleKeyPress(event) {{
            if (event.key === 'Enter') {{
                addTodo();
            }}
        }}
        
        // Initialize
        renderTodos();
    </script>
</body>
</html>"""


def _render_timer(config: WidgetConfig) -> str:
    """Render a timer/stopwatch widget.
    
    Args:
        config: Widget configuration
        
    Returns:
        HTML string for timer widget
    """
    title = config.title or "Timer & Stopwatch"
    styles = _get_base_styles(config.theme)
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {styles}
        .tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }}
        .tab {{
            flex: 1;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            border-radius: 8px;
            background: {'#0f1419' if config.theme == WidgetTheme.DARK else '#f9f9f9'};
            border: 2px solid transparent;
        }}
        .tab.active {{
            border-color: #667eea;
            background: #667eea;
        }}
        .timer-display {{
            font-size: 4em;
            font-family: monospace;
            text-align: center;
            margin: 30px 0;
            font-weight: bold;
        }}
        .controls {{
            display: flex;
            gap: 10px;
            justify-content: center;
            margin: 20px 0;
        }}
        .controls button {{
            padding: 15px 30px;
            font-size: 1.1em;
        }}
        .timer-input {{
            display: flex;
            gap: 10px;
            justify-content: center;
            margin-bottom: 20px;
        }}
        .timer-input input {{
            width: 80px;
            text-align: center;
            font-size: 1.2em;
        }}
        .hidden {{
            display: none;
        }}
    </style>
</head>
<body>
    <div class="widget-container">
        <div class="widget-header">
            <div class="widget-title">⏱️ {title}</div>
        </div>
        <div class="tabs">
            <div class="tab active" onclick="switchTab('stopwatch')">Stopwatch</div>
            <div class="tab" onclick="switchTab('timer')">Timer</div>
        </div>
        
        <!-- Stopwatch -->
        <div id="stopwatch-panel">
            <div class="timer-display" id="stopwatch-display">00:00:00</div>
            <div class="controls">
                <button id="stopwatch-start" onclick="startStopwatch()">Start</button>
                <button onclick="stopStopwatch()">Stop</button>
                <button onclick="resetStopwatch()">Reset</button>
            </div>
        </div>
        
        <!-- Timer -->
        <div id="timer-panel" class="hidden">
            <div class="timer-input">
                <input type="number" id="hours" placeholder="HH" min="0" max="23" value="0">
                <span style="font-size: 2em;">:</span>
                <input type="number" id="minutes" placeholder="MM" min="0" max="59" value="0">
                <span style="font-size: 2em;">:</span>
                <input type="number" id="seconds" placeholder="SS" min="0" max="59" value="0">
            </div>
            <div class="timer-display" id="timer-display">00:00:00</div>
            <div class="controls">
                <button onclick="startTimer()">Start</button>
                <button onclick="stopTimer()">Stop</button>
                <button onclick="resetTimer()">Reset</button>
            </div>
        </div>
    </div>
    <script>
        let stopwatchInterval = null;
        let stopwatchTime = 0;
        let timerInterval = null;
        let timerTime = 0;
        
        function switchTab(tab) {{
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            
            if (tab === 'stopwatch') {{
                document.getElementById('stopwatch-panel').classList.remove('hidden');
                document.getElementById('timer-panel').classList.add('hidden');
            }} else {{
                document.getElementById('stopwatch-panel').classList.add('hidden');
                document.getElementById('timer-panel').classList.remove('hidden');
            }}
        }}
        
        function formatTime(seconds) {{
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = seconds % 60;
            return `${{String(h).padStart(2, '0')}}:${{String(m).padStart(2, '0')}}:${{String(s).padStart(2, '0')}}`;
        }}
        
        // Stopwatch functions
        function startStopwatch() {{
            if (!stopwatchInterval) {{
                stopwatchInterval = setInterval(() => {{
                    stopwatchTime++;
                    document.getElementById('stopwatch-display').textContent = formatTime(stopwatchTime);
                }}, 1000);
            }}
        }}
        
        function stopStopwatch() {{
            if (stopwatchInterval) {{
                clearInterval(stopwatchInterval);
                stopwatchInterval = null;
            }}
        }}
        
        function resetStopwatch() {{
            stopStopwatch();
            stopwatchTime = 0;
            document.getElementById('stopwatch-display').textContent = formatTime(0);
        }}
        
        // Timer functions
        function startTimer() {{
            if (!timerInterval) {{
                if (timerTime === 0) {{
                    const h = parseInt(document.getElementById('hours').value) || 0;
                    const m = parseInt(document.getElementById('minutes').value) || 0;
                    const s = parseInt(document.getElementById('seconds').value) || 0;
                    timerTime = h * 3600 + m * 60 + s;
                }}
                
                if (timerTime > 0) {{
                    timerInterval = setInterval(() => {{
                        timerTime--;
                        document.getElementById('timer-display').textContent = formatTime(timerTime);
                        
                        if (timerTime === 0) {{
                            stopTimer();
                            alert('Timer finished!');
                        }}
                    }}, 1000);
                }}
            }}
        }}
        
        function stopTimer() {{
            if (timerInterval) {{
                clearInterval(timerInterval);
                timerInterval = null;
            }}
        }}
        
        function resetTimer() {{
            stopTimer();
            timerTime = 0;
            document.getElementById('timer-display').textContent = formatTime(0);
            document.getElementById('hours').value = 0;
            document.getElementById('minutes').value = 0;
            document.getElementById('seconds').value = 0;
        }}
    </script>
</body>
</html>"""


def _render_notes(config: WidgetConfig) -> str:
    """Render a notes widget.
    
    Args:
        config: Widget configuration
        
    Returns:
        HTML string for notes widget
    """
    title = config.title or "Notes"
    styles = _get_base_styles(config.theme)
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {styles}
        .notes-list {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .note-card {{
            background: {'#0f1419' if config.theme == WidgetTheme.DARK else '#fff'};
            border: 1px solid {'#333' if config.theme == WidgetTheme.DARK else '#ddd'};
            border-radius: 8px;
            padding: 15px;
            cursor: pointer;
            transition: transform 0.3s;
        }}
        .note-card:hover {{
            transform: translateY(-5px);
        }}
        .note-title {{
            font-weight: bold;
            font-size: 1.1em;
            margin-bottom: 10px;
            color: #667eea;
        }}
        .note-content {{
            font-size: 0.9em;
            line-height: 1.4;
            max-height: 100px;
            overflow: hidden;
        }}
        .note-date {{
            font-size: 0.8em;
            color: #888;
            margin-top: 10px;
        }}
        .note-editor {{
            margin-bottom: 20px;
        }}
        .note-editor textarea {{
            min-height: 200px;
            margin-top: 10px;
        }}
        .editor-buttons {{
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="widget-container">
        <div class="widget-header">
            <div class="widget-title">📔 {title}</div>
        </div>
        <div class="note-editor">
            <input type="text" id="noteTitle" placeholder="Note title..." style="margin-bottom: 10px;">
            <textarea id="noteContent" placeholder="Write your note here..."></textarea>
            <div class="editor-buttons">
                <button onclick="saveNote()">Save Note</button>
                <button onclick="clearEditor()" style="background: #888;">Clear</button>
            </div>
        </div>
        <div class="notes-list" id="notesList"></div>
    </div>
    <script>
        let notes = [];
        let editingIndex = -1;
        
        function renderNotes() {{
            const list = document.getElementById('notesList');
            list.innerHTML = '';
            
            notes.forEach((note, index) => {{
                const card = document.createElement('div');
                card.className = 'note-card';
                card.onclick = () => editNote(index);
                
                card.innerHTML = `
                    <div class="note-title">${{note.title || 'Untitled'}}</div>
                    <div class="note-content">${{note.content.substring(0, 100)}}</div>
                    <div class="note-date">${{new Date(note.date).toLocaleString()}}</div>
                `;
                
                list.appendChild(card);
            }});
        }}
        
        function saveNote() {{
            const title = document.getElementById('noteTitle').value.trim();
            const content = document.getElementById('noteContent').value.trim();
            
            if (!content) {{
                alert('Note content cannot be empty');
                return;
            }}
            
            const note = {{
                title: title || 'Untitled',
                content: content,
                date: new Date().toISOString()
            }};
            
            if (editingIndex >= 0) {{
                notes[editingIndex] = note;
                editingIndex = -1;
            }} else {{
                notes.unshift(note);
            }}
            
            clearEditor();
            renderNotes();
        }}
        
        function editNote(index) {{
            const note = notes[index];
            document.getElementById('noteTitle').value = note.title;
            document.getElementById('noteContent').value = note.content;
            editingIndex = index;
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}
        
        function clearEditor() {{
            document.getElementById('noteTitle').value = '';
            document.getElementById('noteContent').value = '';
            editingIndex = -1;
        }}
        
        // Initialize
        renderNotes();
    </script>
</body>
</html>"""


def _render_card(config: WidgetConfig) -> str:
    """Render a card component.
    
    Args:
        config: Widget configuration
        
    Returns:
        HTML string for card component
    """
    title = config.title or "Card"
    content = config.data or "Card content goes here"
    styles = _get_base_styles(config.theme)
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {styles}
        .card {{
            background: {'#0f1419' if config.theme == WidgetTheme.DARK else '#fff'};
            border: 1px solid {'#333' if config.theme == WidgetTheme.DARK else '#ddd'};
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
        }}
        .card-content {{
            line-height: 1.8;
        }}
    </style>
</head>
<body>
    <div class="widget-container">
        <div class="card">
            <div class="widget-header">
                <div class="widget-title">{title}</div>
            </div>
            <div class="card-content">
                {content}
            </div>
        </div>
    </div>
</body>
</html>"""


# Register built-in widgets
WidgetRegistry.register(WidgetType.CALCULATOR, _render_calculator)
WidgetRegistry.register(WidgetType.TODO, _render_todo)
WidgetRegistry.register(WidgetType.TIMER, _render_timer)
WidgetRegistry.register(WidgetType.NOTES, _render_notes)
WidgetRegistry.register(WidgetType.CARD, _render_card)


def render_webapp(
    widget_type: str | WidgetType,
    theme: str | WidgetTheme = "dark",
    title: Optional[str] = None,
    data: Optional[Any] = None,
    **props
) -> str:
    """Render a web application widget.
    
    This is the main entry point for rendering widgets. It accepts various
    parameters and returns a complete HTML document.
    
    Args:
        widget_type: Type of widget to render (e.g., "calculator", "todo")
        theme: Visual theme ("light", "dark", or "auto")
        title: Optional custom title for the widget
        data: Optional data payload for the widget
        **props: Additional widget-specific properties
        
    Returns:
        Complete HTML document string
        
    Raises:
        ValueError: If widget type is not registered or invalid
        
    Examples:
        >>> html = render_webapp("calculator", theme="dark")
        >>> html = render_webapp(WidgetType.TODO, title="My Tasks")
        >>> html = render_webapp("timer", theme="light")
    """
    # Convert string types to enums
    if isinstance(widget_type, str):
        try:
            widget_type = WidgetType(widget_type.lower())
        except ValueError:
            raise ValueError(
                f"Unknown widget type: {widget_type}. "
                f"Available types: {', '.join(t.value for t in WidgetType)}"
            )
    
    if isinstance(theme, str):
        try:
            theme = WidgetTheme(theme.lower())
        except ValueError:
            theme = WidgetTheme.DARK
    
    # Create configuration
    config = WidgetConfig(
        type=widget_type,
        theme=theme,
        title=title,
        data=data,
        props=props
    )
    
    # Render the widget
    return WidgetRegistry.render(config)


def parse_webapp_tag(tag_content: str) -> Dict[str, Any]:
    """Parse a webapp XML-style tag to extract parameters.
    
    This function parses tags like:
        <webapp type="calculator" theme="dark" />
        <webapp type="todo" title="My Tasks" />
    
    Args:
        tag_content: Content of the webapp tag
        
    Returns:
        Dictionary of parsed parameters
        
    Examples:
        >>> parse_webapp_tag('<webapp type="calculator" theme="dark" />')
        {'type': 'calculator', 'theme': 'dark'}
    """
    import re
    
    params = {}
    
    # Extract attributes using regex
    attr_pattern = r'(\w+)="([^"]*)"'
    matches = re.findall(attr_pattern, tag_content)
    
    for key, value in matches:
        params[key] = value
    
    return params


__all__ = [
    "WidgetType",
    "WidgetTheme",
    "WidgetConfig",
    "WidgetRegistry",
    "render_webapp",
    "parse_webapp_tag",
]
