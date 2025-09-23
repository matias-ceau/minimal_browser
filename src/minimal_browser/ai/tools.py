"""AI tools and response processing"""

import re
from typing import Tuple, Optional
from urllib.parse import quote
import base64


class ResponseProcessor:
    """Processes AI responses and determines actions"""
    
    @staticmethod
    def parse_response(response: str) -> Tuple[str, str]:
        """
        Parse AI response and return (action_type, content)
        
        Returns:
            - ("navigate", url) for navigation
            - ("search", query) for search
            - ("html", html_content) for HTML generation
        """
        response = response.strip()
        
        # Check for explicit action prefixes
        if response.startswith("NAVIGATE:"):
            return "navigate", response[9:].strip()
        elif response.startswith("SEARCH:"):
            return "search", response[7:].strip()
        elif response.startswith("HTML:"):
            return "html", response[5:].strip()
        
        # Intelligent parsing based on content
        return ResponseProcessor._intelligent_parse(response)
    
    @staticmethod
    def _intelligent_parse(response: str) -> Tuple[str, str]:
        """Intelligently parse response without explicit prefixes"""
        response_lower = response.lower()
        
        # Navigation patterns
        nav_patterns = [
            r"(?:navigate|go|open|visit)\s+(?:to\s+)?([^\s]+\.[a-z]{2,})",
            r"(?:open|visit)\s+([a-z]+\.com|[a-z]+\.org|[a-z]+\.net)",
        ]
        
        for pattern in nav_patterns:
            match = re.search(pattern, response_lower)
            if match:
                url = match.group(1)
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                return "navigate", url
        
        # Search patterns
        if any(word in response_lower for word in ['search for', 'find', 'look up']):
            # Extract search query
            search_match = re.search(r'(?:search for|find|look up)\s+"?([^"]+)"?', response_lower)
            if search_match:
                return "search", search_match.group(1)
        
        # HTML generation patterns
        html_indicators = [
            'create', 'make', 'generate', 'build', 'design',
            'todo', 'calculator', 'form', 'page', 'website'
        ]
        
        if any(indicator in response_lower for indicator in html_indicators):
            return "html", ResponseProcessor._wrap_as_html(response)
        
        # Default: treat as search for short responses, HTML for long ones
        if len(response.split()) <= 5:
            return "search", response
        else:
            return "html", ResponseProcessor._wrap_as_html(response)
    
    @staticmethod
    def _wrap_as_html(content: str) -> str:
        """Wrap text content in HTML"""
        # Convert markdown-like formatting
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
        content = content.replace('\n\n', '</p><p>')
        content = content.replace('\n', '<br>')
        
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
        .content {{ 
            background: rgba(255,255,255,0.1); 
            padding: 30px; 
            border-radius: 15px; 
            backdrop-filter: blur(10px);
        }}
        h1 {{ font-size: 2.5em; margin-bottom: 20px; }}
        p {{ margin-bottom: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="content">
            <h1>🤖 AI Response</h1>
            <p>{content}</p>
        </div>
    </div>
</body>
</html>"""


class URLBuilder:
    """Builds data URLs for HTML content"""
    
    @staticmethod
    def create_data_url(html_content: str) -> str:
        """Create base64 data URL from HTML content"""
        encoded_html = base64.b64encode(html_content.encode('utf-8')).decode('ascii')
        return f"data:text/html;base64,{encoded_html}"
    
    @staticmethod
    def create_search_url(query: str, engine: str = "google") -> str:
        """Create search URL"""
        if engine == "google":
            return f"https://www.google.com/search?q={quote(query)}"
        elif engine == "duckduckgo":
            return f"https://duckduckgo.com/?q={quote(query)}"
        else:
            return f"https://www.google.com/search?q={quote(query)}"