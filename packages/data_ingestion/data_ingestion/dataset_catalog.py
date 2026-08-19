"""数据集 catalog / ledger 契约。"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

DEFAULT_DATASET_ID = "ticoAg/baicao-knowledge"


class CatalogError(ValueError):
    pass


class SourceFilter(BaseModel):
    source_provider: str
    dataset_name: str
    file_path: str
    import_scope_key: str


class CatalogSource(BaseModel):
    model_config = ConfigDict(extra="allow")

    source_id: str
    title: str
    status: str
    kind: str
    publish: bool = False
    filter: SourceFilter
    planned: dict
    completed: dict
    paths: dict


class Catalog(BaseModel):
    model_config = ConfigDict(extra="allow")

    dataset_id: str
    visibility: str
    knowledge_model: str
    updated_at: str
    sources: list[CatalogSource] = Field(default_factory=list)

    def source(self, source_id: str) -> CatalogSource:
        for item in self.sources:
            if item.source_id == source_id:
                return item
        raise CatalogError(f"unknown source_id: {source_id}")


class LedgerTask(BaseModel):
    model_config = ConfigDict(extra="allow")

    task_id: str
    source_id: str
    status: str
    unit: str
    planned_units: int | None = None
    completed_units: int | None = None


class Ledger(BaseModel):
    model_config = ConfigDict(extra="allow")

    updated_at: str
    repo_plan: str | None = None
    tasks: list[LedgerTask] = Field(default_factory=list)


def load_catalog(path: Path) -> Catalog:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"invalid catalog: {path}: {exc}") from exc
    catalog = Catalog.model_validate(raw)
    if catalog.visibility not in {"private", "public"}:
        raise CatalogError("visibility must be private or public")
    if catalog.dataset_id != DEFAULT_DATASET_ID:
        raise CatalogError(f"dataset_id must be {DEFAULT_DATASET_ID}")
    return catalog


def load_ledger(path: Path, catalog: Catalog) -> Ledger:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"invalid ledger: {path}: {exc}") from exc
    ledger = Ledger.model_validate(raw)
    known = {item.source_id for item in catalog.sources}
    for task in ledger.tasks:
        if task.source_id not in known:
            raise CatalogError(f"unknown source_id: {task.source_id}")
    return ledger
