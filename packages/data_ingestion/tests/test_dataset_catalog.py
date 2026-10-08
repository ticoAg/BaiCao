import json
from pathlib import Path

import pytest

from data_ingestion.dataset_catalog import CatalogError, load_catalog, load_ledger

REPO = Path(__file__).resolve().parents[3]


def write_catalog(path: Path, **overrides) -> Path:
    body = {
        "dataset_id": "ticoAg/baicao-knowledge",
        "visibility": "private",
        "knowledge_model": "packages/knowledge_model",
        "updated_at": "2026-08-17",
        "sources": [
            {
                "source_id": "national-standard-2022-pharmacopoeia",
                "title": "2022年中药药典",
                "status": "imported",
                "kind": "pharmacopoeia_entries",
                "publish": True,
                "filter": {
                    "source_provider": "huggingface",
                    "dataset_name": "ZJUFanLab/TCMChat-dataset-600k",
                    "file_path": "pretrain/train/books/national_standard/2022年中药药典.txt",
                    "import_scope_key": "huggingface|ZJUFanLab/TCMChat-dataset-600k|pretrain/train/books/national_standard/2022年中药药典.txt",
                },
                "planned": {"unit": "entries", "count": 605},
                "completed": {"unit": "entries", "count": 605},
                "paths": {
                    "source_doc": "sources/national-standard-2022-pharmacopoeia/SOURCE.md",
                    "view": "sources/national-standard-2022-pharmacopoeia/VIEW.md",
                },
            },
            {
                "source_id": "daoyi-suyang",
                "title": "道医苏子阳",
                "status": "imported",
                "kind": "narrative_medical_cases",
                "publish": True,
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
            },
        ],
    }
    body.update(overrides)
    path.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
    return path


def test_load_catalog_locks_private_and_two_sources(tmp_path: Path):
    catalog = load_catalog(write_catalog(tmp_path / "catalog.json"))
    assert catalog.dataset_id == "ticoAg/baicao-knowledge"
    assert catalog.visibility == "private"
    assert {item.source_id for item in catalog.sources} == {
        "national-standard-2022-pharmacopoeia",
        "daoyi-suyang",
    }
    assert catalog.source("daoyi-suyang").filter.import_scope_key == (
        "manual:baicao-knowledge:daoyi-suyang"
    )
    assert all(source.publish for source in catalog.sources)


def test_accept_public_visibility(tmp_path: Path):
    path = write_catalog(tmp_path / "catalog.json", visibility="public")
    assert load_catalog(path).visibility == "public"


def test_reject_unknown_visibility(tmp_path: Path):
    path = write_catalog(tmp_path / "catalog.json", visibility="internal")
    with pytest.raises(CatalogError, match="private or public"):
        load_catalog(path)


def test_ledger_tasks_must_reference_known_sources(tmp_path: Path):
    catalog = load_catalog(write_catalog(tmp_path / "catalog.json"))
    ledger_path = tmp_path / "ledger.json"
    ledger_path.write_text(
        json.dumps(
            {
                "updated_at": "2026-08-17",
                "repo_plan": "docs/architecture/knowledge-dataset.md",
                "tasks": [
                    {
                        "task_id": "ghost",
                        "source_id": "not-a-source",
                        "status": "done",
                        "unit": "entries",
                        "planned_units": 1,
                        "completed_units": 1,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    with pytest.raises(CatalogError, match="not-a-source"):
        load_ledger(ledger_path, catalog)


@pytest.mark.skipif(
    not (REPO / "datasets/baicao-knowledge/catalog.json").exists(),
    reason="local dataset staging missing",
)
def test_repo_catalog_matches_known_sources():
    catalog = load_catalog(REPO / "datasets/baicao-knowledge/catalog.json")
    assert catalog.visibility == "private"
    assert catalog.dataset_id == "ticoAg/baicao-knowledge"
    assert {source.release_tier for source in catalog.sources} == {"public", "restricted"}
    assert all(source.license_status for source in catalog.sources)
    assert all(source.release_tier == ("public" if source.publish else "restricted") for source in catalog.sources)
