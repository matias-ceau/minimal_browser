"""AI integration module"""

from .worker import AIWorker
from .models import MODELS, DEFAULT_MODEL, get_model, list_models
from .auth import auth_manager
from .tools import ResponseProcessor, URLBuilder
from .schemas import (
    AIAction,
    NavigateAction,
    SearchAction,
    HtmlAction,
    ConversationMemory,
    ConversationMessage,
)

__all__ = [
    "AIWorker", 
    "MODELS", 
    "DEFAULT_MODEL", 
    "get_model", 
    "list_models",
    "auth_manager",
    "ResponseProcessor",
    "URLBuilder",
    "AIAction",
    "NavigateAction",
    "SearchAction",
    "HtmlAction",
    "ConversationMessage",
    "ConversationMemory",
]
