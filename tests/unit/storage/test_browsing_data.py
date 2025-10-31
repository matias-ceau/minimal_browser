"""Unit tests for browsing data management."""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Direct module import to avoid loading __init__.py with PySide6 dependency
import importlib.util


def import_module_direct(name: str, filepath: str):
    """Import module directly from file without loading parent __init__.py."""
    spec = importlib.util.spec_from_file_location(name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


src_dir = Path(__file__).parent.parent.parent.parent / "src" / "minimal_browser"

# Import utils module first
utils_module = import_module_direct(
    "minimal_browser.storage.utils", str(src_dir / "storage" / "utils.py")
)
sys.modules["minimal_browser.storage.utils"] = utils_module

# Import browsing_data module
browsing_data_module = import_module_direct(
    "minimal_browser.storage.browsing_data", 
    str(src_dir / "storage" / "browsing_data.py")
)

# Import classes
HistoryEntry = browsing_data_module.HistoryEntry
HistoryStore = browsing_data_module.HistoryStore
TabState = browsing_data_module.TabState
Session = browsing_data_module.Session
SessionManager = browsing_data_module.SessionManager
CacheManager = browsing_data_module.CacheManager
CookieManager = browsing_data_module.CookieManager
BrowsingDataManager = browsing_data_module.BrowsingDataManager
CacheStats = browsing_data_module.CacheStats


class TestHistoryEntry:
    """Test HistoryEntry model."""

    def test_create_history_entry(self):
        """Test creating a history entry."""
        entry = HistoryEntry(url="https://example.com", title="Example Site")
        assert entry.url == "https://example.com"
        assert entry.title == "Example Site"
        assert entry.visit_count == 1
        assert isinstance(entry.visit_time, datetime)

    def test_history_entry_defaults(self):
        """Test history entry default values."""
        entry = HistoryEntry(url="https://example.com")
        assert entry.title == ""
        assert entry.visit_count == 1


class TestHistoryStore:
    """Test HistoryStore class."""

    def test_create_history_store(self):
        """Test creating a history store."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "history.db"
            store = HistoryStore(db_path)
            assert store.db_path == db_path
            assert db_path.exists()

    def test_add_history_entry(self):
        """Test adding a history entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "history.db"
            store = HistoryStore(db_path)
            
            store.add("https://example.com", "Example Site")
            
            recent = store.get_recent(limit=1)
            assert len(recent) == 1
            assert recent[0].url == "https://example.com"
            assert recent[0].title == "Example Site"

    def test_add_duplicate_url_updates_count(self):
        """Test adding duplicate URL updates visit count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "history.db"
            store = HistoryStore(db_path)
            
            # Add same URL twice in quick succession
            store.add("https://example.com", "Example")
            store.add("https://example.com", "Example")
            
            recent = store.get_recent(limit=10)
            # Should have 1 entry with visit_count = 2
            url_entries = [e for e in recent if e.url == "https://example.com"]
            assert len(url_entries) == 1
            assert url_entries[0].visit_count == 2

    def test_search_history(self):
        """Test searching history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "history.db"
            store = HistoryStore(db_path)
            
            store.add("https://example.com", "Example Site")
            store.add("https://test.com", "Test Site")
            store.add("https://demo.com", "Demo Site")
            
            results = store.search("example")
            assert len(results) == 1
            assert results[0].url == "https://example.com"
            
            results = store.search("Site")
            assert len(results) == 3

    def test_get_recent_history(self):
        """Test getting recent history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "history.db"
            store = HistoryStore(db_path)
            
            # Add multiple entries
            for i in range(5):
                store.add(f"https://example{i}.com", f"Site {i}")
            
            recent = store.get_recent(limit=3)
            assert len(recent) == 3
            # Most recent should be first
            assert recent[0].url == "https://example4.com"

    def test_get_by_date_range(self):
        """Test getting history by date range."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "history.db"
            store = HistoryStore(db_path)
            
            # Add entries
            store.add("https://example.com", "Example")
            
            # Query date range
            now = datetime.utcnow()
            yesterday = now - timedelta(days=1)
            tomorrow = now + timedelta(days=1)
            
            results = store.get_by_date_range(yesterday, tomorrow)
            assert len(results) >= 1
            assert results[0].url == "https://example.com"

    def test_clear_all_history(self):
        """Test clearing all history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "history.db"
            store = HistoryStore(db_path)
            
            # Add entries
            store.add("https://example.com", "Example")
            store.add("https://test.com", "Test")
            
            # Clear all
            deleted = store.clear()
            assert deleted == 2
            
            recent = store.get_recent()
            assert len(recent) == 0

    def test_clear_history_older_than(self):
        """Test clearing history older than a date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "history.db"
            store = HistoryStore(db_path)
            
            # Add an entry
            store.add("https://example.com", "Example")
            
            # Clear entries older than yesterday (should delete nothing)
            yesterday = datetime.utcnow() - timedelta(days=1)
            deleted = store.clear(older_than=yesterday)
            
            recent = store.get_recent()
            # Should still have entries since they're from today
            assert len(recent) == 1

    def test_export_to_json(self):
        """Test exporting history to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "history.db"
            store = HistoryStore(db_path)
            
            store.add("https://example.com", "Example")
            
            export_path = Path(tmpdir) / "export.json"
            store.export_to_json(export_path)
            
            assert export_path.exists()
            
            with open(export_path) as f:
                data = json.load(f)
                assert len(data) >= 1
                assert data[0]["url"] == "https://example.com"

    def test_get_stats(self):
        """Test getting history statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "history.db"
            store = HistoryStore(db_path)
            
            store.add("https://example.com", "Example")
            store.add("https://test.com", "Test")
            store.add("https://example.com", "Example")  # Duplicate
            
            stats = store.get_stats()
            assert stats["total_entries"] >= 2
            assert stats["unique_urls"] >= 2


class TestTabState:
    """Test TabState model."""

    def test_create_tab_state(self):
        """Test creating a tab state."""
        tab = TabState(url="https://example.com", title="Example")
        assert tab.url == "https://example.com"
        assert tab.title == "Example"
        assert tab.scroll_position == 0

    def test_tab_state_with_scroll(self):
        """Test tab state with scroll position."""
        tab = TabState(url="https://example.com", scroll_position=500)
        assert tab.scroll_position == 500


class TestSession:
    """Test Session model."""

    def test_create_session(self):
        """Test creating a session."""
        session = Session(name="test-session")
        assert session.name == "test-session"
        assert len(session.tabs) == 0
        assert session.active_tab_index == 0

    def test_session_with_tabs(self):
        """Test session with multiple tabs."""
        tabs = [
            TabState(url="https://example.com", title="Example"),
            TabState(url="https://test.com", title="Test")
        ]
        session = Session(name="test-session", tabs=tabs, active_tab_index=1)
        assert len(session.tabs) == 2
        assert session.active_tab_index == 1


class TestSessionManager:
    """Test SessionManager class."""

    def test_create_session_manager(self):
        """Test creating a session manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir)
            assert manager.sessions_dir.exists()

    def test_save_and_load_session(self):
        """Test saving and loading a session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir)
            
            # Create and save session
            tabs = [TabState(url="https://example.com", title="Example")]
            session = Session(name="test", tabs=tabs)
            manager.save_session(session)
            
            # Load session
            loaded = manager.load_session("test")
            assert loaded is not None
            assert loaded.name == "test"
            assert len(loaded.tabs) == 1
            assert loaded.tabs[0].url == "https://example.com"

    def test_load_nonexistent_session(self):
        """Test loading a session that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir)
            
            loaded = manager.load_session("nonexistent")
            assert loaded is None

    def test_list_sessions(self):
        """Test listing sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir)
            
            # Save multiple sessions
            for i in range(3):
                session = Session(name=f"session{i}")
                manager.save_session(session)
            
            sessions = manager.list_sessions()
            assert len(sessions) == 3
            assert "session0" in sessions
            assert "session1" in sessions
            assert "session2" in sessions

    def test_delete_session(self):
        """Test deleting a session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir)
            
            # Save session
            session = Session(name="test")
            manager.save_session(session)
            
            # Delete session
            result = manager.delete_session("test")
            assert result is True
            
            # Verify deleted
            loaded = manager.load_session("test")
            assert loaded is None

    def test_delete_nonexistent_session(self):
        """Test deleting a nonexistent session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir)
            
            result = manager.delete_session("nonexistent")
            assert result is False

    def test_get_last_session(self):
        """Test getting the most recent session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir)
            
            # Save multiple sessions
            session1 = Session(name="session1")
            manager.save_session(session1)
            
            import time
            time.sleep(0.01)  # Ensure different timestamps
            
            session2 = Session(name="session2")
            manager.save_session(session2)
            
            last = manager.get_last_session()
            assert last is not None
            assert last.name == "session2"


class TestCacheManager:
    """Test CacheManager class."""

    def test_create_cache_manager(self):
        """Test creating a cache manager."""
        manager = CacheManager()
        assert manager is not None

    def test_get_cache_stats(self):
        """Test getting cache stats."""
        manager = CacheManager()
        stats = manager.get_stats()
        assert isinstance(stats, CacheStats)
        assert stats.size_bytes >= 0

    def test_clear_cache(self):
        """Test clearing cache."""
        manager = CacheManager()
        result = manager.clear_cache()
        assert isinstance(result, bool)

    def test_set_cache_size(self):
        """Test setting cache size."""
        manager = CacheManager()
        result = manager.set_cache_size(100)
        assert isinstance(result, bool)


class TestCookieManager:
    """Test CookieManager class."""

    def test_create_cookie_manager(self):
        """Test creating a cookie manager."""
        manager = CookieManager()
        assert manager is not None

    def test_list_cookies(self):
        """Test listing cookies."""
        manager = CookieManager()
        cookies = manager.list_cookies()
        assert isinstance(cookies, list)

    def test_delete_cookie(self):
        """Test deleting a cookie."""
        manager = CookieManager()
        result = manager.delete_cookie("test_cookie")
        assert isinstance(result, bool)

    def test_clear_all_cookies(self):
        """Test clearing all cookies."""
        manager = CookieManager()
        result = manager.clear_all_cookies()
        assert isinstance(result, bool)


class TestBrowsingDataManager:
    """Test BrowsingDataManager class."""

    def test_create_browsing_data_manager(self):
        """Test creating a browsing data manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_db = Path(tmpdir) / "history.db"
            sessions_dir = Path(tmpdir) / "sessions"
            
            manager = BrowsingDataManager(
                history_db_path=history_db,
                sessions_dir=sessions_dir
            )
            
            assert manager.history is not None
            assert manager.sessions is not None
            assert manager.cache is not None
            assert manager.cookies is not None

    def test_clear_all_data(self):
        """Test clearing all browsing data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_db = Path(tmpdir) / "history.db"
            sessions_dir = Path(tmpdir) / "sessions"
            
            manager = BrowsingDataManager(
                history_db_path=history_db,
                sessions_dir=sessions_dir
            )
            
            # Add some history
            manager.history.add("https://example.com", "Example")
            
            # Clear all data
            results = manager.clear_all_data()
            
            assert "history_deleted" in results
            assert results["history_deleted"] >= 1

    def test_export_data(self):
        """Test exporting browsing data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_db = Path(tmpdir) / "history.db"
            sessions_dir = Path(tmpdir) / "sessions"
            export_dir = Path(tmpdir) / "export"
            
            manager = BrowsingDataManager(
                history_db_path=history_db,
                sessions_dir=sessions_dir
            )
            
            # Add some data
            manager.history.add("https://example.com", "Example")
            
            # Export data
            results = manager.export_data(export_dir)
            
            assert "history_exported" in results
            assert Path(results["history_exported"]).exists()
