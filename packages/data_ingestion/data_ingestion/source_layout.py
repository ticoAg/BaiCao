"""每源一份结构一致的 agent 工作目录。"""

from __future__ import annotations

from pathlib import Path

from data_ingestion.dataset_catalog import Catalog, load_catalog

WORK_PARTITIONS = ("queue", "extracts", "notes")
TRACKED_FILES = ("SOURCE.md", "VIEW.md")


def dataset_root(repo_root: Path) -> Path:
    return repo_root / "datasets/baicao-knowledge"


def catalog_path(repo_root: Path) -> Path:
    return dataset_root(repo_root) / "catalog.json"


def source_dir(repo_root: Path, source_id: str) -> Path:
    return dataset_root(repo_root) / "sources" / source_id


def work_dir(repo_root: Path, source_id: str) -> Path:
    return source_dir(repo_root, source_id) / "work"


def processed_latest_dir(repo_root: Path, source_id: str) -> Path:
    return source_dir(repo_root, source_id) / "processed" / "latest"


def load_repo_catalog(repo_root: Path) -> Catalog:
    return load_catalog(catalog_path(repo_root))


def ensure_source_layout(repo_root: Path, source_id: str) -> Path:
    root = source_dir(repo_root, source_id)
    root.mkdir(parents=True, exist_ok=True)
    processed_latest_dir(repo_root, source_id).mkdir(parents=True, exist_ok=True)
    work = work_dir(repo_root, source_id)
    for name in WORK_PARTITIONS:
        (work / name).mkdir(parents=True, exist_ok=True)
    return root


def ensure_catalog_layouts(repo_root: Path) -> list[str]:
    catalog = load_repo_catalog(repo_root)
    ids = [item.source_id for item in catalog.sources]
    for source_id in ids:
        ensure_source_layout(repo_root, source_id)
    return ids


def validate_source_layout(repo_root: Path, source_id: str) -> list[str]:
    errors: list[str] = []
    root = source_dir(repo_root, source_id)
    for name in TRACKED_FILES:
        if not (root / name).is_file():
            errors.append(f"{source_id} missing {name}")
    work = work_dir(repo_root, source_id)
    for name in WORK_PARTITIONS:
        if not (work / name).is_dir():
            errors.append(f"{source_id} missing work/{name}")
    if not processed_latest_dir(repo_root, source_id).is_dir():
        errors.append(f"{source_id} missing processed/latest")
    return errors


def validate_catalog_layouts(repo_root: Path) -> list[str]:
    catalog = load_repo_catalog(repo_root)
    errors: list[str] = []
    for item in catalog.sources:
        errors.extend(validate_source_layout(repo_root, item.source_id))
    return errors
