"""Help content template loader"""

from pathlib import Path


def get_help_content() -> str:
    """Load and return the help.html template content."""
    template_path = Path(__file__).parent / "help.html"
    
    if not template_path.exists():
        # Fallback content if template is missing
        return """<!DOCTYPE html>
<html>
<head>
    <title>Help Not Found</title>
</head>
<body>
    <h1>Help template not found</h1>
    <p>The help.html template could not be loaded.</p>
</body>
</html>"""
    
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()
