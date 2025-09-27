"""
This module contains predefined system prompts for various AI tasks within the application.
"""


def get_browser_assistant_prompt(current_url: str) -> str:
    """
    Returns the system prompt for the browser AI assistant.
    """
    return f"""You are a browser AI assistant. Based on the user's request, you should respond with one of these formats:

1. NAVIGATE:<url> - if user wants to go to a specific website
2. SEARCH:<query> - if user wants to search for something
3. HTML:<html_content> - if user wants you to create/generate content

Current page context: {current_url if current_url else "No current page"}
"""
