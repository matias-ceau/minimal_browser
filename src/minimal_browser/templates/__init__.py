"""HTML templates for AI-generated content"""

from .help import get_help_content
from .calculator import get_calculator_html
from .todo import get_todo_html

__all__ = ["get_help_content", "get_calculator_html", "get_todo_html"]