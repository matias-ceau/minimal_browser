# Browser Screenshots

This directory contains screenshots demonstrating the Minimal Browser's capabilities.

## Screenshots

### 01_browser_launch.png
**Browser Initial Launch**
- Shows the browser starting with the default Google homepage
- Demonstrates the clean, minimal UI design
- Status bar shows mode (NORMAL) and page title

### 02_example_com.png
**Basic Web Navigation**
- Example.com loaded and rendered
- Demonstrates basic HTML rendering capabilities
- Simple, fast page load

### 03_python_org.png
**Complex Website Rendering**
- Python.org with full JavaScript support
- Modern website with dynamic content
- Shows browser can handle production websites

### 04_help_screen.png
**Built-in Help System**
- Accessible via `?` keybinding
- Shows all vim-like keybindings
- Demonstrates modal interface (NORMAL/COMMAND/INSERT modes)
- Documents navigation, search, and AI features

## How Screenshots Are Generated

These screenshots are automatically captured using integration tests:

1. **Manual capture:** Run `scripts/capture_screenshots.py` with xvfb:
   ```bash
   xvfb-run -a -s "-screen 0 1280x720x24" python scripts/capture_screenshots.py
   ```

2. **Integration tests:** The `tests/integration/test_app_launch.py` file includes screenshot capture functionality.

## Screenshot Specifications

- **Resolution:** 1280x720 (720p)
- **Format:** PNG
- **Color Depth:** 24-bit
- **Captured with:** Qt WebEngine on virtual X11 display (Xvfb)

## Updating Screenshots

To update screenshots when features change:

```bash
# Install dependencies
sudo apt-get install xvfb

# Run screenshot capture script
cd /path/to/minimal_browser
xvfb-run -a -s "-screen 0 1280x720x24" uv run python scripts/capture_screenshots.py
```

The script will automatically:
- Launch the browser
- Navigate to different pages
- Wait for content to load
- Capture high-quality screenshots
- Save them in this directory
