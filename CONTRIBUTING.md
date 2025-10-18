# Contributing to Minimal Browser

Welcome to the Minimal Browser project! This guide will help you get set up and contributing effectively, whether you're working independently or integrating AI-suggested modifications.

## 🔥 TL;DR: How to Merge AI Modifications

**If an AI assistant suggested changes and you want to integrate them:**

1. **Quick validation**: `python -m py_compile src/minimal_browser/[file].py`
2. **Test functionality**: `python -m minimal_browser` (or `uv run python -m minimal_browser`)  
3. **Check it works**: Try the specific feature the AI modified
4. **Commit**: `git add . && git commit -m "feat: [what was changed]"`
5. **Push**: `git push` (if working on a feature branch)

**For complex changes**: Read the detailed sections below, especially "Working with AI-Suggested Modifications".

## 🚀 Quick Start

### Prerequisites

- **Python 3.13+** (required for PySide6 compatibility)
- **uv** package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **OpenRouter API key** for AI functionality (optional for development)

### Development Setup

#### Option 1: Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/matias-ceau/minimal_browser.git
cd minimal_browser

# Install dependencies
uv sync

# Set up environment (optional, for AI features)
export OPENROUTER_API_KEY="your-api-key-here"

# Test the installation
uv run python -m py_compile src/minimal_browser/main.py
```

#### Option 2: Using pip (Fallback)

If `uv` is not available in your environment:

```bash
# Clone the repository
git clone https://github.com/matias-ceau/minimal_browser.git
cd minimal_browser

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies manually (refer to pyproject.toml)
pip install openai>=1.107.2 pyside6>=6.9.2 requests>=2.32.5 pydantic>=2.8.2

# Set up environment (optional, for AI features)
export OPENROUTER_API_KEY="your-api-key-here"

# Test the installation
python -m py_compile src/minimal_browser/main.py
```

### Running the Browser

```bash
# Basic run
uv run python -m minimal_browser

# With a starting URL
uv run python -m minimal_browser https://github.com

# Development mode (for debugging)
uv run python -m minimal_browser --debug
```

### API Key Management

Minimal Browser supports **secure API key storage** through system keychains for persistent credential management.

#### Option 1: System Keychain (Recommended for Development)

Store your API keys securely in your system keychain (GNOME Keyring/macOS Keychain/Windows Credential Manager):

```python
# From Python REPL or script
from minimal_browser.ai.auth import auth_manager

# Store OpenRouter key
auth_manager.set_key('openrouter', 'sk-or-v1-...', store_in_keychain=True)

# Verify it's stored
print(auth_manager.list_keychain_providers())
```

Keys stored this way persist across sessions and don't need to be set in environment variables.

#### Option 2: Environment Variables (Quick Setup)

For quick testing or CI/CD environments:

```bash
export OPENROUTER_API_KEY="your-api-key-here"
export OPENAI_API_KEY="your-openai-key"       # Optional
export ANTHROPIC_API_KEY="your-anthropic-key" # Optional
```

**Priority order:** Environment variables take precedence over keychain storage, allowing temporary overrides.

#### Checking Key Status

```bash
# Start Python REPL with the module
python -c "
from minimal_browser.ai.auth import auth_manager
print('Loaded providers:', auth_manager.list_providers())
print('Keychain providers:', auth_manager.list_keychain_providers())
"
```

## 🤖 Working with AI-Suggested Modifications

### Understanding AI Suggestions

AI assistants (like GitHub Copilot, ChatGPT, or Claude) can suggest code modifications for this project. Here's how to effectively work with them:

#### What AI Can Help With
- **Code completion** for existing patterns
- **Bug fixes** based on error messages  
- **Feature implementation** following established architecture
- **Documentation improvements**
- **Refactoring** to improve code quality

#### What to Watch Out For
- **Architecture violations** - AI might not understand our engine abstraction or modal patterns
- **Dependency issues** - AI might suggest packages we don't want to add
- **Security concerns** - Especially around HTML rendering and WebEngine settings
- **Breaking changes** - AI might not understand backward compatibility needs

### When AI Suggests Code Changes

If you're working with GitHub Copilot or another AI assistant that suggests modifications:

1. **Read the suggestion carefully**
   - What is the AI trying to accomplish?
   - Does it align with our project goals?
   - Does it follow our architectural patterns?

2. **Understand the context**
   ```bash
   # Check which files the AI wants to modify
   # Review the current implementation first
   cat src/minimal_browser/[relevant_file].py
   
   # Check related architecture documentation
   grep -n "relevant_pattern" ARCHITECTURE.md
   ```

3. **Evaluate against project patterns**
   - **AI Actions**: Does it follow the Pydantic schema pattern?
   - **Web Engines**: Does it maintain the abstract interface?
   - **Modal UI**: Does it preserve vim-like behavior?
   - **Data URLs**: Does it use our established HTML rendering pattern?

4. **Test the changes**
   ```bash
   # Always compile-check first
   python -m py_compile src/minimal_browser/[modified_file].py
   
   # Then test functionality
   python -m minimal_browser  # or uv run if available
   ```

### Common AI Modification Scenarios

#### Scenario 1: "Add a new AI action type"
```python
# AI might suggest adding to src/minimal_browser/ai/schemas.py
class NewAction(BaseModel):
    action_type: Literal["new_feature"] = "new_feature"
    data: str
```

**Validation checklist:**
- [ ] Does it follow the existing `BaseModel` pattern?
- [ ] Is it added to the `AIAction` Union type?
- [ ] Is there a corresponding parser in `ResponseProcessor`?
- [ ] Is there a handler in the main browser class?

#### Scenario 2: "Improve error handling"
AI might suggest comprehensive try-catch blocks or error logging.

**Validation checklist:**
- [ ] Does it maintain user experience (notifications vs crashes)?
- [ ] Does it log appropriately without being too verbose?
- [ ] Does it preserve the modal interface during errors?

#### Scenario 3: "Add new keybinding"
AI might suggest new vim-like shortcuts.

**Validation checklist:**
- [ ] Does it conflict with existing shortcuts?
- [ ] Is it mode-aware (different behavior in NORMAL vs COMMAND mode)?
- [ ] Is it documented in the help system?

### Merging AI Modifications

#### Option 1: Direct Integration (Small Changes)
For small, straightforward changes:

```bash
# Apply the suggested changes to your files
# Test thoroughly
uv run python -m minimal_browser

# Commit with descriptive message
git add .
git commit -m "feat: implement [specific functionality]

- [describe what was changed]
- [note any AI assistance used]"
```

#### Option 2: Feature Branch (Larger Changes)
For substantial modifications:

```bash
# Create a feature branch
git checkout -b feature/ai-suggested-improvement

# Apply and test changes
# ... make modifications ...

# Test thoroughly
uv run python -m minimal_browser

# Commit with clear messages
git add .
git commit -m "feat: [description of changes]"

# Push and create PR
git push origin feature/ai-suggested-improvement
```

#### Option 3: Incremental Integration (Complex Changes)
For complex AI suggestions:

1. **Break down the suggestion** into smaller, testable pieces
2. **Implement incrementally**, testing each piece
3. **Commit frequently** with clear messages
4. **Document any architectural implications**

## 🏗️ Development Workflow

### Code Style and Quality

```bash
# Format code (if ruff is available)
ruff format src/

# Type checking (if mypy is available)
mypy src/

# Basic syntax validation
uv run python -m py_compile src/minimal_browser/minimal_browser.py
```

### Testing Your Changes

The project now has a comprehensive testing infrastructure using pytest. See [TESTING.md](TESTING.md) for complete documentation.

**Quick testing workflow:**

1. **Run all tests**:
   ```bash
   pytest
   # or use the test runner
   python run_tests.py
   ```

2. **Run specific test suite**:
   ```bash
   pytest tests/unit/ai/  # AI module tests
   pytest tests/unit/rendering/  # Rendering tests
   ```

3. **Run with coverage**:
   ```bash
   pytest --cov=src/minimal_browser --cov-report=html
   ```

4. **Manual testing** (still important for UI/integration):
   - Smoke test the core functionality
   - Test modal navigation (vim-like keybindings)
   - Test AI integration (if you have an API key)
   - Test web engine functionality

For manual testing details, see below.

### Architecture Considerations

When making changes, keep these patterns in mind:

- **Engine Abstraction**: Maintain the `WebEngine` interface for cross-platform support
- **AI Action Pipeline**: Follow the Pydantic schema pattern for AI responses
- **Modal Interface**: Preserve vim-like keybinding conventions
- **Data URLs**: Use the established pattern for AI-generated HTML

See `ARCHITECTURE.md` for detailed architectural guidelines.

## 🔧 Troubleshooting

### Common Issues

#### "Module not found" errors
```bash
# Ensure dependencies are installed
uv sync

# Check Python version
python --version  # Should be 3.13+
```

#### Qt/WebEngine issues on Linux
```bash
# For Wayland users
export QT_QPA_PLATFORM=wayland

# For X11 fallback
export QT_QPA_PLATFORM=xcb

# For headless testing
export QT_QPA_PLATFORM=offscreen
```

#### AI functionality not working
```bash
# Check API key is set
echo $OPENROUTER_API_KEY

# Test with fallback model
# Modify src/minimal_browser/ai/models.py to use a known working model
```

#### Git/merge issues
```bash
# If you have uncommitted changes and need to pull
git stash
git pull
git stash pop

# If you get merge conflicts
git status  # shows conflicted files
# Edit files to resolve conflicts (look for <<<< markers)
git add [resolved_files]
git commit

# If you accidentally committed to wrong branch
git log --oneline -5  # find the commit hash
git checkout correct-branch
git cherry-pick [commit_hash]
```

#### Working with forks (external contributors)
```bash
# Keep your fork up to date
git remote add upstream https://github.com/matias-ceau/minimal_browser.git
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

### Getting Help

1. **Check existing documentation**:
   - `README.md` for basic setup
   - `ARCHITECTURE.md` for technical details  
   - `FEATURE_REQUESTS.md` for planned features

2. **Search existing issues** on GitHub

3. **Create a new issue** with:
   - Python version
   - Operating system
   - Steps to reproduce
   - Error messages/logs

## 📝 Commit Guidelines

### Commit Message Format

```
type: brief description

- Detailed point about what changed
- Another detail if needed
- Note any AI assistance used
```

### Commit Types

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

### Examples

```bash
git commit -m "feat: add configurable AI model fallbacks

- Allow users to specify preferred model order
- Implement graceful degradation when models fail
- Add configuration validation
- AI-assisted implementation with manual review"
```

## 🎯 Focus Areas for Contributors

### High Priority (P0)
- **Documentation improvements** (this file, README updates)
- **Bug fixes** for existing functionality
- **Test coverage expansion** (add more test cases to existing tests)

### Medium Priority (P1)
- **AI model configuration** improvements
- **Security enhancements** for HTML sanitization
- **Performance optimizations**

### Low Priority (P2)
- **New rendering templates**
- **Additional web engine implementations**
- **Advanced AI features**

See `FEATURE_REQUESTS.md` and `ROADMAP.md` for detailed feature planning.

## 🤝 Pull Request Process

1. **Fork the repository** (for external contributors)
2. **Create a feature branch** from `main`
3. **Make your changes** following the guidelines above
4. **Test thoroughly** using the manual testing process
5. **Write clear commit messages** with appropriate types
6. **Update documentation** if needed
7. **Submit a pull request** with:
   - Clear description of changes
   - Reference to any related issues
   - Notes on testing performed
   - Any AI assistance acknowledgment

### PR Review Criteria

- [ ] Code compiles without errors
- [ ] Manual testing shows no regressions
- [ ] Architecture patterns are followed
- [ ] Commit messages are clear and descriptive
- [ ] Documentation is updated if needed

## 📜 License

By contributing, you agree that your contributions will be licensed under the same terms as the project (license pending - confirm with maintainer).