import zipfile
from pathlib import Path

import pytest

from app.pipeline.materialization import SourceMaterializationService


def build_zip(path, files: dict[str, str]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)


@pytest.mark.asyncio
async def test_materialize_uploaded_zip_extracts_archive(tmp_path):
    service = SourceMaterializationService(storage_root=str(tmp_path))
    uploaded = tmp_path / "uploads" / "dataset.zip"
    uploaded.parent.mkdir(parents=True, exist_ok=True)
    build_zip(
        uploaded,
        {
            "README.md": "# demo\n",
            "data.jsonl": '{"name":"陈皮"}\n',
        },
    )

    result = await service.materialize(
        run_id="pipeline-1",
        source_type="local_upload",
        source_input={
            "upload_token": uploaded.name,
            "stored_path": str(uploaded),
        },
    )

    assert result.is_archive is True
    assert result.archive_format == "zip"
    assert result.readme_path is not None
    assert result.readme_path.endswith("README.md")
    assert any(path.endswith("data.jsonl") for path in result.candidate_files)


@pytest.mark.asyncio
async def test_materialize_huggingface_repo_returns_repo_urls(tmp_path):
    service = SourceMaterializationService(storage_root=str(tmp_path))

    result = service.build_huggingface_metadata("ZJUFanLab/TCMChat-dataset-600k")

    assert result["repo_url"] == "https://huggingface.co/datasets/ZJUFanLab/TCMChat-dataset-600k"
    assert result["readme_url"] == "https://huggingface.co/datasets/ZJUFanLab/TCMChat-dataset-600k/resolve/main/README.md"


@pytest.mark.asyncio
async def test_materialize_remote_url_downloads_into_cache_and_extracts(tmp_path, monkeypatch):
    service = SourceMaterializationService(storage_root=str(tmp_path))
    fixture_zip = tmp_path / "fixture.zip"
    build_zip(
        fixture_zip,
        {
            "README.md": "# remote\n",
            "records.csv": "node_name,source\n陈皮,本草纲目\n",
        },
    )

    def fake_download(url: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(fixture_zip.read_bytes())

    monkeypatch.setattr(service, "_download_remote_url", fake_download)

    result = await service.materialize(
        run_id="pipeline-remote",
        source_type="remote_url",
        source_input={"url": "https://example.com/dataset.zip"},
    )

    assert result.cache_hit is False
    assert result.is_archive is True
    assert result.readme_content == "# remote\n"
    assert any(path.endswith("records.csv") for path in result.candidate_files)


@pytest.mark.asyncio
async def test_materialize_huggingface_repo_populates_cache_and_workdir(tmp_path, monkeypatch):
    service = SourceMaterializationService(
        storage_root=str(tmp_path / "tmp/data"),
        huggingface_cache_root=str(tmp_path / ".cache" / "huggingface"),
    )

    def fake_snapshot(repo_id: str, cache_dir: Path) -> None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "README.md").write_text("# hf repo\n", encoding="utf-8")
        (cache_dir / "data.jsonl").write_text('{"name":"陈皮"}\n', encoding="utf-8")

    monkeypatch.setattr(service, "_download_huggingface_repo", fake_snapshot)

    result = await service.materialize(
        run_id="pipeline-hf",
        source_type="huggingface_repo",
        source_input={"repo_id": "ZJUFanLab/TCMChat-dataset-600k"},
    )

    assert result.repo_url == "https://huggingface.co/datasets/ZJUFanLab/TCMChat-dataset-600k"
    assert result.readme_content == "# hf repo\n"
    assert any(path.endswith("data.jsonl") for path in result.candidate_files)
    assert Path(result.source_dir).resolve() != (tmp_path / ".cache" / "huggingface" / "ZJUFanLab/TCMChat-dataset-600k").resolve()


@pytest.mark.asyncio
async def test_materialize_huggingface_repo_skips_hub_internal_cache_dir(tmp_path, monkeypatch):
    service = SourceMaterializationService(
        storage_root=str(tmp_path / "tmp/data"),
        huggingface_cache_root=str(tmp_path / ".cache" / "huggingface"),
    )

    def fake_snapshot(repo_id: str, cache_dir: Path) -> None:
        (cache_dir / ".cache" / "huggingface" / "download").mkdir(parents=True, exist_ok=True)
        (cache_dir / ".cache" / "huggingface" / "download" / "README.md.metadata").write_text("meta", encoding="utf-8")
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "README.md").write_text("# hf repo\n", encoding="utf-8")
        (cache_dir / "data.jsonl").write_text('{"name":"陈皮"}\n', encoding="utf-8")

    monkeypatch.setattr(service, "_download_huggingface_repo", fake_snapshot)

    result = await service.materialize(
        run_id="pipeline-hf-clean",
        source_type="huggingface_repo",
        source_input={"repo_id": "ZJUFanLab/TCMChat-dataset-600k"},
    )

    source_dir = Path(result.source_dir)
    assert not (source_dir / ".cache").exists()
    assert (source_dir / "README.md").exists()
