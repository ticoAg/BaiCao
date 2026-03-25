from __future__ import annotations

from app.storage.objects.base import ObjectStorage, StoredObject


class InMemoryObjectStorage(ObjectStorage):
    def __init__(self) -> None:
        self._buckets: set[str] = set()
        self._objects: dict[tuple[str, str], tuple[bytes, StoredObject]] = {}

    def ensure_bucket(self, bucket: str) -> None:
        self._buckets.add(bucket)

    def put_jsonl(
        self,
        *,
        bucket: str,
        key: str,
        content: bytes,
        metadata: dict[str, str] | None = None,
    ) -> StoredObject:
        self.ensure_bucket(bucket)
        stored = StoredObject(
            bucket=bucket,
            key=key,
            size=len(content),
            metadata=dict(metadata or {}),
        )
        self._objects[(bucket, key)] = (content, stored)
        return stored

    def stat_object(self, bucket: str, key: str) -> StoredObject:
        try:
            _, stored = self._objects[(bucket, key)]
        except KeyError as exc:
            raise FileNotFoundError(f"Object not found: {bucket}/{key}") from exc
        return stored

    def get_object(self, bucket: str, key: str) -> bytes:
        try:
            content, _ = self._objects[(bucket, key)]
        except KeyError as exc:
            raise FileNotFoundError(f"Object not found: {bucket}/{key}") from exc
        return content
