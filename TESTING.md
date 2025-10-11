# Testing Guide for Minimal Browser

This document provides comprehensive information about the testing infrastructure for the Minimal Browser project.

## Overview

The Minimal Browser project uses **pytest** as its testing framework, providing:
- Comprehensive unit tests for individual components
- Integration tests for component interactions
- Automated test discovery and execution
- Coverage reporting capabilities
- CI/CD compatible test running

## Table of Contents

- [Quick Start](#quick-start)
- [Test Organization](#test-organization)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Test Fixtures](#test-fixtures)
- [Coverage Reports](#coverage-reports)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Installing Test Dependencies

Using `uv` (recommended):
```bash
uv sync --dev
```

Using `pip`:
```bash
pip install -e ".[dev]"
# or
pip install pytest pytest-cov
```

### Running All Tests

```bash
# Using the test runner script
python run_tests.py

# Or directly with pytest
pytest

# Or with uv
uv run pytest
```

### Running Specific Test Suites

```bash
# Run only unit tests
python run_tests.py --unit

# Run only integration tests
python run_tests.py --integration

# Run specific test file
pytest tests/unit/ai/test_schemas.py

# Run specific test class
pytest tests/unit/ai/test_schemas.py::TestNavigateAction

# Run specific test method
pytest tests/unit/ai/test_schemas.py::TestNavigateAction::test_valid_navigate_action
```

## Test Organization

The test suite follows a clear organizational structure:

```
tests/
├── conftest.py              # Shared fixtures and pytest configuration
├── unit/                    # Unit tests for individual components
│   ├── ai/                  # AI module tests
│   │   ├── test_schemas.py  # Pydantic model tests
│   │   └── test_tools.py    # Response processor tests
│   ├── engines/             # Web engine tests
│   ├── rendering/           # HTML rendering tests
│   │   └── test_html.py     # HTML utilities tests
│   ├── storage/             # Storage layer tests
│   │   └── test_conversations.py
│   └── ui/                  # UI component tests
└── integration/             # Integration tests
    ├── ai/                  # AI integration tests
    ├── engines/             # Engine integration tests
    └── ...
```

### Test Categories

Tests are organized by category using pytest markers:

- **unit**: Tests for individual functions/classes in isolation
- **integration**: Tests for component interactions
- **ui**: Tests requiring UI components (may fail in headless environments)
- **slow**: Tests that take significant time (>1 second)
- **requires_api_key**: Tests requiring OpenRouter API key

## Running Tests

### Basic Usage

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with very verbose output
pytest -vv
```

### Filtering Tests

```bash
# Run tests matching a keyword
pytest -k "navigate"

# Run tests matching multiple keywords
pytest -k "navigate or search"

# Run tests NOT matching a keyword
pytest -k "not slow"

# Run only marked tests
pytest -m unit
pytest -m "unit and not slow"
```

### Using the Test Runner

The `run_tests.py` script provides convenient shortcuts:

```bash
# Run all tests
./run_tests.py

# Run unit tests only
./run_tests.py --unit

# Run with coverage
./run_tests.py --coverage

# Run verbose
./run_tests.py -v

# Run specific file
./run_tests.py tests/unit/ai/test_schemas.py

# Run with keyword filter
./run_tests.py -k "navigate"

# Disable warnings
./run_tests.py --no-warnings
```

## Writing Tests

### Basic Test Structure

```python
"""Unit tests for [component name]."""

from __future__ import annotations

import pytest

from minimal_browser.ai.schemas import NavigateAction


class TestNavigateAction:
    """Test NavigateAction model."""

    def test_valid_navigate_action(self):
        """Test creating a valid NavigateAction."""
        action = NavigateAction(url="https://example.com")
        assert action.type == "navigate"
        assert str(action.url) == "https://example.com/"

    def test_invalid_navigate_action(self):
        """Test NavigateAction validation."""
        with pytest.raises(ValidationError):
            NavigateAction(url="not-a-url")
```

### Test Naming Conventions

- **Test files**: `test_<module_name>.py`
- **Test classes**: `Test<ClassName>` (PascalCase)
- **Test methods**: `test_<what_it_tests>` (snake_case)
- **Docstrings**: All tests should have descriptive docstrings

### Test Patterns

#### Testing Pydantic Models

```python
def test_model_validation(self):
    """Test model validates input correctly."""
    # Valid input
    model = MyModel(field="value")
    assert model.field == "value"
    
    # Invalid input
    with pytest.raises(ValidationError):
        MyModel(field="")
```

#### Testing Functions

```python
def test_function_output(self):
    """Test function returns expected output."""
    result = my_function("input")
    assert result == "expected_output"

def test_function_raises_error(self):
    """Test function raises error on invalid input."""
    with pytest.raises(ValueError):
        my_function(None)
```

#### Testing with Fixtures

```python
def test_with_fixture(self, sample_html):
    """Test using shared fixture."""
    result = process_html(sample_html)
    assert "<h1>" in result
```

### Parameterized Tests

Use `pytest.mark.parametrize` for testing multiple inputs:

```python
@pytest.mark.parametrize("url,expected", [
    ("https://example.com", True),
    ("http://test.org", True),
    ("not-a-url", False),
])
def test_url_validation(url, expected):
    """Test URL validation with various inputs."""
    result = is_valid_url(url)
    assert result == expected
```

## Test Fixtures

### Available Fixtures

Fixtures are defined in `tests/conftest.py`:

#### `sample_html`
Provides sample HTML content for testing.

```python
def test_html_processing(sample_html):
    """Test HTML processing."""
    result = process_html(sample_html)
    assert result is not None
```

#### `sample_url`
Provides a sample URL (`https://example.com`).

```python
def test_navigation(sample_url):
    """Test navigation."""
    navigate_to(sample_url)
```

#### `sample_ai_responses`
Provides a dictionary of sample AI responses:
- `navigate`: Navigation command
- `search`: Search query
- `html`: HTML generation
- `plain_url`: Plain URL
- `plain_search`: Natural language search
- `todo_html`: Todo list generation

```python
def test_response_parsing(sample_ai_responses):
    """Test parsing various AI responses."""
    action = parse_response(sample_ai_responses["navigate"])
    assert isinstance(action, NavigateAction)
```

#### `mock_openrouter_api_key`
Sets a mock API key in environment variables.

```python
def test_api_client(mock_openrouter_api_key):
    """Test API client initialization."""
    client = AIClient()
    assert client.api_key is not None
```

### Creating Custom Fixtures

Add fixtures to `tests/conftest.py`:

```python
@pytest.fixture
def custom_data():
    """Provide custom test data."""
    return {"key": "value"}
```

## Coverage Reports

### Generating Coverage

```bash
# Terminal report
pytest --cov=src/minimal_browser --cov-report=term-missing

# HTML report
pytest --cov=src/minimal_browser --cov-report=html

# Using test runner
./run_tests.py --coverage
```

### Viewing HTML Coverage

After running with `--cov-report=html`:

```bash
# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage Goals

- **Overall coverage**: Target 80%+
- **Critical modules**: Target 90%+
  - `ai/schemas.py`
  - `ai/tools.py`
  - `rendering/html.py`
- **UI modules**: Best effort (may require mocking)

## CI/CD Integration

### Running Tests in CI

The test suite is designed to work in CI environments:

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests with coverage
pytest --cov=src/minimal_browser --cov-report=xml --cov-report=term

# Exit with error code if tests fail
# (pytest returns non-zero on failure)
```

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      - name: Run tests
        run: |
          pytest --cov=src/minimal_browser --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Troubleshooting

### Common Issues

#### ImportError: No module named 'minimal_browser'

**Solution**: Ensure you've installed the package in development mode:
```bash
pip install -e .
# or
uv sync
```

#### Tests requiring PySide6 fail in headless environment

**Solution**: Mark tests with `@pytest.mark.ui` and skip in CI:
```python
@pytest.mark.ui
def test_browser_ui():
    """Test requiring display."""
    pass
```

Run tests excluding UI:
```bash
pytest -m "not ui"
```

#### Fixture not found

**Solution**: Ensure `conftest.py` is in the right location and pytest can discover it:
```bash
pytest --fixtures  # List all available fixtures
```

### Environment-Specific Tests

For tests requiring specific environment setup:

```python
@pytest.mark.skipif(
    os.getenv("OPENROUTER_API_KEY") is None,
    reason="Requires OpenRouter API key"
)
def test_api_integration():
    """Test requiring API key."""
    pass
```

### Debugging Tests

```bash
# Run with Python debugger on failure
pytest --pdb

# Run last failed tests only
pytest --lf

# Show local variables on failure
pytest -l

# Stop after first failure
pytest -x
```

## Best Practices

1. **Write tests first**: Consider TDD for new features
2. **Keep tests isolated**: Each test should be independent
3. **Use descriptive names**: Test names should clearly indicate what they test
4. **Test edge cases**: Don't just test the happy path
5. **Mock external dependencies**: Don't rely on network/API in unit tests
6. **Keep tests fast**: Unit tests should run in milliseconds
7. **Use fixtures**: Share common setup code
8. **Document complex tests**: Add comments explaining non-obvious test logic

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Pydantic testing](https://docs.pydantic.dev/latest/concepts/validation/)
- [Project CONTRIBUTING.md](CONTRIBUTING.md)

## Getting Help

If you encounter issues with testing:
1. Check this documentation
2. Review existing tests for examples
3. Check pytest documentation
4. Open an issue on GitHub
