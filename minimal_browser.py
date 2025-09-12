#!/usr/bin/env python3

import sys
from PyQt6.QtCore import QUrl, Qt, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut, QFont
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings


class VimBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Vim modes
        self.mode = "NORMAL"
        self.command_buffer = ""
        
        # Buffer management
        self.buffers = []
        self.current_buffer = 0
        
        # Create web view with optimized settings
        self.browser = QWebEngineView()
        
        # Optimize web engine settings for speed
        settings = self.browser.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.XSSAuditingEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.SpatialNavigationEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.HyperlinkAuditingEnabled, False)
        
        # Use default profile for better caching
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
        profile.setHttpCacheMaximumSize(50 * 1024 * 1024)  # 50MB cache
        
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
        
        # Load initial URL
        initial_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.google.com"
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
        QShortcut(QKeySequence("a"), self, self.ai_search_mode)     # AI/LLM search
        QShortcut(QKeySequence("F1"), self, self.show_help)        # Help
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
            if key in [':', '/', 's', 'a', 'r', 'h', 'l', 'n', 'p', 'o', 't', 'x', 'q', 'j', 'k', 'd', 'u', 'g']:
                # Let shortcuts handle these
                pass
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Position command line at bottom center
        if hasattr(self, 'command_line'):
            width = min(400, self.width() - 40)
            self.command_line.resize(width, 30)
            self.command_line.move(
                (self.width() - width) // 2,
                self.height() - 50
            )
    
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
    
    def show_help(self):
        if self.mode == "NORMAL":
            help_content = self.get_help_content()
            # Create a data URL with the help content
            help_url = f"data:text/html;charset=utf-8,{help_content}"
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
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        qurl = QUrl(url)
        self.browser.load(qurl)
        
        # Add to buffers if not already there
        if url not in self.buffers:
            self.buffers.append(url)
            self.current_buffer = len(self.buffers) - 1
        else:
            self.current_buffer = self.buffers.index(url)
        
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
            self.browser.load(QUrl(self.buffers[self.current_buffer]))
            self.update_title()
    
    def prev_buffer(self):
        if self.mode == "NORMAL" and len(self.buffers) > 1:
            self.current_buffer = (self.current_buffer - 1) % len(self.buffers)
            self.browser.load(QUrl(self.buffers[self.current_buffer]))
            self.update_title()
    
    def scroll_page(self, pixels):
        if self.mode == "NORMAL":
            self.browser.page().runJavaScript(f"window.scrollBy(0, {pixels});")
    
    def scroll_top(self):
        if self.mode == "NORMAL":
            self.browser.page().runJavaScript("window.scrollTo(0, 0);")
    
    def scroll_bottom(self):
        if self.mode == "NORMAL":
            self.browser.page().runJavaScript("window.scrollTo(0, document.body.scrollHeight);")
    
    def quit_if_normal(self):
        if self.mode == "NORMAL":
            self.close()
    
    def show_buffers(self):
        # Show buffer info briefly in title
        if self.buffers:
            buf_info = f"Buffers: {', '.join(f'{i+1}:{url.split("/")[-1][:20]}' for i, url in enumerate(self.buffers))}"
            self.setWindowTitle(buf_info)
            self.mode_timer.start(3000)  # Hide after 3 seconds
    
    def update_title(self):
        if self.mode == "NORMAL":
            # Show buffer info subtly
            if self.buffers:
                current_domain = self.buffers[self.current_buffer].split('/')[2] if '/' in self.buffers[self.current_buffer] else self.buffers[self.current_buffer]
                title = f"[{self.current_buffer + 1}/{len(self.buffers)}] {current_domain}"
            else:
                title = "Vim Browser"
        else:
            title = f"-- {self.mode} --"
        
        self.setWindowTitle(title)
    
    def hide_mode_indicator(self):
        if self.mode == "NORMAL":
            self.update_title()
    
    def smart_search(self, query):
        """Smart search - detects if it's a URL or search query"""
        query = query.strip()
        if not query:
            return
        
        # Check if it looks like a URL
        if ('.' in query and ' ' not in query) or query.startswith(('http://', 'https://')):
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
            <tr><td><span class="key">/</span></td><td>Search in page</td></tr>
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
        <p><span class="key">s python tutorial</span> → Google search</p>
        <p><span class="key">s github.com</span> → Open GitHub</p>
        <p><span class="key">a explain quantum computing</span> → Ask ChatGPT</p>
        <p><span class="key">o reddit.com</span> → Open Reddit</p>
    </div>
    
    <p style="margin-top: 40px; color: #666;">Press <span class="key">Escape</span> to return to normal browsing</p>
</body>
</html>""".replace('\n', '').replace('"', '%22')


if __name__ == "__main__":
    # Set up application with optimizations
    app = QApplication(sys.argv)
    
    # Create and show browser
    browser = VimBrowser()
    browser.show()
    
    sys.exit(app.exec())
