from pathlib import Path

import pytest

from data_ingestion.dataset_catalog import load_catalog
from data_ingestion.source_layout import (
    catalog_path,
    dataset_root,
    ensure_catalog_layouts,
    processed_latest_dir,
    validate_catalog_layouts,
    work_dir,
)

REPO = Path(__file__).resolve().parents[3]


@pytest.mark.skipif(
    not catalog_path(REPO).is_file(),
    reason="local dataset staging missing",
)
def test_catalog_sources_have_consistent_agent_layout():
    catalog = load_catalog(catalog_path(REPO))
    assert catalog.sources, "catalog must list sources"
    ids = ensure_catalog_layouts(REPO)
    catalog_ids = [item.source_id for item in catalog.sources]
    assert ids == catalog_ids
    errors = validate_catalog_layouts(REPO)
    assert errors == []
    for item in catalog.sources:
        root = dataset_root(REPO)
        assert (root / item.paths["source_doc"]).is_file()
        assert (root / item.paths["view"]).is_file()
        assert work_dir(REPO, item.source_id).is_dir()
        assert processed_latest_dir(REPO, item.source_id).is_dir()
