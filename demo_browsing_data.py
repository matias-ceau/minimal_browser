#!/usr/bin/env python3
"""
Demo script for browsing data management module.

This script demonstrates the key features of the browsing data management module.
"""

import sys
import tempfile
from datetime import datetime, timedelta, UTC
from pathlib import Path

# Direct import to avoid Qt dependencies
import importlib.util

def import_module_direct(name: str, filepath: str):
    """Import module directly from file."""
    spec = importlib.util.spec_from_file_location(name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# Setup paths
src_dir = Path(__file__).parent / "src" / "minimal_browser"

# Import utils first
utils_module = import_module_direct(
    "minimal_browser.storage.utils", 
    str(src_dir / "storage" / "utils.py")
)
sys.modules["minimal_browser.storage.utils"] = utils_module

# Import browsing_data module
browsing_data = import_module_direct(
    "minimal_browser.storage.browsing_data",
    str(src_dir / "storage" / "browsing_data.py")
)

BrowsingDataManager = browsing_data.BrowsingDataManager
HistoryStore = browsing_data.HistoryStore
SessionManager = browsing_data.SessionManager
Session = browsing_data.Session
TabState = browsing_data.TabState


def demo_history_tracking():
    """Demonstrate history tracking features."""
    print("\n=== History Tracking Demo ===\n")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "history.db"
        history = HistoryStore(db_path)
        
        # Track some visits
        print("Adding history entries...")
        history.add("https://github.com", "GitHub")
        history.add("https://stackoverflow.com", "Stack Overflow")
        history.add("https://python.org", "Python.org")
        history.add("https://github.com", "GitHub")  # Visit again
        
        # Search history
        print("\nSearching for 'github':")
        results = history.search("github")
        for entry in results:
            print(f"  {entry.title}: {entry.url} (visited {entry.visit_count} time(s))")
        
        # Get recent history
        print("\nRecent history (all):")
        recent = history.get_recent()
        for entry in recent:
            print(f"  {entry.title}: {entry.url}")
        
        # Get statistics
        print("\nHistory statistics:")
        stats = history.get_stats()
        print(f"  Total entries: {stats['total_entries']}")
        print(f"  Unique URLs: {stats['unique_urls']}")


def demo_session_management():
    """Demonstrate session management features."""
    print("\n=== Session Management Demo ===\n")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        sessions_dir = Path(tmpdir) / "sessions"
        sessions = SessionManager(sessions_dir)
        
        # Create and save a work session
        print("Creating work session...")
        work_session = Session(
            name="work",
            tabs=[
                TabState(url="https://github.com", title="GitHub"),
                TabState(url="https://mail.google.com", title="Gmail"),
                TabState(url="https://calendar.google.com", title="Calendar"),
            ],
            active_tab_index=0
        )
        sessions.save_session(work_session)
        print(f"  Saved session with {len(work_session.tabs)} tabs")
        
        # Create and save a research session
        print("\nCreating research session...")
        research_session = Session(
            name="research",
            tabs=[
                TabState(url="https://arxiv.org", title="arXiv"),
                TabState(url="https://scholar.google.com", title="Google Scholar"),
            ],
            active_tab_index=1
        )
        sessions.save_session(research_session)
        
        # List all sessions
        print("\nAvailable sessions:")
        all_sessions = sessions.list_sessions()
        for session_name in all_sessions:
            print(f"  - {session_name}")
        
        # Load a session
        print("\nLoading 'work' session:")
        loaded = sessions.load_session("work")
        if loaded:
            for i, tab in enumerate(loaded.tabs):
                active = " (active)" if i == loaded.active_tab_index else ""
                print(f"  Tab {i}: {tab.title}{active}")


def demo_data_management():
    """Demonstrate integrated data management."""
    print("\n=== Integrated Data Management Demo ===\n")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        manager = BrowsingDataManager(
            history_db_path=config_dir / "history.db",
            sessions_dir=config_dir / "sessions"
        )
        
        # Track some browsing
        print("Tracking browsing activity...")
        manager.history.add("https://example.com", "Example Domain")
        manager.history.add("https://test.com", "Test Site")
        manager.history.add("https://demo.com", "Demo Site")
        
        # Save current session
        print("\nSaving current session...")
        current = Session(
            name="current",
            tabs=[
                TabState(url="https://example.com", title="Example"),
                TabState(url="https://test.com", title="Test"),
            ]
        )
        manager.sessions.save_session(current)
        
        # Export all data
        print("\nExporting browsing data...")
        export_dir = config_dir / "export"
        results = manager.export_data(export_dir)
        print(f"  History exported to: {results['history_exported']}")
        print(f"  Sessions exported: {results['sessions_exported']}")
        
        # Clear old history (keep last 30 days)
        print("\nClearing old history (demo: older than 30 days)...")
        thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
        results = manager.clear_all_data(
            clear_history=True,
            clear_cache=False,
            clear_cookies=False,
            history_older_than=thirty_days_ago
        )
        print(f"  Entries deleted: {results['history_deleted']}")


def main():
    """Run all demos."""
    print("=" * 60)
    print("Browsing Data Management Module Demo")
    print("=" * 60)
    
    demo_history_tracking()
    demo_session_management()
    demo_data_management()
    
    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
