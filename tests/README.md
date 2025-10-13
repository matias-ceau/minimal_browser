# Tests Directory

This directory contains the comprehensive test suite for the Minimal Browser project.

## Structure

```
tests/
├── conftest.py              # Pytest configuration and shared fixtures
├── test_utils.py            # Shared test utilities
├── unit/                    # Unit tests for individual components
│   ├── ai/                  # AI module tests
│   │   ├── test_schemas.py  # Pydantic model validation tests
│   │   └── test_tools.py    # Response processor tests
│   ├── engines/             # Web engine tests
│   ├── rendering/           # HTML rendering tests
│   │   └── test_html.py     # HTML utilities and data URL tests
│   ├── storage/             # Storage layer tests
│   │   └── test_conversations.py  # Conversation logging tests
│   └── ui/                  # UI component tests
└── integration/             # Integration tests
    └── ...
```

## Running Tests

See [TESTING.md](../TESTING.md) for comprehensive testing documentation.

### Quick Start

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=src/minimal_browser

# Run specific test file
pytest tests/unit/ai/test_schemas.py
```

## Test Coverage

Current test coverage by module:

- **AI Schemas** (`ai/schemas.py`): Comprehensive Pydantic model validation tests
- **AI Tools** (`ai/tools.py`): Response parsing and action conversion tests
- **HTML Rendering** (`rendering/html.py`): Data URL creation and HTML wrapping tests
- **Storage** (`storage/conversations.py`): Conversation logging and memory tests

## Adding New Tests

1. Create test file following naming convention: `test_<module>.py`
2. Import required modules and fixtures
3. Create test classes: `Test<ComponentName>`
4. Write test methods: `test_<what_it_tests>`
5. Add docstrings explaining what each test validates
6. Run tests to ensure they pass

Example:

```python
"""Unit tests for my new component."""

import pytest
from minimal_browser.my_module import MyComponent


class TestMyComponent:
    """Test MyComponent class."""

    def test_basic_functionality(self):
        """Test basic component functionality."""
        component = MyComponent()
        assert component.process("input") == "expected_output"
```

## Test Requirements

- **Unit tests**: Should test individual functions/classes in isolation
- **Integration tests**: Should test component interactions
- **No external dependencies**: Use mocks for API calls, file systems, etc.
- **Fast execution**: Unit tests should complete in milliseconds
- **Clear assertions**: Each test should have clear pass/fail conditions
- **Good documentation**: All tests should have descriptive docstrings

## CI/CD Compatibility

Tests are designed to run in CI/CD environments:
- No display required (UI tests are marked and can be skipped)
- No API keys required for unit tests
- Deterministic results (no random data, time-dependent logic)
- Fast execution for quick feedback

## Troubleshooting

See [TESTING.md](../TESTING.md#troubleshooting) for common issues and solutions.
