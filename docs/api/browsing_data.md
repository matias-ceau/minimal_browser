# Browsing Data Management API Documentation

## Overview

The `browsing_data.py` module provides comprehensive data persistence and management for the Minimal Browser. It implements history tracking, session management, cache management, and cookie storage with a clean, well-tested API.

## Architecture

The module is organized into four main components:

1. **History Management**: SQLite-backed storage for browsing history
2. **Session Management**: JSON-based session snapshots for tab state persistence
3. **Cache Management**: Interface for Qt WebEngine cache operations
4. **Cookie Management**: Interface for Qt WebEngine cookie operations

All components are integrated through the `BrowsingDataManager` facade class.

## Data Models

### HistoryEntry

Represents a single browsing history entry.

```python
from minimal_browser.storage.browsing_data import HistoryEntry

entry = HistoryEntry(
    url="https://example.com",
    title="Example Domain",
    visit_time=datetime.utcnow(),  # defaults to current time
    visit_count=1  # incremented on repeated visits
)
```

**Fields:**
- `url` (str): The visited URL
- `title` (str): Page title (defaults to empty string)
- `visit_time` (datetime): Timestamp of visit (auto-generated)
- `visit_count` (int): Number of times visited (defaults to 1)

### TabState

Represents the state of a single browser tab.

```python
from minimal_browser.storage.browsing_data import TabState

tab = TabState(
    url="https://example.com",
    title="Example Domain",
    scroll_position=0  # vertical scroll position in pixels
)
```

**Fields:**
- `url` (str): Current URL
- `title` (str): Page title (defaults to empty string)
- `scroll_position` (int): Vertical scroll position (defaults to 0)

### Session

Represents a browser session with multiple tabs.

```python
from minimal_browser.storage.browsing_data import Session, TabState

session = Session(
    name="work-session",
    tabs=[
        TabState(url="https://github.com", title="GitHub"),
        TabState(url="https://stackoverflow.com", title="Stack Overflow")
    ],
    active_tab_index=0,
    created_at=datetime.utcnow()  # auto-generated
)
```

**Fields:**
- `name` (str): Session identifier
- `tabs` (List[TabState]): List of tab states
- `active_tab_index` (int): Index of currently active tab
- `created_at` (datetime): Session creation timestamp (auto-generated)

## API Reference

### HistoryStore

SQLite-backed browser history storage.

**Key Features:**
- Automatic URL deduplication (30-minute window)
- Full-text search on URLs and titles
- Date range filtering
- JSON export
- Secure deletion with VACUUM

**Example Usage:**

```python
from minimal_browser.storage.browsing_data import HistoryStore
from pathlib import Path

history = HistoryStore(Path.home() / ".config/minimal_browser/history.db")

# Track visits
history.add("https://github.com", "GitHub")

# Search history
results = history.search("github", limit=10)

# Clear old history
from datetime import datetime, timedelta
week_ago = datetime.utcnow() - timedelta(days=7)
deleted = history.clear(older_than=week_ago)
```

### SessionManager

JSON-based browser session management.

**Key Features:**
- Named session profiles
- Tab state preservation
- Session restoration
- Automatic "last session" tracking

**Example Usage:**

```python
from minimal_browser.storage.browsing_data import SessionManager, Session, TabState
from pathlib import Path

sessions = SessionManager(Path.home() / ".config/minimal_browser/sessions")

# Create and save session
session = Session(
    name="work",
    tabs=[
        TabState(url="https://github.com", title="GitHub"),
        TabState(url="https://mail.google.com", title="Gmail")
    ]
)
sessions.save_session(session)

# Restore session
restored = sessions.load_session("work")
```

### BrowsingDataManager

Comprehensive browsing data management facade.

**Key Features:**
- Unified interface for all browsing data
- Bulk data clearing operations
- Data export functionality
- Component integration

**Example Usage:**

```python
from minimal_browser.storage.browsing_data import BrowsingDataManager
from pathlib import Path

config_dir = Path.home() / ".config/minimal_browser"
manager = BrowsingDataManager(
    history_db_path=config_dir / "history.db",
    sessions_dir=config_dir / "sessions"
)

# Track browsing
manager.history.add("https://example.com", "Example")

# Clear all data
results = manager.clear_all_data(
    clear_history=True,
    clear_cache=True,
    clear_cookies=True
)
```

## Integration with Configuration

The module integrates with the browser's configuration system via `StorageConfig`:

```python
from minimal_browser.config.default_config import StorageConfig

config = StorageConfig()
# config.history_db_path -> Path to history database
# config.sessions_dir -> Path to sessions directory
```

## Security and Privacy

- All data stored locally (no cloud sync by default)
- Secure deletion with SQLite VACUUM
- Granular control over data retention
- No tracking or telemetry

## Testing

Run comprehensive tests:

```bash
pytest tests/unit/storage/test_browsing_data.py -v
```

34 tests covering all functionality including:
- Data model validation
- SQLite operations
- Session management
- Cache and cookie interfaces

## Complete API Documentation

For detailed method signatures and examples, see the inline documentation in `src/minimal_browser/storage/browsing_data.py`.
