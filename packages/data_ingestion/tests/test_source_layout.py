from pathlib import Path

from data_ingestion.dataset_catalog import load_catalog
from data_ingestion.source_layout import (
    catalog_path,
    dataset_root,
    ensure_catalog_layouts,
    processed_latest_dir,
    validate_catalog_layouts,
    work_dir,
)


def test_catalog_sources_have_consistent_agent_layout():
    repo = Path(__file__).resolve().parents[3]
    catalog = load_catalog(catalog_path(repo))
    assert catalog.sources, "catalog must list sources"
    ids = ensure_catalog_layouts(repo)
    catalog_ids = [item.source_id for item in catalog.sources]
    assert ids == catalog_ids
    errors = validate_catalog_layouts(repo)
    assert errors == []
    for item in catalog.sources:
        root = dataset_root(repo)
        assert (root / item.paths["source_doc"]).is_file()
        assert (root / item.paths["view"]).is_file()
        assert work_dir(repo, item.source_id).is_dir()
        assert processed_latest_dir(repo, item.source_id).is_dir()
