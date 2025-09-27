"""Persistent conversation logging utilities."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List

from .utils import ensure_dir, read_json, write_json


ConversationEntry = Dict[str, str]


class ConversationLog:
    """Simple JSON-backed conversation history store."""

    def __init__(self, path: str | Path, *, max_entries: int = 500) -> None:
        self.path = Path(path)
        ensure_dir(self.path.parent)
        self.max_entries = max_entries
        self._entries: List[ConversationEntry] = self._load()

    def _load(self) -> List[ConversationEntry]:
        if self.path.exists():
            data = read_json(self.path)
            if isinstance(data, list):  # defensive
                return [entry for entry in data if isinstance(entry, dict)]
        return []

    @property
    def entries(self) -> List[ConversationEntry]:
        return list(self._entries)

    def append(self, query: str, response: str) -> None:
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "response": response,
        }
        self._entries.append(entry)
        self.compact()
        self.save()

    def extend(self, items: Iterable[ConversationEntry]) -> None:
        for item in items:
            if isinstance(item, dict):
                self._entries.append(item)
        self.compact()
        self.save()

    def compact(self) -> None:
        if len(self._entries) > self.max_entries:
            overflow = len(self._entries) - self.max_entries
            if overflow > 0:
                del self._entries[:overflow]

    def clear(self) -> None:
        self._entries.clear()
        self.save()

    def save(self) -> None:
        write_json(self.path, self._entries)
        pass  # Placeholder for future implementation
