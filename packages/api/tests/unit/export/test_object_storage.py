from app.core.config import Settings
from app.storage.objects.memory import InMemoryObjectStorage


def test_memory_object_storage_puts_jsonl_bytes():
    storage = InMemoryObjectStorage()
    payload = b'{"node_name":"\xe9\x99\x88\xe7\x9a\xae"}\n'

    result = storage.put_jsonl(
        bucket="pipeline-exports",
        key="run-1/export-1/snapshot.jsonl",
        content=payload,
        metadata={"run_id": "run-1"},
    )

    assert result.bucket == "pipeline-exports"
    assert result.key == "run-1/export-1/snapshot.jsonl"
    assert result.size == len(payload)
    assert storage.get_object("pipeline-exports", "run-1/export-1/snapshot.jsonl") == payload


def test_settings_expose_object_storage_defaults():
    settings = Settings()

    assert settings.object_storage_endpoint == "localhost:19000"
    assert settings.object_storage_bucket == "baicao-pipeline-exports"
    assert settings.object_storage_secure is False
