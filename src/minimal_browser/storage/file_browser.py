"""File browser with embedding support for code and assets."""

from __future__ import annotations

import json
import mimetypes
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    import faiss
    import numpy as np
    from openai import OpenAI

try:
    import faiss  # type: ignore[import-untyped]
    import numpy as np  # noqa: F401

    FAISS_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency guard
    FAISS_AVAILABLE = False

try:
    from openai import OpenAI  # noqa: F401

    OPENAI_AVAILABLE = True
except ImportError:  # pragma: no cover
    OPENAI_AVAILABLE = False


EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536


def _get_embedding(text: str, client: Optional[OpenAI] = None) -> List[float]:
    """Generate embedding for text using OpenAI API.

    Args:
        text: Text to embed
        client: Optional OpenAI client instance

    Returns:
        Embedding vector as list of floats
    """
    if not OPENAI_AVAILABLE:
        raise ImportError(
            "openai is required for embeddings; install with 'uv sync --extra storage'"
        )

    if client is None:
        client = OpenAI()

    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return list(response.data[0].embedding)


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
                self.mime_type = (
                    mimetypes.guess_type(str(path))[0] or "application/octet-stream"
                )
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
                if item.name.startswith("."):
                    continue
                try:
                    entries.append(FileEntry(item))
                except (OSError, PermissionError):
                    continue

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

            return path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, PermissionError, UnicodeDecodeError):
            return None


class FileIndexer:
    """Index files with embeddings for semantic search using FAISS and OpenAI."""

    def __init__(
        self,
        collection_name: str = "file_browser",
        db_path: Optional[Path] = None,
        client: Optional[OpenAI] = None,
    ):
        """Initialize file indexer with FAISS and SQLite.

        Args:
            collection_name: Name of the collection
            db_path: Path to store index and metadata, defaults to ~/.minimal-browser/file_index/
            client: Optional OpenAI client instance
        """
        if not FAISS_AVAILABLE:
            raise ImportError(
                "faiss-cpu is required for FileIndexer; "
                "install with 'uv sync --extra storage'"
            )

        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai is required for embeddings; install with 'uv sync --extra storage'"
            )

        if db_path is None:
            db_path = Path.home() / ".minimal-browser" / "file_index"

        self.db_path = db_path / collection_name
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.client = client or OpenAI()

        self.index: Optional[faiss.IndexFlatIP] = None
        self.id_counter: int = 0

        self._init_sqlite()
        self._load_or_create_index()

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(str(self.db_path / "metadata.db"))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_sqlite(self) -> None:
        """Initialize SQLite metadata table."""
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_metadata (
                    id INTEGER PRIMARY KEY,
                    path TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT,
                    content_hash TEXT
                )
            """)

    def _load_or_create_index(self) -> None:
        """Load existing index or create new one."""
        import faiss

        index_path = self.db_path / "index.faiss"
        counter_path = self.db_path / "counter.json"

        if index_path.exists():
            self.index = faiss.read_index(str(index_path))
        else:
            self.index = faiss.IndexFlatIP(EMBEDDING_DIMENSION)

        if counter_path.exists():
            self.id_counter = json.loads(counter_path.read_text())

    def _save_index(self) -> None:
        """Save index and counter to disk."""
        import faiss

        if self.index is None:
            return

        faiss.write_index(self.index, str(self.db_path / "index.faiss"))
        (self.db_path / "counter.json").write_text(json.dumps(self.id_counter))

    def _get_next_id(self) -> int:
        """Get next available ID and increment counter."""
        current_id = self.id_counter
        self.id_counter += 1
        return current_id

    def index_file(self, path: Path, content: str) -> None:
        """Index a file's content with embeddings.

        Args:
            path: Path to the file
            content: File content to index
        """
        import faiss
        import numpy as np

        if self.index is None:
            return

        try:
            embedding = _get_embedding(content, self.client)
            vector = np.array([embedding], dtype=np.float32)
            faiss.normalize_L2(vector)

            doc_id = self._get_next_id()
            self.index.add(vector)

            with self._get_conn() as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO file_metadata (id, path, name, type, content_hash)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        doc_id,
                        str(path),
                        path.name,
                        mimetypes.guess_type(str(path))[0] or "unknown",
                        str(hash(content)),
                    ),
                )

            self._save_index()
        except Exception as e:
            print(f"Failed to index {path}: {e}")

    def index_directory(
        self, directory: Path, recursive: bool = True, max_files: int = 100
    ) -> int:
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
                    if entry.mime_type and entry.mime_type.startswith(
                        ("text/", "application/json", "application/xml")
                    ):
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
        import faiss
        import numpy as np

        if self.index is None or self.index.ntotal == 0:
            return []

        try:
            embedding = _get_embedding(query, self.client)
            vector = np.array([embedding], dtype=np.float32)
            faiss.normalize_L2(vector)

            n_results = min(n_results, self.index.ntotal)
            distances, indices = self.index.search(vector, n_results)

            matches = []
            with self._get_conn() as conn:
                for idx in indices[0]:
                    cursor = conn.execute(
                        "SELECT path, name, type FROM file_metadata WHERE id = ?",
                        (int(idx),),
                    )
                    row = cursor.fetchone()
                    if row:
                        matches.append(
                            {
                                "path": row["path"],
                                "name": row["name"],
                                "type": row["type"],
                            }
                        )

            return matches
        except Exception as e:
            print(f"Search failed: {e}")
            return []
