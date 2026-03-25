from __future__ import annotations

from io import BytesIO
from typing import cast

from minio import Minio

from app.storage.objects.base import ObjectStorage, StoredObject


class MinioObjectStorage(ObjectStorage):
    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool = False,
    ) -> None:
        self._client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

    def ensure_bucket(self, bucket: str) -> None:
        if not self._client.bucket_exists(bucket):
            self._client.make_bucket(bucket)

    def put_jsonl(
        self,
        *,
        bucket: str,
        key: str,
        content: bytes,
        metadata: dict[str, str] | None = None,
    ) -> StoredObject:
        self.ensure_bucket(bucket)
        object_metadata = cast(dict[str, str | list[str] | tuple[str]] | None, dict(metadata or {}))
        result = self._client.put_object(
            bucket,
            key,
            data=BytesIO(content),
            length=len(content),
            content_type="application/x-ndjson",
            metadata=object_metadata,
        )
        return StoredObject(
            bucket=bucket,
            key=key,
            size=len(content),
            metadata=dict(metadata or {}),
            etag=result.etag,
        )

    def stat_object(self, bucket: str, key: str) -> StoredObject:
        stat = self._client.stat_object(bucket, key)
        raw_metadata = dict(stat.metadata or {})
        metadata = {str(k): str(v) for k, v in raw_metadata.items()}
        return StoredObject(
            bucket=bucket,
            key=key,
            size=int(stat.size or 0),
            metadata=metadata,
            etag=stat.etag,
        )

    def get_object(self, bucket: str, key: str) -> bytes:
        response = self._client.get_object(bucket, key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()
