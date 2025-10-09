"""Bookmark storage and management."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal, Optional
from pydantic import BaseModel, Field, StringConstraints

from .utils import ensure_dir, read_json, write_json


class Bookmark(BaseModel):
    """Represents a single bookmark entry."""

    id: str = Field(description="Unique identifier for the bookmark")
    title: str = Field(description="Human-readable title for the bookmark")
    url: str = Field(description="URL or file path being bookmarked")
    content: Optional[str] = Field(default=None, description="Snippet or content excerpt")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    bookmark_type: Literal["url", "snippet", "file"] = Field(
        default="url", description="Type of bookmark"
    )
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Additional metadata"
    )

    def matches_query(self, query: str) -> bool:
        """Check if this bookmark matches a search query."""
        query_lower = query.lower()
        return (
            query_lower in self.title.lower()
            or query_lower in self.url.lower()
            or (self.content and query_lower in self.content.lower())
            or any(query_lower in tag.lower() for tag in self.tags)
        )


class BookmarkStore:
    """JSON-backed bookmark storage with search capabilities."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        ensure_dir(self.path.parent)
        self._bookmarks: dict[str, Bookmark] = self._load()

    def _load(self) -> dict[str, Bookmark]:
        """Load bookmarks from disk."""
        if self.path.exists():
            data = read_json(self.path)
            if isinstance(data, list):  # Support both list and dict formats
                return {bm["id"]: Bookmark(**bm) for bm in data if isinstance(bm, dict)}
            elif isinstance(data, dict):
                return {k: Bookmark(**v) for k, v in data.items()}
        return {}

    def save(self) -> None:
        """Persist bookmarks to disk."""
        # Save as list for better JSON compatibility
        bookmark_list = [bm.model_dump(mode="python") for bm in self._bookmarks.values()]
        write_json(self.path, bookmark_list)

    def add(self, bookmark: Bookmark) -> None:
        """Add or update a bookmark."""
        bookmark.updated_at = datetime.utcnow()
        self._bookmarks[bookmark.id] = bookmark
        self.save()

    def remove(self, bookmark_id: str) -> bool:
        """Remove a bookmark by ID. Returns True if removed, False if not found."""
        if bookmark_id in self._bookmarks:
            del self._bookmarks[bookmark_id]
            self.save()
            return True
        return False

    def get(self, bookmark_id: str) -> Optional[Bookmark]:
        """Retrieve a bookmark by ID."""
        return self._bookmarks.get(bookmark_id)

    def list_all(self) -> list[Bookmark]:
        """Return all bookmarks sorted by creation date."""
        return sorted(
            self._bookmarks.values(), key=lambda b: b.created_at, reverse=True
        )

    def search(self, query: str) -> list[Bookmark]:
        """Search bookmarks by query string."""
        if not query:
            return self.list_all()
        
        results = [bm for bm in self._bookmarks.values() if bm.matches_query(query)]
        return sorted(results, key=lambda b: b.updated_at, reverse=True)

    def search_by_tag(self, tag: str) -> list[Bookmark]:
        """Find all bookmarks with a specific tag."""
        results = [
            bm for bm in self._bookmarks.values() if tag.lower() in (t.lower() for t in bm.tags)
        ]
        return sorted(results, key=lambda b: b.updated_at, reverse=True)

    def get_all_tags(self) -> list[str]:
        """Return all unique tags across bookmarks."""
        tags = set()
        for bm in self._bookmarks.values():
            tags.update(bm.tags)
        return sorted(tags)

    def clear(self) -> None:
        """Remove all bookmarks."""
        self._bookmarks.clear()
        self.save()
