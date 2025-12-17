# Playwright GUI Test Screenshots

This directory contains screenshots automatically captured by Playwright-based GUI tests. These screenshots prove that web content renders correctly and provide visual verification of browser functionality.

## Test Coverage

The Playwright test suite (`tests/integration/test_playwright_gui.py`) captures screenshots for:

1. **Simple HTML Pages** (`playwright_example_com.png`)
   - Basic HTML rendering
   - Static content display

2. **Complex Websites** (`playwright_python_org.png`)
   - Modern web pages with JavaScript
   - CSS styling and layouts

3. **Custom HTML Content** (`playwright_html_rendering.png`)
   - AI-generated HTML rendering
   - Data URL support
   - Modern CSS features (gradients, backdrop filters)

4. **Navigation Sequences** (`playwright_nav_step*.png`)
   - Multi-step browsing
   - Forward/back navigation
   - URL history

5. **Comprehensive Suite** (`playwright_suite_*.png`)
   - Multiple scenarios in one test run
   - Search engines, documentation sites
   - Various content types

## Running the Tests

### Basic Test Run
```bash
# Run all Playwright tests
pytest tests/integration/test_playwright_gui.py -v -s -m playwright

# Run a specific test
pytest tests/integration/test_playwright_gui.py::TestPlaywrightGUI::test_playwright_can_load_simple_page -v -s
```

### Prerequisites
```bash
# Install dependencies
uv sync

# Install Playwright browsers (only needed once)
uv run playwright install chromium
```

### Viewing Screenshots
Screenshots are saved to `assets/screenshots/playwright/` and can be viewed with any image viewer:

```bash
# Open with default image viewer (Linux)
xdg-open assets/screenshots/playwright/playwright_example_com.png

# Or use eog, feh, etc.
eog assets/screenshots/playwright/*.png
```

## How It Works

The Playwright tests:
1. Launch a Chromium browser instance in headless mode
2. Navigate to test URLs or render custom HTML
3. Wait for page load and rendering to complete
4. Capture screenshots at 1280x720 resolution
5. Save PNG files to this directory

These screenshots provide visual proof that:
- Web pages load correctly
- Content renders as expected
- Navigation works properly
- HTML/CSS features are supported

## Comparison with Minimal Browser

While these tests use Playwright/Chromium, they serve as a baseline for comparison with the Minimal Browser's Qt WebEngine rendering. Both should produce similar visual output when rendering the same content, proving that the Minimal Browser works correctly.

## CI/CD Integration

These tests are designed to run in CI environments without a display:
- Playwright runs in headless mode
- No X server or Wayland required
- Screenshots are captured using virtual framebuffer
- Tests pass on GitHub Actions, GitLab CI, etc.

## Test Markers

The tests use pytest markers for organization:
- `@pytest.mark.playwright` - Identifies Playwright-based tests
- `@pytest.mark.integration` - Integration tests requiring full setup
- `@pytest.mark.slow` - Tests that take longer to run

Filter by markers:
```bash
# Only Playwright tests
pytest -m playwright

# Exclude slow tests
pytest -m "playwright and not slow"
```
