"""File browser with embedding support for code and assets."""

from __future__ import annotations

import os
import mimetypes
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import chromadb  # type: ignore[import-untyped]
except ImportError as exc:  # pragma: no cover - optional dependency guard
    raise ImportError(
        "chromadb is required for file browser embeddings; install minimal-browser with the 'storage' extras."
    ) from exc


class FileEntry:
    """Represents a file or directory entry."""

    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self.is_dir = path.is_dir()
        self.is_file = path.is_file()
        
        if self.is_file:
            try:
                self.size = path.stat().st_size
                self.mime_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
            except (OSError, PermissionError):
                self.size = 0
                self.mime_type = "unknown"
        else:
            self.size = 0
            self.mime_type = "directory"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for rendering."""
        return {
            "name": self.name,
            "path": str(self.path),
            "is_dir": self.is_dir,
            "is_file": self.is_file,
            "size": self.size,
            "mime_type": self.mime_type,
        }


class FileBrowser:
    """Browse local file system with embedding indexing."""

    def __init__(self, root_path: Optional[Path] = None):
        """Initialize file browser.
        
        Args:
            root_path: Starting directory, defaults to home directory
        """
        self.root_path = root_path or Path.home()
        self.current_path = self.root_path

    def list_directory(self, path: Optional[Path] = None) -> List[FileEntry]:
        """List files and directories in the given path.
        
        Args:
            path: Directory to list, defaults to current_path
            
        Returns:
            List of FileEntry objects
        """
        target_path = path or self.current_path
        
        try:
            entries = []
            for item in sorted(target_path.iterdir()):
                # Skip hidden files
                if item.name.startswith('.'):
                    continue
                try:
                    entries.append(FileEntry(item))
                except (OSError, PermissionError):
                    # Skip files we can't access
                    continue
            
            # Sort: directories first, then files
            entries.sort(key=lambda e: (not e.is_dir, e.name.lower()))
            return entries
        except (OSError, PermissionError):
            return []

    def navigate_to(self, path: str) -> bool:
        """Navigate to a new directory.
        
        Args:
            path: Path to navigate to (can be relative or absolute)
            
        Returns:
            True if navigation succeeded, False otherwise
        """
        target = Path(path).expanduser().resolve()
        
        if target.is_dir():
            self.current_path = target
            return True
        return False

    def go_up(self) -> bool:
        """Navigate to parent directory.
        
        Returns:
            True if navigation succeeded, False if already at root
        """
        parent = self.current_path.parent
        if parent != self.current_path:
            self.current_path = parent
            return True
        return False

    def read_file(self, path: Path, max_size: int = 1024 * 1024) -> Optional[str]:
        """Read file content if it's a text file.
        
        Args:
            path: Path to file
            max_size: Maximum file size to read (default 1MB)
            
        Returns:
            File content as string, or None if not readable
        """
        try:
            if path.stat().st_size > max_size:
                return None
                
            # Try to read as text
            return path.read_text(encoding='utf-8', errors='ignore')
        except (OSError, PermissionError, UnicodeDecodeError):
            return None


class FileIndexer:
    """Index files with embeddings for semantic search."""

    def __init__(self, collection_name: str = "file_browser"):
        """Initialize file indexer with ChromaDB.
        
        Args:
            collection_name: Name of the ChromaDB collection
        """
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def index_file(self, path: Path, content: str) -> None:
        """Index a file's content with embeddings.
        
        Args:
            path: Path to the file
            content: File content to index
        """
        metadata = {
            "path": str(path),
            "name": path.name,
            "type": mimetypes.guess_type(str(path))[0] or "unknown",
        }
        
        # Create a unique ID for the document
        doc_id = str(path)
        
        try:
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id]
            )
        except Exception as e:
            print(f"Failed to index {path}: {e}")

    def index_directory(self, directory: Path, recursive: bool = True, max_files: int = 100) -> int:
        """Index all text files in a directory.
        
        Args:
            directory: Directory to index
            recursive: Whether to recurse into subdirectories
            max_files: Maximum number of files to index
            
        Returns:
            Number of files indexed
        """
        browser = FileBrowser(directory)
        indexed_count = 0
        
        def _index_dir(path: Path) -> None:
            nonlocal indexed_count
            
            if indexed_count >= max_files:
                return
                
            entries = browser.list_directory(path)
            for entry in entries:
                if indexed_count >= max_files:
                    return
                    
                if entry.is_file:
                    # Only index text-like files
                    if entry.mime_type and entry.mime_type.startswith(('text/', 'application/json', 'application/xml')):
                        content = browser.read_file(entry.path)
                        if content:
                            self.index_file(entry.path, content)
                            indexed_count += 1
                elif entry.is_dir and recursive:
                    _index_dir(entry.path)
        
        _index_dir(directory)
        return indexed_count

    def search_files(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search indexed files by semantic similarity.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of matching files with metadata
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            matches = []
            if results.get('metadatas') and results['metadatas'][0]:
                for metadata in results['metadatas'][0]:
                    matches.append(metadata)
            
            return matches
        except Exception as e:
            print(f"Search failed: {e}")
            return []
