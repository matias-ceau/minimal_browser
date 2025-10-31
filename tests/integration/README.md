# Integration Tests

This directory contains integration tests that verify the browser works end-to-end.

## Limitations

The integration tests require a display server and Qt graphics libraries that are not available in CI environments. Specifically, PySide6 requires:
- libEGL.so.1 (OpenGL ES library)
- A display server (X11, Wayland, or offscreen rendering support)

## Running Integration Tests Locally

To run these tests on your local machine:

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get install libegl1 libxkbcommon-x11-0 libxcb-cursor0

# Run with offscreen platform
QT_QPA_PLATFORM=offscreen pytest tests/integration/ -v

# Or with actual display
pytest tests/integration/ -v
```

## What These Tests Verify

- **test_browser_smoke.py**:
  - Browser can be instantiated
  - Modules can be imported
  - URL building works
  - AI action parsing works
  - Conversation storage works
  - Screenshot capability exists
  - (When display available) Full browser renders and captures screenshots

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
