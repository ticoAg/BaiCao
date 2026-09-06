"""校验 catalog 并上传 private Hugging Face dataset。"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from data_ingestion.dataset_catalog import (
    CatalogError,
    DEFAULT_DATASET_ID,
    RELEASE_PUBLIC,
    RELEASE_RESTRICTED,
    load_catalog,
)

METADATA_NAMES = {"README.md", "catalog.json", "SOURCE.md", "VIEW.md", "ledger.json"}


class PublishError(ValueError):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def plan_upload(dataset_root: Path) -> list[Path]:
    catalog_path = dataset_root / "catalog.json"
    try:
        load_catalog(catalog_path)
    except CatalogError as exc:
        raise PublishError(str(exc)) from exc
    selected: list[Path] = []
    for path in dataset_root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(dataset_root)
        parts = relative.parts
        if relative.suffix == ".jsonl":
            continue
        if parts[0] == "exports" or "exports" in parts:
            continue
        if "work" in parts or "processed" in parts:
            continue
        if "source" in parts and path.name != "SOURCE.md":
            continue
        if parts[0] == "data" and relative.suffix == ".parquet":
            if len(parts) == 3 and parts[1] in {RELEASE_PUBLIC, RELEASE_RESTRICTED}:
                selected.append(path)
            continue
        if path.name in METADATA_NAMES or (parts[0] == "tasks" and relative.suffix in {".md", ".json"}):
            selected.append(path)
    return sorted(selected)


def upload_dataset(dataset_root: Path, repo_id: str, token: str | None) -> None:
    from huggingface_hub import HfApi

    catalog = load_catalog(dataset_root / "catalog.json")
    files = plan_upload(dataset_root)
    api = HfApi(token=token)
    private = catalog.visibility == "private"
    api.create_repo(repo_id=repo_id, repo_type="dataset", private=private, exist_ok=True)
    api.update_repo_settings(repo_id=repo_id, repo_type="dataset", private=private)
    allow_patterns = [path.relative_to(dataset_root).as_posix() for path in files]
    api.upload_folder(
        folder_path=str(dataset_root),
        repo_id=repo_id,
        repo_type="dataset",
        allow_patterns=allow_patterns,
        delete_patterns="*",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=None)
    parser.add_argument("--repo-id", default=os.environ.get("BAICAO_HF_DATASET_ID") or DEFAULT_DATASET_ID)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    dataset_root = (args.dataset_root or (repo_root() / "datasets/baicao-knowledge")).resolve()
    files = plan_upload(dataset_root)
    payload = {
        "ok": True,
        "dry_run": args.dry_run,
        "repo_id": args.repo_id,
        "file_count": len(files),
        "files": [path.relative_to(dataset_root).as_posix() for path in files],
    }
    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    upload_dataset(dataset_root, args.repo_id, os.environ.get("HF_TOKEN"))
    print(json.dumps({**payload, "uploaded": True, "url": f"https://huggingface.co/datasets/{args.repo_id}"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
