#!/usr/bin/env python3
"""
Example script demonstrating the Smart Bookmarks feature.
This script shows how to use the BookmarkStore API directly.
"""

import sys
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src" / "minimal_browser"))

from storage.bookmarks import BookmarkStore, Bookmark
from rendering.html import render_template

def demo_bookmarks():
    """Demonstrate bookmark functionality."""
    
    # Create a temporary bookmark store
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = Path(f.name)
    
    try:
        print("=" * 60)
        print("Smart Bookmarks Demo")
        print("=" * 60)
        
        # Initialize store
        store = BookmarkStore(temp_path)
        print(f"\n✓ Initialized bookmark store at: {temp_path}")
        
        # Add some sample bookmarks
        bookmarks_to_add = [
            Bookmark(
                id='python-docs',
                title='Python Documentation',
                url='https://docs.python.org',
                tags=['python', 'documentation', 'reference'],
                bookmark_type='url',
                content='Official Python 3 documentation'
            ),
            Bookmark(
                id='github',
                title='GitHub',
                url='https://github.com',
                tags=['development', 'git', 'code'],
                bookmark_type='url'
            ),
            Bookmark(
                id='code-snippet',
                title='Quick Sort Algorithm',
                url='file:///snippets/quicksort.py',
                tags=['python', 'algorithm', 'sorting'],
                bookmark_type='snippet',
                content='def quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    ...'
            ),
        ]
        
        print("\n📚 Adding bookmarks...")
        for bm in bookmarks_to_add:
            store.add(bm)
            print(f"  ✓ {bm.title} ({bm.bookmark_type})")
        
        # List all bookmarks
        print(f"\n📋 Total bookmarks: {len(store.list_all())}")
        
        # Search functionality
        print("\n🔍 Search results for 'python':")
        results = store.search('python')
        for bm in results:
            print(f"  • {bm.title} - {bm.url}")
        
        # Tag search
        print("\n🏷️  Bookmarks with tag 'python':")
        tag_results = store.search_by_tag('python')
        for bm in tag_results:
            print(f"  • {bm.title} (tags: {', '.join(bm.tags)})")
        
        # All tags
        all_tags = store.get_all_tags()
        print(f"\n🏷️  All unique tags ({len(all_tags)}):")
        print(f"  {', '.join(all_tags)}")
        
        # Get specific bookmark
        print("\n📖 Retrieve specific bookmark:")
        bm = store.get('github')
        if bm:
            print(f"  ID: {bm.id}")
            print(f"  Title: {bm.title}")
            print(f"  URL: {bm.url}")
            print(f"  Tags: {', '.join(bm.tags)}")
        
        # Remove a bookmark
        print("\n🗑️  Removing bookmark 'github'...")
        if store.remove('github'):
            print("  ✓ Bookmark removed")
            print(f"  Remaining: {len(store.list_all())} bookmarks")
        
        # Render HTML view
        print("\n🎨 Rendering HTML view...")
        html = render_template(
            'bookmarks.html',
            {
                'bookmarks': store.list_all(),
                'total_count': len(store.list_all()),
                'tag_count': len(store.get_all_tags()),
                'query': None
            }
        )
        print(f"  ✓ Generated HTML ({len(html)} characters)")
        
        print("\n" + "=" * 60)
        print("✅ Demo completed successfully!")
        print("=" * 60)
        
    finally:
        # Cleanup
        temp_path.unlink()
        print(f"\n🧹 Cleaned up temporary file")


if __name__ == '__main__':
    demo_bookmarks()
