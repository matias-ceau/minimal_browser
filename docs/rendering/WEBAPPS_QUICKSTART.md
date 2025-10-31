# Webapps Module - Quick Start Guide

## Installation

The webapps module is part of the minimal_browser package:

```bash
pip install minimal-browser
```

Or with uv:
```bash
uv sync
```

## Basic Usage

### Import the Module

```python
from minimal_browser.rendering.webapps import render_webapp
```

### Render a Widget

```python
# Render a calculator
html = render_webapp("calculator")

# Render with custom theme
html = render_webapp("calculator", theme="light")

# Render with custom title
html = render_webapp("todo", title="My Tasks")
```

## Available Widgets

| Widget | Type String | Description |
|--------|------------|-------------|
| Calculator | `"calculator"` | Scientific calculator with basic operations |
| Todo List | `"todo"` | Task management with completion tracking |
| Timer | `"timer"` | Stopwatch and countdown timer |
| Notes | `"notes"` | Simple note-taking application |
| Card | `"card"` | Content display card |

## AI Integration Examples

### Using Natural Language

When users interact with the AI, these phrases automatically generate widgets:

- **Calculator**: "create a calculator", "show me a calculator"
- **Todo**: "make a todo list", "I need a task manager"
- **Timer**: "create a timer", "I need a stopwatch"
- **Notes**: "give me a notes app", "create note-taking"

### Using Explicit Commands

The AI can also use explicit prefixes:

```
WEBAPP: calculator
WEBAPP: <webapp type="todo" theme="dark" />
WEBAPP: <webapp type="timer" title="My Timer" />
```

## Code Examples

### Example 1: Simple Calculator

```python
from minimal_browser.rendering.webapps import render_webapp
from minimal_browser.rendering.html import create_data_url

# Render the widget
html = render_webapp("calculator", theme="dark")

# Convert to data URL for browser display
data_url = create_data_url(html)

# Now you can load this in a browser:
# browser.load(data_url)
```

### Example 2: Custom Todo List

```python
html = render_webapp(
    widget_type="todo",
    theme="light",
    title="Shopping List"
)
```

### Example 3: Multiple Widgets

```python
# Create all available widgets
widgets = {
    "calc": render_webapp("calculator", title="Calculator"),
    "tasks": render_webapp("todo", title="My Tasks"),
    "time": render_webapp("timer", title="Timer"),
    "memo": render_webapp("notes", title="Notes"),
}

# Save to files or display in tabs
for name, html in widgets.items():
    with open(f"{name}.html", "w") as f:
        f.write(html)
```

## Widget Features

### Calculator
- ✓ Basic operations (+, -, ×, ÷)
- ✓ Decimal numbers
- ✓ Clear and backspace
- ✓ Real-time calculation

### Todo List
- ✓ Add new tasks
- ✓ Mark as complete
- ✓ Delete tasks
- ✓ Statistics display

### Timer
- ✓ Stopwatch mode
- ✓ Countdown timer
- ✓ Hour:Minute:Second format
- ✓ Alert on completion

### Notes
- ✓ Create notes
- ✓ Edit existing notes
- ✓ Timestamp tracking
- ✓ Card-based layout

## Customization

### Theme Options

```python
# Dark theme (default)
html = render_webapp("calculator", theme="dark")

# Light theme
html = render_webapp("calculator", theme="light")

# Auto theme (uses system preference - future)
html = render_webapp("calculator", theme="auto")
```

### Custom Titles

```python
html = render_webapp(
    "calculator",
    title="Scientific Calculator"
)
```

### Custom Data

```python
html = render_webapp(
    "card",
    title="Welcome",
    data="<p>This is a custom card with <strong>HTML</strong> content.</p>"
)
```

## Testing

Test your widgets:

```bash
# Run all webapps tests
pytest tests/unit/rendering/test_webapps.py -v

# Test specific features
pytest tests/unit/rendering/test_webapps.py::TestRenderWebapp -v
```

## Troubleshooting

### Widget doesn't display
- Ensure you're using a valid widget type
- Check that the HTML is properly encoded
- Verify the data URL is correctly formatted

### JavaScript doesn't work
- Make sure the browser allows JavaScript execution
- Check browser console for errors
- Verify no CSP restrictions

### Theme not applied
- Check the theme parameter is valid ("light", "dark", "auto")
- Invalid themes fall back to "dark"

## Next Steps

- Read the full documentation: `docs/rendering/WEBAPPS.md`
- Explore AI integration: `src/minimal_browser/ai/tools.py`
- Add custom widgets: See "Contributing" in main docs
- Review security guidelines: See "Security Considerations" section

## Support

For issues or questions:
- Check the main project README
- Review the test files for examples
- See the ROADMAP.md for planned features
