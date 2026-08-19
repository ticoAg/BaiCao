import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from data_ingestion.cli.dataset_publish import plan_upload, upload_dataset


def _write_catalog(root: Path, visibility: str = "private") -> None:
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


def test_plan_upload_accepts_public(tmp_path: Path):
    _write_catalog(tmp_path, visibility="public")
    assert plan_upload(tmp_path) == [tmp_path / "catalog.json"]


def test_plan_upload_excludes_payloads(tmp_path: Path):
    _write_catalog(tmp_path)
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


def test_upload_dataset_replaces_remote_contents(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _write_catalog(tmp_path, visibility="public")
    api = MagicMock()
    monkeypatch.setitem(sys.modules, "huggingface_hub", SimpleNamespace(HfApi=MagicMock(return_value=api)))

    upload_dataset(tmp_path, "ticoAg/baicao-knowledge", None)

    api.create_repo.assert_called_once_with(
        repo_id="ticoAg/baicao-knowledge", repo_type="dataset", private=False, exist_ok=True
    )
    api.update_repo_settings.assert_called_once_with(
        repo_id="ticoAg/baicao-knowledge", repo_type="dataset", private=False
    )
    api.upload_folder.assert_called_once_with(
        folder_path=str(tmp_path),
        repo_id="ticoAg/baicao-knowledge",
        repo_type="dataset",
        allow_patterns=["catalog.json"],
        delete_patterns="*",
    )
