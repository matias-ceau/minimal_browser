# File Browser with Embeddings - Feature Documentation

## Overview
FR-053 implements a local file browser with semantic search capabilities using ChromaDB embeddings.

## Features

### 1. File Browser Interface
- Browse local directories with a modern, vim-style UI
- Visual file type indicators (folders, Python files, images, etc.)
- File size and MIME type display
- Click-to-navigate for directories
- Parent directory and home shortcuts

### 2. File Indexing
- Automatic text file detection (text/*, JSON, XML)
- ChromaDB-based embedding storage
- Configurable indexing limits (default 100 files)
- Recursive directory indexing
- Progress notifications

### 3. Semantic Search
- Query indexed files by semantic similarity
- Returns top N matches (default 10)
- Results display with file paths and types
- Handles search failures gracefully

## Commands

### `:files [path]` or `:fb [path]`
Browse local file system starting from the specified path.
- **Without path**: Opens home directory
- **With path**: Opens specified directory (supports ~ expansion)
- **Examples**:
  - `:files` - Browse home directory
  - `:files ~/Documents` - Browse Documents folder
  - `:fb /tmp` - Browse /tmp directory

### `:index [path]`
Index files in the specified directory with embeddings.
- **Without path**: Indexes home directory
- **With path**: Indexes specified directory
- **Behavior**:
  - Recursive indexing (up to 100 files by default)
  - Only indexes text-based files
  - Shows progress and completion notifications
- **Examples**:
  - `:index` - Index home directory
  - `:index ~/projects` - Index projects folder

### `:search-files <query>`
Search indexed files using semantic similarity.
- **Requires**: Files must be indexed first using `:index`
- **Returns**: Top 10 matching files
- **Examples**:
  - `:search-files python function definition` - Find Python files with functions
  - `:search-files configuration settings` - Find config files
  - `:search-files error handling` - Find files with error handling code

## Technical Architecture

### Module Structure
```
src/minimal_browser/
├── storage/
│   ├── file_browser.py       # Core file browser logic
│   │   ├── FileEntry         # File/directory metadata
│   │   ├── FileBrowser       # Directory navigation
│   │   └── FileIndexer       # Embedding indexer
│   └── __init__.py
├── templates/
│   └── file_browser.html     # File browser UI template
├── rendering/
│   └── html.py               # Jinja2 rendering + filesizeformat filter
└── minimal_browser.py        # Integration into VimBrowser
```

### Key Classes

#### FileEntry
Represents a file or directory entry with metadata.
- Properties: `name`, `path`, `is_dir`, `is_file`, `size`, `mime_type`
- Method: `to_dict()` - Convert to dictionary for template rendering

#### FileBrowser
Provides file system navigation capabilities.
- `list_directory(path)` - List files and directories
- `navigate_to(path)` - Change current directory
- `go_up()` - Navigate to parent directory
- `read_file(path, max_size)` - Read text file content

#### FileIndexer
Manages file indexing with ChromaDB embeddings.
- `index_file(path, content)` - Index a single file
- `index_directory(directory, recursive, max_files)` - Index directory
- `search_files(query, n_results)` - Semantic search

### Template Context
The file browser template receives:
```python
{
    "current_path": str,      # Current directory path
    "parent_path": str|None,  # Parent directory (None if at root)
    "home_path": str,         # User home directory
    "entries": [              # List of file entries
        {
            "name": str,
            "path": str,
            "is_dir": bool,
            "is_file": bool,
            "size": int,
            "mime_type": str,
        }
    ]
}
```

## UI Design

### Color Scheme
- Background: Blue gradient (#1e3c72 to #2a5298)
- Directories: Green (#81c784)
- Files: Light gray (#e0e0e0)
- Hover: Slight translation and brightness increase
- Monospace font: Monaco, Menlo, Ubuntu Mono

### File Icons
- 📁 Directories
- 📄 Text files
- 🖼️ Images
- 🎬 Videos
- 🎵 Audio
- 🐍 Python files
- 📜 JavaScript files
- 🌐 HTML files
- 📋 Other files

## Integration with AI

The file browser is designed to enable AI-assisted development workflows:

1. **Browse project files**: `:files ~/my-project`
2. **Index codebase**: `:index ~/my-project`
3. **Search semantically**: `:search-files database connection logic`
4. **Future**: AI can reference indexed files in responses (planned)

## Dependencies

- **chromadb**: Required for embedding storage and search
- **PySide6**: Required for Qt WebEngine rendering
- **jinja2**: Required for template rendering

All dependencies are already specified in `pyproject.toml`.

## Error Handling

The implementation includes robust error handling:
- **Permission errors**: Skipped silently during directory listing
- **Large files**: Files > 1MB skipped during indexing
- **Non-text files**: Binary files excluded from indexing
- **Missing directories**: User-friendly error notifications
- **Search failures**: Graceful fallback with error messages

## Future Enhancements

Potential improvements from FEATURE_REQUESTS.md:
- **FR-052**: Smart Bookmark Vault integration
- **AI Context**: Surface indexed file content in AI prompts
- **File Preview**: Display file contents in browser
- **Advanced Filters**: Filter by file type, size, date
- **Export**: Export file lists and search results

## Testing

Basic testing checklist:
1. ✅ Syntax validation with `python -m py_compile`
2. ✅ Module imports correctly
3. ✅ Template renders without errors
4. ⚠️ Manual testing required (requires PySide6 + chromadb)
5. ⚠️ UI validation with screenshots (requires display)

## Notes

- The file browser uses `file://` URLs for navigation
- Hidden files (starting with `.`) are automatically filtered
- Directory entries are sorted with directories first
- The implementation follows existing patterns in the codebase
- Commands are added to the vim-style help system (`:help`)
