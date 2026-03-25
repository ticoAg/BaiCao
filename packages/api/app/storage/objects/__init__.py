from app.core.config import Settings
from app.storage.objects.base import ObjectStorage, StoredObject
from app.storage.objects.memory import InMemoryObjectStorage
from app.storage.objects.minio import MinioObjectStorage

def build_object_storage(settings: Settings) -> ObjectStorage:
    return MinioObjectStorage(
        endpoint=settings.object_storage_endpoint,
        access_key=settings.object_storage_access_key,
        secret_key=settings.object_storage_secret_key,
        secure=settings.object_storage_secure,
    )

__all__ = [
    "build_object_storage",
    "InMemoryObjectStorage",
    "MinioObjectStorage",
    "ObjectStorage",
    "StoredObject",
]
