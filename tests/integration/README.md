# Integration Tests

This directory contains integration tests that verify the browser works end-to-end.

## Test Files

### test_headless_launch.py
Headless tests that prove the app can launch and function without a display.
These tests work in CI environments using Qt's offscreen platform.

**Tests:**
- App instantiation
- Initial state verification
- URL navigation
- Modal interface (NORMAL/COMMAND/INSERT modes)
- Help screen accessibility

**Running:**
```bash
QT_QPA_PLATFORM=offscreen pytest tests/integration/test_headless_launch.py -v
```

### test_app_launch.py
Full integration tests with screenshot capture for documentation.
Requires a display or virtual framebuffer.

**Tests:**
- Browser window launch
- Initial state verification
- Screenshot capture of key features
- Navigation functionality
- Help screen rendering
- Modal interface demonstration

**Running:**
```bash
# With actual display
pytest tests/integration/test_app_launch.py -v

# With virtual framebuffer (Xvfb)
xvfb-run pytest tests/integration/test_app_launch.py -v

# With offscreen rendering
QT_QPA_PLATFORM=offscreen pytest tests/integration/test_app_launch.py -v
```

## Limitations

Some integration tests require Qt graphics libraries and may not work in all CI environments. Specifically, PySide6 requires:
- libEGL.so.1 (OpenGL ES library)
- A display server (X11, Wayland, or offscreen rendering support)

## Running Integration Tests Locally

To run these tests on your local machine:

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get install libegl1 libxkbcommon-x11-0 libxcb-cursor0

# Run all integration tests with offscreen platform
QT_QPA_PLATFORM=offscreen pytest tests/integration/ -v

# Run with actual display
pytest tests/integration/ -v

# Run specific test file
pytest tests/integration/test_headless_launch.py -v
```

## What These Tests Verify

### Core Functionality
- ✅ Browser can be instantiated
- ✅ Initial state is correct (NORMAL mode, empty buffer)
- ✅ URL navigation works
- ✅ Modal interface functions (vim-like modes)
- ✅ Help screen can be displayed
- ✅ Browser doesn't crash on basic operations

### Screenshot Capture (when display available)
- Browser UI rendering
- Web page display
- Help screen documentation
- Different browser states

## CI Testing Strategy

Since integration tests cannot run in CI without display support:
1. Unit tests verify individual components work correctly
2. Integration tests are skipped in CI (marked with `@pytest.mark.skipif`)
3. Manual testing is recommended before releases
4. Future: Consider adding headless Chrome/Playwright tests as alternative

## Manual Testing Checklist

Before releases, manually verify:
- [ ] Browser launches: `python -m minimal_browser`
- [ ] Page loads correctly
- [ ] AI integration works (requires OPENROUTER_API_KEY)
- [ ] Keybindings respond (vim-like navigation)
- [ ] Command palette opens (`:`, `/`, etc.)
- [ ] Screenshots can be captured
- [ ] Different rendering engines work

## Future Improvements

- Add Docker container with graphics support for CI
- Use virtual framebuffer (Xvfb) in CI
- Add Playwright/Selenium-style E2E tests
- Mock Qt components more comprehensively in unit tests
