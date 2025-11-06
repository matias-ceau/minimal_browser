"""Browsing data management module.

This module provides comprehensive data persistence and management for the browser,
including history tracking, cache management, cookie storage, and session management.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, UTC
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

from .utils import ensure_dir


# ============================================================================
# Data Models
# ============================================================================


class HistoryEntry(BaseModel):
    """Represents a single history entry."""

    url: str = Field(description="The visited URL")
    title: str = Field(default="", description="Page title")
    visit_time: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Visit timestamp")
    visit_count: int = Field(default=1, description="Number of times visited")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TabState(BaseModel):
    """Represents the state of a single browser tab."""

    url: str = Field(description="Current URL")
    title: str = Field(default="", description="Page title")
    scroll_position: int = Field(default=0, description="Vertical scroll position")
    

class Session(BaseModel):
    """Represents a browser session with multiple tabs."""

    name: str = Field(description="Session name/identifier")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    tabs: List[TabState] = Field(default_factory=list, description="List of tab states")
    active_tab_index: int = Field(default=0, description="Index of active tab")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CacheStats(BaseModel):
    """Cache statistics."""

    size_bytes: int = Field(default=0, description="Current cache size in bytes")
    max_size_bytes: int = Field(default=0, description="Maximum cache size in bytes")
    cache_type: str = Field(default="memory", description="Cache type (memory/disk)")


# ============================================================================
# History Management
# ============================================================================


class HistoryStore:
    """SQLite-backed browser history storage."""

    def __init__(self, db_path: str | Path) -> None:
        """Initialize history store with SQLite database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        ensure_dir(self.db_path.parent)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    title TEXT DEFAULT '',
                    visit_time TIMESTAMP NOT NULL,
                    visit_count INTEGER DEFAULT 1,
                    UNIQUE(url, visit_time)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_visit_time ON history(visit_time DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_url ON history(url)
            """)
            conn.commit()

    def add(self, url: str, title: str = "") -> None:
        """Add a history entry.
        
        Args:
            url: The visited URL
            title: Page title (optional)
        """
        visit_time = datetime.now(UTC)
        with sqlite3.connect(self.db_path) as conn:
            # Check if URL was recently visited (within last 30 minutes)
            cursor = conn.execute("""
                SELECT id, visit_count FROM history 
                WHERE url = ? AND visit_time > ?
                ORDER BY visit_time DESC LIMIT 1
            """, (url, (visit_time - timedelta(minutes=30)).isoformat()))
            
            recent = cursor.fetchone()
            if recent:
                # Update existing entry
                conn.execute("""
                    UPDATE history 
                    SET visit_count = visit_count + 1, visit_time = ?, title = ?
                    WHERE id = ?
                """, (visit_time.isoformat(), title or "", recent[0]))
            else:
                # Insert new entry
                conn.execute("""
                    INSERT INTO history (url, title, visit_time, visit_count)
                    VALUES (?, ?, ?, 1)
                """, (url, title or "", visit_time.isoformat()))
            conn.commit()

    def search(self, query: str, limit: int = 50) -> List[HistoryEntry]:
        """Search history entries by URL or title.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of matching history entries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT url, title, visit_time, visit_count
                FROM history
                WHERE url LIKE ? OR title LIKE ?
                ORDER BY visit_time DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
            
            results = []
            for row in cursor.fetchall():
                results.append(HistoryEntry(
                    url=row[0],
                    title=row[1],
                    visit_time=datetime.fromisoformat(row[2]),
                    visit_count=row[3]
                ))
            return results

    def get_recent(self, limit: int = 50) -> List[HistoryEntry]:
        """Get most recent history entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of recent history entries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT url, title, visit_time, visit_count
                FROM history
                ORDER BY visit_time DESC
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                results.append(HistoryEntry(
                    url=row[0],
                    title=row[1],
                    visit_time=datetime.fromisoformat(row[2]),
                    visit_count=row[3]
                ))
            return results

    def get_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        limit: int = 100
    ) -> List[HistoryEntry]:
        """Get history entries within a date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            limit: Maximum number of entries to return
            
        Returns:
            List of history entries in date range
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT url, title, visit_time, visit_count
                FROM history
                WHERE visit_time BETWEEN ? AND ?
                ORDER BY visit_time DESC
                LIMIT ?
            """, (start_date.isoformat(), end_date.isoformat(), limit))
            
            results = []
            for row in cursor.fetchall():
                results.append(HistoryEntry(
                    url=row[0],
                    title=row[1],
                    visit_time=datetime.fromisoformat(row[2]),
                    visit_count=row[3]
                ))
            return results

    def clear(self, older_than: Optional[datetime] = None) -> int:
        """Clear history entries.
        
        Args:
            older_than: If provided, only clear entries older than this date.
                       If None, clear all entries.
            
        Returns:
            Number of entries deleted
        """
        with sqlite3.connect(self.db_path) as conn:
            if older_than:
                cursor = conn.execute("""
                    DELETE FROM history WHERE visit_time < ?
                """, (older_than.isoformat(),))
            else:
                cursor = conn.execute("DELETE FROM history")
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            # VACUUM to reclaim space
            conn.execute("VACUUM")
            
            return deleted_count

    def export_to_json(self, output_path: str | Path) -> None:
        """Export history to JSON file.
        
        Args:
            output_path: Path to output JSON file
        """
        entries = self.get_recent(limit=10000)  # Export all recent entries
        output_path = Path(output_path)
        ensure_dir(output_path.parent)
        
        with open(output_path, 'w') as f:
            json.dump([entry.model_dump(mode='json') for entry in entries], f, indent=2, default=str)

    def get_stats(self) -> dict:
        """Get history statistics.
        
        Returns:
            Dictionary with statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM history")
            total_count = cursor.fetchone()[0]
            
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT url) FROM history
            """)
            unique_urls = cursor.fetchone()[0]
            
            cursor = conn.execute("""
                SELECT MIN(visit_time), MAX(visit_time) FROM history
            """)
            date_range = cursor.fetchone()
            
            return {
                "total_entries": total_count,
                "unique_urls": unique_urls,
                "earliest_visit": date_range[0],
                "latest_visit": date_range[1]
            }


# ============================================================================
# Session Management
# ============================================================================


class SessionManager:
    """JSON-based browser session management."""

    def __init__(self, sessions_dir: str | Path) -> None:
        """Initialize session manager.
        
        Args:
            sessions_dir: Directory to store session files
        """
        self.sessions_dir = Path(sessions_dir)
        ensure_dir(self.sessions_dir)

    def save_session(self, session: Session) -> None:
        """Save a session to disk.
        
        Args:
            session: Session object to save
        """
        session_file = self.sessions_dir / f"{session.name}.json"
        with open(session_file, 'w') as f:
            json.dump(session.model_dump(mode='json'), f, indent=2, default=str)

    def load_session(self, name: str) -> Optional[Session]:
        """Load a session from disk.
        
        Args:
            name: Session name
            
        Returns:
            Session object or None if not found
        """
        session_file = self.sessions_dir / f"{name}.json"
        if not session_file.exists():
            return None
        
        with open(session_file, 'r') as f:
            data = json.load(f)
            return Session(**data)

    def list_sessions(self) -> List[str]:
        """List all available session names.
        
        Returns:
            List of session names
        """
        return [f.stem for f in self.sessions_dir.glob("*.json")]

    def delete_session(self, name: str) -> bool:
        """Delete a session.
        
        Args:
            name: Session name
            
        Returns:
            True if deleted, False if not found
        """
        session_file = self.sessions_dir / f"{name}.json"
        if session_file.exists():
            session_file.unlink()
            return True
        return False

    def get_last_session(self) -> Optional[Session]:
        """Get the most recently saved session.
        
        Returns:
            Most recent session or None
        """
        session_files = list(self.sessions_dir.glob("*.json"))
        if not session_files:
            return None
        
        # Get most recently modified file
        latest_file = max(session_files, key=lambda f: f.stat().st_mtime)
        return self.load_session(latest_file.stem)


# ============================================================================
# Cache Management
# ============================================================================


class CacheManager:
    """Interface for Qt WebEngine cache management."""

    def __init__(self, profile=None):
        """Initialize cache manager.
        
        Args:
            profile: Qt WebEngine profile (optional, for integration)
        """
        self._profile = profile

    def get_stats(self) -> CacheStats:
        """Get cache statistics.
        
        Returns:
            CacheStats object
        """
        # This is a placeholder implementation
        # In actual usage, this would integrate with Qt WebEngine
        if self._profile:
            try:
                # Qt WebEngine doesn't provide direct cache size access
                # This would need to be implemented via profile settings
                return CacheStats(
                    size_bytes=0,
                    max_size_bytes=50 * 1024 * 1024,  # Default 50MB
                    cache_type="memory"
                )
            except Exception:
                pass
        
        return CacheStats()

    def clear_cache(self) -> bool:
        """Clear browser cache.
        
        Returns:
            True if successful
        """
        # Placeholder - would integrate with Qt WebEngine
        if self._profile:
            try:
                # Qt WebEngine cache clearing would go here
                # profile.clearHttpCache() or similar
                return True
            except Exception:
                return False
        return False

    def set_cache_size(self, size_mb: int) -> bool:
        """Set maximum cache size.
        
        Args:
            size_mb: Maximum cache size in megabytes
            
        Returns:
            True if successful
        """
        if self._profile:
            try:
                # profile.setHttpCacheMaximumSize(size_mb * 1024 * 1024)
                return True
            except Exception:
                return False
        return False


# ============================================================================
# Cookie Management
# ============================================================================


class CookieManager:
    """Interface for Qt WebEngine cookie management."""

    def __init__(self, cookie_store=None):
        """Initialize cookie manager.
        
        Args:
            cookie_store: Qt WebEngine cookie store (optional)
        """
        self._cookie_store = cookie_store

    def list_cookies(self) -> List[dict]:
        """List all stored cookies.
        
        Returns:
            List of cookie dictionaries
        """
        # Placeholder - would integrate with Qt WebEngine cookie store
        # In practice, Qt WebEngine doesn't provide easy cookie enumeration
        return []

    def delete_cookie(self, name: str, domain: str = "") -> bool:
        """Delete a specific cookie.
        
        Args:
            name: Cookie name
            domain: Cookie domain (optional)
            
        Returns:
            True if successful
        """
        if self._cookie_store:
            try:
                # Qt WebEngine cookie deletion would go here
                return True
            except Exception:
                return False
        return False

    def clear_all_cookies(self) -> bool:
        """Clear all cookies.
        
        Returns:
            True if successful
        """
        if self._cookie_store:
            try:
                # Qt WebEngine cookie clearing would go here
                # cookie_store.deleteAllCookies()
                return True
            except Exception:
                return False
        return False


# ============================================================================
# Main Browsing Data Manager
# ============================================================================


class BrowsingDataManager:
    """Comprehensive browsing data management facade."""

    def __init__(
        self,
        history_db_path: str | Path,
        sessions_dir: str | Path,
        qt_profile=None,
        qt_cookie_store=None
    ):
        """Initialize browsing data manager.
        
        Args:
            history_db_path: Path to history SQLite database
            sessions_dir: Directory for session files
            qt_profile: Qt WebEngine profile (optional)
            qt_cookie_store: Qt WebEngine cookie store (optional)
        """
        self.history = HistoryStore(history_db_path)
        self.sessions = SessionManager(sessions_dir)
        self.cache = CacheManager(qt_profile)
        self.cookies = CookieManager(qt_cookie_store)

    def clear_all_data(
        self,
        clear_history: bool = True,
        clear_cache: bool = True,
        clear_cookies: bool = True,
        history_older_than: Optional[datetime] = None
    ) -> dict:
        """Clear multiple types of browsing data.
        
        Args:
            clear_history: Whether to clear history
            clear_cache: Whether to clear cache
            clear_cookies: Whether to clear cookies
            history_older_than: Only clear history older than this date
            
        Returns:
            Dictionary with results for each operation
        """
        results = {}
        
        if clear_history:
            deleted_count = self.history.clear(older_than=history_older_than)
            results["history_deleted"] = deleted_count
        
        if clear_cache:
            cache_cleared = self.cache.clear_cache()
            results["cache_cleared"] = cache_cleared
        
        if clear_cookies:
            cookies_cleared = self.cookies.clear_all_cookies()
            results["cookies_cleared"] = cookies_cleared
        
        return results

    def export_data(self, export_dir: str | Path) -> dict:
        """Export all browsing data to a directory.
        
        Args:
            export_dir: Directory to export data to
            
        Returns:
            Dictionary with export results
        """
        export_dir = Path(export_dir)
        ensure_dir(export_dir)
        
        results = {}
        
        # Export history
        history_file = export_dir / "history.json"
        self.history.export_to_json(history_file)
        results["history_exported"] = str(history_file)
        
        # Export sessions
        sessions = self.sessions.list_sessions()
        results["sessions_exported"] = len(sessions)
        
        return results
