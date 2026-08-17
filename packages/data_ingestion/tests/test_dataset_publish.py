import json
from pathlib import Path

import pytest

from data_ingestion.cli.dataset_publish import PublishError, plan_upload


def _write_private_catalog(root: Path, visibility: str = "private") -> None:
    catalog = {
        "dataset_id": "ticoAg/baicao-knowledge",
        "visibility": visibility,
        "knowledge_model": "packages/knowledge_model",
        "updated_at": "2026-08-17",
        "sources": [
            {
                "source_id": "daoyi-suyang",
                "title": "道医苏子阳",
                "status": "imported",
                "kind": "narrative_medical_cases",
                "filter": {
                    "source_provider": "manual",
                    "dataset_name": "baicao-knowledge",
                    "file_path": "sources/daoyi-suyang/source/道医苏子阳.md",
                    "import_scope_key": "manual:baicao-knowledge:daoyi-suyang",
                },
                "planned": {"unit": "chapters", "count": 389},
                "completed": {"unit": "chapters", "count": 389},
                "paths": {
                    "source_doc": "sources/daoyi-suyang/SOURCE.md",
                    "view": "sources/daoyi-suyang/VIEW.md",
                },
            }
        ],
    }
    (root / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")


def test_plan_upload_rejects_public(tmp_path: Path):
    _write_private_catalog(tmp_path, visibility="public")
    with pytest.raises(PublishError, match="private"):
        plan_upload(tmp_path)


def test_plan_upload_excludes_payloads(tmp_path: Path):
    _write_private_catalog(tmp_path)
    (tmp_path / "README.md").write_text("# baicao-knowledge\n", encoding="utf-8")
    (tmp_path / "tasks").mkdir()
    (tmp_path / "tasks" / "ledger.json").write_text("{}", encoding="utf-8")
    source_dir = tmp_path / "sources" / "daoyi-suyang"
    source_dir.mkdir(parents=True)
    (source_dir / "SOURCE.md").write_text("# SOURCE\n", encoding="utf-8")
    (source_dir / "VIEW.md").write_text("# VIEW\n", encoding="utf-8")
    (source_dir / "source").mkdir()
    (source_dir / "source" / "道医苏子阳.md").write_text("novel body\n", encoding="utf-8")
    processed = source_dir / "processed" / "latest"
    processed.mkdir(parents=True)
    (processed / "records.jsonl").write_text("{}\n", encoding="utf-8")
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "records.parquet").write_bytes(b"PAR1")
    (tmp_path / "exports").mkdir()
    (tmp_path / "exports" / "graph-zh-live.json").write_text("{}", encoding="utf-8")

    files = plan_upload(tmp_path)
    relative = {str(path.relative_to(tmp_path)) for path in files}
    assert "catalog.json" in relative
    assert "README.md" in relative
    assert "sources/daoyi-suyang/SOURCE.md" in relative
    assert "sources/daoyi-suyang/VIEW.md" in relative
    assert "tasks/ledger.json" in relative
    assert "data/records.parquet" in relative
    assert not any(name.endswith(".jsonl") for name in relative)
    assert not any(
        "source/" in name and name.endswith(".md") and "SOURCE.md" not in name for name in relative
    )
    assert not any(name.startswith("exports/") for name in relative)
