# Web Applications Rendering Module

## Overview

The `webapps.py` module provides a comprehensive framework for rendering interactive web applications and widgets within the minimal browser. It enables the AI to generate rich, interactive experiences like calculators, todo lists, timers, and notes apps.

## Features

- **Widget Registry**: Extensible system for registering and managing widget types
- **Interactive Templates**: Pre-built templates for common widget types
- **Theme Support**: Light and dark theme support for all widgets
- **AI Integration**: Seamless integration with the AI response processing pipeline
- **Type Safety**: Pydantic-based validation for all widget configurations

## Built-in Widgets

### 1. Calculator
A fully functional scientific calculator with:
- Basic arithmetic operations (+, -, ×, ÷)
- Decimal support
- Clear and backspace functions
- Keyboard-like button layout

**Usage:**
```python
from minimal_browser.rendering.webapps import render_webapp

html = render_webapp("calculator", theme="dark", title="My Calculator")
```

**AI Command Examples:**
- "create a calculator"
- "show me a calculator"
- "I need a calculator"

### 2. Todo List
A task management widget featuring:
- Add/remove tasks
- Mark tasks as completed
- Task statistics (total, completed, remaining)
- Persistent state during session

**Usage:**
```python
html = render_webapp("todo", theme="dark", title="My Tasks")
```

**AI Command Examples:**
- "create a todo list"
- "I need a todo app"
- "make me a task manager"

### 3. Timer & Stopwatch
Dual-mode timing widget with:
- **Stopwatch Mode**: Count up with start/stop/reset
- **Timer Mode**: Countdown timer with alarm
- Tab interface for easy switching
- Clean, easy-to-read display

**Usage:**
```python
html = render_webapp("timer", theme="dark", title="Timer")
```

**AI Command Examples:**
- "create a timer"
- "I need a stopwatch"
- "make me a timer app"

### 4. Notes
A simple note-taking application with:
- Create and edit notes
- Card-based layout
- Click to edit functionality
- Timestamp tracking

**Usage:**
```python
html = render_webapp("notes", theme="dark", title="My Notes")
```

**AI Command Examples:**
- "create a notes app"
- "I need note-taking"
- "give me a notes widget"

### 5. Card
A simple card component for displaying content:
- Customizable title and content
- Clean, minimal design
- Supports HTML content

**Usage:**
```python
html = render_webapp("card", title="Info", data="<p>Content here</p>")
```

## API Reference

### `render_webapp(widget_type, theme="dark", title=None, data=None, **props)`

Main entry point for rendering widgets.

**Parameters:**
- `widget_type` (str | WidgetType): Type of widget to render
- `theme` (str | WidgetTheme): Visual theme ("light", "dark", or "auto")
- `title` (str, optional): Custom title for the widget
- `data` (Any, optional): Data payload for the widget
- `**props`: Additional widget-specific properties

**Returns:**
- `str`: Complete HTML document

**Raises:**
- `ValueError`: If widget type is not registered or invalid

**Example:**
```python
html = render_webapp(
    widget_type="calculator",
    theme="dark",
    title="Scientific Calculator"
)
```

### `WidgetRegistry`

Registry for managing widget templates.

**Methods:**

#### `register(widget_type, template_func)`
Register a new widget template.

**Parameters:**
- `widget_type` (WidgetType): The widget type to register
- `template_func` (callable): Function that generates HTML

#### `is_registered(widget_type)`
Check if a widget type is registered.

**Returns:**
- `bool`: True if registered, False otherwise

#### `list_widgets()`
Get all registered widget types.

**Returns:**
- `List[WidgetType]`: List of registered widget types

#### `render(config)`
Render a widget from configuration.

**Parameters:**
- `config` (WidgetConfig): Widget configuration

**Returns:**
- `str`: HTML string

### `parse_webapp_tag(tag_content)`

Parse XML-style webapp tags to extract parameters.

**Parameters:**
- `tag_content` (str): Content of the webapp tag

**Returns:**
- `Dict[str, Any]`: Dictionary of parsed parameters

**Example:**
```python
params = parse_webapp_tag('<webapp type="calculator" theme="dark" />')
# Returns: {'type': 'calculator', 'theme': 'dark'}
```

## AI Integration

The webapps module integrates with the AI response processing system through the `WebappAction` schema.

### WebappAction Schema

```python
class WebappAction(BaseModel):
    type: Literal["webapp"] = "webapp"
    widget_type: str
    theme: Optional[str] = None
    title: Optional[str] = None
```

### AI Response Formats

The AI can generate webapp widgets using several formats:

1. **Explicit Prefix:**
   ```
   WEBAPP: calculator
   ```

2. **XML-style Tag:**
   ```
   WEBAPP: <webapp type="calculator" theme="dark" />
   ```

3. **With Custom Title:**
   ```
   WEBAPP: <webapp type="todo" title="My Tasks" />
   ```

4. **Intelligent Keyword Detection:**
   The system automatically detects keywords like "calculator", "todo", "timer", "stopwatch", and "notes" in natural language:
   - "show me a calculator" → Calculator widget
   - "I need a todo list" → Todo widget
   - "create a timer" → Timer widget

## Security Considerations

### JavaScript Execution
All widgets execute JavaScript in the browser context. The following security measures should be considered:

1. **Content Security Policy**: Widgets should run in isolated contexts
2. **No External Resources**: All JavaScript is inline, no external dependencies
3. **No Network Requests**: Widgets operate entirely client-side
4. **Input Sanitization**: User input should be sanitized before display

### Recommendations

- Always review AI-generated widget code before rendering
- Consider implementing CSP headers for enhanced security
- Use the browser's built-in sandbox features when available
- Validate and sanitize any user-provided data

### Current Security Posture

The minimal browser currently uses relaxed WebEngine settings for AI-generated HTML:
- `LocalContentCanAccessRemoteUrls` is enabled for data URLs
- XSS auditing is disabled to allow dynamic AI content

**Note**: These settings are necessary for the current functionality but should be reviewed for production use. See the main project ROADMAP.md for planned security enhancements.

## Theme System

The module supports three theme modes:

### Dark Theme (Default)
- Background: `#1a1a2e`
- Card background: `#16213e`
- Text: `#eee`
- Accent: `#667eea`

### Light Theme
- Background: `#f5f5f5`
- Card background: `#fff`
- Text: `#333`
- Accent: `#667eea`

### Auto Theme
Automatically detects system preference (future enhancement)

## Performance

- **Lazy Loading**: Widgets are rendered on-demand
- **No External Dependencies**: All CSS and JavaScript is inline
- **Lightweight**: Minimal HTML/CSS/JS footprint
- **Fast Rendering**: Sub-millisecond template generation

## Testing

Comprehensive test suite with 36+ tests covering:

- Widget type enumeration
- Theme configuration
- Widget registry functionality
- HTML rendering validation
- Theme application
- Widget customization
- Tag parsing

Run tests with:
```bash
pytest tests/unit/rendering/test_webapps.py -v
```

## Examples

### Creating a Calculator
```python
from minimal_browser.rendering.webapps import render_webapp

html = render_webapp("calculator", theme="dark")
# Display in browser...
```

### Creating a Custom-Themed Todo List
```python
html = render_webapp(
    "todo",
    theme="light",
    title="Work Tasks"
)
```

### Creating Multiple Widgets
```python
widgets = ["calculator", "todo", "timer", "notes"]

for widget_type in widgets:
    html = render_webapp(widget_type, theme="dark")
    # Save or display each widget...
```

## Future Enhancements

Planned features for future releases:

- [ ] Chart/graph widget with data visualization
- [ ] Dashboard widget for multiple components
- [ ] Grid and table layout components
- [ ] Timeline component for sequential data
- [ ] Custom color schemes beyond light/dark
- [ ] Widget state persistence
- [ ] Export functionality for widgets
- [ ] Accessibility improvements (ARIA labels, keyboard navigation)
- [ ] Responsive design enhancements
- [ ] Animation and transition effects

## Contributing

To add new widgets:

1. Create a render function following the pattern:
   ```python
   def _render_my_widget(config: WidgetConfig) -> str:
       # Generate HTML...
       return html
   ```

2. Register the widget:
   ```python
   WidgetRegistry.register(WidgetType.MY_WIDGET, _render_my_widget)
   ```

3. Add tests in `tests/unit/rendering/test_webapps.py`

4. Update this documentation

## License

Part of the minimal_browser project. See main project LICENSE for details.
