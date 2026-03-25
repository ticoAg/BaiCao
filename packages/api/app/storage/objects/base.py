from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(slots=True)
class StoredObject:
    bucket: str
    key: str
    size: int
    metadata: dict[str, str] = field(default_factory=dict)
    etag: str | None = None


class ObjectStorage(ABC):
    @abstractmethod
    def ensure_bucket(self, bucket: str) -> None:
        """Create the bucket when it does not already exist."""

    @abstractmethod
    def put_jsonl(
        self,
        *,
        bucket: str,
        key: str,
        content: bytes,
        metadata: dict[str, str] | None = None,
    ) -> StoredObject:
        """Store a JSONL payload and return its persisted metadata."""

    @abstractmethod
    def stat_object(self, bucket: str, key: str) -> StoredObject:
        """Return metadata about a stored object."""

    @abstractmethod
    def get_object(self, bucket: str, key: str) -> bytes:
        """Fetch a previously stored object."""
