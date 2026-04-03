"""Lightweight storage implementations using local files, SQLite, and FAISS."""

from __future__ import annotations

import json
import os
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


class ObjectStorage:
    """Local file-based object storage."""

    def __init__(self, bucket_name: str, base_path: Optional[Path] = None):
        """Initialize object storage with a local directory.

        Args:
            bucket_name: Name of the "bucket" (subdirectory)
            base_path: Base directory for storage, defaults to ~/.minimal-browser/storage
        """
        if base_path is None:
            base_path = Path.home() / ".minimal-browser" / "storage"

        self.base_path = base_path / bucket_name
        self.base_path.mkdir(parents=True, exist_ok=True)

    def upload(self, key: str, data: bytes) -> None:
        """Store data as a file.

        Args:
            key: Object key (will be used as filename)
            data: Binary data to store
        """
        file_path = self.base_path / key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)

    def download(self, key: str) -> bytes:
        """Retrieve data from a file.

        Args:
            key: Object key (filename)

        Returns:
            Binary data stored at key

        Raises:
            FileNotFoundError: If key does not exist
        """
        file_path = self.base_path / key
        return file_path.read_bytes()


class KVStorage:
    """SQLite-based key-value storage."""

    def __init__(self, table_name: str, db_path: Optional[Path] = None):
        """Initialize KV storage with SQLite backend.

        Args:
            table_name: Name of the table to use
            db_path: Path to SQLite database, defaults to ~/.minimal-browser/kv.db
        """
        if db_path is None:
            db_path = Path.home() / ".minimal-browser" / "kv.db"

        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self.table_name = table_name
        self._init_table()

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_table(self) -> None:
        """Create table if it doesn't exist."""
        with self._get_conn() as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

    def put_item(self, item: Dict[str, Any]) -> None:
        """Store an item in the database.

        Args:
            item: Dictionary with 'key' and 'value' keys
        """
        key = item.get("key", "")
        value = json.dumps(item)

        with self._get_conn() as conn:
            conn.execute(
                f"INSERT OR REPLACE INTO {self.table_name} (key, value) VALUES (?, ?)",
                (key, value),
            )

    def get_item(self, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieve an item by key.

        Args:
            key: Dictionary containing the key to look up

        Returns:
            Item dictionary if found, None otherwise
        """
        key_value = key.get("key", "")

        with self._get_conn() as conn:
            cursor = conn.execute(
                f"SELECT value FROM {self.table_name} WHERE key = ?", (key_value,)
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row["value"])
        return None


class VectorStorage:
    """FAISS-based vector storage with OpenAI embeddings."""

    def __init__(
        self,
        collection_name: str,
        db_path: Optional[Path] = None,
        client: Optional[OpenAI] = None,
    ):
        """Initialize vector storage with FAISS backend.

        Args:
            collection_name: Name of the collection
            db_path: Path to store index and metadata, defaults to ~/.minimal-browser/vectors/
            client: Optional OpenAI client instance
        """
        if not FAISS_AVAILABLE:
            raise ImportError(
                "faiss-cpu is required for VectorStorage; "
                "install with 'uv sync --extra storage'"
            )

        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai is required for embeddings; install with 'uv sync --extra storage'"
            )

        if db_path is None:
            db_path = Path.home() / ".minimal-browser" / "vectors"

        self.db_path = db_path / collection_name
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.client = client or OpenAI()

        self.index: Optional[faiss.IndexFlatIP] = None
        self.metadata: Dict[int, Dict[str, Any]] = {}
        self.id_counter: int = 0

        self._load_or_create_index()

    def _load_or_create_index(self) -> None:
        """Load existing index or create new one."""
        import faiss

        index_path = self.db_path / "index.faiss"
        meta_path = self.db_path / "metadata.json"
        counter_path = self.db_path / "counter.json"

        if index_path.exists():
            self.index = faiss.read_index(str(index_path))
        else:
            self.index = faiss.IndexFlatIP(EMBEDDING_DIMENSION)

        if meta_path.exists():
            self.metadata = json.loads(meta_path.read_text())
            self.metadata = {int(k): v for k, v in self.metadata.items()}

        if counter_path.exists():
            self.id_counter = json.loads(counter_path.read_text())

    def _save(self) -> None:
        """Save index and metadata to disk."""
        import faiss

        if self.index is None:
            return

        faiss.write_index(self.index, str(self.db_path / "index.faiss"))
        (self.db_path / "metadata.json").write_text(json.dumps(self.metadata))
        (self.db_path / "counter.json").write_text(json.dumps(self.id_counter))

    def add_vector(self, text: str, metadata: Dict[str, Any]) -> None:
        """Add a vector with associated metadata.

        Args:
            text: Text to embed and store
            metadata: Metadata associated with the vector
        """
        import faiss
        import numpy as np

        if self.index is None:
            return

        embedding = _get_embedding(text, self.client)
        vector = np.array([embedding], dtype=np.float32)

        faiss.normalize_L2(vector)
        self.index.add(vector)

        self.metadata[self.id_counter] = metadata
        self.id_counter += 1

        self._save()

    def query(self, query_text: str, n_results: int = 5) -> Dict[str, Any]:
        """Query for similar vectors.

        Args:
            query_text: Text to search for
            n_results: Number of results to return

        Returns:
            Dictionary with 'metadatas' and 'distances' keys
        """
        import faiss
        import numpy as np

        if self.index is None or self.index.ntotal == 0:
            return {"metadatas": [[]], "distances": [[]]}

        embedding = _get_embedding(query_text, self.client)
        vector = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(vector)

        n_results = min(n_results, self.index.ntotal)
        distances, indices = self.index.search(vector, n_results)

        metadatas = [
            self.metadata.get(int(idx), {})
            for idx in indices[0]
            if int(idx) in self.metadata
        ]

        return {"metadatas": [metadatas], "distances": [distances[0].tolist()]}
