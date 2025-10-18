# Smart Bookmarks Feature

## Overview

The Smart Bookmarks feature (FR-052) provides a powerful bookmarking system for the Minimal Browser with support for:
- 🔖 Bookmarking URLs, files, and code snippets
- 🏷️ Tag-based organization
- 🔍 Full-text search across titles, URLs, content, and tags
- 🎨 Beautiful HTML interface for viewing bookmarks
- 💾 JSON-based persistent storage

## Usage

### Command Reference

All bookmark commands start with `:bm` followed by a subcommand:

#### Add Bookmark
```vim
:bm add                  " Bookmark current page without tags
:bm add tag1,tag2        " Bookmark current page with tags
```

#### View Bookmarks
```vim
:bm list                 " Show all bookmarks in a styled HTML view
:bm                      " Alias for :bm list
```

#### Search Bookmarks
```vim
:bm search python        " Search for bookmarks containing "python"
:bm search docs          " Search across title, URL, content, and tags
```

#### Manage Bookmarks
```vim
:bm del <id>            " Delete bookmark by ID (shown in bookmark view)
:bm tags                " Show all unique tags across bookmarks
```

### Workflow Example

1. **Navigate to a page you want to bookmark**
   ```vim
   o https://docs.python.org
   ```

2. **Bookmark the page with relevant tags**
   ```vim
   :bm add python,documentation,reference
   ```

3. **View your bookmarks**
   ```vim
   :bm list
   ```

4. **Search for bookmarks later**
   ```vim
   :bm search python
   ```

## Features

### Bookmark Types

The system supports three types of bookmarks:

1. **URL Bookmarks** - Regular web pages
2. **Snippet Bookmarks** - Code snippets or text content
3. **File Bookmarks** - Local file references

### Search Capabilities

The search function matches across:
- Bookmark title (case-insensitive)
- URL or file path
- Content/snippet text
- Tags

### Tag System

- Tags are comma-separated during creation
- Tags enable categorization and filtering
- View all tags with `:bm tags`
- Search by specific tag with `:bm search #tagname`

### Storage

Bookmarks are stored in JSON format at:
```
~/.config/minimal_browser/bookmarks.json
```

Each bookmark includes:
- Unique ID
- Title
- URL/path
- Optional content snippet
- Tags
- Creation and update timestamps
- Type (url/snippet/file)

## UI Features

The bookmark list view (`:bm list`) provides:
- 📊 Statistics (total bookmarks, unique tags)
- 🎨 Color-coded bookmark types
- 🏷️ Visual tag display
- 🔍 Search result filtering
- 📅 Creation timestamps
- ⚡ Quick navigation by clicking bookmarks

## Architecture

### Files Added/Modified

```
src/minimal_browser/
├── storage/
│   └── bookmarks.py           # BookmarkStore and Bookmark models
├── templates/
│   └── bookmarks.html         # HTML template for bookmark view
├── ai/
│   └── schemas.py             # Added BookmarkAction
├── config/
│   └── default_config.py      # Added bookmarks_path config
├── minimal_browser.py         # Added bookmark commands
└── main.py                    # Initialize BookmarkStore

demo_bookmarks.py              # Demo script showing API usage
```

### Key Components

1. **Bookmark Model** (`storage/bookmarks.py`)
   - Pydantic model for type safety
   - Fields: id, title, url, content, tags, timestamps, type
   - `matches_query()` method for search

2. **BookmarkStore** (`storage/bookmarks.py`)
   - JSON-backed persistence
   - Methods: add, remove, get, list_all, search, search_by_tag, get_all_tags
   - Automatic timestamp management

3. **Commands** (`minimal_browser.py`)
   - `execute_bookmark_command()` - Command dispatcher
   - `show_bookmarks()` - Render bookmarks HTML

4. **Template** (`templates/bookmarks.html`)
   - Jinja2 template with styled cards
   - Responsive grid layout
   - Interactive elements

## Testing

Run the demo script to test functionality:

```bash
python demo_bookmarks.py
```

This demonstrates:
- Creating bookmarks
- Searching by text and tags
- Listing all bookmarks
- Removing bookmarks
- Rendering HTML views

## Future Enhancements

Potential improvements (not yet implemented):
- 🧠 Embedding-based semantic search (using VectorStorage)
- 📤 Export bookmarks to Markdown/HTML
- 📥 Import bookmarks from browsers
- 🔄 Sync across devices
- 📸 Screenshot thumbnails
- 🤖 AI-powered tagging suggestions
- 📊 Analytics and usage statistics

## API Usage

For programmatic access:

```python
from minimal_browser.storage.bookmarks import BookmarkStore, Bookmark

# Initialize
store = BookmarkStore("path/to/bookmarks.json")

# Create bookmark
bm = Bookmark(
    id="unique-id",
    title="My Bookmark",
    url="https://example.com",
    tags=["example", "test"],
    bookmark_type="url"
)
store.add(bm)

# Search
results = store.search("example")
for bm in results:
    print(f"{bm.title}: {bm.url}")

# Get all tags
tags = store.get_all_tags()
print(f"Tags: {tags}")
```

## Configuration

Bookmark storage path can be configured in `config.toml`:

```toml
[storage]
bookmarks_path = "/custom/path/bookmarks.json"
```

Default: `~/.config/minimal_browser/bookmarks.json`
